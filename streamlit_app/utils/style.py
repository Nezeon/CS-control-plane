"""
Dark theme styling for the CS Control Plane Streamlit app.
"""

# Tier colors
TIER_COLORS = {
    1: "#00F5D4",  # Teal (Supervisor)
    2: "#8B5CF6",  # Violet (Lane Leads)
    3: "#22D3EE",  # Cyan (Specialists)
    4: "#64748B",  # Slate (Foundation)
}

# Lane colors
LANE_COLORS = {
    "control": "#00F5D4",
    "support": "#FBBF24",
    "value": "#34D399",
    "delivery": "#22D3EE",
}

# Severity colors
SEVERITY_COLORS = {
    "P1": "#EF4444",
    "P2": "#F97316",
    "P3": "#EAB308",
    "P4": "#6B7280",
    "critical": "#EF4444",
    "high": "#F97316",
    "medium": "#EAB308",
    "low": "#6B7280",
}

# Health colors
def health_color(score: float) -> str:
    if score >= 70:
        return "#34D399"  # Green
    elif score >= 40:
        return "#FBBF24"  # Amber
    else:
        return "#FB7185"  # Rose


CUSTOM_CSS = """
<style>
    /* Dark void theme */
    .stApp {
        background-color: #0a0a0f;
        color: #e2e8f0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f0f1a;
        border-right: 1px solid rgba(0, 245, 212, 0.1);
    }

    /* Headers */
    h1, h2, h3 {
        color: #f1f5f9 !important;
        font-family: 'Space Grotesk', sans-serif;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: #00F5D4 !important;
        font-family: 'Space Grotesk', sans-serif;
    }

    [data-testid="stMetricDelta"] > div {
        font-family: 'IBM Plex Mono', monospace;
    }

    /* Chat messages */
    .chat-user {
        background: rgba(139, 92, 246, 0.15);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
    }

    .chat-assistant {
        background: rgba(0, 245, 212, 0.08);
        border: 1px solid rgba(0, 245, 212, 0.2);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
    }

    /* Agent tier badges */
    .tier-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
    }

    .tier-1 { background: rgba(0, 245, 212, 0.2); color: #00F5D4; }
    .tier-2 { background: rgba(139, 92, 246, 0.2); color: #8B5CF6; }
    .tier-3 { background: rgba(34, 211, 238, 0.2); color: #22D3EE; }
    .tier-4 { background: rgba(100, 116, 139, 0.2); color: #94A3B8; }

    /* Tables */
    .stDataFrame {
        border: 1px solid rgba(0, 245, 212, 0.1);
        border-radius: 8px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 245, 212, 0.2), rgba(139, 92, 246, 0.2));
        border: 1px solid rgba(0, 245, 212, 0.3);
        color: #e2e8f0;
        border-radius: 8px;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 245, 212, 0.3), rgba(139, 92, 246, 0.3));
        border-color: rgba(0, 245, 212, 0.5);
    }

    /* Status indicators */
    .status-healthy { color: #34D399; }
    .status-watch { color: #FBBF24; }
    .status-at-risk { color: #FB7185; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(15, 15, 26, 0.8);
        border: 1px solid rgba(0, 245, 212, 0.1);
        border-radius: 8px;
    }
</style>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
"""


def inject_css():
    """Call this at the top of every page to apply custom styling."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
