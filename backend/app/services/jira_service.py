"""
Jira Service -- Atlassian Cloud REST API client for UCSC ticket integration.

Uses httpx with Basic Auth (email + API token).
Provides:
  - Issue search (JQL)
  - Single issue fetch
  - Issue-to-Ticket mapping
  - Customer resolution via jira_project_key
  - JQL builder for sync
"""

import logging
from base64 import b64encode
from datetime import datetime, timedelta
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger("services.jira")

# Jira priority -> our severity mapping
JIRA_PRIORITY_MAP = {
    "highest": "P1",
    "high": "P2",
    "medium": "P3",
    "low": "P4",
    "lowest": "P5",
    "p1": "P1",
    "p2": "P2",
    "p3": "P3",
    "p4": "P4",
    "p5": "P5",
    "critical": "P1",
    "major": "P2",
    "minor": "P3",
    "trivial": "P4",
}

# Jira status -> our status mapping
JIRA_STATUS_MAP = {
    "to do": "open",
    "open": "open",
    "new": "open",
    "in progress": "in_progress",
    "in review": "in_progress",
    "review": "in_progress",
    "waiting for customer": "in_progress",
    "waiting for support": "in_progress",
    "blocked": "in_progress",
    "done": "resolved",
    "resolved": "resolved",
    "closed": "closed",
    "won't do": "closed",
    "cancelled": "closed",
    "duplicate": "closed",
}

# Fields to request from Jira (keep payload small)
JIRA_FIELDS = [
    "summary", "description", "status", "priority", "issuetype",
    "assignee", "reporter", "created", "updated", "resolutiondate",
    "project", "labels", "components",
]


class JiraService:
    """Atlassian Cloud Jira REST API client."""

    def __init__(self):
        self._client: Optional[httpx.Client] = None

    @property
    def configured(self) -> bool:
        return bool(settings.JIRA_API_URL and settings.JIRA_EMAIL and settings.JIRA_API_TOKEN)

    def _get_client(self) -> httpx.Client:
        """Lazy-init httpx client with Basic Auth."""
        if self._client is None:
            if not self.configured:
                raise RuntimeError("Jira not configured: set JIRA_API_URL, JIRA_EMAIL, JIRA_API_TOKEN")

            credentials = b64encode(
                f"{settings.JIRA_EMAIL}:{settings.JIRA_API_TOKEN}".encode()
            ).decode()

            self._client = httpx.Client(
                base_url=f"{settings.JIRA_API_URL.rstrip('/')}/rest/api/3",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
            )
        return self._client

    # -- Search ---------------------------------------------------------------

    def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        start_at: int = 0,
        fields: list[str] | None = None,
    ) -> dict:
        """
        Search Jira issues using JQL.
        Returns raw Jira response: {issues, total, startAt, maxResults}
        """
        client = self._get_client()
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "startAt": start_at,
            "fields": fields or JIRA_FIELDS,
        }

        logger.info(f"[Jira] Searching: {jql} (start={start_at}, max={max_results})")
        # Use new /search/jql endpoint (old POST /search is deprecated/410)
        params = {
            "jql": jql,
            "maxResults": max_results,
            "startAt": start_at,
            "fields": ",".join(fields or JIRA_FIELDS),
        }
        resp = client.get("/search/jql", params=params)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"[Jira] Found {len(data.get('issues', []))} issues")
        return data

    def search_all_issues(self, jql: str, page_size: int = 50, max_issues: int = 3000) -> list[dict]:
        """Paginate through results for a JQL query (capped at max_issues)."""
        all_issues = []
        start_at = 0

        while True:
            data = self.search_issues(jql, max_results=page_size, start_at=start_at)
            issues = data.get("issues", [])
            all_issues.extend(issues)

            if data.get("isLast", True) or len(issues) < page_size:
                break
            start_at += len(issues)

            if len(all_issues) >= max_issues:
                logger.info(f"[Jira] Hit max_issues cap ({max_issues}), stopping pagination")
                break

        return all_issues

    def get_issue(self, issue_key: str) -> dict:
        """Fetch a single Jira issue by key (e.g. CS-123)."""
        client = self._get_client()
        resp = client.get(f"/issue/{issue_key}", params={"fields": ",".join(JIRA_FIELDS)})
        resp.raise_for_status()
        return resp.json()

    # -- Mapping --------------------------------------------------------------

    def map_issue_to_ticket(self, issue: dict) -> dict:
        """
        Convert a Jira issue to our Ticket model fields.
        Returns a dict with model fields + underscore-prefixed metadata.
        """
        fields = issue.get("fields", {})

        # Status mapping
        jira_status = (fields.get("status", {}).get("name") or "open").lower()
        status = JIRA_STATUS_MAP.get(jira_status, "open")

        # Priority/severity mapping
        jira_priority = (fields.get("priority", {}).get("name") or "medium").lower()
        severity = JIRA_PRIORITY_MAP.get(jira_priority, "P3")

        # Issue type
        issue_type = fields.get("issuetype", {}).get("name", "Task")

        # Description: Jira v3 uses ADF (Atlassian Document Format)
        description = self._extract_description_text(fields.get("description"))

        # Dates
        created_at = self._parse_jira_date(fields.get("created"))
        updated_at = self._parse_jira_date(fields.get("updated"))
        resolved_at = self._parse_jira_date(fields.get("resolutiondate"))

        # SLA deadline: created_at + configurable hours per severity
        sla_deadline = None
        if created_at:
            sla_hours_map = {
                "P1": settings.SLA_HOURS_P1,
                "P2": settings.SLA_HOURS_P2,
                "P3": settings.SLA_HOURS_P3,
                "P4": settings.SLA_HOURS_P4,
            }
            sla_hours = sla_hours_map.get(severity, settings.SLA_HOURS_P3)
            sla_deadline = created_at + timedelta(hours=sla_hours)

        # Assignee
        assignee_email = None
        assignee_name = None
        if fields.get("assignee"):
            assignee_email = fields["assignee"].get("emailAddress")
            assignee_name = fields["assignee"].get("displayName")

        # Reporter
        reporter_name = None
        if fields.get("reporter"):
            reporter_name = fields["reporter"].get("displayName")

        # Project key (for customer mapping)
        project_key = fields.get("project", {}).get("key", "")

        # Labels and components
        labels = list(fields.get("labels", []))
        components = [c.get("name", "") for c in fields.get("components", [])]

        return {
            "jira_id": issue.get("key"),
            "summary": fields.get("summary", ""),
            "description": description,
            "ticket_type": issue_type,
            "severity": severity,
            "status": status,
            "created_at": created_at,
            "updated_at": updated_at,
            "resolved_at": resolved_at,
            "sla_deadline": sla_deadline,
            # Metadata (underscore-prefixed, not stored directly on Ticket)
            "_project_key": project_key,
            "_assignee_email": assignee_email,
            "_assignee_name": assignee_name,
            "_reporter_name": reporter_name,
            "_labels": labels,
            "_components": components,
            "_jira_status_raw": jira_status,
            "_jira_priority_raw": jira_priority,
        }

    def _extract_description_text(self, description) -> str:
        """Extract plain text from Jira ADF or plain string."""
        if not description:
            return ""
        if isinstance(description, str):
            return description

        parts: list[str] = []
        self._walk_adf(description, parts)
        return "\n".join(parts)

    def _walk_adf(self, node: dict, parts: list):
        """Recursively walk ADF nodes to extract text content."""
        if not isinstance(node, dict):
            return
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
        elif node.get("type") == "hardBreak":
            parts.append("\n")
        for child in node.get("content", []):
            self._walk_adf(child, parts)

    def _parse_jira_date(self, date_str: str | None) -> datetime | None:
        """Parse Jira ISO date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("+0000", "+00:00"))
        except (ValueError, AttributeError):
            return None

    # -- Write Operations -----------------------------------------------------

    def update_issue_labels(self, issue_key: str, labels: list[str]) -> bool:
        """Update labels on a Jira issue. Returns True on success."""
        try:
            client = self._get_client()
            resp = client.put(
                f"/issue/{issue_key}",
                json={"fields": {"labels": labels}},
            )
            resp.raise_for_status()
            logger.info(f"[Jira] Updated labels on {issue_key}: {labels}")
            return True
        except Exception as e:
            logger.error(f"[Jira] Failed to update labels on {issue_key}: {e}")
            return False

    def add_comment(self, issue_key: str, comment_text: str) -> bool:
        """Add a comment to a Jira issue (ADF format). Returns True on success."""
        try:
            client = self._get_client()
            # Jira v3 requires Atlassian Document Format for comments
            adf_body = {
                "body": {
                    "version": 1,
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": comment_text}],
                        }
                    ],
                }
            }
            resp = client.post(f"/issue/{issue_key}/comment", json=adf_body)
            resp.raise_for_status()
            logger.info(f"[Jira] Added comment to {issue_key}")
            return True
        except Exception as e:
            logger.error(f"[Jira] Failed to add comment to {issue_key}: {e}")
            return False

    # -- Customer Resolution --------------------------------------------------

    def resolve_customer_id(self, db, project_key: str):
        """Look up customer by jira_project_key. Returns (customer_id, customer_name) or (None, None)."""
        from app.models.customer import Customer

        if not project_key:
            return None, None

        customer = db.query(Customer).filter_by(jira_project_key=project_key).first()
        if customer:
            return customer.id, customer.name

        return None, None

    # -- JQL Builder ----------------------------------------------------------

    def build_sync_jql(
        self,
        project_keys: list[str] | None = None,
        since: str | None = None,
    ) -> str:
        """
        Build JQL for sync.

        Args:
            project_keys: Jira project keys to sync. Defaults to JIRA_DEFAULT_PROJECT.
            since: ISO date string -- only fetch issues updated after this date.
        """
        if settings.JIRA_SYNC_JQL:
            jql = settings.JIRA_SYNC_JQL
            if since:
                jql += f" AND updated >= '{since}'"
            return jql

        keys = project_keys or [settings.JIRA_DEFAULT_PROJECT]
        projects = ", ".join(keys)
        jql = f"project in ({projects})"

        if since:
            jql += f" AND updated >= '{since}'"

        jql += " ORDER BY updated DESC"
        return jql


jira_service = JiraService()
