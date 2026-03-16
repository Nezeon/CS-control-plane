"""
Tier 2: Episodic Memory — Per-agent execution diary backed by ChromaDB.

Stores summaries of past pipeline runs with importance scores.
Retrieval uses tri-factor scoring: 35% relevance + 25% recency + 40% importance.
Consolidation summarizes oldest entries when count exceeds threshold.
"""

import logging
import math
import uuid
from datetime import datetime, timezone

from app.chromadb_client import episodic_memory as episodic_collection

logger = logging.getLogger("memory.episodic")

# Tri-factor scoring weights
RELEVANCE_WEIGHT = 0.35
RECENCY_WEIGHT = 0.25
IMPORTANCE_WEIGHT = 0.40

# Consolidation thresholds
CONSOLIDATION_TRIGGER = 25
CONSOLIDATION_OLDEST_N = 15
CONSOLIDATION_OUTPUT_N = 3
CONSOLIDATION_IMPORTANCE = 9

# Recency decay
RECENCY_HALF_LIFE_DAYS = 30.0


class EpisodicMemory:

    def __init__(self, agent_id: str, agent_name: str = "", tier: int = 3, lane: str = ""):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.tier = tier
        self.lane = lane
        self._collection = episodic_collection

    def remember(
        self,
        summary: str,
        importance: int = 5,
        customer_id: str = "",
        customer_name: str = "",
        event_type: str = "",
        execution_id: str = "",
    ) -> str | None:
        """Store a new episodic memory entry. Returns entry ID or None on failure."""
        if not self._collection:
            logger.warning("episodic_memory collection unavailable")
            return None

        entry_id = f"ep-{self.agent_id}-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        metadata = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "customer_id": str(customer_id) if customer_id else "",
            "customer_name": customer_name,
            "event_type": event_type,
            "execution_id": str(execution_id) if execution_id else "",
            "importance": str(importance),
            "tier": str(self.tier),
            "lane": self.lane or "",
            "timestamp": now,
            "is_consolidated": "false",
        }
        clean_meta = {k: str(v) if v is not None else "" for k, v in metadata.items()}

        try:
            self._collection.upsert(
                ids=[entry_id],
                documents=[summary],
                metadatas=[clean_meta],
            )
            logger.info(f"Episodic memory stored: {entry_id} (importance={importance})")
            self._maybe_consolidate()
            return entry_id
        except Exception as e:
            logger.error(f"Failed to store episodic memory: {e}")
            return None

    def recall_similar(self, query: str, n: int = 5) -> list[dict]:
        """
        Find similar past experiences using tri-factor scoring.

        Returns list of dicts sorted by combined_score descending:
        [{"id", "text", "metadata", "relevance", "recency", "importance_score", "combined_score"}]
        """
        if not self._collection:
            return []

        try:
            fetch_n = min(n * 3, 50)
            results = self._collection.query(
                query_texts=[query],
                n_results=fetch_n,
                where={"agent_id": self.agent_id},
            )
            scored = self._apply_tri_factor_scoring(results)
            return scored[:n]
        except Exception as e:
            logger.warning(f"Episodic recall failed: {e}")
            return []

    def get_recent(self, n: int = 5) -> list[dict]:
        """Get the most recent episodic memories for this agent."""
        if not self._collection:
            return []

        try:
            results = self._collection.query(
                query_texts=["agent execution summary"],
                n_results=min(n * 2, 50),
                where={"agent_id": self.agent_id},
            )
            entries = self._format_raw_results(results)
            entries.sort(
                key=lambda e: e.get("metadata", {}).get("timestamp", ""),
                reverse=True,
            )
            return entries[:n]
        except Exception as e:
            logger.warning(f"Episodic get_recent failed: {e}")
            return []

    def get_entry_count(self) -> int:
        """Count how many episodic entries this agent has."""
        if not self._collection:
            return 0
        try:
            results = self._collection.get(where={"agent_id": self.agent_id})
            return len(results.get("ids", []))
        except Exception as e:
            logger.warning(f"Episodic count failed: {e}")
            return 0

    # ── Tri-Factor Scoring ──────────────────────────────────────────

    def _apply_tri_factor_scoring(self, raw_results: dict) -> list[dict]:
        """
        Re-rank ChromaDB results using tri-factor scoring:
        combined = 0.35 * relevance + 0.25 * recency + 0.40 * (importance / 10)
        """
        entries = self._format_raw_results(raw_results)
        now = datetime.now(timezone.utc)

        for entry in entries:
            meta = entry.get("metadata", {})

            # Factor 1: Relevance (from ChromaDB cosine distance)
            relevance = entry.get("similarity", 0.0)

            # Factor 2: Recency (exponential decay)
            try:
                ts = datetime.fromisoformat(meta.get("timestamp", ""))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                days_old = (now - ts).total_seconds() / 86400.0
            except (ValueError, TypeError):
                days_old = 365.0
            recency = math.exp(-days_old / RECENCY_HALF_LIFE_DAYS)

            # Factor 3: Importance (normalized 1-10 to 0-1)
            try:
                importance_raw = int(meta.get("importance", "5"))
            except (ValueError, TypeError):
                importance_raw = 5
            importance_norm = min(max(importance_raw, 1), 10) / 10.0

            # Combined score
            combined = (
                RELEVANCE_WEIGHT * relevance
                + RECENCY_WEIGHT * recency
                + IMPORTANCE_WEIGHT * importance_norm
            )

            entry["relevance"] = round(relevance, 4)
            entry["recency"] = round(recency, 4)
            entry["importance_score"] = round(importance_norm, 4)
            entry["combined_score"] = round(combined, 4)

        entries.sort(key=lambda e: e["combined_score"], reverse=True)
        return entries

    # ── Consolidation ───────────────────────────────────────────────

    def _maybe_consolidate(self) -> None:
        """
        If entry count exceeds threshold, summarize the oldest entries
        into high-level insight entries using Claude.
        """
        count = self.get_entry_count()
        if count <= CONSOLIDATION_TRIGGER:
            return

        logger.info(
            f"Episodic consolidation triggered for {self.agent_id}: "
            f"{count} entries > {CONSOLIDATION_TRIGGER} threshold"
        )

        try:
            # Get all entries for this agent
            all_entries = self._collection.get(where={"agent_id": self.agent_id})
            if not all_entries or not all_entries.get("ids"):
                return

            # Build tuples and filter out already-consolidated entries
            entries_with_ts = []
            ids = all_entries["ids"]
            docs = all_entries.get("documents", [])
            metas = all_entries.get("metadatas", [])

            for i, entry_id in enumerate(ids):
                meta = metas[i] if i < len(metas) else {}
                if meta.get("is_consolidated") == "true":
                    continue
                ts = meta.get("timestamp", "")
                doc = docs[i] if i < len(docs) else ""
                entries_with_ts.append((entry_id, ts, doc, meta))

            # Sort oldest first
            entries_with_ts.sort(key=lambda x: x[1])

            to_consolidate = entries_with_ts[:CONSOLIDATION_OLDEST_N]
            if len(to_consolidate) < CONSOLIDATION_OLDEST_N:
                return

            # Summarize using Claude
            from app.services import claude_service

            summaries_text = "\n---\n".join(
                f"[{tc[1]}] (importance: {tc[3].get('importance', '5')})\n{tc[2]}"
                for tc in to_consolidate
            )

            consolidation_prompt = (
                f"You are summarizing past execution memories for agent '{self.agent_name}' "
                f"(ID: {self.agent_id}).\n\n"
                f"Below are {len(to_consolidate)} past execution summaries. "
                f"Distill them into exactly {CONSOLIDATION_OUTPUT_N} high-level insight paragraphs. "
                f"Each insight should capture a key pattern, lesson learned, or recurring theme.\n\n"
                f"Return ONLY the {CONSOLIDATION_OUTPUT_N} insights, separated by '---' on its own line.\n\n"
                f"Past memories:\n{summaries_text}"
            )

            response = claude_service.generate_sync(
                system_prompt="You are a memory consolidation system. Distill agent memories into key insights.",
                user_message=consolidation_prompt,
                max_tokens=2048,
                temperature=0.3,
            )

            if "error" in response:
                logger.error(f"Consolidation Claude call failed: {response}")
                return

            # Parse response into N insights
            raw_insights = response["content"].split("---")
            insights = [i.strip() for i in raw_insights if i.strip()]
            insights = insights[:CONSOLIDATION_OUTPUT_N]

            if not insights:
                logger.warning("Consolidation produced no insights")
                return

            # Delete old entries
            ids_to_delete = [tc[0] for tc in to_consolidate]
            self._collection.delete(ids=ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} old episodic entries")

            # Insert consolidated insights
            now = datetime.now(timezone.utc).isoformat()
            for insight_text in insights:
                insight_id = f"ep-{self.agent_id}-consolidated-{uuid.uuid4().hex[:8]}"
                meta = {
                    "agent_id": self.agent_id,
                    "agent_name": self.agent_name,
                    "customer_id": "",
                    "customer_name": "",
                    "event_type": "consolidation",
                    "execution_id": "",
                    "importance": str(CONSOLIDATION_IMPORTANCE),
                    "tier": str(self.tier),
                    "lane": self.lane or "",
                    "timestamp": now,
                    "is_consolidated": "true",
                }
                clean_meta = {k: str(v) if v is not None else "" for k, v in meta.items()}
                self._collection.upsert(
                    ids=[insight_id],
                    documents=[insight_text],
                    metadatas=[clean_meta],
                )

            logger.info(
                f"Consolidation complete: {len(ids_to_delete)} entries → {len(insights)} insights"
            )

        except Exception as e:
            logger.error(f"Consolidation failed: {e}")

    # ── Helpers ──────────────────────────────────────────────────────

    def _format_raw_results(self, results: dict) -> list[dict]:
        """Convert ChromaDB query results to list of dicts with similarity."""
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
            formatted.append({
                "id": doc_id,
                "text": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "similarity": round(similarity, 3),
            })

        return formatted
