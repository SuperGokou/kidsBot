"""
Response Parser for KidBot

Extracts hidden command tags from LLM responses and returns
clean text for TTS along with parsed commands.

Tag Protocol:
- Mode switches: [[MODE: story]], [[MODE: game]], etc.
- Actions: [[ACTION: nod]], [[ACTION: dance]], etc.
"""

import re
from typing import Optional


# Valid modes and actions for validation
VALID_MODES = {"chat", "story", "learning", "game"}
VALID_ACTIONS = {"nod", "shake_head", "dance", "happy", "sad", "wave", "think", "celebrate"}


def parse_response(full_text: str) -> tuple[dict[str, Optional[str]], str]:
    """
    Parse LLM response to extract hidden commands and clean text.

    Args:
        full_text: Raw response from LLM containing potential [[...]] tags

    Returns:
        Tuple of (commands_dict, clean_text)
        - commands_dict: {'mode': 'story' or None, 'action': 'happy' or None}
        - clean_text: Text with all tags removed, ready for TTS
    """
    commands = {
        "mode": None,
        "action": None
    }

    if not full_text:
        return commands, ""

    # Pattern to match [[TAG: value]] format
    tag_pattern = r'\[\[([A-Z_]+):\s*([^\]]+)\]\]'

    # Find all tags
    matches = re.findall(tag_pattern, full_text, re.IGNORECASE)

    for tag_type, tag_value in matches:
        tag_type = tag_type.upper().strip()
        tag_value = tag_value.lower().strip()

        if tag_type == "MODE":
            if tag_value in VALID_MODES:
                commands["mode"] = tag_value
            else:
                print(f"[Parser] Unknown mode: {tag_value}")

        elif tag_type == "ACTION":
            if tag_value in VALID_ACTIONS:
                commands["action"] = tag_value
            else:
                print(f"[Parser] Unknown action: {tag_value}")

    # Remove all tags from text for TTS
    clean_text = re.sub(r'\[\[[^\]]+\]\]', '', full_text)

    # Clean up extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return commands, clean_text


def extract_tags_only(full_text: str) -> list[tuple[str, str]]:
    """
    Extract just the tags from text without processing.

    Args:
        full_text: Raw response text

    Returns:
        List of (tag_type, tag_value) tuples
    """
    tag_pattern = r'\[\[([A-Z_]+):\s*([^\]]+)\]\]'
    return re.findall(tag_pattern, full_text, re.IGNORECASE)


def format_tag(tag_type: str, value: str) -> str:
    """
    Format a tag for output.

    Args:
        tag_type: MODE or ACTION
        value: The tag value

    Returns:
        Formatted tag string like [[MODE: story]]
    """
    return f"[[{tag_type.upper()}: {value}]]"
