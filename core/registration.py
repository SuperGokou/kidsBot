"""
Owner Registration Module for KidBot

Provides reusable functions for voice registration that can be used
by both the standalone registration script and the main application.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

# Lazy import resemblyzer - may not be available in cloud deployment
_resemblyzer_available = False
preprocess_wav = None

try:
    from resemblyzer import preprocess_wav
    _resemblyzer_available = True
except ImportError:
    pass

if TYPE_CHECKING:
    from resemblyzer import VoiceEncoder


def is_demo_mode() -> bool:
    """
    Check if running in demo mode (cloud deployment without voice registration).

    Demo mode is enabled when:
    - DEMO_MODE environment variable is set to "true" or "1"
    - Or running on Streamlit Cloud (detected via various environment indicators)

    Returns:
        True if in demo mode, False otherwise
    """
    demo_env = os.environ.get("DEMO_MODE", "").lower()
    if demo_env in ("true", "1", "yes"):
        return True

    # Check if running on Streamlit Cloud - multiple detection methods
    # Method 1: STREAMLIT_SHARING_MODE (older Streamlit Cloud)
    if os.environ.get("STREAMLIT_SHARING_MODE"):
        return True

    # Method 2: HOME path for adminuser (Streamlit Cloud container)
    home = os.environ.get("HOME", "")
    if home.startswith("/home/adminuser") or home.startswith("/mount/src"):
        return True

    # Method 3: Check for Streamlit Cloud specific paths
    if os.path.exists("/mount/src"):
        return True

    # Method 4: HOSTNAME pattern (Streamlit Cloud uses specific patterns)
    hostname = os.environ.get("HOSTNAME", "")
    if hostname.startswith("streamlit-") or "streamlit" in hostname.lower():
        return True

    return False


def register_owner_from_audio(encoder: "VoiceEncoder", audio_path: str, embedding_path: str) -> bool:
    """
    Extract speaker embedding from audio and save to file.

    Args:
        encoder: Resemblyzer VoiceEncoder instance
        audio_path: Path to the WAV audio file
        embedding_path: Path where the embedding will be saved

    Returns:
        True if registration succeeded, False otherwise
    """
    if not _resemblyzer_available or preprocess_wav is None:
        print("[Registration] Resemblyzer not available - cannot register voice")
        return False

    try:
        # Preprocess audio and extract embedding
        wav = preprocess_wav(audio_path)
        embedding = encoder.embed_utterance(wav)

        # Save embedding
        Path(embedding_path).parent.mkdir(parents=True, exist_ok=True)
        np.save(embedding_path, embedding)

        return True

    except Exception as e:
        print(f"[Registration] Error: {e}")
        return False


def check_owner_registered(config: dict) -> bool:
    """
    Check if owner embedding file exists or if running in demo mode.

    In demo mode (cloud deployment), voice registration is skipped
    and the app is accessible without owner verification.

    Args:
        config: Configuration dictionary from config.yaml

    Returns:
        True if owner is registered or in demo mode, False otherwise
    """
    # Demo mode bypasses registration requirement
    if is_demo_mode():
        return True

    path = config.get("voice_security", {}).get(
        "owner_embedding_path",
        "data/voice_prints/owner_embedding.npy"
    )
    return Path(path).exists()


def get_owner_embedding_path(config: dict) -> str:
    """
    Get the owner embedding path from config.

    Args:
        config: Configuration dictionary from config.yaml

    Returns:
        Path to the owner embedding file
    """
    return config.get("voice_security", {}).get(
        "owner_embedding_path",
        "data/voice_prints/owner_embedding.npy"
    )
