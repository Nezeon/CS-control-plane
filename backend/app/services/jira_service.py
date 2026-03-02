import logging

logger = logging.getLogger("services.jira_mock")


class JiraService:
    """Mock Jira integration. Returns realistic fake data."""

    def get_ticket(self, jira_id: str) -> dict:
        """Mock: return a fake Jira ticket dict."""
        return {
            "key": jira_id,
            "fields": {
                "summary": f"Mock ticket {jira_id}",
                "description": "Mock description for testing",
                "issuetype": {"name": "Bug"},
                "priority": {"name": "High"},
                "status": {"name": "Open"},
                "assignee": {"displayName": "Vignesh"},
                "created": "2026-02-20T10:00:00Z",
                "updated": "2026-02-25T14:30:00Z",
            },
        }

    def update_ticket(self, jira_id: str, fields: dict) -> bool:
        """Mock: pretend to update a Jira ticket."""
        logger.info(f"[JIRA MOCK] Updated {jira_id}: {fields}")
        return True

    def get_recent_tickets(self, project: str = "CS", limit: int = 20) -> list[dict]:
        """Mock: return list of recent tickets."""
        return [
            self.get_ticket(f"{project}-{i}")
            for i in range(1, min(limit + 1, 6))
        ]
