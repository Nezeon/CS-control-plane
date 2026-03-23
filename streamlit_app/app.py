"""
CS Control Plane — Streamlit Dashboard
Main entry point. Run with: streamlit run app.py
"""

import streamlit as st
from utils.style import inject_css
from utils import api

st.set_page_config(
    page_title="CS Control Plane",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Auth State ──
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None

# ── Login Page ──
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# CS Control Plane")
        st.markdown("*AI-Powered Customer Success Orchestration*")
        st.divider()

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                try:
                    result = api.login(email, password)
                    st.session_state.authenticated = True
                    st.session_state.user = result.get("user", {"email": email})
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

        st.caption("Sign in with your admin credentials")
    st.stop()

# ── Sidebar ──
with st.sidebar:
    st.markdown("### CS Control Plane")
    user = st.session_state.user
    if user:
        st.caption(f"Signed in as **{user.get('full_name', user.get('email', '?'))}**")
    st.divider()

    st.page_link("app.py", label="Home", icon="🏠")
    st.page_link("pages/1_Ask.py", label="Ask AI", icon="💬")
    st.page_link("pages/2_Dashboard.py", label="Dashboard", icon="📊")
    st.page_link("pages/3_Customers.py", label="Customers", icon="👥")
    st.page_link("pages/4_Agents.py", label="Agents", icon="🤖")
    st.page_link("pages/5_Tickets.py", label="Tickets", icon="🎫")

    st.divider()
    if st.button("Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

# ── Home Page ──
st.markdown("# Welcome to CS Control Plane")
st.markdown("*Your AI-powered command center for Customer Success*")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Quick Actions")
    st.markdown("""
    - **Ask AI** — Query the system about customers, tickets, calls
    - **Dashboard** — KPI overview, health scores, activity feed
    - **Customers** — Browse customer portfolio with health scores
    - **Agents** — View the 4-tier AI agent hierarchy
    - **Tickets** — Browse support tickets and triage status
    """)

with col2:
    st.markdown("### System Status")
    try:
        health = api.get("/health")
        st.success(f"Backend: {health.get('status', 'unknown')} (v{health.get('version', '?')})")
    except Exception as e:
        st.error(f"Backend unreachable: {e}")

    try:
        customers = api.get_customers(limit=1)
        st.info(f"Database: Connected (seeded)")
    except Exception:
        st.warning("Database: No data or connection error")
