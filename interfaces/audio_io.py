"""
Audio Input/Output Manager for KidBot

Handles speech recognition (STT) and text-to-speech (TTS)
for natural voice interaction with VAD-based auto-stop recording.

Note: Microphone features require PyAudio. On platforms where PyAudio
is not available (e.g., Streamlit Cloud), microphone features are disabled
but TTS playback still works. Use st.audio_input() for browser-based audio.
"""

import asyncio
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple

import edge_tts
import pygame
import speech_recognition as sr

from core.utils import (
    DEFAULT_TTS_VOICE,
    DEFAULT_LISTEN_TIMEOUT,
    DEFAULT_ENERGY_THRESHOLD,
    DEFAULT_PAUSE_THRESHOLD,
    DEFAULT_NON_SPEAKING_DURATION,
)

# Check if PyAudio is available (required for microphone access)
PYAUDIO_AVAILABLE = False
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    print("[AudioManager] PyAudio not available - microphone features disabled")
    print("[AudioManager] Use st.audio_input() for browser-based audio capture")


class AudioManager:
    """Manages audio input (microphone) and output (speaker) with VAD support."""

    def __init__(self, config: dict, auto_calibrate: bool = True):
        """
        Initialize the Audio Manager.

        Args:
            config: Configuration dictionary from config.yaml
            auto_calibrate: If True, calibrate microphone on startup
        """
        self.config = config
        audio_config = config.get("audio", {})

        # Track if microphone is available
        self._microphone_available = PYAUDIO_AVAILABLE

        # TTS settings
        self.tts_voice = audio_config.get("tts_voice", DEFAULT_TTS_VOICE)
        self.temp_audio_file = audio_config.get("temp_audio_file", "temp_output.mp3")

        # STT settings - VAD-based
        self.listen_timeout = audio_config.get("listen_timeout", DEFAULT_LISTEN_TIMEOUT)
        self.phrase_time_limit = audio_config.get("phrase_time_limit", 10)  # 10 seconds for long sentences

        # Continuous mode settings
        self._continuous_mode = False
        self._stop_requested = False
        self._is_listening = False
        self._is_calibrated = False

        # Initialize speech recognizer with HIGH SENSITIVITY settings
        self.recognizer = sr.Recognizer()

        # Energy threshold - LOW value for high sensitivity (300 is good for quiet rooms)
        # This will be auto-adjusted if dynamic_energy_threshold is True
        self.recognizer.energy_threshold = audio_config.get("energy_threshold", DEFAULT_ENERGY_THRESHOLD)

        # Dynamic energy adjustment - auto-calibrates to ambient noise
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15  # React faster to volume changes
        self.recognizer.dynamic_energy_ratio = 1.5

        # Pause detection - how long silence before stopping
        self.recognizer.pause_threshold = DEFAULT_PAUSE_THRESHOLD
        self.recognizer.operation_timeout = None
        self.recognizer.phrase_threshold = 0.3  # Minimum seconds to consider as speech
        self.recognizer.non_speaking_duration = DEFAULT_NON_SPEAKING_DURATION

        # Initialize pygame mixer for audio playback
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Ensure temp directory exists
        self.temp_dir = Path(tempfile.gettempdir())

        # Auto-calibrate microphone on startup (only if PyAudio available)
        if auto_calibrate and self._microphone_available:
            self.calibrate_noise()

    def is_microphone_available(self) -> bool:
        """Check if microphone features are available (PyAudio installed)."""
        return self._microphone_available

    def calibrate_noise(self, duration: float = 2.0) -> bool:
        """
        Calibrate microphone for ambient noise level.

        Should be called at startup or when environment changes.
        This sets the energy_threshold based on actual background noise.

        Args:
            duration: Seconds to sample ambient noise (default 2.0)

        Returns:
            True if calibration succeeded, False otherwise
        """
        if not self._microphone_available:
            print("[Mic] Calibration skipped - PyAudio not available")
            return False

        print(f"[Mic] Calibrating background noise... Please stay silent for {duration} seconds.")

        try:
            with sr.Microphone() as source:
                # Sample ambient noise and set threshold accordingly
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                self._is_calibrated = True

                # Log the calibrated threshold
                print(f"[Mic] Calibration complete. Energy threshold: {self.recognizer.energy_threshold:.0f}")
                return True

        except OSError as e:
            print(f"[Mic] Calibration failed - microphone error: {e}")
            self._microphone_available = False
            return False
        except Exception as e:
            print(f"[Mic] Calibration failed: {e}")
            return False

    def is_calibrated(self) -> bool:
        """Check if microphone has been calibrated."""
        return self._is_calibrated

    def listen(self) -> str:
        """
        Listen to the microphone using VAD and convert speech to text.

        Uses Voice Activity Detection to automatically stop when user
        stops speaking (silence detection via pause_threshold).

        Returns:
            Recognized text, or empty string if nothing recognized/timeout
        """
        text, _ = self._listen_internal(save_path=None)
        return text

    def listen_and_save(self, save_path: str) -> Tuple[str, Optional[str]]:
        """
        Listen with VAD, save audio as WAV, and convert speech to text.

        Args:
            save_path: Path to save the WAV audio file

        Returns:
            Tuple of (recognized text, audio file path or None if failed)
        """
        return self._listen_internal(save_path=save_path)

    def _listen_internal(self, save_path: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Internal VAD-based listening method.

        Key behavior:
        - Waits for speech to start (up to listen_timeout)
        - Automatically stops when user pauses (pause_threshold)
        - phrase_time_limit prevents cutting off long sentences

        Args:
            save_path: If provided, save audio to this path

        Returns:
            Tuple of (recognized text, audio file path or None)
        """
        if not self._microphone_available:
            print("[AudioManager] Microphone not available - use st.audio_input() instead")
            return "", None

        if self._stop_requested:
            return "", None

        self._is_listening = True

        try:
            with sr.Microphone() as source:
                # Quick re-calibration if not already calibrated, or brief adjustment
                if not self._is_calibrated:
                    print("[Mic] Quick calibration...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                    self._is_calibrated = True
                else:
                    # Brief adjustment for any environmental changes
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)

                # Listen with VAD - automatically stops on silence
                try:
                    # This blocks until speech is detected and then stops
                    # when pause_threshold seconds of silence occur
                    audio = self.recognizer.listen(
                        source,
                        timeout=self.listen_timeout,  # Max wait for speech to start
                        phrase_time_limit=self.phrase_time_limit  # 10s default - allows long sentences
                    )
                except sr.WaitTimeoutError:
                    # No speech detected within timeout - this is OK
                    self._is_listening = False
                    return "", None

            self._is_listening = False

            # Check if stop was requested during listening
            if self._stop_requested:
                return "", None

            # Save audio to WAV file if path provided
            saved_path = None
            if save_path:
                try:
                    wav_data = audio.get_wav_data()
                    with open(save_path, "wb") as f:
                        f.write(wav_data)
                    saved_path = save_path
                except Exception as e:
                    print(f"[AudioManager] Failed to save audio: {e}")

            # Convert speech to text using Google Speech Recognition
            try:
                text = self.recognizer.recognize_google(audio)
                return text.strip(), saved_path
            except sr.UnknownValueError:
                # Speech was not understood
                return "", saved_path
            except sr.RequestError as e:
                print(f"[AudioManager] Speech recognition service error: {e}")
                return "", saved_path

        except OSError as e:
            print(f"[AudioManager] Microphone error: {e}")
            self._is_listening = False
            return "", None
        except Exception as e:
            print(f"[AudioManager] Listen error: {e}")
            self._is_listening = False
            return "", None

    def speak(self, text: str):
        """
        Convert text to speech and play it (blocking).

        Args:
            text: The text to speak
        """
        if not text.strip():
            return

        # Use unique filename to avoid permission issues
        unique_name = f"vv_speech_{uuid.uuid4().hex[:8]}.mp3"
        audio_path = self.temp_dir / unique_name

        try:
            # Run async TTS generation
            asyncio.run(self._generate_speech(text, str(audio_path)))

            # Play the audio file
            self._play_audio(str(audio_path))

        except Exception as e:
            print(f"[AudioManager] Speech synthesis error: {e}")

        finally:
            # Unload music before cleanup
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

            # Clean up temp file
            try:
                if audio_path.exists():
                    time.sleep(0.1)
                    os.remove(audio_path)
            except Exception:
                pass

    async def _generate_speech(self, text: str, output_path: str):
        """Generate speech audio using edge-tts."""
        communicate = edge_tts.Communicate(text, self.tts_voice)
        await communicate.save(output_path)

    def _play_audio(self, audio_path: str):
        """Play an audio file using pygame mixer (blocking)."""
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()

            # Wait for playback to finish, but check for stop requests
            while pygame.mixer.music.get_busy():
                if self._stop_requested:
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)

        except Exception as e:
            print(f"[AudioManager] Audio playback error: {e}")

    def speak_async(self, text: str):
        """Non-blocking version of speak."""
        if not text.strip():
            return

        audio_path = self.temp_dir / self.temp_audio_file

        try:
            asyncio.run(self._generate_speech(text, str(audio_path)))
            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()
        except Exception as e:
            print(f"[AudioManager] Async speech error: {e}")

    def stop_speaking(self):
        """Stop any currently playing audio."""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def is_speaking(self) -> bool:
        """Check if audio is currently playing."""
        return pygame.mixer.music.get_busy()

    def is_listening(self) -> bool:
        """Check if currently listening."""
        return self._is_listening

    def set_volume(self, volume: float):
        """Set the playback volume (0.0 to 1.0)."""
        volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(volume)

    def test_microphone(self) -> bool:
        """Test if the microphone is working."""
        if not self._microphone_available:
            print("[AudioManager] Microphone test skipped - PyAudio not available")
            return False

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                return True
        except Exception as e:
            print(f"[AudioManager] Microphone test failed: {e}")
            self._microphone_available = False
            return False

    def test_speaker(self) -> bool:
        """Test if the speaker is working."""
        try:
            self.speak("Hello!")
            return True
        except Exception as e:
            print(f"[AudioManager] Speaker test failed: {e}")
            return False

    def cleanup(self):
        """Clean up audio resources."""
        self._stop_requested = True
        self._is_listening = False
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                pygame.mixer.quit()
        except Exception:
            pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.cleanup()
        return False

    def set_continuous_mode(self, enabled: bool):
        """
        Enable or disable continuous conversation mode.

        Args:
            enabled: True to enable, False to disable
        """
        self._continuous_mode = enabled
        if enabled:
            # Extended timeouts for continuous listening
            self.listen_timeout = 15  # Wait longer for speech to start
            self.phrase_time_limit = 15  # Allow longer sentences in continuous mode
            self.recognizer.pause_threshold = 0.6  # Still fast but slightly longer for continuous
        else:
            # Restore optimized defaults
            self.listen_timeout = 10
            self.phrase_time_limit = 10  # 10 seconds for normal mode
            self.recognizer.pause_threshold = 0.5

    def request_stop(self):
        """Request to stop listening/speaking."""
        self._stop_requested = True
        self._is_listening = False
        self.stop_speaking()

    def clear_stop_request(self):
        """Clear the stop request flag."""
        self._stop_requested = False

    def is_stop_requested(self) -> bool:
        """Check if stop has been requested."""
        return self._stop_requested

    def is_continuous_mode(self) -> bool:
        """Check if continuous mode is enabled."""
        return self._continuous_mode
