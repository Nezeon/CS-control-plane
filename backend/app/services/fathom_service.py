"""
Fathom API client.

Wraps the Fathom external API (https://api.fathom.ai/external/v1) to fetch
meetings, transcripts, summaries, and manage webhooks.

Rate limit: 60 requests / minute per user (across all API keys).
Auth: X-Api-Key header.
"""

import logging
from datetime import datetime

import httpx

from app.config import settings

logger = logging.getLogger("services.fathom")

_TIMEOUT = 30.0  # seconds


class FathomAPIError(Exception):
    """Raised when the Fathom API returns a non-2xx response."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Fathom API {status_code}: {detail}")


class FathomService:
    """Real Fathom API client using httpx."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.FATHOM_API_KEY
        self.base_url = (base_url or settings.FATHOM_API_BASE_URL).rstrip("/")

    @property
    def _headers(self) -> dict:
        return {"X-Api-Key": self.api_key}

    def _check_configured(self) -> None:
        if not self.api_key:
            raise FathomAPIError(0, "FATHOM_API_KEY not configured")

    # ------------------------------------------------------------------
    # Meetings
    # ------------------------------------------------------------------

    async def list_meetings(
        self,
        *,
        cursor: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        recorded_by: list[str] | None = None,
        teams: list[str] | None = None,
        include_transcript: bool = False,
        include_summary: bool = False,
        include_action_items: bool = False,
        include_crm_matches: bool = False,
    ) -> dict:
        """
        GET /meetings — list meetings with optional filters.

        Returns {"limit": int, "next_cursor": str|None, "items": [Meeting]}.
        """
        self._check_configured()

        params: dict = {}
        if cursor:
            params["cursor"] = cursor
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before
        if recorded_by:
            params["recorded_by[]"] = recorded_by
        if teams:
            params["teams[]"] = teams
        if include_transcript:
            params["include_transcript"] = "true"
        if include_summary:
            params["include_summary"] = "true"
        if include_action_items:
            params["include_action_items"] = "true"
        if include_crm_matches:
            params["include_crm_matches"] = "true"

        return await self._get("/meetings", params=params)

    async def list_all_meetings(
        self,
        *,
        created_after: str | None = None,
        created_before: str | None = None,
        include_transcript: bool = False,
        include_summary: bool = False,
        include_action_items: bool = False,
    ) -> list[dict]:
        """
        Paginate through ALL meetings matching the filters.
        Returns the full list of Meeting objects.
        """
        all_items: list[dict] = []
        cursor = None

        while True:
            page = await self.list_meetings(
                cursor=cursor,
                created_after=created_after,
                created_before=created_before,
                include_transcript=include_transcript,
                include_summary=include_summary,
                include_action_items=include_action_items,
            )
            all_items.extend(page.get("items", []))

            cursor = page.get("next_cursor")
            if not cursor:
                break

        logger.info(f"Fetched {len(all_items)} meetings from Fathom")
        return all_items

    # ------------------------------------------------------------------
    # Transcript + Summary (per recording)
    # ------------------------------------------------------------------

    async def get_transcript(self, recording_id: int) -> dict:
        """
        GET /recordings/{recording_id}/transcript

        Returns {"transcript": [{"speaker": {...}, "text": str, "timestamp": str}]}.
        """
        self._check_configured()
        return await self._get(f"/recordings/{recording_id}/transcript")

    async def get_summary(self, recording_id: int) -> dict:
        """
        GET /recordings/{recording_id}/summary

        Returns {"summary": {"template_name": str|None, "markdown_formatted": str|None}}.
        """
        self._check_configured()
        return await self._get(f"/recordings/{recording_id}/summary")

    # ------------------------------------------------------------------
    # Teams
    # ------------------------------------------------------------------

    async def list_teams(self, cursor: str | None = None) -> dict:
        """GET /teams — list teams."""
        self._check_configured()
        params = {"cursor": cursor} if cursor else {}
        return await self._get("/teams", params=params)

    async def list_team_members(
        self, *, team: str | None = None, cursor: str | None = None
    ) -> dict:
        """GET /team_members — list team members."""
        self._check_configured()
        params: dict = {}
        if team:
            params["team"] = team
        if cursor:
            params["cursor"] = cursor
        return await self._get("/team_members", params=params)

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    async def create_webhook(
        self,
        destination_url: str,
        *,
        triggered_for: list[str] | None = None,
        include_transcript: bool = True,
        include_summary: bool = True,
        include_action_items: bool = True,
        include_crm_matches: bool = False,
    ) -> dict:
        """
        POST /webhooks — register a new webhook.

        Returns the created webhook including its `secret` (only returned once).
        """
        self._check_configured()

        body = {
            "destination_url": destination_url,
            "triggered_for": triggered_for or ["my_recordings", "shared_team_recordings"],
            "include_transcript": include_transcript,
            "include_summary": include_summary,
            "include_action_items": include_action_items,
            "include_crm_matches": include_crm_matches,
        }

        return await self._post("/webhooks", json_body=body)

    async def delete_webhook(self, webhook_id: str) -> None:
        """DELETE /webhooks/{id}."""
        self._check_configured()
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.delete(
                f"{self.base_url}/webhooks/{webhook_id}",
                headers=self._headers,
            )
            if resp.status_code not in (204, 200):
                raise FathomAPIError(resp.status_code, resp.text)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def build_flat_transcript(self, transcript_items: list[dict]) -> str:
        """
        Convert Fathom's transcript array into a flat text block
        suitable for feeding into the Call Intelligence agent.

        Input:  [{"speaker": {"display_name": "Alice"}, "text": "Hello", "timestamp": "00:01:23"}, ...]
        Output: "[00:01:23] Alice: Hello\n[00:02:10] Bob: Hi there\n..."
        """
        lines = []
        for item in transcript_items:
            speaker_name = item.get("speaker", {}).get("display_name", "Unknown")
            timestamp = item.get("timestamp", "")
            text = item.get("text", "")
            lines.append(f"[{timestamp}] {speaker_name}: {text}")
        return "\n".join(lines)

    def extract_participants(self, meeting: dict) -> list[str]:
        """Extract unique participant names from a meeting object."""
        names: set[str] = set()

        recorder = meeting.get("recorded_by", {})
        if recorder.get("name"):
            names.add(recorder["name"])

        for invitee in meeting.get("calendar_invitees", []):
            if invitee.get("name"):
                names.add(invitee["name"])
            elif invitee.get("email"):
                names.add(invitee["email"])

        return sorted(names)

    def estimate_duration_minutes(self, meeting: dict) -> int | None:
        """Calculate call duration from recording timestamps."""
        start = meeting.get("recording_start_time")
        end = meeting.get("recording_end_time")
        if not start or not end:
            return None
        try:
            t_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
            t_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
            return max(1, int((t_end - t_start).total_seconds() / 60))
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------
    # Internal HTTP helpers
    # ------------------------------------------------------------------

    async def _get(self, path: str, *, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{self.base_url}{path}",
                headers=self._headers,
                params=params,
            )
            if resp.status_code == 429:
                raise FathomAPIError(429, "Rate limited — 60 requests/minute exceeded")
            if resp.status_code != 200:
                raise FathomAPIError(resp.status_code, resp.text[:500])
            return resp.json()

    async def _post(self, path: str, *, json_body: dict) -> dict:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{self.base_url}{path}",
                headers=self._headers,
                json=json_body,
            )
            if resp.status_code not in (200, 201):
                raise FathomAPIError(resp.status_code, resp.text[:500])
            return resp.json()


# Singleton
fathom_service = FathomService()
