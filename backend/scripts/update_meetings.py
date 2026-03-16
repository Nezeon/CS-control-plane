"""
Append new meeting chunks to the ChromaDB meeting_knowledge collection.

Reads a JSON file of new chunks (same format as chunks_for_lookup.json),
deduplicates against existing data, and upserts into ChromaDB + JSON files.

Usage:
    python -m scripts.update_meetings path/to/latest_meetings_chunks.json

The input file should contain a JSON array of objects with:
    chunk_id, meeting_id, meeting_title, category, section_type, content
"""

import json
import sys
from pathlib import Path

# Resolve paths relative to backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data" / "meeting_knowledge"
CHUNKS_PATH = DATA_DIR / "chunks_for_lookup.json"
METADATA_PATH = DATA_DIR / "vector_metadata.json"
CHROMADB_PATH = BACKEND_DIR.parent / "chromadb_data"


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.update_meetings <new_chunks.json>")
        sys.exit(1)

    new_path = Path(sys.argv[1])
    if not new_path.exists():
        print(f"File not found: {new_path}")
        sys.exit(1)

    # Load new chunks
    with open(new_path, "r", encoding="utf-8") as f:
        new_chunks = json.load(f)
    print(f"New chunks to add: {len(new_chunks)}")

    # Load existing chunks for dedup
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        existing_chunks = json.load(f)
    existing_ids = {c["chunk_id"] for c in existing_chunks}

    # Filter duplicates
    unique_chunks = [c for c in new_chunks if c["chunk_id"] not in existing_ids]
    dupes = len(new_chunks) - len(unique_chunks)
    if dupes:
        print(f"Skipping {dupes} duplicate chunks")
    if not unique_chunks:
        print("Nothing new to add.")
        return

    # Connect to ChromaDB
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMADB_PATH))
    collection = client.get_or_create_collection("meeting_knowledge")
    before = collection.count()

    # Prepare and upsert into ChromaDB
    ids = []
    documents = []
    metadatas = []
    for c in unique_chunks:
        content = c.get("content", "")
        if not content.strip():
            continue
        ids.append(str(c["chunk_id"]))
        documents.append(content)
        metadatas.append({
            "meeting_id": str(c.get("meeting_id", "")),
            "meeting_title": c.get("meeting_title", ""),
            "category": c.get("category", ""),
            "section_type": c.get("section_type", ""),
        })

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.upsert(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )

    after = collection.count()
    print(f"ChromaDB: {before} -> {after} chunks (+{after - before})")

    # Update JSON files to stay in sync
    updated_chunks = existing_chunks + unique_chunks
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_chunks, f, indent=2, ensure_ascii=False)

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        existing_meta = json.load(f)
    new_meta = [
        {
            "chunk_id": c["chunk_id"],
            "meeting_id": c["meeting_id"],
            "meeting_title": c["meeting_title"],
            "category": c["category"],
            "section_type": c["section_type"],
        }
        for c in unique_chunks
    ]
    updated_meta = existing_meta + new_meta
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_meta, f, indent=2, ensure_ascii=False)

    print(f"JSON files updated: {len(updated_chunks)} chunks, {len(updated_meta)} metadata entries")
    print("Done.")


if __name__ == "__main__":
    main()
