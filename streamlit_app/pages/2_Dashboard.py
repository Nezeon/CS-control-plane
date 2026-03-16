"""
Dashboard — KPI overview, customer health, recent activity.
"""

import streamlit as st
import pandas as pd
from utils.style import inject_css, health_color, SEVERITY_COLORS
from utils import api

st.set_page_config(page_title="Dashboard | CS Control Plane", page_icon="📊", layout="wide")
inject_css()

if not st.session_state.get("authenticated"):
    st.warning("Please sign in first.")
    st.page_link("app.py", label="Go to Login")
    st.stop()

st.markdown("# 📊 Command Center")

# ── KPI Metrics ──
try:
    stats = api.get_dashboard_stats()
except Exception:
    stats = {}

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Customers", stats.get("total_customers", "—"))
with col2:
    avg_health = stats.get("avg_health_score")
    st.metric("Avg Health", f"{avg_health:.0f}" if avg_health else "—")
with col3:
    st.metric("Open Tickets", stats.get("open_tickets", "—"))
with col4:
    st.metric("Active Alerts", stats.get("active_alerts", "—"))
with col5:
    st.metric("Recent Calls", stats.get("recent_calls", "—"))

st.divider()

# ── Customer Health Table ──
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("### Customer Health Overview")
    try:
        customers = api.get_customers(limit=20)
        if customers:
            rows = []
            for c in customers:
                health = c.get("current_health") or c.get("health_score", 0)
                tier = c.get("tier", "—")
                risk = "At Risk" if health < 40 else ("Watch" if health < 70 else "Healthy")
                rows.append({
                    "Customer": c.get("name", "Unknown"),
                    "Health": int(health),
                    "Tier": tier,
                    "Risk": risk,
                    "ARR": c.get("arr", "—"),
                })

            df = pd.DataFrame(rows)
            df = df.sort_values("Health", ascending=True)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Health": st.column_config.ProgressColumn(
                        "Health",
                        min_value=0,
                        max_value=100,
                        format="%d",
                    ),
                },
            )
        else:
            st.info("No customers found. Run the seed script to populate data.")
    except Exception as e:
        st.error(f"Failed to load customers: {e}")

with col_right:
    st.markdown("### Recent Activity")
    try:
        events = api.get_recent_events(limit=10)
        if events:
            for event in events[:10]:
                event_type = event.get("event_type", "unknown")
                source = event.get("source", "")
                status = event.get("status", "")
                icon = {
                    "jira_ticket_created": "🎫",
                    "fathom_recording_ready": "📞",
                    "daily_health_check": "💊",
                    "ticket_escalated": "🚨",
                    "user_chat_general": "💬",
                    "user_chat_fathom": "💬",
                    "user_chat_health": "💬",
                    "user_chat_ticket": "💬",
                }.get(event_type, "📌")

                st.markdown(f"{icon} **{event_type}** — {status}")
        else:
            st.info("No recent events.")
    except Exception as e:
        st.error(f"Failed to load events: {e}")

st.divider()

# ── Alerts ──
st.markdown("### Active Alerts")
try:
    alerts = api.get_alerts(limit=10)
    if alerts:
        for alert in alerts[:10]:
            severity = alert.get("severity", "medium")
            color = SEVERITY_COLORS.get(severity, "#6B7280")
            title = alert.get("title", "Untitled Alert")
            description = alert.get("description", "")
            customer = alert.get("customer_name", "")

            with st.expander(f"{'🔴' if severity in ('critical', 'P1') else '🟡'} [{severity.upper()}] {title}"):
                if customer:
                    st.markdown(f"**Customer:** {customer}")
                st.markdown(description)
    else:
        st.success("No active alerts.")
except Exception as e:
    st.error(f"Failed to load alerts: {e}")
