"""
Dependency injection and global state management.
"""

from typing import Optional

# Global instances (initialized on startup)
_config: Optional[dict] = None
_llm_client = None
_memory_manager = None
_voice_gatekeeper = None


def init_dependencies(config: dict):
    """Initialize all dependencies with config."""
    global _config, _llm_client, _memory_manager, _voice_gatekeeper
    
    _config = config
    
    # Import here to avoid circular imports
    from .llm_client import DeepSeekClient
    from .memory import MemoryManager
    from .voice_security import VoiceGatekeeper
    
    # Initialize LLM client
    try:
        _llm_client = DeepSeekClient(config)
        print("[Dependencies] LLM client initialized")
    except Exception as e:
        print(f"[Dependencies] LLM client failed: {e}")
    
    # Initialize memory manager
    try:
        _memory_manager = MemoryManager(config)
        print("[Dependencies] Memory manager initialized")
    except Exception as e:
        print(f"[Dependencies] Memory manager failed: {e}")
    
    # Initialize voice gatekeeper
    try:
        _voice_gatekeeper = VoiceGatekeeper(config)
        print("[Dependencies] Voice gatekeeper initialized")
    except Exception as e:
        print(f"[Dependencies] Voice gatekeeper failed: {e}")
    
    print("[Dependencies] All services initialized")


def get_config() -> Optional[dict]:
    """Get configuration."""
    return _config


def get_llm_client():
    """Get LLM client instance."""
    return _llm_client


def get_memory_manager():
    """Get memory manager instance."""
    return _memory_manager


def get_voice_gatekeeper():
    """Get voice gatekeeper instance."""
    return _voice_gatekeeper
