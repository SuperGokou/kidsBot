"""
Response parser for extracting commands from LLM responses.
"""

import re
from typing import Tuple, Dict


def parse_response(response: str) -> Tuple[Dict[str, str], str]:
    """
    Parse LLM response for hidden command tags.
    
    Commands are embedded as XML-like tags:
    - <MODE:story> - Switch to story mode
    - <ACTION:play_sound> - Trigger an action
    
    Returns:
        Tuple of (commands dict, cleaned response text)
    """
    commands = {}
    clean_response = response
    
    # Extract MODE commands
    mode_match = re.search(r'<MODE:(\w+)>', response)
    if mode_match:
        commands['mode'] = mode_match.group(1)
        clean_response = re.sub(r'<MODE:\w+>', '', clean_response)
    
    # Extract ACTION commands
    action_match = re.search(r'<ACTION:(\w+)>', response)
    if action_match:
        commands['action'] = action_match.group(1)
        clean_response = re.sub(r'<ACTION:\w+>', '', clean_response)
    
    # Clean up whitespace
    clean_response = clean_response.strip()
    
    return commands, clean_response
