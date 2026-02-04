"""
Shared Utilities for KidBot

Common utility functions used across multiple modules.
"""

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Generator

import yaml


# =============================================================================
# Constants
# =============================================================================

# Paths
DEFAULT_CONFIG_PATH = "config/config.yaml"
ASSETS_DIR = "assets"

# Audio Configuration
DEFAULT_TTS_VOICE = "en-US-AnaNeural"
DEFAULT_LISTEN_TIMEOUT = 10
DEFAULT_PHRASE_TIMEOUT = None
DEFAULT_ENERGY_THRESHOLD = 300
DEFAULT_PAUSE_THRESHOLD = 0.5
DEFAULT_NON_SPEAKING_DURATION = 0.3

# LLM Configuration
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 256
EXTRACTION_TEMPERATURE = 0.1

# Voice Security
DEFAULT_SIMILARITY_THRESHOLD = 0.25
DEFAULT_OWNER_EMBEDDING_PATH = "data/voice_prints/owner_embedding.npy"

# UI Constants
SIDEBAR_WIDTH = "90px"
HEADER_HEIGHT = "70px"
MIC_BUTTON_SIZE = "112px"
ROBOT_FRAME_SIZE = "280px"

# Responsive Breakpoints
BREAKPOINT_TABLET = 768
BREAKPOINT_MOBILE = 480

# Exit Commands
EXIT_PHRASES = frozenset([
    "goodbye", "bye bye", "bye", "see you", "quit", "exit"
])


# =============================================================================
# File Utilities
# =============================================================================

def safe_remove_file(file_path: str, silent: bool = True) -> bool:
    """
    Safely remove a file, optionally suppressing errors.

    Args:
        file_path: Path to the file to remove
        silent: If True, suppress exceptions and return False on failure

    Returns:
        True if file was removed, False otherwise
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        if not silent:
            raise
        print(f"[Utils] Failed to remove file {file_path}: {e}")
        return False


@contextmanager
def temp_audio_file(suffix: str = ".wav") -> Generator[str, None, None]:
    """
    Context manager for creating and cleaning up temporary audio files.

    Args:
        suffix: File extension for the temp file

    Yields:
        Path to the temporary file
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
        yield tmp_path
    finally:
        if tmp_path:
            safe_remove_file(tmp_path)


# =============================================================================
# Configuration Utilities
# =============================================================================

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the configuration file (relative to project root)

    Returns:
        Configuration dictionary, empty dict if file not found
    """
    # Try relative path first
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # Try relative to this file's parent (project root)
    project_root = Path(__file__).parent.parent
    config_file = project_root / config_path
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # Try /mount/src/kidsbot for Streamlit Cloud
    cloud_path = Path("/mount/src/kidsbot") / config_path
    if cloud_path.exists():
        with open(cloud_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    print(f"[Config] Warning: Config file not found at {config_path}")
    return {}


def get_config_value(config: dict, *keys, default=None):
    """
    Safely get a nested config value.

    Args:
        config: Configuration dictionary
        *keys: Keys to traverse
        default: Default value if not found

    Returns:
        The config value or default
    """
    value = config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
        if value is None:
            return default
    return value


# =============================================================================
# String Utilities
# =============================================================================

def format_banner(title: str, width: int = 50, char: str = "=") -> str:
    """
    Format a banner string for console output.

    Args:
        title: The title text
        width: Total width of the banner
        char: Character to use for borders

    Returns:
        Formatted banner string
    """
    border = char * width
    return f"\n{border}\n  {title}\n{border}"


def format_divider(width: int = 50, char: str = "-") -> str:
    """
    Format a divider string for console output.

    Args:
        width: Width of the divider
        char: Character to use

    Returns:
        Divider string
    """
    return char * width
