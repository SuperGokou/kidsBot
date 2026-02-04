"""
Voice Security Module for KidBot

Provides speaker verification to ensure only the registered owner
can interact with the robot. Uses Streamlit caching for performance.
"""

from pathlib import Path

import numpy as np
import streamlit as st

from core.registration import is_demo_mode

# Lazy import resemblyzer - may not be available in demo mode
_resemblyzer_available = False
VoiceEncoder = None
preprocess_wav = None

try:
    from resemblyzer import VoiceEncoder, preprocess_wav
    _resemblyzer_available = True
except ImportError:
    print("[VoiceGatekeeper] Resemblyzer not available - voice verification disabled")


# =============================================================================
# Cached Resource Loaders
# =============================================================================

@st.cache_resource
def load_voice_encoder():
    """
    Load and cache the Resemblyzer voice encoder model.

    This is decorated with @st.cache_resource to ensure the model
    is only loaded once, even across Streamlit reruns.

    Returns:
        Loaded VoiceEncoder model or None if not available
    """
    if not _resemblyzer_available or VoiceEncoder is None:
        print("[Cache] Resemblyzer not available - skipping voice encoder")
        return None

    print("[Cache] Loading Resemblyzer voice encoder...")
    return VoiceEncoder()


@st.cache_resource
def get_voice_gatekeeper(_config: dict) -> "VoiceGatekeeper":
    """
    Get a cached VoiceGatekeeper instance.

    The underscore prefix on _config tells Streamlit not to hash it
    (since dicts can be complex to hash).

    Args:
        _config: Configuration dictionary from config.yaml

    Returns:
        Cached VoiceGatekeeper instance
    """
    print("[Cache] Creating VoiceGatekeeper instance...")
    return VoiceGatekeeper(_config)


class VoiceGatekeeper:
    """
    Verifies if the current speaker matches the registered owner.

    Uses Resemblyzer's speaker encoder for embedding extraction
    and cosine similarity for verification.

    In demo mode (cloud deployment), voice verification is disabled
    and all users are allowed access.
    """

    def __init__(self, config: dict):
        """
        Initialize the VoiceGatekeeper.

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        voice_config = config.get("voice_security", {})

        # Check if in demo mode - disable voice security
        self.demo_mode = is_demo_mode()
        if self.demo_mode:
            print("[VoiceGatekeeper] Running in DEMO MODE - voice verification disabled")
            self.enabled = False
        else:
            self.enabled = voice_config.get("enabled", True)

        self.threshold = voice_config.get("threshold", 0.25)
        self.owner_embedding_path = voice_config.get(
            "owner_embedding_path",
            "data/voice_prints/owner_embedding.npy"
        )

        self.encoder = None
        self.owner_embedding = None

        if self.enabled and _resemblyzer_available:
            self._load_model()
            self._load_owner_embedding()

    def _load_model(self):
        """Load the Resemblyzer voice encoder model using cached loader."""
        self.encoder = load_voice_encoder()

    def _load_owner_embedding(self):
        """Load the owner's voice embedding."""
        embedding_path = Path(self.owner_embedding_path)

        if not embedding_path.exists():
            print(f"[VoiceGatekeeper] WARNING: Owner embedding not found at {embedding_path}")
            print("[VoiceGatekeeper] Please run 'python register_owner.py' to register your voice.")
            self.owner_embedding = None
            return

        self.owner_embedding = np.load(embedding_path)

    def _extract_embedding(self, audio_path: str) -> np.ndarray:
        """
        Extract speaker embedding from an audio file.

        Args:
            audio_path: Path to the WAV audio file

        Returns:
            256-dimensional speaker embedding
        """
        if not _resemblyzer_available or preprocess_wav is None:
            return None

        # Preprocess and encode
        wav = preprocess_wav(audio_path)
        embedding = self.encoder.embed_utterance(wav)
        return embedding

    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Similarity score between -1 and 1
        """
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

    def verify_user(self, audio_path: str) -> bool:
        """
        Verify if the speaker in the audio matches the registered owner.

        Args:
            audio_path: Path to the WAV audio file to verify

        Returns:
            True if the speaker is verified as the owner, False otherwise
        """
        # Demo mode - allow all access
        if self.demo_mode:
            return True

        # If voice security is disabled, always return True
        if not self.enabled:
            return True

        # If resemblyzer not available, allow access
        if not _resemblyzer_available or self.encoder is None:
            print("[VoiceGatekeeper] Voice encoder not available - allowing access")
            return True

        # If no owner embedding, warn and allow access (first-time setup)
        if self.owner_embedding is None:
            print("[VoiceGatekeeper] No owner registered - allowing access")
            return True

        # Check if audio file exists
        if not Path(audio_path).exists():
            print(f"[VoiceGatekeeper] Audio file not found: {audio_path}")
            return False

        try:
            # Extract embedding from current audio
            current_embedding = self._extract_embedding(audio_path)

            # Calculate similarity
            similarity = self._cosine_similarity(self.owner_embedding, current_embedding)

            # Debug output
            is_owner = similarity > self.threshold
            status = "OWNER" if is_owner else "STRANGER"
            print(f"[DEBUG] Similarity Score: {similarity:.2f} -> {status}")

            return is_owner

        except Exception as e:
            print(f"[VoiceGatekeeper] Verification error: {e}")
            # On error, deny access for safety
            return False

    def is_ready(self) -> bool:
        """Check if the gatekeeper is properly initialized."""
        if self.demo_mode or not self.enabled:
            return True
        return self.encoder is not None and self.owner_embedding is not None

    def reload_owner_embedding(self):
        """Reload the owner embedding from disk (useful after re-registration)."""
        self._load_owner_embedding()
