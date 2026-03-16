"""
Customers — Browse customer portfolio with health scores and details.
"""

import streamlit as st
import pandas as pd
from utils.style import inject_css, health_color
from utils import api

st.set_page_config(page_title="Customers | CS Control Plane", page_icon="👥", layout="wide")
inject_css()

if not st.session_state.get("authenticated"):
    st.warning("Please sign in first.")
    st.page_link("app.py", label="Go to Login")
    st.stop()

st.markdown("# 👥 Customer Portfolio")

# ── Filters ──
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search = st.text_input("Search customers", placeholder="Type a customer name...")
with col2:
    risk_filter = st.selectbox("Risk Level", ["All", "Healthy", "Watch", "At Risk"])
with col3:
    tier_filter = st.selectbox("Tier", ["All", "Enterprise", "Growth", "Starter"])

# ── Load Customers ──
try:
    customers = api.get_customers(limit=50)
except Exception as e:
    st.error(f"Failed to load customers: {e}")
    customers = []

# Apply filters
filtered = customers
if search:
    filtered = [c for c in filtered if search.lower() in c.get("name", "").lower()]
if risk_filter != "All":
    def _risk(c):
        h = c.get("current_health") or c.get("health_score", 50)
        if h < 40:
            return "At Risk"
        elif h < 70:
            return "Watch"
        return "Healthy"
    filtered = [c for c in filtered if _risk(c) == risk_filter]
if tier_filter != "All":
    filtered = [c for c in filtered if c.get("tier", "").lower() == tier_filter.lower()]

# ── Customer Cards ──
if filtered:
    for i in range(0, len(filtered), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(filtered):
                break
            c = filtered[idx]
            health = c.get("current_health") or c.get("health_score", 0)
            risk = "At Risk" if health < 40 else ("Watch" if health < 70 else "Healthy")
            risk_icon = "🔴" if risk == "At Risk" else ("🟡" if risk == "Watch" else "🟢")

            with col:
                with st.container(border=True):
                    st.markdown(f"### {c.get('name', 'Unknown')}")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Health", f"{int(health)}")
                    m2.metric("Tier", c.get("tier", "—"))
                    m3.metric("Risk", f"{risk_icon} {risk}")

                    st.caption(f"ARR: {c.get('arr', '—')} | CSM: {c.get('csm', '—')}")

                    if st.button("View Detail", key=f"detail_{c.get('id', idx)}", use_container_width=True):
                        st.session_state.selected_customer = c
                        st.session_state.selected_customer_id = str(c.get("id"))
else:
    st.info("No customers match your filters.")

# ── Customer Detail ──
if st.session_state.get("selected_customer"):
    st.divider()
    c = st.session_state.selected_customer
    cid = st.session_state.get("selected_customer_id")

    st.markdown(f"## {c.get('name', 'Unknown')} — Detail View")

    tab1, tab2, tab3 = st.tabs(["Health History", "Tickets", "Call Insights"])

    with tab1:
        try:
            scores = api.get_health_scores(cid, days=30) if cid else []
            if scores:
                df = pd.DataFrame(scores)
                if "date" in df.columns and "overall_score" in df.columns:
                    st.line_chart(df.set_index("date")["overall_score"])
                elif "calculated_at" in df.columns and "overall_score" in df.columns:
                    st.line_chart(df.set_index("calculated_at")["overall_score"])
                else:
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No health score history available.")
        except Exception as e:
            st.error(f"Failed to load health scores: {e}")

    with tab2:
        try:
            tickets = api.get_tickets(limit=20)
            customer_tickets = [t for t in tickets if str(t.get("customer_id")) == cid]
            if customer_tickets:
                for t in customer_tickets[:10]:
                    sev = t.get("severity", "P3")
                    with st.expander(f"[{sev}] {t.get('title', 'Untitled')} — {t.get('status', '?')}"):
                        st.markdown(t.get("description", "No description"))
            else:
                st.info("No tickets for this customer.")
        except Exception:
            st.info("No tickets available.")

    with tab3:
        try:
            insights = api.get_call_insights(limit=50)
            customer_insights = [i for i in insights if str(i.get("customer_id")) == cid]
            if customer_insights:
                for ins in customer_insights[:10]:
                    sentiment = ins.get("sentiment", "neutral")
                    icon = "😊" if sentiment == "positive" else ("😐" if sentiment == "neutral" else "😟")
                    with st.expander(f"{icon} {ins.get('call_date', '?')} — {sentiment}"):
                        st.markdown(ins.get("summary", "No summary"))
                        if ins.get("action_items"):
                            st.markdown("**Action Items:**")
                            for item in ins["action_items"]:
                                st.markdown(f"- {item}")
            else:
                st.info("No call insights for this customer.")
        except Exception:
            st.info("No call insights available.")
