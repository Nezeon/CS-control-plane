"""
Agents — View the 4-tier AI agent hierarchy.
"""

import streamlit as st
from utils.style import inject_css, TIER_COLORS, LANE_COLORS
from utils import api

st.set_page_config(page_title="Agents | CS Control Plane", page_icon="🤖", layout="wide")
inject_css()

if not st.session_state.get("authenticated"):
    st.warning("Please sign in first.")
    st.page_link("app.py", label="Go to Login")
    st.stop()

st.markdown("# 🤖 Agent Hierarchy")
st.markdown("13 AI agents organized in a 4-tier hierarchy: Supervisor → Lane Leads → Specialists → Foundation")

# ── Load Agents ──
try:
    agents = api.get_agents()
except Exception as e:
    st.error(f"Failed to load agents: {e}")
    agents = []

if not agents:
    st.info("No agent data available. Make sure the backend is running.")
    st.stop()

# ── Group by Tier ──
tiers = {1: [], 2: [], 3: [], 4: []}
for agent in agents:
    tier = agent.get("tier", 3)
    tiers[tier].append(agent)

tier_names = {
    1: "Tier 1 — Supervisor",
    2: "Tier 2 — Lane Leads",
    3: "Tier 3 — Specialists",
    4: "Tier 4 — Foundation",
}

for tier_num in [1, 2, 3, 4]:
    tier_agents = tiers.get(tier_num, [])
    if not tier_agents:
        continue

    color = TIER_COLORS.get(tier_num, "#64748B")
    st.markdown(f"### <span style='color: {color}'>{tier_names[tier_num]}</span>", unsafe_allow_html=True)

    cols = st.columns(min(len(tier_agents), 4))
    for i, agent in enumerate(tier_agents):
        with cols[i % len(cols)]:
            with st.container(border=True):
                name = agent.get("name", agent.get("agent_id", "Unknown"))
                agent_id = agent.get("agent_id", "")
                lane = agent.get("lane", "")
                role = agent.get("role", "")
                personality = agent.get("personality", "")
                traits = agent.get("traits", [])
                tools = agent.get("tools", [])

                lane_color = LANE_COLORS.get(lane, "#64748B")

                st.markdown(f"**{name}**")
                st.caption(f"`{agent_id}` · <span style='color: {lane_color}'>{lane}</span>", unsafe_allow_html=True)

                if role:
                    st.markdown(f"*{role}*")

                if personality:
                    st.markdown(f"_{personality[:120]}{'...' if len(personality) > 120 else ''}_")

                if traits:
                    trait_str = " · ".join(traits[:5])
                    st.caption(f"Traits: {trait_str}")

                if tools:
                    tool_str = " · ".join(tools[:5])
                    st.caption(f"Tools: {tool_str}")

    st.divider()
