"""
Executive Brief Service -- Generates a consolidated Slack message for C-level executives.

Pulls data from trend_service, alert_rules_engine, and direct DB queries,
then formats a single Block Kit message covering:
  1. Portfolio Health
  2. Attention Required (critical items)
  3. Ticket Summary
  4. Call Intelligence
  5. Pipeline Snapshot
  6. Top 3 Actions (AI-generated via Haiku)

Scheduled: Wednesday & Friday at 9:00 AM IST.
Manual trigger: POST /api/executive/brief
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger("services.executive_brief")


def _truncate(text: str, max_len: int = 80) -> str:
    """Truncate text at the last word boundary within max_len, appending '...'."""
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rsplit(" ", 1)[0]
    return truncated + "..."


def _gather_portfolio_health(db: Session) -> dict:
    """Portfolio snapshot: risk distribution, avg health, upcoming renewals."""
    from app.services.trend_service import trend_service
    snapshot = trend_service.portfolio_snapshot(db)
    health_trends = trend_service.health_trends(db, days=7)

    # Compute week-over-week avg change
    daily = health_trends.get("daily_avg", [])
    if len(daily) >= 2:
        first_half = daily[: len(daily) // 2]
        second_half = daily[len(daily) // 2 :]
        avg_first = sum(d["avg_score"] for d in first_half) / len(first_half) if first_half else 0
        avg_second = sum(d["avg_score"] for d in second_half) / len(second_half) if second_half else 0
        avg_change = round(avg_second - avg_first)
    else:
        avg_change = 0

    # Current avg from latest day
    current_avg = daily[-1]["avg_score"] if daily else 0

    # Renewal ARR from deals
    renewal_arr = 0
    for r in snapshot.get("upcoming_renewals", []):
        # We don't have ARR in snapshot — leave as count only
        pass

    return {
        "total_customers": snapshot.get("total_customers", 0),
        "risk_distribution": snapshot.get("risk_distribution", {}),
        "current_avg": current_avg,
        "avg_change": avg_change,
        "renewals_60d": [
            r for r in snapshot.get("upcoming_renewals", [])
            if r.get("renewal_date")  # already filtered to 90d, we'll further filter in format
        ],
        "biggest_drops": health_trends.get("biggest_drops", []),
    }


def _gather_attention_items(db: Session) -> list[dict]:
    """Top critical items needing executive attention."""
    items = []
    now = datetime.now(timezone.utc)
    start_7d = now - timedelta(days=7)

    # 1. Customers with health decline >10 pts in last 7 days
    drops = db.execute(text("""
        WITH earliest AS (
            SELECT DISTINCT ON (customer_id) customer_id, score AS old_score
            FROM health_scores
            WHERE calculated_at >= :start
            ORDER BY customer_id, calculated_at ASC
        ),
        latest AS (
            SELECT DISTINCT ON (customer_id) customer_id, score AS new_score
            FROM health_scores
            WHERE calculated_at >= :start
            ORDER BY customer_id, calculated_at DESC
        )
        SELECT c.id, c.name, e.old_score, l.new_score,
               (e.old_score - l.new_score) AS drop_amount,
               c.metadata->>'cs_manager' AS cs_manager
        FROM customers c
        JOIN earliest e ON e.customer_id = c.id
        JOIN latest l ON l.customer_id = c.id
        WHERE (e.old_score - l.new_score) > 10
          AND c.is_active = true
        ORDER BY drop_amount DESC
        LIMIT 5
    """), {"start": start_7d}).fetchall()

    for r in drops:
        detail = f"Health dropped from {r.old_score} to {r.new_score} (-{r.drop_amount} pts)"
        # Check if renewal is near
        renewal_row = db.execute(text("""
            SELECT renewal_date FROM customers
            WHERE id = :cid AND renewal_date IS NOT NULL
              AND renewal_date <= CURRENT_DATE + INTERVAL '90 days'
        """), {"cid": r.id}).first()
        if renewal_row:
            days_to = (renewal_row.renewal_date - datetime.now(timezone.utc).date()).days
            detail += f". Renewal in {days_to} days"
        if r.cs_manager:
            detail += f" (CS: {r.cs_manager})"
        items.append({
            "severity": "critical" if r.drop_amount > 20 else "high",
            "customer": r.name,
            "detail": detail,
            "action": "Executive check-in call needed",
        })

    # 2. P0/P1 tickets stale >3 days
    stale = db.execute(text("""
        SELECT c.name, t.summary, t.severity,
               EXTRACT(DAY FROM NOW() - t.created_at)::int AS days_open,
               c.metadata->>'cs_manager' AS cs_manager
        FROM tickets t
        JOIN customers c ON t.customer_id = c.id
        WHERE t.severity IN ('P0', 'P1', 'critical')
          AND t.status NOT IN ('resolved', 'closed')
          AND t.created_at < NOW() - INTERVAL '3 days'
          AND c.is_active = true
        ORDER BY t.severity ASC, days_open DESC
        LIMIT 5
    """)).fetchall()

    for r in stale:
        # Escalate severity based on how long the ticket has been open
        if r.days_open > 90:
            severity = "critical"
        else:
            severity = "high"
        detail = f"{r.severity} ticket \"{_truncate(r.summary)}\" open {r.days_open} days"
        if r.cs_manager:
            detail += f" (CS: {r.cs_manager})"
        items.append({
            "severity": severity,
            "customer": r.name,
            "detail": detail,
            "action": "Engineering follow-up required",
        })

    # 3. Open critical/high alerts
    alerts = db.execute(text("""
        SELECT a.title, a.severity, c.name, a.suggested_action
        FROM alerts a
        JOIN customers c ON a.customer_id = c.id
        WHERE a.status = 'open'
          AND a.severity IN ('critical', 'high')
        ORDER BY CASE a.severity WHEN 'critical' THEN 0 ELSE 1 END, a.created_at DESC
        LIMIT 3
    """)).fetchall()

    for r in alerts:
        items.append({
            "severity": r.severity,
            "customer": r.name,
            "detail": r.title,
            "action": r.suggested_action or "Review and take action",
        })

    # Sort by severity and deduplicate by customer+detail
    severity_order = {"critical": 0, "high": 1, "medium": 2}
    items.sort(key=lambda x: severity_order.get(x["severity"], 3))

    # Deduplicate
    seen = set()
    unique = []
    for item in items:
        key = (item["customer"], item["detail"][:40])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:5]


def _gather_ticket_summary(db: Session) -> dict:
    """7-day ticket velocity + P0/P1 aging count."""
    from app.services.trend_service import trend_service
    velocity = trend_service.ticket_velocity(db, days=7)

    # P0/P1 aging >3 days
    aging = db.execute(text("""
        SELECT COUNT(*) AS cnt
        FROM tickets
        WHERE severity IN ('P0', 'P1', 'critical')
          AND status NOT IN ('resolved', 'closed')
          AND created_at < NOW() - INTERVAL '3 days'
    """)).scalar() or 0

    # Top issue pattern (most common category/keyword in summaries)
    top_pattern = db.execute(text("""
        SELECT LOWER(SPLIT_PART(summary, ' ', 1) || ' ' || SPLIT_PART(summary, ' ', 2)) AS pattern,
               COUNT(*) AS cnt
        FROM tickets
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY pattern
        HAVING COUNT(*) >= 2
        ORDER BY cnt DESC
        LIMIT 1
    """)).first()

    return {
        "created": velocity["totals"]["created"],
        "resolved": velocity["totals"]["resolved"],
        "net_open": velocity["totals"]["net_open"],
        "by_severity": velocity.get("by_severity", []),
        "p0p1_aging": aging,
        "top_pattern": top_pattern.pattern if top_pattern else None,
        "top_pattern_count": top_pattern.cnt if top_pattern else 0,
    }


def _gather_call_intelligence(db: Session) -> dict:
    """7-day call insights: count, sentiment, overdue action items, risks."""
    from app.services.trend_service import trend_service
    sentiment = trend_service.sentiment_shifts(db, days=7)

    call_count = db.execute(text("""
        SELECT COUNT(*) FROM call_insights
        WHERE processed_at >= NOW() - INTERVAL '7 days'
    """)).scalar() or 0

    # Pending action items (from calls with action items in last 14 days)
    pending_actions = db.execute(text("""
        SELECT COUNT(*) FROM action_items
        WHERE status != 'completed'
          AND created_at >= NOW() - INTERVAL '14 days'
    """)).scalar() or 0

    # Overdue action items (>3 days old, not completed)
    overdue_actions = db.execute(text("""
        SELECT COUNT(*) FROM action_items
        WHERE status != 'completed'
          AND created_at < NOW() - INTERVAL '3 days'
          AND created_at >= NOW() - INTERVAL '14 days'
    """)).scalar() or 0

    # Top risk signals from recent calls
    risk_rows = db.execute(text("""
        SELECT ci.risks, c.name
        FROM call_insights ci
        LEFT JOIN customers c ON ci.customer_id = c.id
        WHERE ci.processed_at >= NOW() - INTERVAL '7 days'
          AND ci.risks IS NOT NULL
          AND jsonb_array_length(ci.risks) > 0
        ORDER BY ci.processed_at DESC
        LIMIT 5
    """)).fetchall()

    top_risks = []
    for r in risk_rows:
        if r.risks:
            for risk in r.risks[:1]:
                risk_text = risk.get("description", str(risk)) if isinstance(risk, dict) else str(risk)
                top_risks.append(f"\"{_truncate(risk_text)}\" ({r.name})")
        if len(top_risks) >= 2:
            break

    return {
        "call_count": call_count,
        "avg_sentiment": sentiment.get("avg_score"),
        "distribution": sentiment.get("distribution", {}),
        "negative_calls": [
            {"customer": c["customer_name"], "sentiment": c["sentiment"]}
            for c in sentiment.get("recent_negative", [])[:3]
        ],
        "pending_actions": pending_actions,
        "overdue_actions": overdue_actions,
        "top_risks": top_risks,
    }


def _gather_pipeline_snapshot(db: Session) -> dict:
    """Deal pipeline: open deals, win rate, stalled, top deal, conversions."""
    # Open deals
    open_deals = db.execute(text("""
        SELECT COUNT(*) AS cnt, COALESCE(SUM(amount), 0) AS total_value
        FROM deals
        WHERE stage NOT IN ('Closed Won', 'Closed Lost')
    """)).first()

    # Win rate (last 30 days)
    closed = db.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE stage = 'Closed Won') AS won,
            COUNT(*) FILTER (WHERE stage = 'Closed Lost') AS lost
        FROM deals
        WHERE hubspot_updated_at >= NOW() - INTERVAL '30 days'
          AND stage IN ('Closed Won', 'Closed Lost')
    """)).first()

    won = closed.won if closed else 0
    lost = closed.lost if closed else 0
    win_rate = round(won / (won + lost) * 100) if (won + lost) > 0 else None

    # Stalled deals (>30 days no update, using HubSpot's hs_lastmodifieddate)
    stalled_count = db.execute(text("""
        SELECT COUNT(*)
        FROM deals
        WHERE stage NOT IN ('Closed Won', 'Closed Lost')
          AND hubspot_updated_at < NOW() - INTERVAL '30 days'
    """)).scalar() or 0

    # Top deal by amount
    top_deal = db.execute(text("""
        SELECT deal_name, company_name, amount, stage
        FROM deals
        WHERE stage NOT IN ('Closed Won', 'Closed Lost')
          AND amount IS NOT NULL
        ORDER BY amount DESC
        LIMIT 1
    """)).first()

    return {
        "open_count": open_deals.cnt if open_deals else 0,
        "total_value": float(open_deals.total_value) if open_deals else 0,
        "win_rate": win_rate,
        "stalled_count": stalled_count,
        "top_deal": {
            "name": top_deal.deal_name,
            "company": top_deal.company_name,
            "amount": float(top_deal.amount),
            "stage": top_deal.stage,
        } if top_deal else None,
    }


def _generate_top_actions(
    attention_items: list,
    ticket_summary: dict,
    call_intel: dict,
    pipeline: dict,
    portfolio: dict,
) -> list[str]:
    """Use Claude Haiku to generate top 3 prioritized actions."""
    from app.services.claude_service import ClaudeService
    claude = ClaudeService()

    # Build context for Claude
    context_parts = []

    if attention_items:
        lines = [f"- [{i['severity'].upper()}] {i['customer']}: {i['detail']}. Action: {i['action']}" for i in attention_items[:5]]
        context_parts.append("ATTENTION ITEMS:\n" + "\n".join(lines))

    if ticket_summary.get("p0p1_aging"):
        context_parts.append(f"TICKETS: {ticket_summary['p0p1_aging']} P0/P1 tickets aging >3 days. {ticket_summary['created']} created, {ticket_summary['resolved']} resolved this week.")

    if call_intel.get("overdue_actions"):
        context_parts.append(f"CALLS: {call_intel['overdue_actions']} overdue action items from calls. {call_intel['call_count']} calls this week.")

    if pipeline.get("stalled_count"):
        context_parts.append(f"PIPELINE: {pipeline['stalled_count']} stalled deals (>30 days). {pipeline['open_count']} open deals worth ${pipeline['total_value']:,.0f}.")

    renewals_soon = [r for r in portfolio.get("renewals_60d", []) if r.get("risk_level") in ("high_risk", "critical")]
    if renewals_soon:
        names = ", ".join(r["name"] for r in renewals_soon[:3])
        context_parts.append(f"RENEWALS: At-risk customers with upcoming renewal: {names}")

    if not context_parts:
        return ["No critical actions this period — portfolio is stable."]

    system = "You are a CS executive advisor. Given the current portfolio state, output exactly 3 prioritized actions. Each action should be 1 sentence, actionable, and specific. Format: just the 3 lines, no numbering, no bullets, no extra text."
    user_msg = "\n\n".join(context_parts)

    result = claude.generate_fast_sync(
        system_prompt=system,
        user_message=user_msg,
        max_tokens=300,
        temperature=0.2,
    )

    if result.get("error"):
        logger.warning(f"[ExecBrief] Claude call failed: {result['error']}")
        # Fallback: use the top attention items as actions
        return [f"{i['customer']}: {i['action']}" for i in attention_items[:3]] or ["Review portfolio — no AI summary available."]

    lines = [line.strip() for line in result["content"].strip().split("\n") if line.strip()]
    # Strip any numbering prefixes (e.g. "1. ", "- ")
    cleaned = []
    for line in lines[:3]:
        for prefix in ("1. ", "2. ", "3. ", "- ", "• "):
            if line.startswith(prefix):
                line = line[len(prefix):]
                break
        cleaned.append(line)
    return cleaned or ["Review portfolio — no AI summary available."]


def _format_brief_blocks(
    portfolio: dict,
    attention: list,
    tickets: dict,
    calls: dict,
    pipeline: dict,
    top_actions: list,
) -> list[dict]:
    """Build Slack Block Kit blocks for the executive brief."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A, %B %d, %Y")

    blocks = []

    # ── Header ──
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": f"CS Portfolio Brief — {date_str}", "emoji": True},
    })

    # ── Section 1: Portfolio Health ──
    # Map risk_level values to display buckets.
    # Health monitor writes: healthy, watch, high_risk, critical
    # Older data may use: low, medium, high, critical
    risk = portfolio["risk_distribution"]
    healthy = risk.get("healthy", 0) + risk.get("low", 0)
    watch = risk.get("watch", 0) + risk.get("medium", 0)
    high_risk = risk.get("high_risk", 0) + risk.get("high", 0)
    critical = risk.get("critical", 0)
    known_keys = {"healthy", "watch", "high_risk", "critical", "low", "medium", "high"}
    unscored = sum(v for k, v in risk.items() if k not in known_keys)

    change_str = ""
    if portfolio["avg_change"] > 0:
        change_str = f" (up {portfolio['avg_change']} pts from last week)"
    elif portfolio["avg_change"] < 0:
        change_str = f" (down {abs(portfolio['avg_change'])} pts from last week)"

    renewals_60d = [r for r in portfolio.get("renewals_60d", [])
                    if r.get("renewal_date") and _days_until(r["renewal_date"]) <= 60]

    risk_line = f"Healthy: {healthy}  |  Watch: {watch}  |  At-Risk: {high_risk}  |  Critical: {critical}"
    if unscored:
        risk_line += f"  |  Unscored: {unscored}"

    renewal_str = f"Renewals in next 60 days: {len(renewals_60d)} customers"
    if renewals_60d:
        renewal_names = ", ".join(r["name"] for r in renewals_60d[:5])
        renewal_str += f": {renewal_names}"

    portfolio_text = (
        f"*Portfolio Health* ({portfolio['total_customers']} active customers)\n"
        f"{risk_line}\n"
        f"Avg Health Score: {portfolio['current_avg']}/100{change_str}\n"
        f"{renewal_str}"
    )
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": portfolio_text}})
    blocks.append({"type": "divider"})

    # ── Section 2: Attention Required ──
    if attention:
        severity_emoji = {"critical": ":red_circle:", "high": ":large_orange_circle:", "medium": ":large_yellow_circle:"}
        attention_lines = []
        for i, item in enumerate(attention[:5], 1):
            emoji = severity_emoji.get(item["severity"], ":white_circle:")
            attention_lines.append(f"{i}. {emoji} *{item['customer']}* — {item['detail']}. _{item['action']}_")
        attention_text = "*Attention Required*\n" + "\n".join(attention_lines)
    else:
        attention_text = "*Attention Required*\nNo critical items this period. :white_check_mark:"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": attention_text}})
    blocks.append({"type": "divider"})

    # ── Section 3: Ticket Summary ──
    net_indicator = f"+{tickets['net_open']}" if tickets['net_open'] >= 0 else str(tickets['net_open'])
    ticket_text = (
        f"*Ticket Summary* (last 7 days)\n"
        f"Created: {tickets['created']}  |  Resolved: {tickets['resolved']}  |  Net Open: {net_indicator}"
    )
    if tickets["p0p1_aging"]:
        ticket_text += f"\nP0/P1 aging (>3 days): {tickets['p0p1_aging']} tickets"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": ticket_text}})
    blocks.append({"type": "divider"})

    # ── Section 4: Call Intelligence ──
    avg_sent_str = f"{calls['avg_sentiment']:.2f}" if calls["avg_sentiment"] is not None else "N/A"
    sent_label = "Positive" if (calls.get("avg_sentiment") or 0) >= 0.5 else "Mixed" if (calls.get("avg_sentiment") or 0) >= 0.3 else "Negative"

    call_text = (
        f"*Call Intelligence* (last 7 days)\n"
        f"Calls recorded: {calls['call_count']}  |  Avg Sentiment: {avg_sent_str} ({sent_label})"
    )

    if calls["negative_calls"]:
        neg_names = ", ".join(c["customer"] for c in calls["negative_calls"] if c.get("customer"))
        if neg_names:
            call_text += f"\nNegative/Mixed calls: {neg_names}"

    if calls["pending_actions"]:
        overdue_str = f" ({calls['overdue_actions']} overdue >3 days)" if calls["overdue_actions"] else ""
        call_text += f"\nPending action items: {calls['pending_actions']}{overdue_str}"

    if calls["top_risks"]:
        call_text += f"\nKey risks: {' | '.join(calls['top_risks'][:2])}"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": call_text}})
    blocks.append({"type": "divider"})

    # ── Section 5: Pipeline Snapshot ──
    total_val_str = f"${pipeline['total_value']:,.0f}" if pipeline["total_value"] else "N/A"
    if pipeline["win_rate"] is not None:
        win_rate_str = f"{pipeline['win_rate']}%"
    else:
        win_rate_str = "No deals closed in 30d"

    pipeline_text = (
        f"*Pipeline Snapshot*\n"
        f"Open deals: {pipeline['open_count']}  |  Total value: {total_val_str}\n"
        f"Win rate (30d): {win_rate_str}  |  Stalled (>30d): {pipeline['stalled_count']}"
    )

    if pipeline.get("top_deal"):
        td = pipeline["top_deal"]
        stage_name = td["stage"] or "Unknown"
        pipeline_text += f"\nTop deal: {td['name']} ({td['company']}) at {stage_name} — ${td['amount']:,.0f}"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": pipeline_text}})
    blocks.append({"type": "divider"})

    # ── Section 6: Top 3 Actions ──
    action_emojis = [":red_circle:", ":large_orange_circle:", ":large_yellow_circle:"]
    action_lines = []
    for i, action in enumerate(top_actions[:3]):
        emoji = action_emojis[i] if i < len(action_emojis) else ":white_circle:"
        action_lines.append(f"{i + 1}. {emoji} {action}")

    actions_text = "*Top Actions This Week*\n" + "\n".join(action_lines)
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": actions_text}})
    blocks.append({"type": "divider"})

    # ── Footer ──
    dashboard_url = settings.DASHBOARD_BASE_URL
    footer_parts = [f"Generated by CS Control Plane | Data as of {now.strftime('%b %d, %Y %I:%M %p')} IST"]
    if dashboard_url:
        footer_parts.append(f"<{dashboard_url}/dashboard|View Portfolio Dashboard>")

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "  |  ".join(footer_parts)}],
    })

    return blocks


def _days_until(date_str: str) -> int:
    """Parse a date string and return days from now."""
    try:
        from datetime import date
        if isinstance(date_str, str):
            d = date.fromisoformat(date_str)
        else:
            d = date_str
        return (d - date.today()).days
    except Exception:
        return 999


def generate_and_send_brief(db: Session) -> dict:
    """
    Main entry point: gather all data, generate brief, send to Slack.

    Returns: {"sent": bool, "sections": dict with counts, "error": str|None}
    """
    logger.info("[ExecBrief] Generating executive brief...")

    try:
        # Gather all data
        portfolio = _gather_portfolio_health(db)
        attention = _gather_attention_items(db)
        tickets = _gather_ticket_summary(db)
        calls = _gather_call_intelligence(db)
        pipeline = _gather_pipeline_snapshot(db)

        # Generate AI top actions
        top_actions = _generate_top_actions(attention, tickets, calls, pipeline, portfolio)

        # Format Block Kit message
        blocks = _format_brief_blocks(portfolio, attention, tickets, calls, pipeline, top_actions)

        # Send to Slack
        from app.services.slack_service import slack_service
        channel = settings.SLACK_CH_EXEC_OVERVIEW

        fallback = (
            f"CS Portfolio Brief — {datetime.now(timezone.utc).strftime('%b %d, %Y')} | "
            f"{portfolio['total_customers']} customers | "
            f"Avg health: {portfolio['current_avg']}/100 | "
            f"{len(attention)} attention items"
        )

        result = slack_service.send_message(channel, fallback, blocks)
        sent = bool(result)

        if sent:
            logger.info(f"[ExecBrief] Brief sent to {channel}")
        else:
            logger.warning(f"[ExecBrief] Failed to send brief to {channel}")

        return {
            "sent": sent,
            "channel": channel,
            "sections": {
                "portfolio_customers": portfolio["total_customers"],
                "attention_items": len(attention),
                "tickets_created_7d": tickets["created"],
                "calls_7d": calls["call_count"],
                "open_deals": pipeline["open_count"],
                "top_actions": len(top_actions),
            },
            "error": None,
        }

    except Exception as e:
        logger.error(f"[ExecBrief] Failed to generate brief: {e}", exc_info=True)
        return {"sent": False, "sections": {}, "error": str(e)}
