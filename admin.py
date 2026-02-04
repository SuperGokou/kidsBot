#!/usr/bin/env python3
"""
Admin Dashboard for KidBot

Voice registration and system management interface.
Run with: streamlit run admin.py
"""

import os
import tempfile
from pathlib import Path

import streamlit as st

from core.utils import load_config, safe_remove_file


def init_session_state():
    """Initialize session state variables."""
    if "encoder" not in st.session_state:
        st.session_state.encoder = None


def get_owner_embedding_path(config: dict) -> str:
    """Get the owner embedding path from config."""
    from core.registration import get_owner_embedding_path as _get_path
    return _get_path(config)


def load_voice_encoder():
    """Load or get cached voice encoder."""
    if st.session_state.encoder is None:
        from resemblyzer import VoiceEncoder
        with st.spinner("Loading voice recognition model..."):
            st.session_state.encoder = VoiceEncoder()
    return st.session_state.encoder


def save_audio_to_wav(audio_file, output_path: str) -> bool:
    """Save audio from st.audio_input to a WAV file."""
    try:
        audio_bytes = audio_file.getvalue()
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return True
    except Exception as e:
        st.error(f"Failed to save audio: {e}")
        return False


def register_voice(encoder, audio_path: str, embedding_path: str) -> bool:
    """Register voice from audio file."""
    from core.registration import register_owner_from_audio
    try:
        return register_owner_from_audio(encoder, audio_path, embedding_path)
    except Exception as e:
        st.error(f"Registration error: {e}")
        return False


def main():
    st.set_page_config(
        page_title="KidBot Admin",
        page_icon="",
        layout="centered"
    )

    # Load config
    config = load_config()
    robot_name = config.get("robot", {}).get("name", "Bobo")
    embedding_path = get_owner_embedding_path(config)
    is_registered = Path(embedding_path).exists()

    # Initialize session state
    init_session_state()

    # Header
    st.title(f"{robot_name} Admin Panel")
    st.caption("Voice Registration & System Management")

    st.divider()

    # Status Section
    st.header("System Status")

    col1, col2 = st.columns(2)
    with col1:
        if is_registered:
            st.success("Owner Registered")
        else:
            st.warning("No Owner Registered")

    with col2:
        st.info(f"Embedding: `{embedding_path}`")

    st.divider()

    # Registration Section
    st.header("Voice Registration")

    if is_registered:
        st.info("Owner voice is already registered. You can re-register or reset below.")

    st.markdown("""
    **Instructions:**
    1. Click the microphone button below
    2. Speak clearly for 5-10 seconds
    3. Wait for processing to complete
    """)

    audio_file = st.audio_input(
        "Record voice sample",
        key="admin_audio"
    )

    if audio_file is not None:
        st.audio(audio_file, format="audio/wav")

        if st.button("Register This Voice", type="primary"):
            with st.spinner("Processing voice registration..."):
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name

                try:
                    if save_audio_to_wav(audio_file, tmp_path):
                        encoder = load_voice_encoder()
                        if register_voice(encoder, tmp_path, embedding_path):
                            st.success("Voice registered successfully!")
                            st.balloons()
                            st.rerun()
                finally:
                    safe_remove_file(tmp_path)

    st.divider()

    # Danger Zone
    st.header("Danger Zone")

    st.markdown(
        '<p style="color: #ff4b4b;">These actions cannot be undone!</p>',
        unsafe_allow_html=True
    )

    # Factory Reset Section
    st.subheader("Factory Reset")

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button(
            "Factory Reset",
            type="primary",
            use_container_width=True
        ):
            st.session_state.show_reset_options = True

    if st.session_state.get("show_reset_options", False):
        st.warning("This will reset the robot to its initial state!")

        # Reset options
        clear_voice = st.checkbox(
            "Clear Voice Registration",
            value=True,
            disabled=not is_registered,
            help="Delete the owner's voice print"
        )

        clear_memory = st.checkbox(
            "Clear Memory Database",
            value=False,
            help="Delete all learned memories and knowledge"
        )

        st.markdown("---")

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("Confirm Reset", type="primary"):
                success_msgs = []
                error_msgs = []

                # Clear voice registration
                if clear_voice and is_registered:
                    try:
                        safe_remove_file(embedding_path, silent=False)
                        success_msgs.append("Voice registration cleared")
                    except Exception as e:
                        error_msgs.append(f"Voice clear failed: {e}")

                # Clear memory database
                if clear_memory:
                    try:
                        import shutil
                        vector_store_path = config.get("paths", {}).get(
                            "vector_store", "data/vector_store"
                        )
                        if Path(vector_store_path).exists():
                            shutil.rmtree(vector_store_path)
                            success_msgs.append("Memory database cleared")
                    except Exception as e:
                        error_msgs.append(f"Memory clear failed: {e}")

                # Show results
                st.session_state.show_reset_options = False

                if success_msgs:
                    st.success("Reset complete: " + ", ".join(success_msgs))
                    st.balloons()

                if error_msgs:
                    for msg in error_msgs:
                        st.error(msg)

                st.rerun()

        with c2:
            if st.button("Cancel"):
                st.session_state.show_reset_options = False
                st.rerun()

    # Quick Actions
    st.subheader("Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Clear Voice Only",
            disabled=not is_registered,
            use_container_width=True
        ):
            if safe_remove_file(embedding_path, silent=False):
                st.success("Voice registration cleared.")
                st.rerun()
            else:
                st.error("Failed to clear voice registration.")

    with col2:
        if st.button(
            "Clear Memory Only",
            use_container_width=True
        ):
            try:
                import shutil
                vector_store_path = config.get("paths", {}).get(
                    "vector_store", "data/vector_store"
                )
                if Path(vector_store_path).exists():
                    shutil.rmtree(vector_store_path)
                    st.success("Memory database cleared.")
                else:
                    st.info("No memory database found.")
            except Exception as e:
                st.error(f"Failed: {e}")

    st.divider()

    # Memory Statistics
    st.divider()
    st.header("Memory Database")

    try:
        from core.memory_rag import MemoryManager
        with st.spinner("Loading memory stats..."):
            mm = MemoryManager(config)
            stats = mm.get_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Memories", stats["total_documents"])
        with col2:
            st.metric("Processed Files", stats["processed_files"])

    except Exception as e:
        st.info(f"Memory database not initialized: {e}")

    # Configuration Info
    st.divider()
    st.header("Configuration")
    with st.expander("View Voice Security Settings"):
        voice_config = config.get("voice_security", {})
        st.json(voice_config)

    with st.expander("View Robot Settings"):
        robot_config = config.get("robot", {})
        st.json(robot_config)

    with st.expander("View RAG Settings"):
        rag_config = config.get("rag", {})
        st.json(rag_config)


if __name__ == "__main__":
    main()
