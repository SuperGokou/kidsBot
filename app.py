#!/usr/bin/env python3
"""
KidBot Chat Interface

Kid-friendly chat interface with voice verification.
Run with: streamlit run app.py
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

import streamlit as st

from core.response_parser import parse_response
from core.utils import load_config, safe_remove_file, DEFAULT_TTS_VOICE
from ui.views.settings_view import render_settings_view
from ui.styles import CUSTOM_CSS
from ui.components import (
    HTML_GRADIENT_BLOBS,
    HTML_HEADER,
    get_robot_html,
    get_sidebar_html,
)


# =============================================================================
# Mode Greetings for Sidebar Switching
# =============================================================================
MODE_GREETINGS = {
    "chat": "I'm back! What do you want to chat about?",
    "story": "Story mode activated! Should I tell you a fairy tale?",
    "learning": "Hi! We are in study mode now. What do you want to learn?",
    "game": "Game mode on! Let's play a game!"
}


# Microphone icon SVG
SVG_MICROPHONE = """
<svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" stroke-width="2" fill="none">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
</svg>
"""


# =============================================================================
# Helper Functions
# =============================================================================

# load_config is imported from core.utils


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "gatekeeper" not in st.session_state:
        st.session_state.gatekeeper = None
    if "memory_manager" not in st.session_state:
        st.session_state.memory_manager = None
    if "llm_client" not in st.session_state:
        st.session_state.llm_client = None
    if "tts_enabled" not in st.session_state:
        st.session_state.tts_enabled = True
    if "play_audio" not in st.session_state:
        st.session_state.play_audio = False
    if "current_view" not in st.session_state:
        st.session_state.current_view = "chat"  # "chat" or "settings"
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = "chat"  # "chat", "story", "learning", "game"

    # Continuous conversation (Jarvis mode) state
    if "is_listening_active" not in st.session_state:
        st.session_state.is_listening_active = False
    if "jarvis_phase" not in st.session_state:
        st.session_state.jarvis_phase = "idle"  # idle | listening | processing | speaking
    if "jarvis_text" not in st.session_state:
        st.session_state.jarvis_text = ""
    if "jarvis_response" not in st.session_state:
        st.session_state.jarvis_response = ""
    if "jarvis_error" not in st.session_state:
        st.session_state.jarvis_error = ""
    if "jarvis_greeting" not in st.session_state:
        st.session_state.jarvis_greeting = False
    # Keep jarvis_active as alias for backward compatibility
    if "jarvis_active" not in st.session_state:
        st.session_state.jarvis_active = False

    # Track previous mode for transition detection
    if "previous_mode" not in st.session_state:
        st.session_state.previous_mode = "chat"

    # Pending mode greeting (for sidebar switch)
    if "pending_mode_greeting" not in st.session_state:
        st.session_state.pending_mode_greeting = None

    # Track if system microphone is available (PyAudio required)
    if "microphone_available" not in st.session_state:
        st.session_state.microphone_available = None  # Will be checked on first use


# =============================================================================
# Cached Resource Loaders
# =============================================================================

@st.cache_resource
def get_llm_client(_config: dict):
    """Get a cached LLM client instance."""
    from core.llm_client import DeepSeekClient
    print("[Cache] Creating DeepSeekClient instance...")
    return DeepSeekClient(_config)


@st.cache_resource
def get_audio_manager(_config: dict):
    """Get a cached AudioManager instance for Jarvis mode."""
    from interfaces.audio_io import AudioManager
    print("[Cache] Creating AudioManager instance...")
    return AudioManager(_config)


def check_owner_registered(config: dict) -> bool:
    """Check if owner is registered."""
    from core.registration import check_owner_registered as _check_registered
    return _check_registered(config)


def save_audio_to_wav(audio_file, output_path: str) -> bool:
    """Save audio from st.audio_input to a WAV file."""
    try:
        audio_bytes = audio_file.getvalue()
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return True
    except Exception as e:
        st.error(f"Oops! Something went wrong: {e}")
        return False


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file to text."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""
    except Exception:
        return ""


def init_chat_components(config: dict):
    """Initialize chat components using cached resource loaders."""
    from core.voice_security import get_voice_gatekeeper
    from core.memory_rag import get_memory_manager

    # Use cached instances - these are loaded only once
    if st.session_state.gatekeeper is None:
        st.session_state.gatekeeper = get_voice_gatekeeper(config)

    if st.session_state.memory_manager is None:
        st.session_state.memory_manager = get_memory_manager(config)

    if st.session_state.llm_client is None:
        st.session_state.llm_client = get_llm_client(config)


def verify_voice(audio_path: str) -> bool:
    """Verify if the voice matches the owner."""
    gatekeeper = st.session_state.gatekeeper
    return gatekeeper.verify_user(audio_path)


def get_bot_response(user_input: str) -> str:
    """Get response from the bot using current mode and trigger auto-learning."""
    import threading

    memory_manager = st.session_state.memory_manager
    llm_client = st.session_state.llm_client
    current_mode = st.session_state.get("current_mode", "chat")

    # Query RAG for context
    context_chunks = memory_manager.query_memory(user_input)

    # Get LLM response with current mode
    response = llm_client.get_response(user_input, context_chunks, mode=current_mode)

    # Auto-Learning: Extract and save personal info in background (only in chat mode)
    if current_mode == "chat":
        def auto_learn():
            try:
                fact = llm_client.extract_personal_info(user_input)
                if fact:
                    memory_manager.add_memory(fact)
            except Exception as e:
                print(f"[AutoLearn] Background error: {e}")

        # Run extraction in background thread (non-blocking)
        thread = threading.Thread(target=auto_learn, daemon=True)
        thread.start()

    return response


def text_to_speech(text: str) -> Optional[bytes]:
    """
    Convert text to speech audio bytes using edge-tts.

    Args:
        text: Text to convert to speech

    Returns:
        Audio bytes (MP3) or None if failed
    """
    import asyncio
    import edge_tts

    async def generate():
        communicate = edge_tts.Communicate(text, DEFAULT_TTS_VOICE)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    try:
        # Run async function
        audio_bytes = asyncio.run(generate())
        return audio_bytes if audio_bytes else None
    except Exception as e:
        print(f"[TTS] Error: {e}")
        return None


# =============================================================================
# Layout Render Functions
# =============================================================================

def render_background():
    """Render gradient blobs background."""
    st.markdown(HTML_GRADIENT_BLOBS, unsafe_allow_html=True)


def trigger_mode_transition(new_mode: str, config: dict):
    """
    Trigger a mode transition with an announcement message from the bot.

    Args:
        new_mode: The new mode to transition to
        config: Configuration dictionary
    """
    robot_name = config.get("robot", {}).get("name", "Bobo")

    # Mode transition messages
    transition_messages = {
        "chat": f"Hi! I'm {robot_name}, ready to chat with you!",
        "story": f"Story time! I'm {robot_name} the Storyteller now. What kind of story would you like to hear? Maybe one about brave animals, magical kingdoms, or exciting adventures?",
        "learning": f"Learning time! I'm {robot_name} the Teacher now. What would you like to learn about today? I can explain things and then quiz you!",
        "game": f"Game time! I'm {robot_name} the Game Master now. What game would you like to play? We could play 20 Questions, I Spy, Word Chain, or something else!"
    }

    # Add the transition message to chat history
    message = transition_messages.get(new_mode, f"Let's switch to {new_mode} mode!")
    st.session_state.messages.append({
        "role": "assistant",
        "content": message
    })

    # Trigger TTS for the message
    st.session_state.play_audio = True


def render_sidebar():
    """
    Render sidebar with navigation and mode switching buttons.

    Includes: Home, Stories, Learn, Games, and Settings navigation.
    Each button triggers mode transitions via callbacks.
    """
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #FF9F1C 0%, #FFD166 100%);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
            color: white;
            margin: 0 auto 20px auto;
            box-shadow: 4px 4px 8px rgba(0,0,0,0.1), -2px -2px 6px rgba(255,255,255,0.8);
        ">V</div>
        """, unsafe_allow_html=True)

        # Home (Chat mode) - uses callback for mode switching
        st.button("Home", key="nav_home",
                  on_click=on_mode_switch, args=("chat",))

        # Stories mode - uses callback for mode switching
        st.button("Story", key="nav_stories",
                  on_click=on_mode_switch, args=("story",))

        # Learning mode - uses callback for mode switching
        st.button("Learn", key="nav_learn",
                  on_click=on_mode_switch, args=("learning",))

        # Games mode - uses callback for mode switching
        st.button("Game", key="nav_games",
                  on_click=on_mode_switch, args=("game",))

        # Settings - doesn't use Jarvis mode, keep simple click behavior
        if st.button("Settings", key="nav_settings"):
            st.session_state.current_view = "settings"
            st.rerun()


def render_header():
    """Render header with connection status indicator and user avatar."""
    st.markdown(HTML_HEADER, unsafe_allow_html=True)


def render_robot_display(robot_name: str):
    """
    Render robot display with circular frame and animated avatar.

    Args:
        robot_name: Name of the robot to display
    """
    import base64

    image_base64 = None
    bot_gif_path = Path("assets/bot.gif")

    if bot_gif_path.exists():
        with open(bot_gif_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

    st.markdown(get_robot_html(robot_name, image_base64), unsafe_allow_html=True)


def render_mic_button():
    """
    Render microphone button for voice input.

    Returns:
        Audio file from st.audio_input or None
    """
    st.markdown('<div class="mic-container">', unsafe_allow_html=True)
    audio_file = st.audio_input(
        "Tap to talk",
        key="chat_audio",
        label_visibility="collapsed"
    )
    st.markdown('<div class="mic-label">Tap to talk</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    return audio_file


# =============================================================================
# Views
# =============================================================================

def not_setup_view(config: dict):
    """Show when system is not set up."""
    robot_name = config.get("robot", {}).get("name", "Bobo")

    # Render UI shell
    render_background()
    render_sidebar()
    render_header()

    # Main content
    st.markdown(
        f"""
        <div class="robot-container">
            <div class="robot-frame">
                <div class="robot-inner">
                    <div class="robot-placeholder">?</div>
                </div>
            </div>
            <div class="robot-name">Hi! I'm {robot_name}!</div>
            <div class="robot-status">I'm not ready to play yet...</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 25px;
            background: rgba(255,255,255,0.6);
            backdrop-filter: blur(10px);
            border-radius: 25px;
            max-width: 400px;
            margin: 30px auto;
            box-shadow: 4px 4px 15px rgba(0,0,0,0.05), -2px -2px 10px rgba(255,255,255,0.8);
        ">
            <h3 style="color: #5D4E37; margin-bottom: 10px;">Please ask a grown-up to set me up!</h3>
            <p style="color: #8B7355; margin: 0;">They need to run the admin page first.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =============================================================================
# Jarvis Mode Functions
# =============================================================================

def stop_listening_callback():
    """
    Callback function to stop the Jarvis listening loop.

    Sets all listening-related session state flags to their inactive values.
    Called by the Stop button via on_click handler.
    """
    st.session_state.is_listening_active = False
    st.session_state.jarvis_active = False
    st.session_state.jarvis_phase = "idle"


def on_mode_switch(new_mode: str):
    """
    Callback for sidebar mode switching.
    Stops current loop, switches mode, speaks greeting, auto-starts listening.
    """
    # Skip if already in this mode
    if st.session_state.current_mode == new_mode:
        return

    # 1. Stop current Jarvis loop
    st.session_state.is_listening_active = False
    st.session_state.jarvis_active = False
    st.session_state.jarvis_phase = "idle"

    # 2. Update mode state
    st.session_state.current_mode = new_mode
    st.session_state.current_view = "chat"

    # 3. Clear chat history for fresh start in new mode
    st.session_state.messages = []

    # 4. Set flag to trigger greeting + auto-start on next rerun
    st.session_state.pending_mode_greeting = new_mode


def _process_browser_audio(audio_file, config: dict):
    """
    Process audio captured from browser's st.audio_input.

    Used when PyAudio is not available (e.g., Streamlit Cloud).
    """
    import tempfile

    robot_name = config.get("robot", {}).get("name", "Bobo")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Save the browser audio
        if not save_audio_to_wav(audio_file, tmp_path):
            st.error("Could not process audio")
            return

        with st.status("Processing...", expanded=True) as status:
            # Verify voice
            status.update(label="Checking voice...", state="running")
            if not verify_voice(tmp_path):
                status.update(label="Voice not recognized", state="error")
                st.warning("I don't recognize that voice. Please try again!")
                return

            # Transcribe
            status.update(label="Listening...", state="running")
            text = transcribe_audio(tmp_path)

            if not text:
                status.update(label="Couldn't hear", state="error")
                st.warning("I couldn't hear you. Please try again!")
                return

            # Get response
            status.update(label="Thinking...", state="running")

            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": text
            })

            response = get_bot_response(text)

            # Add bot response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

            status.update(label="Done!", state="complete")

            # Play TTS
            if st.session_state.get("tts_enabled", True):
                audio_bytes = text_to_speech(response)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            st.rerun()

    finally:
        safe_remove_file(tmp_path)


def render_jarvis_controls(config: dict):
    """
    Render Jarvis mode start/stop button.

    Args:
        config: Configuration dictionary

    Displays a large, centered mic button to start or stop conversation mode.
    Visual hierarchy: Robot Avatar -> Robot Name -> Mic Button -> "Tap to talk"
    """
    # Check microphone availability on first render
    if st.session_state.microphone_available is None:
        audio_manager = get_audio_manager(config)
        st.session_state.microphone_available = audio_manager.is_microphone_available()

    # If microphone not available, show browser audio input instead
    if not st.session_state.microphone_available:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <p style="color: #8B7355; font-size: 14px; margin-bottom: 15px;">
                Use the microphone button below to record your voice
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Center the browser audio input
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            audio_file = st.audio_input("Record", key="browser_audio", label_visibility="collapsed")
            if audio_file:
                # Process browser audio
                _process_browser_audio(audio_file, config)
        return

    is_active = st.session_state.is_listening_active

    # CSS for the Big Orange Mic button with SVG icon
    # Microphone SVG as data URL (white stroke)
    mic_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='48' height='48' stroke='white' stroke-width='2' fill='none'%3E%3Cpath d='M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z'/%3E%3Cpath d='M19 10v2a7 7 0 0 1-14 0v-2'/%3E%3Cline x1='12' y1='19' x2='12' y2='23'/%3E%3Cline x1='8' y1='23' x2='16' y2='23'/%3E%3C/svg%3E"
    # Stop icon SVG as data URL (white square)
    stop_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='36' height='36' fill='white'%3E%3Crect x='6' y='6' width='12' height='12' rx='2'/%3E%3C/svg%3E"

    button_css = f"""
    <style>
    /* Big Orange Mic Button - Start State */
    .mic-button-wrapper .stButton > button {{
        width: 100px !important;
        height: 100px !important;
        border-radius: 50% !important;
        border: none !important;
        background: linear-gradient(145deg, #FFD166, #FF9F1C) !important;
        box-shadow:
            0 8px 25px rgba(255, 159, 28, 0.45),
            0 4px 10px rgba(255, 159, 28, 0.3),
            inset 0 2px 4px rgba(255, 255, 255, 0.3) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        min-height: 100px !important;
        cursor: pointer !important;
        animation: mic-pulse 2.5s ease-in-out infinite !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        background-image: url("{mic_svg}") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 48px 48px !important;
    }}

    /* Hide the default button text/icon */
    .mic-button-wrapper .stButton > button p,
    .mic-button-wrapper .stButton > button span {{
        display: none !important;
    }}

    /* Pulsing animation for Start button */
    @keyframes mic-pulse {{
        0%, 100% {{
            transform: scale(1);
            box-shadow:
                0 8px 25px rgba(255, 159, 28, 0.45),
                0 4px 10px rgba(255, 159, 28, 0.3),
                inset 0 2px 4px rgba(255, 255, 255, 0.3);
        }}
        50% {{
            transform: scale(1.05);
            box-shadow:
                0 12px 35px rgba(255, 159, 28, 0.55),
                0 6px 15px rgba(255, 159, 28, 0.4),
                inset 0 2px 4px rgba(255, 255, 255, 0.3);
        }}
    }}

    .mic-button-wrapper .stButton > button:hover {{
        animation: none !important;
        transform: scale(1.1) !important;
        box-shadow:
            0 14px 40px rgba(255, 159, 28, 0.6),
            0 8px 20px rgba(255, 159, 28, 0.4),
            inset 0 2px 4px rgba(255, 255, 255, 0.3) !important;
    }}

    .mic-button-wrapper .stButton > button:active {{
        animation: none !important;
        transform: scale(0.95) !important;
    }}

    /* Stop Button - Red pulsing with stop icon */
    .mic-button-wrapper.stop-state .stButton > button {{
        background: linear-gradient(145deg, #FF6B6B, #E74C3C) !important;
        background-image: url("{stop_svg}") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 36px 36px !important;
        box-shadow:
            0 0 0 0 rgba(231, 76, 60, 0.7),
            0 8px 25px rgba(231, 76, 60, 0.5),
            inset 0 2px 4px rgba(255, 255, 255, 0.2) !important;
        animation: stop-pulse 1.5s ease-in-out infinite !important;
    }}

    @keyframes stop-pulse {{
        0%, 100% {{
            box-shadow:
                0 0 0 0 rgba(231, 76, 60, 0.7),
                0 8px 25px rgba(231, 76, 60, 0.5),
                inset 0 2px 4px rgba(255, 255, 255, 0.2);
        }}
        50% {{
            box-shadow:
                0 0 0 15px rgba(231, 76, 60, 0),
                0 8px 25px rgba(231, 76, 60, 0.5),
                inset 0 2px 4px rgba(255, 255, 255, 0.2);
        }}
    }}

    .mic-button-wrapper.stop-state .stButton > button:hover {{
        animation: none !important;
        transform: scale(1.1) !important;
    }}

    /* Tap to talk label */
    .mic-label {{
        text-align: center;
        color: #8B7355;
        font-size: 14px;
        font-weight: 500;
        margin-top: 12px;
        font-family: 'Nunito', sans-serif;
    }}
    </style>
    """
    st.markdown(button_css, unsafe_allow_html=True)

    # Center the button using columns [1, 2, 1] for perfect centering
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Wrapper div for targeting CSS
        wrapper_class = "mic-button-wrapper stop-state" if is_active else "mic-button-wrapper"
        st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)

        if is_active:
            # Stop button with stop icon
            if st.button("", key="jarvis_toggle", on_click=stop_listening_callback, help="Stop listening"):
                pass
            st.markdown('<div class="mic-label">Tap to stop</div>', unsafe_allow_html=True)
        else:
            # Start button with microphone emoji
            if st.button("", key="jarvis_toggle", help="Start talking"):
                st.session_state.is_listening_active = True
                st.session_state.jarvis_active = True
                st.session_state.jarvis_phase = "greeting"
                st.session_state.jarvis_error = ""
                st.session_state.jarvis_greeting = True
                st.rerun()
            st.markdown('<div class="mic-label">Tap to talk</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


def handle_jarvis_stop(config: dict):
    """Handle stop button click."""
    st.session_state.jarvis_active = False
    st.session_state.jarvis_phase = "idle"
    st.session_state.jarvis_text = ""
    st.session_state.jarvis_response = ""


def render_jarvis_status(phase: str):
    """
    Render animated status indicator for current conversation phase.

    Args:
        phase: Current phase - 'listening', 'processing', or 'speaking'

    Displays a colored animated indicator matching the current state.
    """
    phase_config = {
        "listening": {
            "class": "jarvis-listening",
            "text": "Listening...",
        },
        "processing": {
            "class": "jarvis-processing",
            "text": "Thinking...",
        },
        "speaking": {
            "class": "jarvis-speaking",
            "text": "Speaking...",
        }
    }

    cfg = phase_config.get(phase, phase_config["listening"])

    st.markdown(f"""
    <div class="jarvis-status-container">
        <div class="jarvis-indicator {cfg['class']}"></div>
        <div class="jarvis-status-text">{cfg['text']}</div>
    </div>
    """, unsafe_allow_html=True)


def jarvis_conversation_flow(config: dict, audio_file):
    """
    Process audio in Jarvis mode - handles the full flow from audio to response.
    Works with Streamlit's browser-based st.audio_input().
    """
    if audio_file is None:
        return

    # Show processing status
    st.session_state.jarvis_phase = "processing"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Save the audio
        if not save_audio_to_wav(audio_file, tmp_path):
            st.error("Could not save audio")
            return

        # Verify voice
        with st.status("Processing...", expanded=True) as status:
            status.update(label="Checking voice...", state="running")
            if not verify_voice(tmp_path):
                status.update(label="Voice not recognized", state="error")
                st.warning("I don't recognize that voice. Please try again!")
                st.session_state.jarvis_phase = "listening"
                return

            # Transcribe
            status.update(label="Listening...", state="running")
            text = transcribe_audio(tmp_path)

            if not text:
                status.update(label="Couldn't hear", state="error")
                st.warning("I couldn't hear you. Please try again!")
                st.session_state.jarvis_phase = "listening"
                return

            # Get response
            status.update(label="Thinking...", state="running")
            st.session_state.jarvis_phase = "processing"

            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": text
            })

            response = get_bot_response(text)

            # Add bot response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

            status.update(label="Done!", state="complete")

            # Generate and play TTS
            st.session_state.jarvis_phase = "speaking"
            if st.session_state.get("tts_enabled", True):
                audio_bytes = text_to_speech(response)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            # Return to listening
            st.session_state.jarvis_phase = "listening"
            st.rerun()

    finally:
        safe_remove_file(tmp_path)


def render_mode_header(robot_name: str):
    """
    Render the current mode header for non-chat modes.

    Args:
        robot_name: Name of the robot (unused but kept for consistency)

    Only displays for story, learning, and game modes.
    Chat mode has no header to keep the interface clean.
    """
    mode = st.session_state.get("current_mode", "chat")

    # Don't show header for chat mode
    if mode == "chat":
        return

    # Mode-specific titles and colors (only for special modes)
    mode_config = {
        "story": {"title": "Story Time", "color": "#9B59B6"},     # Purple
        "learning": {"title": "Learning", "color": "#3498DB"},    # Blue
        "game": {"title": "Game Time", "color": "#2ECC71"}        # Green
    }
    config = mode_config.get(mode)
    if not config:
        return

    st.markdown(f'''
    <div style="
        text-align: center;
        padding: 12px 20px;
        margin: 10px auto 20px auto;
        max-width: 300px;
        background: rgba(255,255,255,0.7);
        border-radius: 20px;
        box-shadow: 4px 4px 15px rgba(0,0,0,0.05), -2px -2px 10px rgba(255,255,255,0.8);
    ">
        <h2 style="
            color: {config["color"]};
            margin: 0;
            font-family: 'Nunito', sans-serif;
            font-size: 22px;
            font-weight: 700;
        ">{config["title"]}</h2>
    </div>
    ''', unsafe_allow_html=True)


def chat_view(config: dict):
    """
    Main chat interface for kids with Jarvis continuous conversation mode.

    Args:
        config: Configuration dictionary from config.yaml

    Handles:
    - Mode greeting transitions from sidebar
    - Jarvis continuous listening loop (greeting -> listening -> processing -> speaking)
    - Voice verification for speaker authentication
    - RAG-based context retrieval
    - Streaming LLM responses with sentence-level TTS
    - Auto-learning of personal facts
    - Chat history display
    """
    robot_name = config.get("robot", {}).get("name", "Bobo")

    # Initialize components using cached loaders
    init_chat_components(config)

    # =========================================================================
    # HANDLE PENDING MODE GREETING (from sidebar switch)
    # =========================================================================
    if st.session_state.get("pending_mode_greeting"):
        new_mode = st.session_state.pending_mode_greeting
        st.session_state.pending_mode_greeting = None

        # Get audio manager and speak greeting
        audio_manager = get_audio_manager(config)
        greeting = MODE_GREETINGS.get(new_mode, f"Switching to {new_mode} mode!")

        # Add to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": greeting
        })

        # Speak the greeting (blocking) - works even without microphone
        audio_manager.speak(greeting)

        # Auto-start Jarvis loop only if microphone is available
        if audio_manager.is_microphone_available():
            st.session_state.is_listening_active = True
            st.session_state.jarvis_active = True
            st.session_state.jarvis_phase = "listening"
        st.rerun()

    # Render UI shell
    render_background()
    render_sidebar()
    render_header()

    # Mode header (shows current mode)
    render_mode_header(robot_name)

    # Robot display
    render_robot_display(robot_name)

    # Render Jarvis controls (Start/Stop button)
    render_jarvis_controls(config)

    # =========================================================================
    # JARVIS CONTINUOUS CONVERSATION LOOP
    # =========================================================================
    if st.session_state.is_listening_active:
        # Get AudioManager for system microphone access
        audio_manager = get_audio_manager(config)

        # Check if microphone is available (PyAudio required)
        if not audio_manager.is_microphone_available():
            st.warning("Microphone not available. Use the browser audio input instead.")
            st.session_state.is_listening_active = False
            st.session_state.jarvis_active = False
            st.session_state.jarvis_phase = "idle"
            st.rerun()

        audio_manager.clear_stop_request()

        phase = st.session_state.jarvis_phase

        # -----------------------------------------------------------------
        # GREETING PHASE: Play initial greeting when conversation starts
        # -----------------------------------------------------------------
        if phase == "greeting":
            greeting = f"Hi! I'm {robot_name}. How can I help you today?"
            st.session_state.messages.append({
                "role": "assistant",
                "content": greeting
            })

            # Show speaking status
            render_jarvis_status("speaking")

            # Speak the greeting using AudioManager
            audio_manager.speak(greeting)

            # Transition to listening
            st.session_state.jarvis_phase = "listening"
            st.session_state.jarvis_greeting = False
            st.rerun()

        # -----------------------------------------------------------------
        # LISTENING PHASE: Wait for user speech with VAD auto-stop
        # -----------------------------------------------------------------
        elif phase == "listening":
            # Show listening status indicator
            render_jarvis_status("listening")

            # Create temp file for voice verification
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # Listen with VAD - automatically stops when user pauses speaking
                text, audio_path = audio_manager.listen_and_save(tmp_path)

                # Check if stop was requested during listening
                if not st.session_state.is_listening_active:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    return

                if text:
                    # Verify voice matches owner
                    if verify_voice(tmp_path):
                        st.session_state.jarvis_text = text
                        st.session_state.jarvis_phase = "processing"
                    else:
                        # Voice not recognized - keep listening
                        st.session_state.jarvis_error = "Voice not recognized"
                else:
                    # No speech detected (silence/timeout) - keep listening
                    pass

            except Exception as e:
                print(f"[Jarvis] Listen error: {e}")
                st.session_state.jarvis_error = str(e)

            finally:
                # Cleanup temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            # Rerun to continue the loop (either process or keep listening)
            st.rerun()

        # -----------------------------------------------------------------
        # PROCESSING + SPEAKING PHASE: Stream LLM and speak sentence-by-sentence
        # This combines processing and speaking for lower latency
        # Includes voice control: mode switching and action tags
        # -----------------------------------------------------------------
        elif phase == "processing":
            render_jarvis_status("processing")

            user_text = st.session_state.jarvis_text

            # Add user message to history
            st.session_state.messages.append({
                "role": "user",
                "content": user_text
            })

            # Get context from RAG
            memory_manager = st.session_state.memory_manager
            llm_client = st.session_state.llm_client
            current_mode = st.session_state.get("current_mode", "chat")
            context_chunks = memory_manager.query_memory(user_text)

            # Sentence-buffering TTS for lower latency
            sentence_buffer = ""
            full_response = ""
            tags_processed = False
            sentence_endings = {'.', '!', '?', '\u3002', '\uff1f', '\uff01'}  # Include Chinese punctuation

            try:
                # Stream from LLM
                for chunk in llm_client.get_response_stream(user_text, context_chunks, current_mode):
                    # Check if stop was requested
                    if not st.session_state.is_listening_active:
                        break

                    sentence_buffer += chunk
                    full_response += chunk

                    # Process tags early (they come at the start)
                    # Wait until we have some content after potential tags
                    if not tags_processed and len(full_response) > 50:
                        commands, _ = parse_response(full_response)

                        # Handle MODE switch
                        if commands.get("mode"):
                            new_mode = commands["mode"]
                            if new_mode != st.session_state.current_mode:
                                st.session_state.current_mode = new_mode
                                st.toast(f"Switching to {new_mode} mode!")
                                print(f"[VOICE CONTROL] Mode switch: {new_mode}")

                        # Handle ACTION
                        if commands.get("action"):
                            action = commands["action"]
                            print(f"[HARDWARE] Executing action: {action}")
                            # Future: trigger animation/hardware here

                        tags_processed = True

                    # Check for sentence endings (only speak clean text)
                    for ending in sentence_endings:
                        if ending in sentence_buffer:
                            # Find the last sentence ending
                            last_end_pos = -1
                            for e in sentence_endings:
                                pos = sentence_buffer.rfind(e)
                                if pos > last_end_pos:
                                    last_end_pos = pos

                            if last_end_pos >= 0:
                                # Extract complete sentence(s)
                                sentence_to_speak = sentence_buffer[:last_end_pos + 1].strip()
                                sentence_buffer = sentence_buffer[last_end_pos + 1:]

                                # Parse to get clean text (remove tags) before speaking
                                _, clean_sentence = parse_response(sentence_to_speak)

                                # Speak immediately (Pipeline: speak while LLM generates next part)
                                if clean_sentence and st.session_state.get("tts_enabled", True):
                                    audio_manager.speak(clean_sentence)
                            break

                # Process any remaining tags if not done yet
                if not tags_processed and full_response:
                    commands, _ = parse_response(full_response)

                    if commands.get("mode"):
                        new_mode = commands["mode"]
                        if new_mode != st.session_state.current_mode:
                            st.session_state.current_mode = new_mode
                            st.toast(f"Switching to {new_mode} mode!")
                            print(f"[VOICE CONTROL] Mode switch: {new_mode}")

                    if commands.get("action"):
                        action = commands["action"]
                        print(f"[HARDWARE] Executing action: {action}")

                # Speak any remaining text in buffer (clean version)
                if sentence_buffer.strip() and st.session_state.get("tts_enabled", True):
                    if st.session_state.is_listening_active:
                        _, clean_remaining = parse_response(sentence_buffer.strip())
                        if clean_remaining:
                            audio_manager.speak(clean_remaining)

                # Add clean response to history (without tags)
                if full_response:
                    _, clean_response = parse_response(full_response.strip())
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": clean_response
                    })

                # Auto-learning in background
                import threading
                def auto_learn():
                    try:
                        fact = llm_client.extract_personal_info(user_text)
                        if fact:
                            memory_manager.add_memory(fact)
                    except Exception:
                        pass
                threading.Thread(target=auto_learn, daemon=True).start()

            except Exception as e:
                print(f"[Jarvis] Stream error: {e}")
                st.session_state.jarvis_error = str(e)

            # Check if stop was requested
            if not st.session_state.is_listening_active:
                return

            # Loop back to listening
            st.session_state.jarvis_phase = "listening"
            st.session_state.jarvis_text = ""
            st.session_state.jarvis_response = ""
            st.rerun()

    # =========================================================================
    # DISPLAY CHAT HISTORY
    # =========================================================================
    if st.session_state.messages:
        # Show mode-specific history header
        mode = st.session_state.get("current_mode", "chat")
        history_titles = {
            "chat": "Chat History",
            "story": "Story So Far",
            "learning": "Learning Session",
            "game": "Game Progress"
        }
        st.markdown(f"### {history_titles.get(mode, 'Chat History')}")

        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(
                message["role"],
                avatar=None
            ):
                # Show text immediately (Psychology of Speed - users can read while waiting)
                st.markdown(message["content"])

                # Play audio for the latest bot response (if TTS enabled and not in Jarvis mode)
                if (message["role"] == "assistant" and
                    i == len(st.session_state.messages) - 1 and
                    st.session_state.get("play_audio", False) and
                    st.session_state.get("tts_enabled", True) and
                    not st.session_state.jarvis_active):

                    with st.spinner("Speaking..."):
                        audio_bytes = text_to_speech(message["content"])
                        if audio_bytes:
                            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

                    st.session_state.play_audio = False



# =============================================================================
# Main
# =============================================================================

def main():
    st.set_page_config(
        page_title="KidBot",
        page_icon="assets/bot.jpg",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inject custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Load config
    config = load_config()

    # Initialize session state
    init_session_state()

    # Route based on registration status and current view
    if not check_owner_registered(config):
        not_setup_view(config)
    elif st.session_state.current_view == "settings":
        render_settings_view(config)
    else:
        chat_view(config)


if __name__ == "__main__":
    main()
