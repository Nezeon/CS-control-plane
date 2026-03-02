import chromadb

from app.config import settings

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
