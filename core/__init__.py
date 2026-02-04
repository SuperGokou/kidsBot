# Core modules for KidBot
from .memory_rag import MemoryManager, get_memory_manager
from .llm_client import DeepSeekClient
from .voice_security import VoiceGatekeeper, get_voice_gatekeeper
from .response_parser import parse_response
from .registration import register_owner_from_audio, check_owner_registered
from .utils import (
    load_config,
    safe_remove_file,
    temp_audio_file,
    get_config_value,
    EXIT_PHRASES,
    DEFAULT_TTS_VOICE,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
)

__all__ = [
    "MemoryManager",
    "get_memory_manager",
    "DeepSeekClient",
    "VoiceGatekeeper",
    "get_voice_gatekeeper",
    "parse_response",
    "register_owner_from_audio",
    "check_owner_registered",
    "load_config",
    "safe_remove_file",
    "temp_audio_file",
    "get_config_value",
    "EXIT_PHRASES",
    "DEFAULT_TTS_VOICE",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_TOKENS",
]
