# UI components for KidBot
from .styles import CUSTOM_CSS, get_custom_css
from .components import (
    HTML_GRADIENT_BLOBS,
    HTML_HEADER,
    SVG_MICROPHONE,
    get_robot_html,
    get_sidebar_html,
    get_jarvis_status_html,
    get_mode_header_html,
    get_not_setup_html,
    get_setup_prompt_html,
)
from .views.settings_view import render_settings_view

__all__ = [
    # Styles
    "CUSTOM_CSS",
    "get_custom_css",
    # Components
    "HTML_GRADIENT_BLOBS",
    "HTML_HEADER",
    "SVG_MICROPHONE",
    "get_robot_html",
    "get_sidebar_html",
    "get_jarvis_status_html",
    "get_mode_header_html",
    "get_not_setup_html",
    "get_setup_prompt_html",
    # Views
    "render_settings_view",
]
