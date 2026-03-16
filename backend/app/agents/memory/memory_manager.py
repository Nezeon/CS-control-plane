"""
Memory Manager — Facade coordinating the 3-tier memory system.

Tier 1: Working Memory  — In-memory scratchpad for the current pipeline run
Tier 2: Episodic Memory — Per-agent execution diary (ChromaDB)
Tier 3: Semantic Memory — Lane-scoped shared knowledge pool (ChromaDB)

Usage:
    from app.agents.memory import MemoryManager
    mm = MemoryManager("triage_agent")
    mm.set_context("ticket_id", "T-123")
    mm.remember_execution("Triaged ticket T-123 as P2 bug", importance=7)
    context = mm.assemble_context("customer reporting login failures")
"""

import logging
from typing import Any

from app.agents.memory.episodic_memory import EpisodicMemory
from app.agents.memory.semantic_memory import SemanticMemory
from app.agents.memory.working_memory import WorkingMemory
from app.agents.profile_loader import ProfileLoader

logger = logging.getLogger("memory.manager")


class MemoryManager:

    def __init__(self, agent_id: str, lane: str | None = None):
        self.agent_id = agent_id

        # Resolve agent metadata from YAML profiles
        loader = ProfileLoader.get()
        profile = loader.get_agent_profile(agent_id) or {}

        self.agent_name: str = profile.get("name", agent_id)
        self.tier: int = profile.get("tier", 3)
        self.lane: str = lane or profile.get("lane") or "global"

        # Initialize all 3 tiers
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory(
            agent_id=agent_id,
            agent_name=self.agent_name,
            tier=self.tier,
            lane=self.lane,
        )
        self.semantic = SemanticMemory(
            lane=self.lane,
            agent_id=agent_id,
            agent_name=self.agent_name,
        )

        logger.debug(
            f"MemoryManager initialized: {agent_id} "
            f"(name={self.agent_name}, tier={self.tier}, lane={self.lane})"
        )

    # ── Tier 1: Working Memory ────────────────────────────────────

    def set_context(self, key: str, value: Any) -> None:
        """Store a key-value pair in working memory."""
        self.working.set_context(key, value)

    def get_context(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from working memory."""
        return self.working.get_context(key, default)

    def get_working_snapshot(self) -> dict[str, Any]:
        """Get a snapshot of the current working memory."""
        return self.working.get_all()

    def clear_working(self) -> None:
        """Clear working memory. Called by pipeline engine after run completes."""
        self.working.clear()

    # ── Tier 2: Episodic Memory ───────────────────────────────────

    def remember_execution(
        self,
        summary: str,
        importance: int = 5,
        customer_id: str = "",
        customer_name: str = "",
        event_type: str = "",
        execution_id: str = "",
    ) -> str | None:
        """Store a new episodic memory entry. Returns entry ID or None."""
        return self.episodic.remember(
            summary=summary,
            importance=importance,
            customer_id=customer_id,
            customer_name=customer_name,
            event_type=event_type,
            execution_id=execution_id,
        )

    def recall_similar(self, query: str, n: int = 5) -> list[dict]:
        """Find similar past experiences using tri-factor scoring."""
        return self.episodic.recall_similar(query, n)

    def get_recent_memories(self, n: int = 5) -> list[dict]:
        """Get the most recent episodic memories."""
        return self.episodic.get_recent(n)

    # ── Tier 3: Semantic Memory ───────────────────────────────────

    def publish_knowledge(
        self,
        content: str,
        tags: list[str] | None = None,
        importance: int = 5,
        knowledge_type: str = "general",
        customer_id: str = "",
        customer_name: str = "",
    ) -> str | None:
        """Publish a knowledge entry to the lane's shared pool."""
        return self.semantic.publish(
            content=content,
            tags=tags,
            importance=importance,
            knowledge_type=knowledge_type,
            customer_id=customer_id,
            customer_name=customer_name,
        )

    def query_knowledge(
        self,
        query: str,
        n: int = 5,
        customer_id: str | None = None,
    ) -> list[dict]:
        """Query knowledge within the agent's own lane."""
        return self.semantic.query(query, n, customer_id)

    def query_cross_lane(
        self,
        query: str,
        n: int = 3,
        lanes: list[str] | None = None,
    ) -> list[dict]:
        """Query knowledge from other lanes."""
        return self.semantic.query_cross_lane(query, n, lanes)

    def query_global_knowledge(self, query: str, n: int = 5) -> list[dict]:
        """Query knowledge across all lanes."""
        return self.semantic.query_global(query, n)

    # ── Convenience ───────────────────────────────────────────────

    def assemble_context(
        self,
        task_description: str,
        n_episodic: int = 3,
        n_semantic: int = 3,
    ) -> dict:
        """
        Assemble a full context dict from all 3 memory tiers.

        Returns:
            {
                "working": {key: value, ...},
                "episodic": [{id, text, combined_score, ...}, ...],
                "semantic": [{id, text, similarity, ...}, ...],
                "global_knowledge": [{id, text, similarity, ...}, ...],
            }
        """
        return {
            "working": self.working.get_all(),
            "episodic": self.episodic.recall_similar(task_description, n_episodic),
            "semantic": self.semantic.query(task_description, n_semantic),
            "global_knowledge": self.semantic.query_global(task_description, n_semantic),
        }

    def get_stats(self) -> dict:
        """Get stats about memory usage for this agent."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "tier": self.tier,
            "lane": self.lane,
            "working_memory_active": self.working.is_active,
            "working_memory_keys": list(self.working.get_all().keys()),
            "episodic_entry_count": self.episodic.get_entry_count(),
        }
