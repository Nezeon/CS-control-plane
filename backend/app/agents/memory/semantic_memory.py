"""
Tier 3: Semantic Memory — Lane-scoped shared knowledge pool backed by ChromaDB.

Agents publish learned insights to their lane's knowledge pool.
Other agents (same lane or cross-lane) can query for collective intelligence.
Tags are stored as comma-separated strings (ChromaDB metadata limitation).
"""

import logging
import uuid
from datetime import datetime, timezone

from app.chromadb_client import shared_knowledge as knowledge_collection

logger = logging.getLogger("memory.semantic")

VALID_LANES = {"support", "value", "delivery", "global"}


class SemanticMemory:

    def __init__(self, lane: str, agent_id: str = "", agent_name: str = ""):
        self.lane = lane if lane in VALID_LANES else "global"
        self.agent_id = agent_id
        self.agent_name = agent_name
        self._collection = knowledge_collection

    def publish(
        self,
        content: str,
        tags: list[str] | None = None,
        importance: int = 5,
        knowledge_type: str = "general",
        customer_id: str = "",
        customer_name: str = "",
        lane_override: str | None = None,
    ) -> str | None:
        """Publish a knowledge entry to the lane's shared pool. Returns entry ID or None."""
        if not self._collection:
            logger.warning("shared_knowledge collection unavailable")
            return None

        entry_id = f"sk-{self.agent_id}-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        target_lane = lane_override if lane_override in VALID_LANES else self.lane

        metadata = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "lane": target_lane,
            "tags": ",".join(tags) if tags else "",
            "importance": str(importance),
            "knowledge_type": knowledge_type,
            "customer_id": str(customer_id) if customer_id else "",
            "customer_name": customer_name,
            "timestamp": now,
        }
        clean_meta = {k: str(v) if v is not None else "" for k, v in metadata.items()}

        try:
            self._collection.upsert(
                ids=[entry_id],
                documents=[content],
                metadatas=[clean_meta],
            )
            logger.info(f"Knowledge published: {entry_id} (lane={target_lane}, type={knowledge_type})")
            return entry_id
        except Exception as e:
            logger.error(f"Failed to publish knowledge: {e}")
            return None

    def query(
        self,
        query_text: str,
        n: int = 5,
        customer_id: str | None = None,
    ) -> list[dict]:
        """Query knowledge within this agent's lane."""
        where_filter: dict = {"lane": self.lane}
        if customer_id:
            where_filter = {"$and": [{"lane": self.lane}, {"customer_id": str(customer_id)}]}
        return self._execute_query(query_text, n, where_filter)

    def query_cross_lane(
        self,
        query_text: str,
        n: int = 3,
        lanes: list[str] | None = None,
    ) -> list[dict]:
        """Query knowledge from other lanes (excludes own lane by default)."""
        if lanes:
            target_lanes = [l for l in lanes if l in VALID_LANES and l != self.lane]
        else:
            target_lanes = [l for l in VALID_LANES if l != self.lane]

        if not target_lanes:
            return []

        where_filter: dict = {"lane": {"$in": target_lanes}}
        return self._execute_query(query_text, n, where_filter)

    def query_global(self, query_text: str, n: int = 5) -> list[dict]:
        """Query knowledge across all lanes (no lane filter)."""
        return self._execute_query(query_text, n, where_filter={})

    def _execute_query(self, query_text: str, n: int, where_filter: dict) -> list[dict]:
        """Run a ChromaDB query with the given filter and format results."""
        if not self._collection:
            return []

        try:
            kwargs: dict = {
                "query_texts": [query_text],
                "n_results": min(n, 50),
            }
            if where_filter:
                kwargs["where"] = where_filter

            results = self._collection.query(**kwargs)
            return self._format_results(results)
        except Exception as e:
            logger.warning(f"Knowledge query failed: {e}")
            return []

    def _format_results(self, results: dict) -> list[dict]:
        """Convert ChromaDB query results to list of dicts with similarity and parsed tags."""
        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        formatted = []
        ids = results["ids"][0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            distance = distances[i] if i < len(distances) else 1.0
            similarity = max(0.0, 1.0 - distance)
            meta = metadatas[i] if i < len(metadatas) else {}

            # Parse comma-separated tags back to list
            raw_tags = meta.get("tags", "")
            tags_list = [t.strip() for t in raw_tags.split(",") if t.strip()] if raw_tags else []

            formatted.append({
                "id": doc_id,
                "text": documents[i] if i < len(documents) else "",
                "metadata": meta,
                "tags": tags_list,
                "similarity": round(similarity, 3),
            })

        return formatted
