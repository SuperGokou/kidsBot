"""
Owner Registration Module for KidBot

Provides reusable functions for voice registration that can be used
by both the standalone registration script and the main application.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from resemblyzer import preprocess_wav

if TYPE_CHECKING:
    from resemblyzer import VoiceEncoder


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
    Check if owner embedding file exists.

    Args:
        config: Configuration dictionary from config.yaml

    Returns:
        True if owner is registered, False otherwise
    """
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
