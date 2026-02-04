"""
HTML Components for KidBot UI

Reusable HTML templates and component generators.
"""

from typing import Optional


# =============================================================================
# Static HTML Components
# =============================================================================

# Gradient blobs background
HTML_GRADIENT_BLOBS = """
<div class="gradient-blob blob-1"></div>
<div class="gradient-blob blob-2"></div>
<div class="gradient-blob blob-3"></div>
<div class="gradient-blob blob-4"></div>
"""

# Header with status
HTML_HEADER = """
<div class="main-header">
    <div class="status-card">
        <div class="status-dot"></div>
        <span class="status-text">Friendship Status: Connected</span>
    </div>
    <div class="user-avatar">
        <svg viewBox="0 0 24 24">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
        </svg>
    </div>
</div>
"""

# Microphone icon SVG
SVG_MICROPHONE = """
<svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" stroke-width="2" fill="none">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
</svg>
"""


# =============================================================================
# Component Generators
# =============================================================================

def get_robot_html(robot_name: str, image_base64: Optional[str] = None) -> str:
    """
    Generate robot display HTML with optional base64 image.

    Args:
        robot_name: Name of the robot to display
        image_base64: Optional base64-encoded image data

    Returns:
        HTML string for the robot display component
    """
    if image_base64:
        inner_content = f'<img src="data:image/gif;base64,{image_base64}" class="robot-image" alt="Robot">'
    else:
        inner_content = '<div class="robot-placeholder">:)</div>'

    return f"""
    <div class="robot-container">
        <div class="robot-frame">
            <div class="robot-inner">
                {inner_content}
            </div>
        </div>
        <div class="robot-name">{robot_name}</div>
    </div>
    """


def get_sidebar_html(current_mode: str = "chat", current_view: str = "chat") -> str:
    """
    Generate sidebar HTML with correct active state based on current mode.

    Args:
        current_mode: Current conversation mode (chat, story, learning, game)
        current_view: Current view (chat, settings)

    Returns:
        HTML string for the sidebar component
    """
    active_states = {
        "home": "active" if current_mode == "chat" and current_view == "chat" else "",
        "story": "active" if current_mode == "story" else "",
        "learning": "active" if current_mode == "learning" else "",
        "game": "active" if current_mode == "game" else "",
        "settings": "active" if current_view == "settings" else ""
    }

    return f"""
<div class="custom-sidebar">
    <div class="sidebar-logo">V</div>
    <div class="sidebar-nav">
        <div class="nav-btn {active_states['home']}" title="Home">
            <svg viewBox="0 0 24 24">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
        </div>
        <div class="nav-btn {active_states['story']}" title="Stories">
            <svg viewBox="0 0 24 24">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
        </div>
        <div class="nav-btn {active_states['learning']}" title="Learn">
            <svg viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4"/>
                <path d="M12 8h.01"/>
            </svg>
        </div>
        <div class="nav-btn {active_states['game']}" title="Games">
            <svg viewBox="0 0 24 24">
                <rect x="2" y="6" width="20" height="12" rx="2"/>
                <path d="M6 12h4"/>
                <path d="M8 10v4"/>
                <circle cx="17" cy="10" r="1"/>
                <circle cx="15" cy="14" r="1"/>
            </svg>
        </div>
        <div class="nav-btn {active_states['settings']}" title="Settings">
            <svg viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
        </div>
    </div>
</div>
"""


def get_jarvis_status_html(phase: str, status_text: str) -> str:
    """
    Generate Jarvis status indicator HTML.

    Args:
        phase: Current phase (listening, processing, speaking)
        status_text: Text to display below the indicator

    Returns:
        HTML string for the status indicator
    """
    phase_class = {
        "listening": "jarvis-listening",
        "processing": "jarvis-processing",
        "speaking": "jarvis-speaking"
    }.get(phase, "jarvis-listening")

    return f"""
    <div class="jarvis-status-container">
        <div class="jarvis-indicator {phase_class}"></div>
        <div class="jarvis-status-text">{status_text}</div>
    </div>
    """


def get_mode_header_html(mode: str) -> str:
    """
    Generate mode header HTML for non-chat modes.

    Args:
        mode: Current mode (story, learning, game)

    Returns:
        HTML string for the mode header, empty string for chat mode
    """
    if mode == "chat":
        return ""

    mode_config = {
        "story": {"title": "Story Time", "color": "#9B59B6"},
        "learning": {"title": "Learning", "color": "#3498DB"},
        "game": {"title": "Game Time", "color": "#2ECC71"}
    }

    config = mode_config.get(mode)
    if not config:
        return ""

    return f'''
    <div style="
        text-align: center;
        padding: 12px 20px;
        margin: 10px auto 20px auto;
        max-width: 300px;
        background: rgba(255,255,255,0.7);
        border-radius: 20px;
        box-shadow: 4px 4px 15px rgba(0,0,0,0.05), -2px -2px 10px rgba(255,255,255,0.8);
    ">
        <h2 style="
            color: {config["color"]};
            margin: 0;
            font-family: 'Nunito', sans-serif;
            font-size: 22px;
            font-weight: 700;
        ">{config["title"]}</h2>
    </div>
    '''


def get_not_setup_html(robot_name: str) -> str:
    """
    Generate HTML for the not-setup state.

    Args:
        robot_name: Name of the robot

    Returns:
        HTML string for the not-setup display
    """
    return f"""
    <div class="robot-container">
        <div class="robot-frame">
            <div class="robot-inner">
                <div class="robot-placeholder">?</div>
            </div>
        </div>
        <div class="robot-name">Hi! I'm {robot_name}!</div>
        <div class="robot-status">I'm not ready to play yet...</div>
    </div>
    """


def get_setup_prompt_html() -> str:
    """
    Generate HTML for the setup prompt message.

    Returns:
        HTML string for the setup prompt
    """
    return """
    <div style="
        text-align: center;
        padding: 25px;
        background: rgba(255,255,255,0.6);
        backdrop-filter: blur(10px);
        border-radius: 25px;
        max-width: 400px;
        margin: 30px auto;
        box-shadow: 4px 4px 15px rgba(0,0,0,0.05), -2px -2px 10px rgba(255,255,255,0.8);
    ">
        <h3 style="color: #5D4E37; margin-bottom: 10px;">Please ask a grown-up to set me up!</h3>
        <p style="color: #8B7355; margin: 0;">They need to run the admin page first.</p>
    </div>
    """
