"""
Slack Service -- Real Slack notifications via slack_sdk.

Sends Block Kit formatted alerts to a configurable channel.
Gracefully degrades: if not configured or SLACK_ENABLED=false, logs and skips.
"""

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger("services.slack")

# Severity → color mapping for Block Kit sidebar
SEVERITY_COLORS = {
    "critical": "#DC2626",  # red-600
    "high": "#EA580C",      # orange-600
    "medium": "#D97706",    # amber-600
    "low": "#2563EB",       # blue-600
}

# Human-readable alert type names for Slack cards
ALERT_TYPE_LABELS = {
    "call_sentiment_pattern": "Negative Call Sentiment",
    "health_drop_15": "Health Score Drop",
    "critical_tickets_stale": "Stale Critical Tickets",
    "renewal_at_risk": "Renewal At Risk",
    "negative_sentiment_streak": "Negative Sentiment Streak",
}


def _friendly_stage(stage: str) -> str:
    """Convert HubSpot stage IDs to human-readable names."""
    STAGE_NAMES = {
        "appointmentscheduled": "Discovery",
        "presentationscheduled": "Demo 1",
        "decisionmakerboughtin": "Demo 2",
        "1166515347": "Pre-POC",
        "219679027": "POC",
        "1157536395": "Negotiation",
        "contractsent": "Contract Sent",
        "closedwon": "Closed Won",
        "closedlost": "Closed Lost",
    }
    return STAGE_NAMES.get(stage, stage.replace("_", " ").title())


def _build_jira_url(base_url: str, jira_id: str) -> str:
    """Build a Jira issue URL. Pattern controlled by JIRA_BROWSE_PATTERN setting."""
    from app.config import settings
    if settings.JIRA_BROWSE_PATTERN == "browse":
        return f"{base_url}/browse/{jira_id}"
    # Default: project-scoped view (Jira Software Cloud)
    project_key = jira_id.split("-")[0] if "-" in jira_id else jira_id
    return (
        f"{base_url}/jira/software/c/projects/{project_key}/issues"
        f"?jql=project%20%3D%20{project_key}%20ORDER%20BY%20created%20DESC"
        f"&selectedIssue={jira_id}"
    )


def _text_to_section_blocks(text: str, label: str | None = None) -> list[dict]:
    """Convert a long text into one or more Slack section blocks.

    Slack section text has a 3000-char limit. This splits on newline/space
    boundaries when the text exceeds that limit.
    """
    full = f"*{label}:*\n{text}" if label else text
    blocks: list[dict] = []
    while len(full) > 3000:
        split_at = full.rfind("\n", 0, 3000)
        if split_at <= 0:
            split_at = full.rfind(" ", 0, 3000)
        if split_at <= 0:
            split_at = 3000
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": full[:split_at]}})
        full = full[split_at:].lstrip()
    if full:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": full}})
    return blocks


class SlackService:
    """Slack WebClient wrapper with Block Kit alert formatting."""

    def __init__(self):
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(settings.SLACK_ENABLED and settings.SLACK_BOT_TOKEN)

    def _get_client(self):
        if self._client is None:
            if not self.configured:
                return None
            from slack_sdk import WebClient
            self._client = WebClient(token=settings.SLACK_BOT_TOKEN)
        return self._client

    def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[list] = None,
        thread_ts: Optional[str] = None,
    ) -> dict | bool:
        """Send a plain or Block Kit message to a Slack channel.

        Returns the API response dict on success (includes 'ts' of the posted
        message), or False on failure.  Passing ``thread_ts`` makes the message
        a threaded reply.
        """
        if not self.configured:
            logger.debug(f"[Slack] Not configured, skipping message to #{channel}")
            return False

        client = self._get_client()
        if not client:
            return False

        try:
            kwargs: dict = {"channel": channel, "text": text}
            if blocks:
                kwargs["blocks"] = blocks
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            resp = client.chat_postMessage(**kwargs)
            if resp["ok"]:
                logger.info(f"[Slack] Message sent to {channel}")
                return resp.data if hasattr(resp, "data") else {"ok": True}
            else:
                logger.warning(f"[Slack] API error: {resp.get('error')}")
                return False
        except Exception as e:
            logger.error(f"[Slack] Failed to send message to {channel}: {e}")
            return False

    def get_user_info(self, user_id: str) -> dict | None:
        """Fetch Slack user profile (display name)."""
        client = self._get_client()
        if not client:
            return None
        try:
            resp = client.users_info(user=user_id)
            if resp["ok"]:
                profile = resp["user"]["profile"]
                return {
                    "display_name": profile.get("display_name") or profile.get("real_name", "Unknown"),
                    "real_name": profile.get("real_name", ""),
                }
            return None
        except Exception as e:
            logger.warning(f"[Slack] Failed to fetch user info for {user_id}: {e}")
            return None

    def send_alert(self, alert) -> bool:
        """
        Send a rich Block Kit alert notification.

        Args:
            alert: Alert model instance with title, severity, description,
                   suggested_action, customer relationship, etc.
        """
        if not self.configured:
            logger.debug(f"[Slack] Not configured, skipping alert '{alert.title}'")
            return False

        channel = settings.SLACK_CH_HEALTH_ALERTS
        severity = (alert.severity or "medium").lower()
        color = SEVERITY_COLORS.get(severity, "#6B7280")
        customer_name = alert.customer.name if alert.customer else "Unknown"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{'🔴' if severity == 'critical' else '🟠' if severity == 'high' else '🟡'} {alert.title}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                    {"type": "mrkdwn", "text": f"*Customer:*\n{customer_name}"},
                    {"type": "mrkdwn", "text": f"*Type:*\n{ALERT_TYPE_LABELS.get(alert.alert_type, (alert.alert_type or '').replace('_', ' ').title())}"},
                    {"type": "mrkdwn", "text": f"*Status:*\n{alert.status}"},
                ],
            },
        ]

        if alert.description:
            blocks.extend(_text_to_section_blocks(alert.description, label="Details"))

        if alert.suggested_action:
            blocks.extend(_text_to_section_blocks(alert.suggested_action, label="Suggested Action"))

        # Deep-link to customer profile on live dashboard
        if alert.customer_id and settings.DASHBOARD_BASE_URL:
            dashboard_url = f"{settings.DASHBOARD_BASE_URL}/dashboard/customer/{alert.customer_id}"
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"<{dashboard_url}|View customer in dashboard>"},
            })

        blocks.append({"type": "divider"})

        # Fallback text for notifications
        fallback = f"[{severity.upper()}] {alert.title} — {customer_name}"

        # Use attachments for color sidebar
        attachments = [{"color": color, "blocks": blocks}]

        return self._send_with_attachments(channel, fallback, attachments)

    def send_call_insight_notification(
        self,
        title: str,
        customer_name: str,
        summary: str,
        sentiment: str,
        sentiment_score: float | None,
        action_items: list,
        risks: list,
        key_topics: list,
        participants: list | None = None,
        call_date: str | None = None,
        meeting_type: str | None = None,
        highlights: list | None = None,
        conclusion: str | None = None,
    ) -> bool:
        """Post a meeting intelligence summary to the CS alerts channel after processing."""
        if not self.configured:
            return False

        channel = settings.SLACK_CH_CALL_INTEL or settings.SLACK_CHAT_CHANNEL

        # Format call date
        date_str = ""
        if call_date:
            try:
                from datetime import datetime
                if isinstance(call_date, str):
                    dt = datetime.fromisoformat(call_date.replace("Z", "+00:00"))
                else:
                    dt = call_date
                date_str = dt.strftime("%b %d, %Y at %I:%M %p")
            except Exception:
                date_str = str(call_date)

        # Sentiment emoji
        sent_emoji = {
            "positive": "🟢", "neutral": "⚪", "mixed": "🟡", "negative": "🔴",
        }.get((sentiment or "").lower(), "⚪")
        score_str = f" ({sentiment_score:.2f})" if sentiment_score is not None else ""

        # Meeting type emoji
        type_emoji = {
            "POC": "🧪", "Demo": "🎬", "Check-in": "📋", "QBR": "📊",
            "Kickoff": "🚀", "Escalation": "🚨", "Training": "🎓",
            "Support": "🛠️", "Renewal": "🔄", "Other": "📞",
        }.get(meeting_type or "Other", "📞")

        # ── Header ──
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📞 Call Intelligence: {title[:120]}",
                    "emoji": True,
                },
            },
        ]

        # ── Meeting type + sentiment + customer ──
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"{type_emoji} *Type:* {meeting_type or 'Other'}  ·  {sent_emoji} {sentiment or 'N/A'}{score_str}"},
                {"type": "mrkdwn", "text": f"👤 *Customer:* {customer_name or 'Unknown'}"},
            ],
        })

        # ── Date + attendees ──
        meta_fields = []
        if date_str:
            meta_fields.append({"type": "mrkdwn", "text": f"📅 {date_str}"})
        if participants:
            names = ", ".join(str(p) for p in participants[:8])
            meta_fields.append({"type": "mrkdwn", "text": f"👥 {names}"})
        if meta_fields:
            blocks.append({"type": "section", "fields": meta_fields})

        blocks.append({"type": "divider"})

        # ── Key Highlights (primary content) — falls back to summary ──
        if highlights:
            highlight_lines = "\n".join(f"• {str(h)[:200]}" for h in highlights[:5])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*📌 Key Highlights*\n{highlight_lines}"},
            })
        elif summary:
            blocks.extend(_text_to_section_blocks(summary, label="📌 Summary"))

        # ── Conclusion ──
        if conclusion:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*🎯 Conclusion*\n{conclusion[:2000]}"},
            })

        # ── Action items (top 5) ──
        if action_items:
            blocks.append({"type": "divider"})
            items_lines = []
            for a in action_items[:5]:
                if isinstance(a, dict):
                    task = a.get("task") or a.get("title") or str(a)
                    owner = a.get("owner", "")
                    items_lines.append(f"• {f'[{owner}] ' if owner else ''}{task}")
                else:
                    items_lines.append(f"• {a}")
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*📋 Action Items*\n" + "\n".join(items_lines)},
            })

        # ── Risk signals (only if present) ──
        if risks:
            blocks.append({"type": "divider"})
            risk_lines = []
            for r in risks[:3]:
                if isinstance(r, dict):
                    risk_lines.append(f"🔴 {r.get('description', str(r))}")
                else:
                    risk_lines.append(f"🔴 {r}")
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*⚠️ Risk Signals*\n" + "\n".join(risk_lines)},
            })

        blocks.append({"type": "divider"})

        # ── Topics (de-emphasized context block) ──
        if key_topics:
            topics_str = ", ".join(str(t) for t in key_topics[:8])
            blocks.append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"🏷️ {topics_str}"},
                ],
            })

        fallback = f"📞 {meeting_type or 'Call'}: {title} ({customer_name or 'Unknown'}) — {sent_emoji} {sentiment or 'N/A'}"
        return bool(self.send_message(channel, fallback, blocks))

    def notify_alert_update(self, alert, new_status: str) -> bool:
        """Send a follow-up notification when an alert status changes."""
        if not self.configured:
            return False

        channel = settings.SLACK_CH_HEALTH_ALERTS
        customer_name = alert.customer.name if alert.customer else "Unknown"
        status_emoji = {"acknowledged": "👀", "resolved": "✅", "dismissed": "🚫"}.get(new_status, "📝")

        text = f"{status_emoji} Alert *{alert.title}* ({customer_name}) → *{new_status}*"

        return self.send_message(channel, text)

    def send_presales_card(
        self,
        channel: str,
        draft_content: dict,
        draft_id: str,
        dashboard_url: str | None = None,
        event_type: str = "deal_stage_changed",
    ) -> dict | bool:
        """Post a rich Pre-Sales Funnel card with metrics, stalled deals, and probabilities.

        Custom Block Kit layout that surfaces pipeline data beautifully instead
        of cramming everything into a generic summary block.
        """
        if not self.configured:
            logger.debug("[Slack] Not configured, skipping presales card")
            return False

        metrics = draft_content.get("funnel_metrics", {})
        stalled = draft_content.get("stalled_deals", [])
        probabilities = draft_content.get("deal_probabilities", [])
        blockers = draft_content.get("top_blockers", [])
        summary = draft_content.get("summary", "Pipeline analysis complete.")
        recommendations = draft_content.get("recommendations", [])

        # ── Header ──
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":bar_chart: Pre-Sales Pipeline Intelligence",
                    "emoji": True,
                },
            },
        ]

        # ── Funnel Metrics Row ──
        total = metrics.get("total_deals", 0)
        open_deals = metrics.get("open_deals", 0)
        won = metrics.get("closed_won", 0)
        lost = metrics.get("closed_lost", 0)
        win_rate = metrics.get("overall_win_rate", 0)

        win_emoji = ":large_green_circle:" if win_rate >= 0.5 else ":large_yellow_circle:" if win_rate >= 0.3 else ":red_circle:"

        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Total Deals:*\n{total}"},
                {"type": "mrkdwn", "text": f"*Open:*\n{open_deals}"},
                {"type": "mrkdwn", "text": f"*Won / Lost:*\n:white_check_mark: {won}  :x: {lost}"},
                {"type": "mrkdwn", "text": f"*Win Rate:*\n{win_emoji} {win_rate:.0%}"},
            ],
        })

        # ── Conversion Funnel ──
        d2d = metrics.get("discovery_to_demo", 0)
        d2p = metrics.get("demo_to_poc", 0)
        p2c = metrics.get("poc_to_close", 0)

        funnel_text = (
            f":arrow_right: Discovery :arrow_right: Demo `{d2d:.0%}`  "
            f":arrow_right: POC `{d2p:.0%}`  "
            f":arrow_right: Close `{p2c:.0%}`"
        )
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Conversion Funnel*\n{funnel_text}"},
        })

        blocks.append({"type": "divider"})

        # ── AI Summary ──
        if summary and summary != "Pipeline analysis complete.":
            blocks.extend(_text_to_section_blocks(summary[:2000], label=":brain: AI Analysis"))

        # ── Stalled Deals (top 5) ──
        if stalled:
            stalled_lines = []
            for d in stalled[:5]:
                amt = f"${d.get('amount', 0):,.0f}" if d.get("amount") else "N/A"
                company = d.get("company_name") or "Unknown"
                days = d.get("days_stalled", 0)
                stage_name = _friendly_stage(d.get("stage", ""))
                days_emoji = ":red_circle:" if days > 60 else ":large_orange_circle:" if days > 45 else ":large_yellow_circle:"
                stalled_lines.append(
                    f"{days_emoji} *{d.get('deal_name', 'Unknown')}* ({company})\n"
                    f"      Stage: _{stage_name}_  |  Stalled: *{days}d*  |  Value: {amt}"
                )
            stalled_text = "\n".join(stalled_lines)
            remaining = len(stalled) - 5
            if remaining > 0:
                stalled_text += f"\n_...and {remaining} more stalled deals_"

            blocks.append({"type": "divider"})
            blocks.extend(_text_to_section_blocks(stalled_text, label=":warning: Stalled Deals"))

        # ── Deal Win Probabilities (top 5) ──
        if probabilities:
            prob_lines = []
            for p in probabilities[:5]:
                prob = p.get("probability", 0)
                amt = f"${p.get('amount', 0):,.0f}" if p.get("amount") else "N/A"
                company = p.get("company_name") or "Unknown"
                prob_emoji = ":large_green_circle:" if prob >= 0.7 else ":large_yellow_circle:" if prob >= 0.4 else ":red_circle:"
                prob_lines.append(
                    f"{prob_emoji} *{p.get('deal_name', 'Unknown')}* ({company})\n"
                    f"      Probability: *{prob:.0%}*  |  Value: {amt}"
                )
            prob_text = "\n".join(prob_lines)

            blocks.append({"type": "divider"})
            blocks.extend(_text_to_section_blocks(prob_text, label=":crystal_ball: Deal Win Probabilities"))

        # ── Top Blockers ──
        if blockers:
            blocker_lines = []
            for b in blockers[:4]:
                stage_name = _friendly_stage(b.get("stage", ""))
                val = f"${b.get('total_value', 0):,.0f}" if b.get("total_value") else "$0"
                blocker_lines.append(f":no_entry: _{stage_name}_ — {b.get('lost_count', 0)} lost ({val})")
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*:tombstone: Where Deals Die*\n" + "\n".join(blocker_lines)},
            })

        # ── Recommendations ──
        if recommendations:
            rec_lines = []
            for i, r in enumerate(recommendations[:5], 1):
                rec_text = r if isinstance(r, str) else str(r)
                rec_lines.append(f"{i}. {rec_text}")
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*:bulb: Recommendations*\n" + "\n".join(rec_lines)},
            })

        # ── Dashboard Link ──
        if dashboard_url:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f":bar_chart: <{dashboard_url}|View Pipeline in Dashboard>"},
            })

        # ── Approve / Edit / Dismiss Buttons ──
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve", "emoji": True},
                    "style": "primary",
                    "action_id": "draft_approve",
                    "value": draft_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                    "action_id": "draft_edit",
                    "value": draft_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Dismiss", "emoji": True},
                    "style": "danger",
                    "action_id": "draft_dismiss",
                    "value": draft_id,
                },
            ],
        })

        # ── Context Footer ──
        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Agent: Pre-Sales Funnel (Jordan Reeves) | Event: `{event_type}` | Draft: `{draft_id[:8]}`"},
            ],
        })

        fallback = (
            f":bar_chart: Pre-Sales Pipeline: {total} deals, "
            f"{win_rate:.0%} win rate, {len(stalled)} stalled"
        )
        return self.send_message(channel, fallback, blocks)

    def send_agent_card(
        self,
        channel: str,
        agent_name: str,
        event_type: str,
        customer_name: str,
        health_score: int | None,
        priority: str | None,
        summary: str,
        action_required: str,
        draft_id: str,
        dashboard_url: str | None = None,
        jira_id: str | None = None,
        jira_base_url: str | None = None,
        confidence: float | None = None,
    ) -> dict | bool:
        """Post a standard agent card with Approve/Edit/Dismiss buttons.

        Per ARCHITECTURE.md Section 6.2. Returns the Slack API response dict
        (including 'ts') on success, or False on failure.
        """
        if not self.configured:
            logger.debug(f"[Slack] Not configured, skipping agent card for {agent_name}")
            return False

        # Header: show jira_id instead of raw event_type when available
        header_text = f"{agent_name} — {jira_id}" if jira_id else f"{agent_name} — {event_type}"

        # Health score with color indicator
        if health_score is not None:
            if health_score >= 80:
                health_str = f":large_green_circle: {health_score}"
            elif health_score >= 50:
                health_str = f":large_yellow_circle: {health_score}"
            else:
                health_str = f":red_circle: {health_score}"
        else:
            health_str = ":white_circle: _Pending_"

        # Priority with severity emoji
        severity_emoji = {"P0": ":red_circle:", "P1": ":large_orange_circle:", "P2": ":large_yellow_circle:", "P3": ":large_blue_circle:"}
        priority_upper = priority.upper() if priority else None
        priority_str = f"{severity_emoji.get(priority_upper, '')} {priority_upper}" if priority_upper else "_N/A_"

        # Fields: Customer, Health, Priority, and optionally Confidence
        fields = [
            {"type": "mrkdwn", "text": f"*Customer:*\n{customer_name or 'Unknown'}"},
            {"type": "mrkdwn", "text": f"*Health:*\n{health_str}"},
            {"type": "mrkdwn", "text": f"*Priority:*\n{priority_str}"},
        ]
        if confidence is not None:
            fields.append({"type": "mrkdwn", "text": f"*Confidence:*\n{confidence:.0%}"})

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text,
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": fields,
            },
            {"type": "divider"},
            *_text_to_section_blocks(summary, label="Summary"),
            *_text_to_section_blocks(action_required, label="Action Required"),
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve", "emoji": True},
                        "style": "primary",
                        "action_id": "draft_approve",
                        "value": draft_id,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                        "action_id": "draft_edit",
                        "value": draft_id,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Dismiss", "emoji": True},
                        "style": "danger",
                        "action_id": "draft_dismiss",
                        "value": draft_id,
                    },
                ],
            },
        ]

        # Add links section (Jira + Dashboard) before actions
        if dashboard_url or (jira_id and jira_base_url):
            link_parts = []
            if jira_id and jira_base_url:
                jira_url = _build_jira_url(jira_base_url, jira_id)
                link_parts.append(f":link: *Jira:* <{jira_url}|{jira_id}>")
            if dashboard_url:
                link_parts.append(f":bar_chart: *Dashboard:* <{dashboard_url}|View in Dashboard>")
            link_text = "  |  ".join(link_parts) if link_parts else "View in dashboard"
            link_section = {
                "type": "section",
                "text": {"type": "mrkdwn", "text": link_text},
            }
            # Insert before the actions block
            blocks.insert(-1, link_section)

        # Context footer with event type
        context_elements = [{"type": "mrkdwn", "text": f"Event: `{event_type}` | Draft: `{draft_id[:8]}`"}]
        blocks.append({"type": "context", "elements": context_elements})

        fallback = f"[{agent_name}] {jira_id or event_type} — {customer_name}: {summary[:120]}"
        return self.send_message(channel, fallback, blocks)

    def _send_with_attachments(self, channel: str, text: str, attachments: list) -> bool:
        """Send a message with attachments (for colored sidebar)."""
        client = self._get_client()
        if not client:
            return False

        try:
            resp = client.chat_postMessage(
                channel=channel,
                text=text,
                attachments=attachments,
            )
            if resp["ok"]:
                logger.info(f"[Slack] Alert sent to {channel}")
                return True
            else:
                logger.warning(f"[Slack] API error: {resp.get('error')}")
                return False
        except Exception as e:
            logger.error(f"[Slack] Failed to send alert to {channel}: {e}")
            return False


slack_service = SlackService()
