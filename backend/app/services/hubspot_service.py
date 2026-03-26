"""
HubSpot Service -- CRM API client for deal pipeline integration.

Uses httpx with Bearer token auth (Private App Token).
Provides:
  - Deal listing and single-deal fetch
  - Pipeline stage definitions
  - Company lookup (for deal-to-customer mapping)
  - Deal-to-internal-model mapping
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger("services.hubspot")

# Properties to request from HubSpot deals
DEAL_PROPERTIES = [
    "dealname", "dealstage", "pipeline", "amount", "closedate",
    "hubspot_owner_id", "hs_lastmodifieddate", "hs_createdate",
    "deal_currency_code",
]


class HubSpotService:
    """HubSpot CRM v3 API client."""

    def __init__(self):
        self._client: Optional[httpx.Client] = None
        self._stage_cache: dict[str, str] = {}  # stage_id -> stage_label

    @property
    def configured(self) -> bool:
        return bool(settings.HUBSPOT_ACCESS_TOKEN)

    def _get_client(self) -> httpx.Client:
        """Lazy-init httpx client with Bearer token auth."""
        if self._client is None:
            if not self.configured:
                raise RuntimeError("HubSpot not configured: set HUBSPOT_ACCESS_TOKEN")

            self._client = httpx.Client(
                base_url=settings.HUBSPOT_API_BASE_URL.rstrip("/"),
                headers={
                    "Authorization": f"Bearer {settings.HUBSPOT_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
            )
        return self._client

    # -- Deals ----------------------------------------------------------------

    def list_deals(
        self,
        properties: list[str] | None = None,
        after: str | None = None,
        limit: int = 100,
    ) -> dict:
        """
        List deals with pagination.
        Returns raw HubSpot response: {results, paging}
        """
        client = self._get_client()
        params: dict = {
            "limit": min(limit, 100),
            "properties": ",".join(properties or DEAL_PROPERTIES),
        }
        if after:
            params["after"] = after

        resp = client.get("/crm/v3/objects/deals", params=params)
        resp.raise_for_status()
        return resp.json()

    def list_all_deals(self, properties: list[str] | None = None, max_deals: int = 5000) -> list[dict]:
        """Paginate through all deals. Returns list of deal objects."""
        all_deals = []
        after = None

        while len(all_deals) < max_deals:
            data = self.list_deals(properties=properties, after=after)
            results = data.get("results", [])
            all_deals.extend(results)

            paging = data.get("paging", {})
            next_page = paging.get("next", {})
            after = next_page.get("after")

            if not after or not results:
                break

        logger.info(f"[HubSpot] Fetched {len(all_deals)} deals total")
        return all_deals

    def get_deal(self, deal_id: str, properties: list[str] | None = None) -> dict:
        """Fetch a single deal by HubSpot ID."""
        client = self._get_client()
        params = {"properties": ",".join(properties or DEAL_PROPERTIES)}
        resp = client.get(f"/crm/v3/objects/deals/{deal_id}", params=params)
        resp.raise_for_status()
        return resp.json()

    # -- Associations ---------------------------------------------------------

    def get_deal_associations(self, deal_id: str, to_object_type: str = "companies") -> list[str]:
        """Get associated object IDs for a deal. Returns list of company IDs."""
        client = self._get_client()
        try:
            resp = client.get(f"/crm/v3/objects/deals/{deal_id}/associations/{to_object_type}")
            resp.raise_for_status()
            data = resp.json()
            return [str(r["id"]) for r in data.get("results", [])]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            raise

    # -- Companies ------------------------------------------------------------

    def get_company(self, company_id: str) -> dict:
        """Fetch a single company by HubSpot ID."""
        client = self._get_client()
        params = {"properties": "name,domain,industry"}
        resp = client.get(f"/crm/v3/objects/companies/{company_id}", params=params)
        resp.raise_for_status()
        return resp.json()

    # -- Pipelines ------------------------------------------------------------

    def list_pipelines(self) -> list[dict]:
        """Fetch all deal pipelines with stages."""
        client = self._get_client()
        resp = client.get("/crm/v3/pipelines/deals")
        resp.raise_for_status()
        return resp.json().get("results", [])

    def load_stage_cache(self) -> dict[str, str]:
        """Build stage_id -> label map from pipelines. Caches in memory."""
        if self._stage_cache:
            return self._stage_cache

        try:
            pipelines = self.list_pipelines()
            for pipeline in pipelines:
                for stage in pipeline.get("stages", []):
                    self._stage_cache[stage["id"]] = stage["label"]
            logger.info(f"[HubSpot] Cached {len(self._stage_cache)} pipeline stages")
        except Exception as e:
            logger.warning(f"[HubSpot] Failed to load pipeline stages: {e}")

        return self._stage_cache

    def get_stage_label(self, stage_id: str) -> str:
        """Resolve stage ID to human-readable label."""
        if not self._stage_cache:
            self.load_stage_cache()
        return self._stage_cache.get(stage_id, stage_id)

    # -- Mapping --------------------------------------------------------------

    def map_deal_to_internal(self, deal: dict, company_name: str | None = None) -> dict:
        """
        Convert HubSpot deal to internal Deal model fields.
        Returns dict ready for Deal(**mapped).
        """
        props = deal.get("properties", {})

        amount = None
        if props.get("amount"):
            try:
                amount = float(props["amount"])
            except (ValueError, TypeError):
                pass

        close_date = None
        if props.get("closedate"):
            close_date = self._parse_hubspot_date(props["closedate"])

        return {
            "hubspot_deal_id": str(deal.get("id", "")),
            "deal_name": props.get("dealname", "Untitled Deal"),
            "stage": props.get("dealstage", ""),
            "pipeline": props.get("pipeline", "default"),
            "amount": amount,
            "close_date": close_date.date() if close_date else None,
            "company_name": company_name,
            "properties": props,
            "hubspot_created_at": self._parse_hubspot_date(props.get("hs_createdate")),
            "hubspot_updated_at": self._parse_hubspot_date(props.get("hs_lastmodifieddate")),
        }

    def _parse_hubspot_date(self, date_str: str | None) -> datetime | None:
        """Parse HubSpot date string (ISO format or epoch ms)."""
        if not date_str:
            return None
        try:
            # HubSpot uses ISO 8601 format
            if "T" in str(date_str):
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt
            # Some fields may be epoch milliseconds
            ts = int(date_str)
            return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        except (ValueError, TypeError, OSError):
            return None


# Singleton instance
hubspot_service = HubSpotService()
