"""
Tickets — Browse support tickets with filtering.
"""

import streamlit as st
import pandas as pd
from utils.style import inject_css, SEVERITY_COLORS
from utils import api

st.set_page_config(page_title="Tickets | CS Control Plane", page_icon="🎫", layout="wide")
inject_css()

if not st.session_state.get("authenticated"):
    st.warning("Please sign in first.")
    st.page_link("app.py", label="Go to Login")
    st.stop()

st.markdown("# 🎫 Ticket Warroom")

# ── Filters ──
col1, col2, col3 = st.columns(3)
with col1:
    severity_filter = st.selectbox("Severity", ["All", "P1", "P2", "P3", "P4"])
with col2:
    status_filter = st.selectbox("Status", ["All", "open", "in_progress", "escalated", "resolved", "closed"])
with col3:
    search = st.text_input("Search tickets", placeholder="Search by title or customer...")

# ── Load Tickets ──
try:
    tickets = api.get_tickets(limit=100)
except Exception as e:
    st.error(f"Failed to load tickets: {e}")
    tickets = []

# Apply filters
filtered = tickets
if severity_filter != "All":
    filtered = [t for t in filtered if t.get("severity") == severity_filter]
if status_filter != "All":
    filtered = [t for t in filtered if t.get("status") == status_filter]
if search:
    lower = search.lower()
    filtered = [t for t in filtered if lower in t.get("title", "").lower() or lower in t.get("customer_name", "").lower()]

# ── KPI Row ──
col1, col2, col3, col4 = st.columns(4)
p1_count = len([t for t in tickets if t.get("severity") == "P1"])
open_count = len([t for t in tickets if t.get("status") in ("open", "in_progress")])
escalated = len([t for t in tickets if t.get("status") == "escalated"])
resolved = len([t for t in tickets if t.get("status") in ("resolved", "closed")])

col1.metric("P1 Critical", p1_count)
col2.metric("Open", open_count)
col3.metric("Escalated", escalated)
col4.metric("Resolved", resolved)

st.divider()

# ── Ticket Table ──
if filtered:
    rows = []
    for t in filtered:
        rows.append({
            "Severity": t.get("severity", "P3"),
            "Title": t.get("title", "Untitled"),
            "Customer": t.get("customer_name", "—"),
            "Status": t.get("status", "—"),
            "Assignee": t.get("assignee", "—"),
            "Created": t.get("created_at", "—")[:10] if t.get("created_at") else "—",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Ticket Detail ──
    st.divider()
    st.markdown("### Ticket Details")
    for t in filtered[:20]:
        sev = t.get("severity", "P3")
        sev_icon = "🔴" if sev == "P1" else ("🟠" if sev == "P2" else ("🟡" if sev == "P3" else "⚪"))

        with st.expander(f"{sev_icon} [{sev}] {t.get('title', 'Untitled')} — {t.get('status', '?')}"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Customer:** {t.get('customer_name', '—')}")
                st.markdown(f"**Assignee:** {t.get('assignee', '—')}")
                st.markdown(f"**Created:** {t.get('created_at', '—')}")
            with col_b:
                st.markdown(f"**Status:** {t.get('status', '—')}")
                st.markdown(f"**SLA Breach:** {'Yes 🚨' if t.get('sla_breach') else 'No'}")

            st.markdown("---")
            st.markdown(t.get("description", "No description available."))

            if t.get("troubleshoot_result"):
                st.markdown("**Troubleshoot Result:**")
                st.json(t["troubleshoot_result"]) if isinstance(t["troubleshoot_result"], dict) else st.markdown(str(t["troubleshoot_result"]))
else:
    st.info("No tickets match your filters.")
