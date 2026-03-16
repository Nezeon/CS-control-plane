"""
Meeting Knowledge Service — ChromaDB-based retrieval over customer meeting records.

Provides 5 retrieval strategies for the Fathom Agent's agentic RAG pipeline:
  1. semantic_search — broad similarity search
  2. filter_by_category — category-constrained search
  3. search_by_section_type — section-type filtered search
  4. filter_by_customer — customer-name search
  5. get_meeting_details — full meeting retrieval

Also provides ingestion: ingest_call_insight() chunks a processed CallInsight
into 4 section-type documents and upserts them into ChromaDB.
"""

import json
import logging
import re
import threading

from app.config import settings

logger = logging.getLogger("services.meeting_knowledge")

# Category and section constants (from external repo data schema)
CATEGORIES = [
    "Problem Resolution",
    "Deployment and Integration",
    "Product Demonstration",
    "Strategic Planning and Review",
    "Enablement and Training",
]

SECTION_TYPES = ["purpose", "key_takeaways", "topics", "next_steps"]

# Keyword map for auto-categorising ingested meetings (checked in order).
_CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Product Demonstration", ["demo", "demonstration", "walkthrough", "showcase", "pov"]),
    ("Problem Resolution", ["issue", "bug", "problem", "outage", "troubleshoot", "incident", "error", "fix", "hotfix"]),
    ("Deployment and Integration", ["deploy", "integration", "setup", "onboard", "install", "migration", "upgrade", "rollout"]),
    ("Strategic Planning and Review", ["qbr", "review", "strategic", "renewal", "planning", "roadmap", "executive", "business review"]),
    # Fallback handled in _infer_category
]


class MeetingKnowledgeService:
    """Singleton service for meeting knowledge retrieval via ChromaDB."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._collection = None

    @property
    def collection(self):
        """Lazy-load the ChromaDB collection."""
        if self._collection is None:
            from app.chromadb_client import meeting_knowledge
            self._collection = meeting_knowledge
        return self._collection

    # ------------------------------------------------------------------
    # 1. Semantic Search
    # ------------------------------------------------------------------

    def semantic_search(
        self,
        query: str,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[dict]:
        """
        Broad semantic similarity search across all meeting chunks.

        Returns list of {chunk_id, text, meeting_id, category, section_type, score}.
        """
        top_k = top_k or settings.FATHOM_TOP_K
        threshold = similarity_threshold or settings.FATHOM_SIMILARITY_THRESHOLD

        if not self.collection:
            logger.warning("meeting_knowledge collection not available")
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

        return self._format_results(results, threshold)

    # ------------------------------------------------------------------
    # 2. Filter by Category
    # ------------------------------------------------------------------

    def filter_by_category(
        self,
        category: str,
        query: str,
        top_k: int | None = None,
    ) -> list[dict]:
        """
        Search within a specific meeting category.

        Categories: Problem Resolution, Deployment and Integration,
        Product Demonstration, Strategic Planning and Review,
        Enablement and Training.
        """
        top_k = top_k or settings.FATHOM_TOP_K

        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"category": category},
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Category filter search failed: {e}")
            return []

        return self._format_results(results)

    # ------------------------------------------------------------------
    # 3. Search by Section Type
    # ------------------------------------------------------------------

    def search_by_section_type(
        self,
        section_type: str,
        query: str,
        top_k: int | None = None,
    ) -> list[dict]:
        """
        Search within a specific section type.

        Section types: purpose, key_takeaways, topics, next_steps.
        """
        top_k = top_k or settings.FATHOM_TOP_K

        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"section_type": section_type},
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Section type search failed: {e}")
            return []

        return self._format_results(results)

    # ------------------------------------------------------------------
    # 4. Filter by Customer
    # ------------------------------------------------------------------

    def filter_by_customer(
        self,
        customer_name: str,
        top_k: int | None = None,
    ) -> list[dict]:
        """
        Find meeting chunks related to a specific customer.

        Uses semantic search with customer name as query, then post-filters
        to keep only chunks that actually mention the customer (case-insensitive)
        in either the document text or meeting title.
        """
        top_k = top_k or settings.FATHOM_TOP_K

        if not self.collection:
            return []

        # Fetch more than needed, then post-filter for actual customer mentions
        fetch_k = top_k * 4
        try:
            results = self.collection.query(
                query_texts=[customer_name],
                n_results=fetch_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Customer filter search failed: {e}")
            return []

        formatted = self._format_results(results, threshold=0.2)

        # Post-filter: use the most distinguishing word from the customer name.
        # The first word is usually the unique company name ("ujjivan", "gulf", "eskan"),
        # while trailing words like "bank", "corp", "insurance" are generic.
        # This handles content saying "Ujjivan's" when user asked about "Ujjivan Bank".
        _GENERIC_SUFFIXES = {"bank", "corp", "inc", "ltd", "llc", "insurance", "group", "finance"}
        name_words = customer_name.lower().split()
        key_words = [w for w in name_words if w not in _GENERIC_SUFFIXES and len(w) >= 3]
        if not key_words:
            key_words = name_words[:1]  # fallback to first word

        matched = []
        for c in formatted:
            searchable = (c["text"] + " " + c["meeting_title"]).lower()
            if all(w in searchable for w in key_words):
                matched.append(c)
        return matched[:top_k]

    # ------------------------------------------------------------------
    # 5. Get Meeting Details
    # ------------------------------------------------------------------

    def get_meeting_details(self, meeting_id: str) -> list[dict]:
        """
        Retrieve all chunks for a specific meeting by meeting_id.
        """
        if not self.collection:
            return []

        try:
            results = self.collection.get(
                where={"meeting_id": meeting_id},
                include=["documents", "metadatas"],
            )
        except Exception as e:
            logger.error(f"Meeting details retrieval failed: {e}")
            return []

        if not results or not results.get("ids"):
            return []

        chunks = []
        for i, doc_id in enumerate(results["ids"]):
            meta = results["metadatas"][i] if results.get("metadatas") else {}
            chunks.append({
                "chunk_id": doc_id,
                "text": results["documents"][i] if results.get("documents") else "",
                "meeting_id": meta.get("meeting_id", meeting_id),
                "meeting_title": meta.get("meeting_title", ""),
                "category": meta.get("category", ""),
                "section_type": meta.get("section_type", ""),
            })

        return chunks

    # ------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------

    def get_all_categories(self) -> list[str]:
        """Return all available meeting categories."""
        return sorted(CATEGORIES)

    def get_all_customers(self) -> list[str]:
        """Extract unique customer names from meeting titles."""
        if not self.collection:
            return []

        try:
            all_data = self.collection.get(include=["metadatas"])
            titles = set()
            for meta in (all_data.get("metadatas") or []):
                title = meta.get("meeting_title", "")
                if title:
                    # Extract customer from "Meeting with <Customer> on <Topic>"
                    parts = title.split(" - ")
                    if len(parts) >= 2:
                        titles.add(parts[0].strip())
                    else:
                        titles.add(title)
            return sorted(titles)
        except Exception as e:
            logger.error(f"Failed to get customer list: {e}")
            return []

    def get_collection_stats(self) -> dict:
        """Return collection statistics."""
        if not self.collection:
            return {"count": 0, "status": "unavailable"}

        try:
            count = self.collection.count()
            return {"count": count, "status": "ready"}
        except Exception as e:
            return {"count": 0, "status": f"error: {e}"}

    # ------------------------------------------------------------------
    # 6. Ingest a processed CallInsight into the knowledge base
    # ------------------------------------------------------------------

    def ingest_call_insight(self, insight_data: dict) -> int:
        """
        Chunk a processed CallInsight into 4 section-type documents and
        upsert them into the meeting_knowledge ChromaDB collection.

        Args:
            insight_data: dict with keys:
                recording_id, title, participants, duration_minutes,
                summary, key_topics, action_items, decisions, risks,
                customer_name (optional)

        Returns:
            Number of chunks upserted (normally 4).
        """
        if not self.collection:
            logger.warning("meeting_knowledge collection unavailable — skipping ingest")
            return 0

        rid = str(insight_data.get("recording_id", "unknown"))
        title = insight_data.get("title", "Untitled")
        participants = insight_data.get("participants", [])
        duration = insight_data.get("duration_minutes")
        summary = insight_data.get("summary", "")
        topics = insight_data.get("key_topics", [])
        actions = insight_data.get("action_items", [])
        decisions = insight_data.get("decisions", [])
        risks = insight_data.get("risks", [])
        customer_name = insight_data.get("customer_name", "")

        # Build meeting_title in the same format as seed data
        meeting_title = title
        if customer_name and customer_name.lower() not in title.lower():
            meeting_title = f"{customer_name} || {title}"

        category = self._infer_category(title, topics)

        # Build 4 section chunks
        purpose_text = f"Meeting: {title}\n"
        if participants:
            purpose_text += f"Participants: {', '.join(participants)}\n"
        if duration:
            purpose_text += f"Duration: {duration} minutes\n"

        takeaways_parts = []
        if summary:
            takeaways_parts.append(summary)
        if decisions:
            takeaways_parts.append("Decisions:\n" + "\n".join(f"- {d}" for d in decisions))
        takeaways_text = "\n\n".join(takeaways_parts) or "No key takeaways recorded."

        topics_parts = []
        if topics:
            topics_parts.append("Topics discussed:\n" + "\n".join(f"- {t}" for t in topics))
        if risks:
            topics_parts.append("Risks identified:\n" + "\n".join(f"- {r}" for r in risks))
        topics_text = "\n\n".join(topics_parts) or "No topics recorded."

        actions_lines = []
        for a in actions:
            if isinstance(a, dict):
                line = f"- {a.get('task', a.get('title', str(a)))}"
                if a.get("owner"):
                    line += f" (Owner: {a['owner']})"
                if a.get("deadline"):
                    line += f" [Due: {a['deadline']}]"
                actions_lines.append(line)
            else:
                actions_lines.append(f"- {a}")
        next_steps_text = "Action items:\n" + "\n".join(actions_lines) if actions_lines else "No action items recorded."

        chunks = [
            (f"{rid}_purpose_1", "purpose", purpose_text),
            (f"{rid}_key_takeaways_2", "key_takeaways", takeaways_text),
            (f"{rid}_topics_3", "topics", topics_text),
            (f"{rid}_next_steps_4", "next_steps", next_steps_text),
        ]

        ids = []
        documents = []
        metadatas = []
        for chunk_id, section_type, content in chunks:
            if not content.strip():
                continue
            ids.append(chunk_id)
            documents.append(content)
            metadatas.append({
                "meeting_id": rid,
                "meeting_title": meeting_title,
                "category": category,
                "section_type": section_type,
            })

        if not ids:
            return 0

        try:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(f"Ingested {len(ids)} chunks for recording {rid} into meeting_knowledge")
            return len(ids)
        except Exception as e:
            logger.error(f"Failed to ingest recording {rid}: {e}")
            return 0

    def backfill_from_db(self) -> dict:
        """
        One-time backfill: read all CallInsight records from PostgreSQL
        and ingest any that are missing from the meeting_knowledge collection.

        Returns:
            {"total": int, "ingested": int, "skipped": int}
        """
        from app.database import get_sync_session
        from app.models.call_insight import CallInsight

        db = get_sync_session()
        try:
            insights = db.query(CallInsight).order_by(CallInsight.processed_at.desc()).all()
            stats = {"total": len(insights), "ingested": 0, "skipped": 0}

            for insight in insights:
                rid = insight.fathom_recording_id or str(insight.id)

                # Check if already in collection
                existing = self.get_meeting_details(rid)
                if existing:
                    stats["skipped"] += 1
                    continue

                # Resolve customer name
                customer_name = ""
                if insight.customer and hasattr(insight.customer, "name"):
                    customer_name = insight.customer.name

                data = {
                    "recording_id": rid,
                    "title": insight.summary[:100] if insight.summary else "Call",
                    "participants": insight.participants or [],
                    "duration_minutes": None,
                    "summary": insight.summary or "",
                    "key_topics": insight.key_topics or [],
                    "action_items": insight.action_items or [],
                    "decisions": insight.decisions or [],
                    "risks": insight.risks or [],
                    "customer_name": customer_name,
                }
                count = self.ingest_call_insight(data)
                if count > 0:
                    stats["ingested"] += 1
                else:
                    stats["skipped"] += 1

            logger.info(f"Backfill complete: {stats}")
            return stats
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Category inference
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_category(title: str, topics: list | None = None) -> str:
        """Infer meeting category from title and topics using keyword matching."""
        search_text = (title + " " + " ".join(topics or [])).lower()
        for category, keywords in _CATEGORY_KEYWORDS:
            for kw in keywords:
                if kw in search_text:
                    return category
        return "Enablement and Training"  # default fallback

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _format_results(
        self,
        results: dict,
        threshold: float | None = None,
    ) -> list[dict]:
        """Convert ChromaDB query results to a flat list of dicts."""
        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        threshold = threshold or settings.FATHOM_SIMILARITY_THRESHOLD
        chunks = []

        ids = results["ids"][0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            # ChromaDB returns L2 distance; lower = more similar
            # Convert to similarity score (1 / (1 + distance))
            distance = distances[i] if i < len(distances) else 0
            similarity = 1.0 / (1.0 + distance)

            if similarity < threshold:
                continue

            meta = metadatas[i] if i < len(metadatas) else {}
            chunks.append({
                "chunk_id": doc_id,
                "text": documents[i] if i < len(documents) else "",
                "meeting_id": meta.get("meeting_id", ""),
                "meeting_title": meta.get("meeting_title", ""),
                "category": meta.get("category", ""),
                "section_type": meta.get("section_type", ""),
                "similarity": round(similarity, 4),
            })

        return chunks


# Singleton instance
meeting_knowledge_service = MeetingKnowledgeService()
