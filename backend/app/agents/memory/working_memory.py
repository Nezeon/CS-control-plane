"""
Tier 1: Working Memory — In-memory scratchpad for the current pipeline run.

Stores current task context, intermediate results, and tool outputs.
Cleared after each pipeline run completes.
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("memory.working")


class WorkingMemory:

    def __init__(self):
        self._store: dict[str, Any] = {}
        self._execution_id: str | None = None
        self._created_at: datetime | None = None

    def set_context(self, key: str, value: Any) -> None:
        """Store a key-value pair in working memory."""
        self._store[key] = value
        if self._created_at is None:
            self._created_at = datetime.now(timezone.utc)

    def get_context(self, key: str, default: Any = None) -> Any:
        """Retrieve a value by key, with optional default."""
        return self._store.get(key, default)

    def get_all(self) -> dict[str, Any]:
        """Return a shallow copy of the entire working memory."""
        return dict(self._store)

    def has(self, key: str) -> bool:
        """Check if a key exists."""
        return key in self._store

    def set_execution_id(self, execution_id: str) -> None:
        """Associate working memory with a specific pipeline execution."""
        self._execution_id = execution_id

    @property
    def execution_id(self) -> str | None:
        return self._execution_id

    @property
    def is_active(self) -> bool:
        """True if working memory has content."""
        return bool(self._store)

    def clear(self) -> None:
        """Wipe all working memory. Called after each pipeline run."""
        entry_count = len(self._store)
        self._store.clear()
        self._execution_id = None
        self._created_at = None
        if entry_count > 0:
            logger.debug(f"Working memory cleared ({entry_count} entries)")
