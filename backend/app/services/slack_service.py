import logging

logger = logging.getLogger("services.slack_mock")


class SlackService:
    """Mock Slack integration."""

    def send_message(self, channel: str, text: str, blocks: list = None) -> bool:
        """Mock: log the message instead of sending to Slack."""
        logger.info(f"[SLACK #{channel}] {text}")
        return True

    def send_alert(
        self, channel: str, alert_title: str, alert_body: str, severity: str
    ) -> bool:
        """Mock: format and send an alert message."""
        logger.info(
            f"[SLACK ALERT #{channel}] [{severity.upper()}] {alert_title}: {alert_body}"
        )
        return True
