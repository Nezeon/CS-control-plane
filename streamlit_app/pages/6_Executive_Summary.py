"""
Executive Summary — Portfolio trends, risk analysis, and proactive alerts.
"""

import streamlit as st
import pandas as pd
from utils.style import inject_css, health_color, SEVERITY_COLORS
from utils import api

st.set_page_config(page_title="Executive Summary | CS Control Plane", page_icon="📈", layout="wide")
inject_css()

if not st.session_state.get("authenticated"):
    st.warning("Please sign in first.")
    st.page_link("app.py", label="Go to Login")
    st.stop()

st.markdown("# 📈 Executive Summary")

# Period selector
col_period, col_refresh, col_rules = st.columns([2, 1, 1])
with col_period:
    days = st.selectbox("Period", [7, 14, 30, 60, 90], index=2, format_func=lambda d: f"Last {d} days")
with col_refresh:
    refresh = st.button("🔄 Refresh")
with col_rules:
    run_rules = st.button("⚡ Run Alert Rules")

if run_rules:
    with st.spinner("Evaluating alert rules..."):
        try:
            result = api.run_alert_rules()
            created = result.get("alerts_created", 0)
            if created > 0:
                st.success(f"Created {created} new alerts")
                for d in result.get("details", []):
                    st.info(f"**{d['rule']}** — {d['customer']}: {d['title']}")
            else:
                st.info(f"Checked {result.get('rules_checked', 0)} rules — no new alerts triggered")
        except Exception as e:
            st.error(f"Failed to run rules: {e}")

# Load data
try:
    data = api.get_executive_summary(days=days)
except Exception as e:
    st.error(f"Failed to load executive summary: {e}")
    st.stop()

portfolio = data.get("portfolio", {})
health = data.get("health_trends", {})
tickets = data.get("ticket_velocity", {})
sentiment = data.get("sentiment", {})

st.divider()

# ── Portfolio Snapshot ──
st.markdown("### Portfolio Snapshot")
snap_cols = st.columns(4)

risk_dist = portfolio.get("risk_distribution", {})
with snap_cols[0]:
    st.metric("Total Customers", portfolio.get("total_customers", 0))
with snap_cols[1]:
    critical = risk_dist.get("critical", 0) + risk_dist.get("high_risk", 0)
    st.metric("At Risk", critical, delta=None)
with snap_cols[2]:
    st.metric("Watch", risk_dist.get("watch", 0))
with snap_cols[3]:
    healthy = risk_dist.get("healthy", 0) + risk_dist.get("unknown", 0)
    st.metric("Healthy", healthy)

# Tier distribution
tier_dist = portfolio.get("tier_distribution", {})
if tier_dist:
    st.markdown("**By Tier:** " + " · ".join(f"{k}: {v}" for k, v in tier_dist.items()))

st.divider()

# ── Health Trends ──
col_health, col_velocity = st.columns(2)

with col_health:
    st.markdown("### Health Score Trend")
    daily_avg = health.get("daily_avg", [])
    if daily_avg:
        df_health = pd.DataFrame(daily_avg)
        df_health["date"] = pd.to_datetime(df_health["date"])
        st.line_chart(df_health.set_index("date")["avg_score"], use_container_width=True)
    else:
        st.info("No health data for this period.")

    # Biggest drops
    drops = health.get("biggest_drops", [])
    if drops:
        st.markdown("**Biggest Health Drops**")
        for d in drops:
            delta = d["delta"]
            st.markdown(
                f"- **{d['name']}**: {d['old_score']} → {d['new_score']} "
                f"(<span style='color: #FB7185'>{delta:+d}</span>)",
                unsafe_allow_html=True,
            )

    # Biggest gains
    gains = health.get("biggest_gains", [])
    if gains:
        st.markdown("**Biggest Health Gains**")
        for g in gains:
            delta = g["delta"]
            st.markdown(
                f"- **{g['name']}**: {g['old_score']} → {g['new_score']} "
                f"(<span style='color: #34D399'>+{delta}</span>)",
                unsafe_allow_html=True,
            )

with col_velocity:
    st.markdown("### Ticket Velocity")
    daily_tickets = tickets.get("daily", [])
    if daily_tickets:
        df_tickets = pd.DataFrame(daily_tickets)
        df_tickets["date"] = pd.to_datetime(df_tickets["date"])
        st.line_chart(
            df_tickets.set_index("date")[["created", "resolved"]],
            use_container_width=True,
        )
    else:
        st.info("No ticket data for this period.")

    totals = tickets.get("totals", {})
    t_cols = st.columns(3)
    with t_cols[0]:
        st.metric("Created", totals.get("created", 0))
    with t_cols[1]:
        st.metric("Resolved", totals.get("resolved", 0))
    with t_cols[2]:
        net = totals.get("net_open", 0)
        st.metric("Net Open", net, delta=f"{net:+d}" if net != 0 else None,
                  delta_color="inverse")

    by_sev = tickets.get("by_severity", [])
    if by_sev:
        st.markdown("**By Severity:** " + " · ".join(
            f"{s['severity']}: {s['count']}" for s in by_sev
        ))

st.divider()

# ── Sentiment ──
st.markdown("### Call Sentiment")
sent_cols = st.columns([2, 3])

with sent_cols[0]:
    dist = sentiment.get("distribution", {})
    if dist:
        df_sent = pd.DataFrame([
            {"Sentiment": k, "Count": v} for k, v in dist.items()
        ])
        st.bar_chart(df_sent.set_index("Sentiment"), use_container_width=True)

    avg_score = sentiment.get("avg_score")
    if avg_score is not None:
        st.metric("Avg Sentiment Score", f"{avg_score:.2f}")

with sent_cols[1]:
    negatives = sentiment.get("recent_negative", [])
    if negatives:
        st.markdown("**Recent Negative/Mixed Calls**")
        for n in negatives[:5]:
            emoji = "🔴" if n["sentiment"] == "negative" else "🟡"
            customer = n.get("customer_name") or "Unknown"
            summary = n.get("summary", "")[:120]
            st.markdown(f"{emoji} **{customer}** — {summary}")
    else:
        st.success("No negative sentiment calls in this period.")

st.divider()

# ── Upcoming Renewals ──
renewals = portfolio.get("upcoming_renewals", [])
if renewals:
    st.markdown("### Upcoming Renewals (Next 90 Days)")
    rows = []
    for r in renewals:
        score = r.get("health_score")
        rows.append({
            "Customer": r["name"],
            "Renewal": r["renewal_date"],
            "Tier": r.get("tier", "—"),
            "Health": int(score) if score else 0,
            "Risk": (r.get("risk_level") or "unknown").replace("_", " ").title(),
        })

    df_renewals = pd.DataFrame(rows)
    st.dataframe(
        df_renewals,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Health": st.column_config.ProgressColumn(
                "Health", min_value=0, max_value=100, format="%d",
            ),
        },
    )
else:
    st.info("No renewals in the next 90 days.")
