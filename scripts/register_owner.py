#!/usr/bin/env python3
"""
Owner Voice Registration Script for KidBot

This script captures the owner's voiceprint for speaker verification.
Run this once to register your voice before using the robot.

Run from project root: python -m scripts.register_owner
Or from scripts dir: python register_owner.py
"""

import os
import sys
import time
from pathlib import Path

import numpy as np
import wave

# Check for PyAudio availability
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

# Add parent directory to path for imports when run directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import load_config


def record_audio(duration: int = 5, sample_rate: int = 16000) -> np.ndarray:
    """
    Record audio from the microphone.

    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate

    Returns:
        Numpy array of audio samples
    """
    chunk = 1024
    audio_format = pyaudio.paInt16
    channels = 1

    p = pyaudio.PyAudio()

    print(f"\nRecording for {duration} seconds...")
    print("Speak now: 'Hello VV, I am your owner'")

    stream = p.open(
        format=audio_format,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk
    )

    frames = []
    for i in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

        # Progress indicator
        progress = int((i + 1) / (sample_rate / chunk * duration) * 20)
        print(f"\r[{'=' * progress}{' ' * (20 - progress)}] {int((i + 1) / (sample_rate / chunk * duration) * 100)}%", end="")

    print("\nRecording complete!")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Convert to numpy array
    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
    return audio_data.astype(np.float32) / 32768.0


def save_wav(audio_data: np.ndarray, file_path: str, sample_rate: int = 16000):
    """Save audio data to WAV file."""
    audio_int16 = (audio_data * 32768).astype(np.int16)

    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


def main():
    """Main registration flow."""
    print("\n" + "=" * 50)
    print("  KidBot - Owner Voice Registration")
    print("=" * 50)

    # Check PyAudio availability
    if not PYAUDIO_AVAILABLE:
        print("\nError: PyAudio is not installed.")
        print("PyAudio is required for microphone access during registration.")
        print("\nTo install PyAudio:")
        print("  Windows: pip install pyaudio")
        print("  macOS:   brew install portaudio && pip install pyaudio")
        print("  Linux:   sudo apt install portaudio19-dev && pip install pyaudio")
        print("\nAlternatively, use the admin web interface for registration.")
        sys.exit(1)

    # Load config
    config = load_config()
    voice_config = config.get("voice_security", {})

    # Setup paths
    embedding_path = voice_config.get(
        "owner_embedding_path",
        "data/voice_prints/owner_embedding.npy"
    )

    # Create directories
    Path(embedding_path).parent.mkdir(parents=True, exist_ok=True)

    # Load resemblyzer model
    print("\nLoading speaker recognition model...")
    from resemblyzer import VoiceEncoder, preprocess_wav

    encoder = VoiceEncoder()
    print("Model loaded successfully!")

    # Prompt for recording
    print("\n" + "-" * 50)
    print("Voice Registration Instructions:")
    print("-" * 50)
    print("1. Make sure you're in a quiet environment")
    print("2. Speak clearly into the microphone")
    print("3. Say: 'Hello VV, I am your owner'")
    print("-" * 50)

    input("\nPress Enter when ready to record...")

    # Record audio
    audio_data = record_audio(duration=5, sample_rate=16000)

    # Save temporary WAV file
    temp_wav = "temp_register.wav"
    save_wav(audio_data, temp_wav, sample_rate=16000)

    # Extract embedding using resemblyzer
    print("\nExtracting voice embedding...")

    # Preprocess and encode
    wav = preprocess_wav(temp_wav)

    if len(wav) < 1600:
        print("Error: Recording too short. Please try again with more speech.")
        os.remove(temp_wav)
        return

    embedding = encoder.embed_utterance(wav)

    # Save embedding
    np.save(embedding_path, embedding)

    print(f"Voice embedding saved to: {embedding_path}")
    print(f"Embedding shape: {embedding.shape}")

    # Cleanup temp file
    try:
        os.remove(temp_wav)
    except Exception:
        pass

    print("\n" + "=" * 50)
    print("  Registration Complete!")
    print("=" * 50)
    print("\nYour voice has been registered successfully.")
    print("The robot will now only respond to your voice.")
    print("\nRun 'python jarvis.py' for continuous conversation mode.")
    print("Or run 'streamlit run app.py' for the web interface.")


if __name__ == "__main__":
    main()
