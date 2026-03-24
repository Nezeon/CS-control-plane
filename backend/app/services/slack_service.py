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
                    {"type": "mrkdwn", "text": f"*Type:*\n{alert.alert_type}"},
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
    ) -> bool:
        """Post a meeting intelligence summary to the CS alerts channel after processing."""
        if not self.configured:
            return False

        channel = settings.SLACK_CHAT_CHANNEL or settings.SLACK_CH_CALL_INTEL

        # Sentiment emoji
        sent_emoji = {
            "positive": "🟢", "neutral": "⚪", "mixed": "🟡", "negative": "🔴",
        }.get((sentiment or "").lower(), "⚪")
        score_str = f" ({sentiment_score:.2f})" if sentiment_score is not None else ""

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📞 New Call Processed: {title[:120]}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Customer:*\n{customer_name or 'Unknown'}"},
                    {"type": "mrkdwn", "text": f"*Sentiment:*\n{sent_emoji} {sentiment or 'N/A'}{score_str}"},
                ],
            },
        ]

        if summary:
            blocks.extend(_text_to_section_blocks(summary, label="Summary"))

        # Key topics
        if key_topics:
            topics_str = ", ".join(str(t) for t in key_topics[:8])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Key Topics:* {topics_str}"},
            })

        # Action items (top 5)
        if action_items:
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
                "text": {"type": "mrkdwn", "text": f"*Action Items:*\n" + "\n".join(items_lines)},
            })

        # Risks
        if risks:
            risk_lines = []
            for r in risks[:3]:
                if isinstance(r, dict):
                    risk_lines.append(f"🔴 {r.get('description', str(r))}")
                else:
                    risk_lines.append(f"🔴 {r}")
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Risk Signals:*\n" + "\n".join(risk_lines)},
            })

        blocks.append({"type": "divider"})

        fallback = f"📞 Call processed: {title} ({customer_name or 'Unknown'}) — {sentiment or 'N/A'}"
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
                link_parts.append(f":link: *Jira:* <{jira_base_url}/browse/{jira_id}|{jira_id}>")
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
