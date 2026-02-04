"""
CSS Styles for KidBot UI

All CSS styles for the Streamlit web interface.
Organized by component for easy maintenance.
"""

# =============================================================================
# CSS Variables
# =============================================================================
CSS_VARIABLES = """
:root {
    --bg-cream: #fffdf5;
    --accent-orange: #FF9F1C;
    --accent-orange-light: #FFD166;
    --text-brown: #5D4E37;
    --text-muted: #8B7355;
    --green-status: #4CAF50;
    --white: #ffffff;
    --shadow-light: rgba(255,255,255,0.9);
    --shadow-dark: rgba(0,0,0,0.1);
    --sidebar-width: 90px;
    --header-height: 70px;
    --font-family: 'Nunito', 'Quicksand', 'Comic Sans MS', sans-serif;
}
"""

# =============================================================================
# CSS Background - Cream base + gradient blobs
# =============================================================================
CSS_BACKGROUND = """
.stApp {
    background-color: var(--bg-cream) !important;
    overflow-x: hidden;
}

.gradient-blob {
    position: fixed;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.5;
    z-index: 0;
    pointer-events: none;
}

.blob-1 {
    width: 400px;
    height: 400px;
    background: linear-gradient(135deg, #FFD166 0%, #FF9F1C 100%);
    top: -100px;
    right: -100px;
}

.blob-2 {
    width: 350px;
    height: 350px;
    background: linear-gradient(135deg, #A8E6CF 0%, #88D8B0 100%);
    bottom: 100px;
    left: -100px;
}

.blob-3 {
    width: 300px;
    height: 300px;
    background: linear-gradient(135deg, #DDA0DD 0%, #DA70D6 100%);
    top: 40%;
    right: -50px;
}

.blob-4 {
    width: 250px;
    height: 250px;
    background: linear-gradient(135deg, #87CEEB 0%, #4FC3F7 100%);
    bottom: -50px;
    left: 30%;
}
"""

# =============================================================================
# CSS Sidebar - Compact Jelly Design
# =============================================================================
CSS_SIDEBAR = """
/* Sidebar container - soft gradient background */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f5f0e8 0%, #ebe6de 100%) !important;
    padding-top: 20px !important;
    display: block !important;
    visibility: visible !important;
    min-width: 180px !important;
    max-width: 200px !important;
}

/* Sidebar inner content - center everything */
[data-testid="stSidebar"] > div:first-child {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    height: 100% !important;
    padding-top: 40px !important;
}

/* Button container - center and add spacing */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 10px !important;
    padding: 0 16px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    width: 100% !important;
}

/* Jelly button - Default state (cream/white with soft shadow) */
[data-testid="stSidebar"] .stButton {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}

[data-testid="stSidebar"] .stButton > button {
    width: 130px !important;
    border-radius: 15px !important;
    background: #FFF8E1 !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    border: none !important;
    padding: 10px 18px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    color: #5D4E37 !important;
    cursor: pointer;
    transition: all 0.2s ease !important;
}

/* Jelly button - Hover state (orange background, white text, pop effect) */
[data-testid="stSidebar"] .stButton > button:hover {
    background: #FFAF45 !important;
    color: white !important;
    transform: scale(1.02) !important;
    box-shadow: 0 6px 12px rgba(255,175,69,0.3) !important;
}

/* Jelly button - Active/pressed state */
[data-testid="stSidebar"] .stButton > button:active {
    transform: scale(0.98) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
}

/* Active page button styling (when using session state) */
[data-testid="stSidebar"] .stButton > button[data-active="true"],
[data-testid="stSidebar"] .active-nav-btn > button {
    background: #FFAF45 !important;
    color: white !important;
    box-shadow: 0 4px 8px rgba(255,175,69,0.25) !important;
}

/* Sidebar section headers */
[data-testid="stSidebar"] .stMarkdown h3,
[data-testid="stSidebar"] .stMarkdown h4 {
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    color: #8B7355 !important;
    margin: 16px 0 8px 0 !important;
    padding-left: 4px !important;
}

/* Sidebar divider */
[data-testid="stSidebar"] hr {
    margin: 12px 0 !important;
    border-color: rgba(93, 78, 55, 0.1) !important;
}
"""

# =============================================================================
# CSS Header - Status bar styling
# =============================================================================
CSS_HEADER = """
.main-header {
    background: rgba(255,253,245,0.8);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 20px;
    border-radius: 20px;
    margin-bottom: 20px;
    box-shadow: 4px 4px 15px rgba(0,0,0,0.05), -2px -2px 10px rgba(255,255,255,0.8);
}

.status-card {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(10px);
    padding: 10px 20px;
    border-radius: 25px;
    box-shadow:
        4px 4px 10px rgba(0,0,0,0.05),
        -2px -2px 8px rgba(255,255,255,0.8);
}

.status-dot {
    width: 12px;
    height: 12px;
    background: var(--green-status);
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(76,175,80,0.5);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.1); }
}

.status-text {
    font-family: var(--font-family);
    font-size: 14px;
    color: var(--text-brown);
    font-weight: 600;
}

.user-avatar {
    width: 45px;
    height: 45px;
    border-radius: 50%;
    background: linear-gradient(135deg, #e0d8d0 0%, #d0c8c0 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow:
        3px 3px 8px rgba(0,0,0,0.08),
        -2px -2px 6px rgba(255,255,255,0.9);
}

.user-avatar svg {
    width: 24px;
    height: 24px;
    stroke: #8B7355;
    stroke-width: 2;
    fill: none;
}

/* Header controls - positioned in header */
.header-controls {
    display: flex;
    align-items: center;
    gap: 10px;
}

.header-btn {
    font-family: var(--font-family);
    font-size: 12px;
    font-weight: 600;
    color: var(--text-brown);
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(10px);
    border: none;
    padding: 8px 16px;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow:
        3px 3px 8px rgba(0,0,0,0.05),
        -2px -2px 6px rgba(255,255,255,0.8);
}

.header-btn:hover {
    transform: scale(1.02);
    background: rgba(255,255,255,0.8);
}

/* Top controls - container that holds the buttons */
.top-controls-wrapper {
    position: fixed !important;
    top: 12px !important;
    right: 80px !important;
    z-index: 1001 !important;
    display: flex !important;
    gap: 10px !important;
}

/* Hide the default Streamlit container structure for top controls */
.top-controls-wrapper .stColumns,
.top-controls-wrapper [data-testid="column"] {
    width: auto !important;
    flex: none !important;
}

.top-controls-wrapper .stButton > button {
    font-size: 12px !important;
    padding: 8px 16px !important;
    border-radius: 20px !important;
    background: rgba(255,255,255,0.7) !important;
    backdrop-filter: blur(10px);
    box-shadow:
        3px 3px 8px rgba(0,0,0,0.05),
        -2px -2px 6px rgba(255,255,255,0.8) !important;
    white-space: nowrap !important;
}
"""

# =============================================================================
# CSS Robot - Circular frame with glow effect
# =============================================================================
CSS_ROBOT = """
.robot-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    margin-top: 20px;
}

.robot-frame {
    width: 280px;
    height: 280px;
    border-radius: 50%;
    background: linear-gradient(145deg, #f8f4ec, #ebe6de);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow:
        20px 20px 40px rgba(0,0,0,0.08),
        -15px -15px 35px rgba(255,255,255,0.9),
        inset -8px -8px 20px rgba(0,0,0,0.03),
        inset 8px 8px 20px rgba(255,255,255,0.7);
}

.robot-frame::before {
    content: '';
    position: absolute;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,159,28,0.15) 0%, transparent 70%);
    z-index: -1;
    animation: glow 3s ease-in-out infinite;
}

@keyframes glow {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.05); opacity: 0.8; }
}

.robot-inner {
    width: 240px;
    height: 240px;
    border-radius: 50%;
    background: linear-gradient(145deg, #fffdf5, #f5f0e8);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    box-shadow:
        inset 6px 6px 15px rgba(0,0,0,0.05),
        inset -6px -6px 15px rgba(255,255,255,0.8);
}

.robot-placeholder {
    font-size: 100px;
    opacity: 0.8;
}

.robot-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.robot-name {
    font-family: var(--font-family);
    font-size: 28px;
    font-weight: 700;
    color: var(--text-brown);
    margin-top: 20px;
    text-align: center;
}

.robot-status {
    font-family: var(--font-family);
    font-size: 16px;
    color: var(--text-muted);
    margin-top: 5px;
}
"""

# =============================================================================
# CSS Mic Button - Large orange gradient button
# =============================================================================
CSS_MIC_BUTTON = """
.mic-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 30px;
    margin-bottom: 20px;
}

.mic-button-wrapper {
    position: relative;
}

.mic-button {
    width: 112px;
    height: 112px;
    border-radius: 50%;
    background: linear-gradient(180deg, #FFD166 0%, #FF9F1C 100%);
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    box-shadow:
        0 10px 30px rgba(255,159,28,0.4),
        0 5px 15px rgba(255,159,28,0.3),
        inset 0 2px 4px rgba(255,255,255,0.4),
        inset 0 -2px 4px rgba(0,0,0,0.1);
}

.mic-button:hover {
    transform: scale(1.05);
    box-shadow:
        0 15px 40px rgba(255,159,28,0.5),
        0 8px 20px rgba(255,159,28,0.4),
        inset 0 2px 4px rgba(255,255,255,0.4),
        inset 0 -2px 4px rgba(0,0,0,0.1);
}

.mic-button:active {
    transform: scale(0.98);
}

.mic-button svg {
    width: 48px;
    height: 48px;
    stroke: white;
    stroke-width: 2.5;
    fill: none;
}

.mic-label {
    font-family: var(--font-family);
    font-size: 14px;
    color: var(--text-muted);
    margin-top: 15px;
    text-align: center;
    width: 100%;
    display: block;
    position: relative;
    left: 0;
    right: 0;
}

/* Style the Streamlit audio input as a circular orange button */
[data-testid="stAudioInput"] {
    display: flex !important;
    justify-content: center !important;
}

[data-testid="stAudioInput"] label {
    display: none !important;
}

/* Make the whole audio input area clickable and styled */
[data-testid="stAudioInput"] > div {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}
"""

# =============================================================================
# CSS Chat - Chat message styling
# =============================================================================
CSS_CHAT = """
.chat-container {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
}

.stChatMessage {
    background: rgba(255,255,255,0.6) !important;
    backdrop-filter: blur(10px);
    border-radius: 20px !important;
    border: none !important;
    padding: 15px !important;
    margin-bottom: 10px !important;
    box-shadow:
        4px 4px 10px rgba(0,0,0,0.03),
        -2px -2px 8px rgba(255,255,255,0.8);
}

[data-testid="stChatMessageContent"] {
    font-family: var(--font-family) !important;
    font-size: 16px !important;
    color: var(--text-brown) !important;
}

/* Chat input */
[data-testid="stChatInput"] {
    position: fixed;
    bottom: 20px;
    left: calc(var(--sidebar-width) + 20px);
    right: 20px;
    z-index: 998;
}

[data-testid="stChatInput"] > div {
    background: rgba(255,255,255,0.8) !important;
    backdrop-filter: blur(10px);
    border-radius: 30px !important;
    border: 2px solid rgba(255,159,28,0.3) !important;
    box-shadow:
        4px 4px 15px rgba(0,0,0,0.05),
        -2px -2px 10px rgba(255,255,255,0.8) !important;
}

[data-testid="stChatInput"] input {
    font-family: var(--font-family) !important;
}

/* Text input fallback styling */
.text-input-section {
    margin-top: 20px;
    padding: 15px;
    background: rgba(255,255,255,0.4);
    border-radius: 20px;
    text-align: center;
}

.text-input-label {
    font-family: var(--font-family);
    font-size: 14px;
    color: var(--text-muted);
    margin-bottom: 10px;
}
"""

# =============================================================================
# CSS Responsive - Tablet/mobile breakpoints
# =============================================================================
CSS_RESPONSIVE = """
@media (max-width: 768px) {
    .custom-sidebar {
        width: 70px;
    }

    .sidebar-logo {
        width: 40px;
        height: 40px;
        font-size: 18px;
    }

    .nav-btn {
        width: 45px;
        height: 45px;
    }

    .main-header {
        left: 70px;
        padding: 0 15px;
    }

    .robot-frame {
        width: 220px;
        height: 220px;
    }

    .robot-inner {
        width: 190px;
        height: 190px;
    }

    .robot-placeholder {
        font-size: 70px;
    }

    .mic-button,
    [data-testid="stAudioInput"] > div {
        width: 90px !important;
        height: 90px !important;
    }
}

@media (max-width: 480px) {
    .custom-sidebar {
        width: 60px;
    }

    .main-header {
        left: 60px;
    }

    .status-card {
        padding: 8px 12px;
    }

    .status-text {
        font-size: 12px;
    }
}
"""

# =============================================================================
# CSS Utilities & Jarvis Animations
# =============================================================================
CSS_UTILITIES = """
/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden !important;}

/* Main content area adjustment */
.main .block-container {
    padding-top: 20px !important;
    padding-right: 20px !important;
    padding-left: 20px !important;
    max-width: 100% !important;
}

/* Font import */
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

/* General text styling */
html, body, [class*="css"] {
    font-family: var(--font-family) !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-family) !important;
    color: var(--text-brown) !important;
}

/* Audio player styling */
audio {
    border-radius: 30px;
}

/* Spinner */
.stSpinner > div {
    border-color: var(--accent-orange) !important;
}

/* Buttons */
.stButton > button {
    font-family: var(--font-family) !important;
    background: linear-gradient(145deg, #f0ebe3, #e5e0d8) !important;
    color: var(--text-brown) !important;
    border: none !important;
    border-radius: 15px !important;
    padding: 10px 25px !important;
    font-weight: 600 !important;
    box-shadow:
        4px 4px 10px rgba(0,0,0,0.08),
        -3px -3px 8px rgba(255,255,255,0.9) !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    transform: scale(1.02) !important;
    box-shadow:
        6px 6px 15px rgba(0,0,0,0.1),
        -4px -4px 10px rgba(255,255,255,0.9) !important;
}

/* Success/Error/Warning */
.stSuccess, .stError, .stWarning {
    border-radius: 15px !important;
    font-family: var(--font-family) !important;
}

/* Dividers */
hr {
    border-color: rgba(0,0,0,0.05) !important;
    margin: 20px 0 !important;
}

/* Jarvis Mode Animations */
@keyframes jarvis-pulse-orange {
    0%, 100% {
        box-shadow: 0 0 0 0 rgba(255, 159, 28, 0.7);
        transform: scale(1);
    }
    50% {
        box-shadow: 0 0 0 20px rgba(255, 159, 28, 0);
        transform: scale(1.05);
    }
}

@keyframes jarvis-spin-blue {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes jarvis-wave-green {
    0%, 100% { transform: scaleY(1); }
    50% { transform: scaleY(1.3); }
}

.jarvis-status-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 15px;
    padding: 20px;
    margin: 20px auto;
    max-width: 300px;
}

.jarvis-indicator {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.jarvis-listening {
    background: linear-gradient(135deg, #FF9F1C, #FFD166);
    animation: jarvis-pulse-orange 1.5s ease-in-out infinite;
}

.jarvis-processing {
    background: linear-gradient(135deg, #3498DB, #5DADE2);
    position: relative;
}

.jarvis-processing::after {
    content: '';
    position: absolute;
    width: 60px;
    height: 60px;
    border: 4px solid transparent;
    border-top-color: white;
    border-radius: 50%;
    animation: jarvis-spin-blue 1s linear infinite;
}

.jarvis-speaking {
    background: linear-gradient(135deg, #2ECC71, #58D68D);
    animation: jarvis-wave-green 0.5s ease-in-out infinite alternate;
}

.jarvis-status-text {
    font-family: var(--font-family);
    font-size: 18px;
    font-weight: 600;
    color: var(--text-brown);
    text-align: center;
}

.jarvis-button-start {
    background: linear-gradient(135deg, #2ECC71, #27AE60) !important;
    color: white !important;
    font-size: 16px !important;
    padding: 15px 40px !important;
    border-radius: 30px !important;
    box-shadow: 0 8px 25px rgba(46, 204, 113, 0.4) !important;
}

.jarvis-button-start:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 12px 35px rgba(46, 204, 113, 0.5) !important;
}

.jarvis-button-stop {
    background: linear-gradient(135deg, #E74C3C, #C0392B) !important;
    color: white !important;
    font-size: 16px !important;
    padding: 15px 40px !important;
    border-radius: 30px !important;
    box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4) !important;
}

.jarvis-button-stop:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 12px 35px rgba(231, 76, 60, 0.5) !important;
}
"""


def get_custom_css() -> str:
    """
    Combine all CSS into a single style block.

    Returns:
        Complete CSS wrapped in <style> tags
    """
    return f"""
<style>
{CSS_VARIABLES}
{CSS_BACKGROUND}
{CSS_SIDEBAR}
{CSS_HEADER}
{CSS_ROBOT}
{CSS_MIC_BUTTON}
{CSS_CHAT}
{CSS_RESPONSIVE}
{CSS_UTILITIES}
</style>
"""


# Pre-built CSS for import
CUSTOM_CSS = get_custom_css()
