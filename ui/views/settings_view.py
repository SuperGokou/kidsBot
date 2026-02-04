"""
Settings View for KidBot

Clean, kid-friendly settings page matching the app's cream/orange theme.
"""

import streamlit as st


def render_settings_view(config: dict):
    """Render the settings page."""
    from ui.components import HTML_GRADIENT_BLOBS

    # Inject settings-specific CSS
    st.markdown(get_settings_css(), unsafe_allow_html=True)

    # Background blobs
    st.markdown(HTML_GRADIENT_BLOBS, unsafe_allow_html=True)

    # Sidebar
    _render_sidebar()

    # Main content
    _render_main_content(config)


def _render_sidebar():
    """Render sidebar with navigation."""
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
            margin: 0 auto 30px auto;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">V</div>
        """, unsafe_allow_html=True)

        # Back to Home button
        if st.button("Back to Home", key="settings_back_home", use_container_width=True):
            st.session_state.current_view = "chat"
            st.session_state.current_mode = "chat"
            st.rerun()


def _render_main_content(config: dict):
    """Render main settings content."""
    robot_name = config.get("robot", {}).get("name", "VV")

    # Page title
    st.markdown(f"""
    <div class="settings-header">
        <h1>Settings</h1>
        <p>Customize {robot_name}'s behavior</p>
    </div>
    """, unsafe_allow_html=True)

    # Settings sections
    col1, col2 = st.columns(2, gap="large")

    with col1:
        _render_audio_card()
        _render_voice_card(config)

    with col2:
        _render_chat_card()
        _render_about_card(config)


def _render_audio_card():
    """Audio settings card."""
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="card-title">Audio</div>
    """, unsafe_allow_html=True)

    # TTS Toggle
    tts_enabled = st.toggle(
        "Enable Voice Responses",
        value=st.session_state.get("tts_enabled", True),
        key="settings_tts_toggle",
        help="Turn on/off the robot's voice"
    )
    st.session_state.tts_enabled = tts_enabled

    # Volume slider
    volume = st.slider(
        "Volume",
        min_value=0,
        max_value=100,
        value=st.session_state.get("volume", 80),
        key="settings_volume",
        format="%d%%"
    )
    st.session_state.volume = volume

    st.markdown('</div>', unsafe_allow_html=True)


def _render_voice_card(config: dict):
    """Voice settings card."""
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="card-title">Voice Recognition</div>
    """, unsafe_allow_html=True)

    # Voice verification status
    from core.registration import check_owner_registered
    is_registered = check_owner_registered(config)

    if is_registered:
        st.success("Voice registered")
    else:
        st.warning("Voice not registered")
        st.caption("Run `python -m scripts.register_owner` to register")

    # Mic sensitivity info
    st.markdown("**Microphone Settings**")
    st.caption("Energy threshold: 300 (auto-adjusting)")
    st.caption("Phrase limit: 10 seconds")

    # Test mic button
    if st.button("Test Microphone", key="test_mic_btn"):
        with st.spinner("Testing..."):
            try:
                from interfaces.audio_io import AudioManager
                audio_mgr = AudioManager(config, auto_calibrate=False)
                if audio_mgr.test_microphone():
                    st.success("Microphone working!")
                else:
                    st.error("Microphone not detected")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown('</div>', unsafe_allow_html=True)


def _render_chat_card():
    """Chat settings card."""
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="card-title">Chat</div>
    """, unsafe_allow_html=True)

    # Current mode display
    current_mode = st.session_state.get("current_mode", "chat")
    mode_names = {
        "chat": "Chat Mode",
        "story": "Story Mode",
        "learning": "Learning Mode",
        "game": "Game Mode"
    }
    st.markdown(f"**Current Mode:** {mode_names.get(current_mode, 'Chat')}")

    # Clear chat history
    if st.button("Clear Chat History", key="clear_history_btn"):
        st.session_state.messages = []
        st.success("Chat history cleared!")
        st.rerun()

    # Message count
    msg_count = len(st.session_state.get("messages", []))
    st.caption(f"Messages in history: {msg_count}")

    st.markdown('</div>', unsafe_allow_html=True)


def _render_about_card(config: dict):
    """About card."""
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="card-title">About</div>
    """, unsafe_allow_html=True)

    robot_name = config.get("robot", {}).get("name", "VV")
    personality = config.get("robot", {}).get("personality", "friendly and helpful")

    st.markdown(f"**Robot Name:** {robot_name}")
    st.markdown(f"**Personality:** {personality}")

    # Version info
    st.markdown("---")
    st.caption("KidBot v1.0")
    st.caption("AI Companion for Kids")

    st.markdown('</div>', unsafe_allow_html=True)


def get_settings_css() -> str:
    """Return CSS for settings page."""
    return """
<style>
/* Settings page header */
.settings-header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
}

.settings-header h1 {
    font-family: 'Nunito', sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: #5D4E37;
    margin: 0 0 8px 0;
}

.settings-header p {
    font-family: 'Nunito', sans-serif;
    font-size: 16px;
    color: #8B7355;
    margin: 0;
}

/* Settings card */
.settings-card {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow:
        4px 4px 15px rgba(0,0,0,0.05),
        -2px -2px 10px rgba(255,255,255,0.8);
}

/* Card title */
.card-title {
    font-family: 'Nunito', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: #5D4E37;
    margin-bottom: 16px;
}

/* Override Streamlit toggle */
[data-testid="stToggle"] > label {
    font-family: 'Nunito', sans-serif !important;
    color: #5D4E37 !important;
}

/* Override Streamlit slider */
[data-testid="stSlider"] > label {
    font-family: 'Nunito', sans-serif !important;
    color: #5D4E37 !important;
}

.stSlider > div > div > div {
    background: linear-gradient(90deg, #FF9F1C 0%, #FFD166 100%) !important;
}

/* Override buttons in settings */
.settings-card .stButton > button {
    background: #FFF8E1 !important;
    color: #5D4E37 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 8px 16px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    transition: all 0.2s ease !important;
}

.settings-card .stButton > button:hover {
    background: #FFAF45 !important;
    color: white !important;
    transform: scale(1.02) !important;
}

/* Success/warning/error messages */
.settings-card [data-testid="stAlert"] {
    border-radius: 12px !important;
    font-family: 'Nunito', sans-serif !important;
}

/* Caption text */
.settings-card [data-testid="stCaption"] {
    color: #8B7355 !important;
}

/* Markdown text in cards */
.settings-card [data-testid="stMarkdown"] p {
    font-family: 'Nunito', sans-serif !important;
    color: #5D4E37 !important;
}

.settings-card hr {
    border-color: rgba(93, 78, 55, 0.1) !important;
    margin: 12px 0 !important;
}
</style>
"""
