"""
ChromaDB vector store wrapper.

Provides add / query / delete operations with a consistent interface
so the rest of the app never imports chromadb directly.
"""
import logging
import uuid
from typing import Any

from app.config import settings
from app.services.chunking import Chunk

logger = logging.getLogger(__name__)

_client = None
_collection = None
COLLECTION_NAME = "syllabus_chunks"


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection '%s' ready at %s", COLLECTION_NAME, settings.chroma_path)
    except Exception as exc:
        logger.error("Failed to initialise ChromaDB: %s", exc)
        raise
    return _collection


def add_chunks(chunks: list[Chunk]) -> int:
    if not chunks:
        return 0
    collection = _get_collection()
    ids = [str(uuid.uuid4()) for _ in chunks]
    documents = [c.text for c in chunks]
    metadatas = [c.metadata for c in chunks]
    try:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("Stored %d chunks in ChromaDB", len(chunks))
        return len(chunks)
    except Exception as exc:
        logger.error("ChromaDB add_chunks failed: %s", exc)
        raise


def query_chunks(
    query_text: str,
    course_id: int,
    n_results: int = 6,
) -> list[dict[str, Any]]:
    collection = _get_collection()
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"course_id": str(course_id)},
        )
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        return [
            {"text": doc, "metadata": meta, "distance": dist}
            for doc, meta, dist in zip(docs, metas, distances)
        ]
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        return []


def delete_course_chunks(course_id: int) -> None:
    collection = _get_collection()
    try:
        collection.delete(where={"course_id": str(course_id)})
        logger.info("Deleted ChromaDB chunks for course_id=%s", course_id)
    except Exception as exc:
        logger.error("ChromaDB delete failed for course_id=%s: %s", course_id, exc)


def collection_count() -> int:
    try:
        return _get_collection().count()
    except Exception:
        return 0
