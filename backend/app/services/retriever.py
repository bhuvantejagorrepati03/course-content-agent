"""
Retrieval service.

Given a user question and a course_id:
  1. Perform semantic search in ChromaDB.
  2. Deduplicate and rank results.
  3. Build a context string + citation list for the LLM.
"""
import logging
import re
from typing import Any

from app.services import vector_store
from app.schemas.chat import CitationOut

logger = logging.getLogger(__name__)


def _deduplicate(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove near-duplicate chunks (same leading 100 chars)."""
    seen: set[str] = set()
    unique = []
    for r in results:
        key = r["text"][:100].strip()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def _build_context(results: list[dict[str, Any]], max_tokens: int = 2500) -> str:
    """Concatenate retrieved chunks into a context string, respecting a word budget."""
    parts = []
    total_words = 0
    for r in results:
        meta = r["metadata"]
        unit_label = meta.get("unit_name", "")
        page = meta.get("page_number", "")
        header = f"[{unit_label} | Page {page}]" if unit_label else f"[Page {page}]"
        block = f"{header}\n{r['text']}"
        words = len(block.split())
        if total_words + words > max_tokens:
            break
        parts.append(block)
        total_words += words
    return "\n\n---\n\n".join(parts)


def _make_citation(meta: dict[str, Any], course_id: int) -> CitationOut:
    unit_name = meta.get("unit_name", "")
    page_raw = meta.get("page_number", "1")
    unit_num_raw = meta.get("unit_number", "0")
    try:
        page = int(page_raw)
    except (ValueError, TypeError):
        page = None
    try:
        unit_num = int(unit_num_raw)
    except (ValueError, TypeError):
        unit_num = None
    return CitationOut(
        filename=meta.get("source_filename", "syllabus.pdf"),
        course_id=course_id,
        course_code=meta.get("course_code"),
        page=page,
        unit=unit_name or None,
        unit_number=unit_num if unit_num else None,
    )


def retrieve(
    question: str,
    course_id: int,
    n_results: int = 6,
) -> tuple[str, list[CitationOut]]:
    """
    Returns (context_string, citations).
    Falls back to empty string / empty citations if the vector store errors.
    """
    try:
        raw = vector_store.query_chunks(question, course_id, n_results=n_results)
    except Exception as exc:
        logger.warning("Vector store unavailable: %s", exc)
        return "", []

    if not raw:
        return "", []

    results = _deduplicate(raw)
    context = _build_context(results)
    citations = [_make_citation(r["metadata"], course_id) for r in results]

    # Deduplicate citations (same filename + page)
    seen_cites: set[str] = set()
    unique_citations = []
    for c in citations:
        key = f"{c.filename}|{c.page}|{c.unit}"
        if key not in seen_cites:
            seen_cites.add(key)
            unique_citations.append(c)

    return context, unique_citations[:4]  # cap at 4 visible citations
