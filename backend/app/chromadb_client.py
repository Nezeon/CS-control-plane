import logging

import chromadb

from app.config import settings

logger = logging.getLogger("chromadb_client")

try:
    if settings.CHROMADB_MODE == "ephemeral":
        logger.info("ChromaDB: using EphemeralClient (in-memory)")
        client = chromadb.EphemeralClient()
    else:
        logger.info(f"ChromaDB: using PersistentClient at {settings.CHROMADB_PATH}")
        client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)

    # Collections for RAG
    ticket_embeddings = client.get_or_create_collection(
        name="ticket_embeddings",
        metadata={"description": "Ticket summary + description + resolution for similarity search"},
    )

    call_insight_embeddings = client.get_or_create_collection(
        name="call_insight_embeddings",
        metadata={"description": "Call summary + topics + risks + decisions for pattern matching"},
    )

    problem_embeddings = client.get_or_create_collection(
        name="problem_embeddings",
        metadata={"description": "Cross-customer problem + root cause + resolution matching"},
    )

    # Meeting Knowledge Base (for Fathom Agent RAG retrieval)
    meeting_knowledge = client.get_or_create_collection(
        name="meeting_knowledge",
        metadata={"description": "155+ real customer meeting chunks for agentic RAG retrieval (5 categories, 4 section types)"},
    )

    # Collections for Agent Memory System
    episodic_memory = client.get_or_create_collection(
        name="episodic_memory",
        metadata={"description": "Per-agent execution diary for experience recall"},
    )

    shared_knowledge = client.get_or_create_collection(
        name="shared_knowledge",
        metadata={"description": "Lane-scoped knowledge pool for collective intelligence"},
    )
except Exception as e:
    logger.error(f"ChromaDB initialization failed: {e}")
    client = None
    ticket_embeddings = None
    call_insight_embeddings = None
    problem_embeddings = None
    meeting_knowledge = None
    episodic_memory = None
    shared_knowledge = None
