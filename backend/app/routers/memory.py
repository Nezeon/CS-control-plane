"""
Memory Router — API endpoints for browsing agent memory.

Prefix: /api/v2/memory

Exposes episodic memory (per-agent diary), working memory (active scratchpad),
semantic knowledge pools (lane-scoped), and cross-memory search.

Memory classes are sync (ChromaDB); wrapped with asyncio.to_thread() for FastAPI.
"""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.memory.episodic_memory import EpisodicMemory
from app.agents.memory.semantic_memory import SemanticMemory, VALID_LANES
from app.agents.profile_loader import ProfileLoader
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.memory import (
    EpisodicMemoryEntry,
    EpisodicMemoryResponse,
    KnowledgeEntry,
    KnowledgePoolResponse,
    MemorySearchResponse,
    MemorySearchResult,
    WorkingMemoryResponse,
)

logger = logging.getLogger("routers.memory")

router = APIRouter(prefix="/api/v2/memory", tags=["memory"])


def _get_agent_profile(agent_id: str) -> dict:
    """Get agent profile from YAML, raise 404 if not found."""
    loader = ProfileLoader.get()
    profile = loader.get_agent_profile(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return profile


# ── Episodic Memory ──────────────────────────────────────────────


@router.get("/{agent_id}/episodic", response_model=EpisodicMemoryResponse)
async def get_episodic_memory(
    agent_id: str,
    customer_id: str | None = Query(default=None, description="Filter by customer"),
    importance_min: int | None = Query(default=None, ge=1, le=10, description="Minimum importance"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """Get episodic memories (past execution diary) for an agent."""
    if agent_id == "all":
        # Fetch memories from ALL agents
        loader = ProfileLoader.get()
        all_agent_ids = loader.get_agent_ids()
        all_entries: list[dict] = []
        fetch_per_agent = max(5, min((limit + offset) * 2 // max(len(all_agent_ids), 1), 20))
        for aid in all_agent_ids:
            p = loader.get_agent_profile(aid) or {}
            ep = EpisodicMemory(
                agent_id=aid,
                agent_name=p.get("name", aid),
                tier=p.get("tier", 3),
                lane=p.get("lane", ""),
            )
            entries_for_agent = await asyncio.to_thread(ep.get_recent, fetch_per_agent)
            all_entries.extend(entries_for_agent)
        # Sort all entries by timestamp descending
        all_entries.sort(
            key=lambda e: e.get("metadata", {}).get("timestamp", ""),
            reverse=True,
        )
        entries = all_entries
        agent_name = "All Agents"
    else:
        profile = _get_agent_profile(agent_id)
        agent_name = profile.get("name", agent_id)

        episodic = EpisodicMemory(
            agent_id=agent_id,
            agent_name=agent_name,
            tier=profile.get("tier", 3),
            lane=profile.get("lane", ""),
        )

        # Fetch more than needed for post-filtering
        fetch_n = min((limit + offset) * 2, 50)
        entries = await asyncio.to_thread(episodic.get_recent, fetch_n)

    # Post-filter
    filtered = []
    for entry in entries:
        meta = entry.get("metadata", {})

        if customer_id and meta.get("customer_id") != customer_id:
            continue

        if importance_min:
            try:
                imp = int(meta.get("importance", "5"))
            except (ValueError, TypeError):
                imp = 5
            if imp < importance_min:
                continue

        filtered.append(entry)

    total = len(filtered)
    page = filtered[offset : offset + limit]

    memories = [
        EpisodicMemoryEntry(
            id=e["id"],
            content=e.get("text", ""),
            customer_name=e.get("metadata", {}).get("customer_name") or None,
            event_type=e.get("metadata", {}).get("event_type") or None,
            execution_id=e.get("metadata", {}).get("execution_id") or None,
            importance=int(e.get("metadata", {}).get("importance", "5")),
            timestamp=_parse_ts(e.get("metadata", {}).get("timestamp")),
        )
        for e in page
    ]

    return EpisodicMemoryResponse(
        agent_id=agent_id,
        agent_name=agent_name,
        memories=memories,
        total=total,
        limit=limit,
        offset=offset,
    )


# ── Working Memory ───────────────────────────────────────────────


@router.get("/{agent_id}/working", response_model=WorkingMemoryResponse)
async def get_working_memory(
    agent_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get working memory (active scratchpad) for an agent.

    Working memory is process-local and ephemeral — cleared after each pipeline run.
    Returns empty when no pipeline is actively running in this process.
    """
    profile = _get_agent_profile(agent_id)

    return WorkingMemoryResponse(
        agent_id=agent_id,
        agent_name=profile.get("name", agent_id),
        is_active=False,
        execution_id=None,
        entries=[],
    )


# ── Knowledge Pool (Semantic Memory) ─────────────────────────────


@router.get("/knowledge/{lane}", response_model=KnowledgePoolResponse)
async def get_knowledge_pool(
    lane: str,
    tags: str | None = Query(default=None, description="Comma-separated tag filter"),
    importance_min: int | None = Query(default=None, ge=1, le=10),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """Get knowledge entries from a lane's shared pool."""
    if lane == "all":
        # Fetch knowledge from ALL lanes
        combined_raw: dict = {"ids": [], "documents": [], "metadatas": []}
        for valid_lane in sorted(VALID_LANES):
            sem = SemanticMemory(lane=valid_lane)

            def _fetch_lane(s=sem, ln=valid_lane):
                if not s._collection:
                    return {"ids": [], "documents": [], "metadatas": []}
                try:
                    return s._collection.get(where={"lane": ln})
                except Exception:
                    return {"ids": [], "documents": [], "metadatas": []}

            lane_raw = await asyncio.to_thread(_fetch_lane)
            combined_raw["ids"].extend(lane_raw.get("ids", []))
            combined_raw["documents"].extend(lane_raw.get("documents", []))
            combined_raw["metadatas"].extend(lane_raw.get("metadatas", []))
        raw = combined_raw
    elif lane not in VALID_LANES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid lane '{lane}'. Must be one of: all, {', '.join(sorted(VALID_LANES))}",
        )
    else:
        semantic = SemanticMemory(lane=lane)

        def _fetch():
            if not semantic._collection:
                return {"ids": [], "documents": [], "metadatas": []}
            try:
                return semantic._collection.get(where={"lane": lane})
            except Exception:
                return {"ids": [], "documents": [], "metadatas": []}

        raw = await asyncio.to_thread(_fetch)

    ids = raw.get("ids", [])
    docs = raw.get("documents", [])
    metas = raw.get("metadatas", [])

    # Parse tag filter
    filter_tags = set()
    if tags:
        filter_tags = {t.strip().lower() for t in tags.split(",") if t.strip()}

    # Build + filter entries
    entries = []
    for i, doc_id in enumerate(ids):
        meta = metas[i] if i < len(metas) else {}
        content = docs[i] if i < len(docs) else ""

        # Tag filter
        raw_tags = meta.get("tags", "")
        entry_tags = [t.strip() for t in raw_tags.split(",") if t.strip()] if raw_tags else []
        if filter_tags and not filter_tags.intersection({t.lower() for t in entry_tags}):
            continue

        # Importance filter
        try:
            imp = int(meta.get("importance", "5"))
        except (ValueError, TypeError):
            imp = 5
        if importance_min and imp < importance_min:
            continue

        entries.append({
            "id": doc_id,
            "content": content,
            "agent_id": meta.get("agent_id") or None,
            "agent_name": meta.get("agent_name") or None,
            "tags": entry_tags,
            "importance": imp,
            "knowledge_type": meta.get("knowledge_type") or None,
            "customer_name": meta.get("customer_name") or None,
            "timestamp": _parse_ts(meta.get("timestamp")),
        })

    # Sort by timestamp descending
    entries.sort(key=lambda e: e["timestamp"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    total = len(entries)
    page = entries[offset : offset + limit]

    return KnowledgePoolResponse(
        lane=lane,
        entries=[KnowledgeEntry(**e) for e in page],
        total=total,
        limit=limit,
        offset=offset,
    )


# ── Memory Search ────────────────────────────────────────────────


@router.get("/search", response_model=MemorySearchResponse)
async def search_memory(
    q: str = Query(..., min_length=1, description="Search query"),
    memory_type: str = Query(default="all", description="all, episodic, or knowledge"),
    agent_id: str | None = Query(default=None, description="Filter episodic by agent"),
    lane: str | None = Query(default=None, description="Filter knowledge by lane"),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """Search across episodic and/or semantic memory."""
    results: list[dict] = []

    # Search episodic memory
    if memory_type in ("all", "episodic"):
        target_agent = agent_id or "cso_orchestrator"
        loader = ProfileLoader.get()
        profile = loader.get_agent_profile(target_agent) or {}
        episodic = EpisodicMemory(
            agent_id=target_agent,
            agent_name=profile.get("name", target_agent),
            tier=profile.get("tier", 3),
            lane=profile.get("lane", ""),
        )

        ep_results = await asyncio.to_thread(episodic.recall_similar, q, limit)
        for e in ep_results:
            meta = e.get("metadata", {})
            results.append({
                "type": "episodic",
                "id": e["id"],
                "content": e.get("text", ""),
                "agent_name": meta.get("agent_name") or None,
                "lane": meta.get("lane") or None,
                "importance": int(meta.get("importance", "5")),
                "relevance_score": e.get("relevance", 0.0),
                "combined_score": e.get("combined_score", 0.0),
                "timestamp": _parse_ts(meta.get("timestamp")),
            })

    # Search semantic knowledge
    if memory_type in ("all", "knowledge"):
        target_lane = lane or "global"
        semantic = SemanticMemory(lane=target_lane)

        if lane:
            sk_results = await asyncio.to_thread(semantic.query, q, limit)
        else:
            sk_results = await asyncio.to_thread(semantic.query_global, q, limit)

        for e in sk_results:
            meta = e.get("metadata", {})
            sim = e.get("similarity", 0.0)
            try:
                imp = int(meta.get("importance", "5"))
            except (ValueError, TypeError):
                imp = 5
            results.append({
                "type": "knowledge",
                "id": e["id"],
                "content": e.get("text", ""),
                "agent_name": meta.get("agent_name") or None,
                "lane": meta.get("lane") or None,
                "importance": imp,
                "relevance_score": sim,
                "combined_score": sim * 0.6 + (imp / 10.0) * 0.4,
                "timestamp": _parse_ts(meta.get("timestamp")),
            })

    # Sort by combined_score and limit
    results.sort(key=lambda r: r["combined_score"], reverse=True)
    results = results[:limit]

    return MemorySearchResponse(
        query=q,
        results=[MemorySearchResult(**r) for r in results],
    )


# ── Helpers ──────────────────────────────────────────────────────


def _parse_ts(ts_str: str | None) -> datetime | None:
    """Parse ISO timestamp string to datetime, returning None on failure."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None
