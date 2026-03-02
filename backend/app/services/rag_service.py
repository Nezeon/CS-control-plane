import logging

from app.chromadb_client import (
    call_insight_embeddings,
    problem_embeddings,
    ticket_embeddings,
)

logger = logging.getLogger("services.rag")


class RAGService:
    def __init__(self):
        self.ticket_collection = ticket_embeddings
        self.insight_collection = call_insight_embeddings
        self.problem_collection = problem_embeddings

    def embed_ticket(self, ticket_id: str, text: str, metadata: dict) -> None:
        """Embed a ticket's text into ticket_embeddings collection."""
        # Ensure metadata values are primitive types for ChromaDB
        clean_meta = {k: str(v) if v is not None else "" for k, v in metadata.items()}
        self.ticket_collection.upsert(
            ids=[ticket_id],
            documents=[text],
            metadatas=[clean_meta],
        )

    def embed_insight(self, insight_id: str, text: str, metadata: dict) -> None:
        """Embed a call insight's summary into call_insight_embeddings."""
        clean_meta = {k: str(v) if v is not None else "" for k, v in metadata.items()}
        self.insight_collection.upsert(
            ids=[insight_id],
            documents=[text],
            metadatas=[clean_meta],
        )

    def embed_problem(self, problem_id: str, text: str, metadata: dict) -> None:
        """Embed a known problem/resolution into problem_embeddings."""
        clean_meta = {k: str(v) if v is not None else "" for k, v in metadata.items()}
        self.problem_collection.upsert(
            ids=[problem_id],
            documents=[text],
            metadatas=[clean_meta],
        )

    def find_similar_tickets(
        self, query_text: str, n_results: int = 5, where: dict = None
    ) -> list[dict]:
        """Find similar tickets by text similarity."""
        try:
            kwargs = {"query_texts": [query_text], "n_results": n_results}
            if where:
                kwargs["where"] = where
            results = self.ticket_collection.query(**kwargs)
            return self._format_results(results)
        except Exception as e:
            logger.warning(f"ChromaDB ticket query failed: {e}")
            return []

    def find_similar_insights(
        self, query_text: str, n_results: int = 5, where: dict = None
    ) -> list[dict]:
        """Find similar call insights."""
        try:
            kwargs = {"query_texts": [query_text], "n_results": n_results}
            if where:
                kwargs["where"] = where
            results = self.insight_collection.query(**kwargs)
            return self._format_results(results)
        except Exception as e:
            logger.warning(f"ChromaDB insight query failed: {e}")
            return []

    def find_similar_problems(
        self, query_text: str, n_results: int = 5
    ) -> list[dict]:
        """Find similar known problems/resolutions."""
        try:
            results = self.problem_collection.query(
                query_texts=[query_text], n_results=n_results
            )
            return self._format_results(results)
        except Exception as e:
            logger.warning(f"ChromaDB problem query failed: {e}")
            return []

    def _format_results(self, results: dict) -> list[dict]:
        """Convert ChromaDB query results to list of dicts."""
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
