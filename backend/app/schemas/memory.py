from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EpisodicMemoryEntry(BaseModel):
    id: str
    content: str
    customer_name: str | None = None
    event_type: str | None = None
    execution_id: str | None = None
    importance: int = 5
    timestamp: datetime | None = None


class EpisodicMemoryResponse(BaseModel):
    agent_id: str
    agent_name: str
    memories: list[EpisodicMemoryEntry]
    total: int
    limit: int
    offset: int


class WorkingMemoryEntry(BaseModel):
    key: str
    value: Any = None


class WorkingMemoryResponse(BaseModel):
    agent_id: str
    agent_name: str
    is_active: bool = False
    execution_id: str | None = None
    entries: list[WorkingMemoryEntry] = []


class KnowledgeEntry(BaseModel):
    id: str
    content: str
    agent_id: str | None = None
    agent_name: str | None = None
    tags: list[str] = []
    importance: int = 5
    knowledge_type: str | None = None
    customer_name: str | None = None
    timestamp: datetime | None = None


class KnowledgePoolResponse(BaseModel):
    lane: str
    entries: list[KnowledgeEntry]
    total: int
    limit: int
    offset: int


class MemorySearchResult(BaseModel):
    type: str
    id: str
    content: str
    agent_name: str | None = None
    lane: str | None = None
    importance: int = 5
    relevance_score: float = 0.0
    combined_score: float = 0.0
    timestamp: datetime | None = None


class MemorySearchResponse(BaseModel):
    query: str
    results: list[MemorySearchResult]
