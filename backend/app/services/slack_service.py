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
        """Post a deal-specific Pre-Sales card for a single deal stage change."""
        if not self.configured:
            logger.debug("[Slack] Not configured, skipping presales card")
            return False

        deal_name = draft_content.get("deal_name", "Unknown")
        company = draft_content.get("company_name", "Unknown")
        amount = draft_content.get("amount")
        old_stage = draft_content.get("old_stage", "")
        new_stage = draft_content.get("new_stage", "")
        probability = draft_content.get("probability")
        factor_scores = draft_content.get("factor_scores", {})
        summary = draft_content.get("summary", "Deal analysis complete.")
        risks = draft_content.get("risks", [])
        next_steps = draft_content.get("next_steps", [])

        old_friendly = _friendly_stage(old_stage) if old_stage else "Unknown"
        new_friendly = _friendly_stage(new_stage) if new_stage else "Unknown"
        amt_str = f"${amount:,.0f}" if amount else "N/A"

        # Determine stage direction
        from app.agents.presales_funnel_agent import STAGE_ORDER
        old_idx = STAGE_ORDER.get(old_stage, -2)
        new_idx = STAGE_ORDER.get(new_stage, -2)
        if new_idx > old_idx:
            direction_emoji = ":arrow_upper_right:"
        elif new_idx < old_idx:
            direction_emoji = ":arrow_lower_right:"
        else:
            direction_emoji = ":arrow_right:"

        # ── Header ──
        header_text = f":handshake: Deal Update: {deal_name}"[:150]
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": header_text, "emoji": True},
            },
        ]

        # ── Metadata Fields ──
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f":office: *Company:*\n{company}"},
                {"type": "mrkdwn", "text": f":moneybag: *Value:*\n{amt_str}"},
            ],
        })

        # ── Stage Transition ──
        if old_stage and new_stage:
            stage_text = f"{direction_emoji} *{old_friendly}*  :arrow_right:  *{new_friendly}*"
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Stage Change*\n{stage_text}"},
            })

        blocks.append({"type": "divider"})

        # ── Win Probability + Factor Breakdown ──
        if probability is not None:
            prob_emoji = ":large_green_circle:" if probability >= 0.7 else ":large_yellow_circle:" if probability >= 0.4 else ":red_circle:"
            prob_text = f"{prob_emoji} *Win Probability: {probability:.0%}*"

            if factor_scores:
                breakdown_parts = []
                for k in ["stage", "engagement", "intent", "sentiment", "velocity"]:
                    v = factor_scores.get(k)
                    if v is not None:
                        breakdown_parts.append(f"{k.title()}: {int(v * 100)}%")
                if breakdown_parts:
                    prob_text += f"\n{' | '.join(breakdown_parts)}"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": prob_text},
            })
        else:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": ":white_circle: *Win Probability:* N/A (deal may be closed)"},
            })

        # ── AI Analysis ──
        if summary and summary != "Deal analysis complete.":
            blocks.append({"type": "divider"})
            blocks.extend(_text_to_section_blocks(summary[:2000], label=":brain: Analysis"))

        # ── Risk Signals ──
        if risks:
            risk_lines = []
            for r in risks[:3]:
                risk_text = r if isinstance(r, str) else r.get("description", str(r)) if isinstance(r, dict) else str(r)
                risk_lines.append(f":red_circle: {risk_text}")
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*:warning: Risk Signals*\n" + "\n".join(risk_lines)},
            })

        # ── Next Steps ──
        if next_steps:
            step_lines = []
            for i, s in enumerate(next_steps[:4], 1):
                step_text = s if isinstance(s, str) else str(s)
                step_lines.append(f"{i}. {step_text}")
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*:clipboard: Next Steps*\n" + "\n".join(step_lines)},
            })

        # ── Dashboard Link ──
        if dashboard_url:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f":bar_chart: <{dashboard_url}|View Deal in Dashboard>"},
            })

        # ── Context Footer ──
        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Agent: Pre-Sales Funnel (Jordan Reeves) | Event: `{event_type}` | Draft: `{draft_id[:8]}`"},
            ],
        })

        if probability is not None:
            fallback = f":handshake: {deal_name} ({company}): {old_friendly} -> {new_friendly}, {probability:.0%} win probability"
        else:
            fallback = f":handshake: {deal_name} ({company}): {old_friendly} -> {new_friendly}"
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
        """Post an informational agent card to Slack.

        Returns the Slack API response dict (including 'ts') on success,
        or False on failure.
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
            *_text_to_section_blocks(action_required, label="Recommendation"),
        ]

        # Add links section (Jira + Dashboard)
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
            # Insert before the context footer
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
