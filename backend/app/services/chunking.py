"""
Syllabus chunking service.

Splits extracted syllabus text into overlapping chunks and attaches
rich metadata so ChromaDB can filter / cite them accurately.
"""
import re
import logging
from dataclasses import dataclass

from app.utils.text_cleaner import clean_text

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 400      # tokens / words (approximate)
DEFAULT_CHUNK_OVERLAP = 80


@dataclass
class Chunk:
    text: str
    metadata: dict


def _word_count(text: str) -> int:
    return len(text.split())


def _split_text_with_overlap(
    text: str,
    max_words: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Simple sliding-window word-level splitter."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        if end == len(words):
            break
        start += max_words - overlap
    return chunks


def chunk_by_units(
    full_text: str,
    paged_texts: list[tuple[int, str]],
    course_id: int,
    course_name: str,
    course_code: str,
    regulation: str,
    program: str,
    source_filename: str,
) -> list[Chunk]:
    """
    Produce a list of Chunk objects with metadata.

    Strategy:
    1. Split full text on unit-header boundaries.
    2. Within each unit segment, create overlapping sub-chunks.
    3. Fall back to page-based chunking for any non-unit content.
    """
    chunks: list[Chunk] = []

    # Build a page-number lookup: word offset → page
    page_lookup: dict[int, int] = {}
    offset = 0
    for page_num, page_text in paged_texts:
        words = page_text.split()
        for i in range(len(words)):
            page_lookup[offset + i] = page_num
        offset += len(words)

    def page_for_text(snippet: str) -> int:
        """Approximate page by finding the snippet in the full text."""
        try:
            idx = full_text.index(snippet[:50])
            word_idx = len(full_text[:idx].split())
            return page_lookup.get(word_idx, 1)
        except (ValueError, IndexError):
            return 1

    # ── Unit-aware splitting ────────────────────────────────────────────────
    unit_pattern = re.compile(
        r"(?:UNIT|MODULE|CHAPTER)\s*[-–:]?\s*([IVXLC0-9]+)[:\s]+([^\n]+)?",
        re.IGNORECASE,
    )
    segments = unit_pattern.split(clean_text(full_text))

    # segments alternates: [pre, unit_num, unit_title, content, unit_num, ...]
    # Process the pre-unit header content first
    base_meta = dict(
        course_id=str(course_id),
        course_name=course_name,
        course_code=course_code,
        regulation=regulation,
        program=program,
        source_filename=source_filename,
    )

    # preamble (before first unit)
    preamble = segments[0] if segments else ""
    if preamble.strip():
        for sub in _split_text_with_overlap(preamble):
            if sub.strip():
                meta = {**base_meta, "unit_number": "0", "unit_name": "Course Overview",
                        "page_number": str(page_for_text(sub))}
                chunks.append(Chunk(text=sub, metadata=meta))

    # iterate unit triples: (num_str, title_str, content_str)
    i = 1
    while i + 2 <= len(segments):
        unit_num_str = segments[i].strip()
        unit_title = (segments[i + 1] or "").strip()
        unit_content = segments[i + 2] if i + 2 < len(segments) else ""
        i += 3

        for sub in _split_text_with_overlap(unit_content):
            if sub.strip():
                meta = {
                    **base_meta,
                    "unit_number": unit_num_str,
                    "unit_name": f"Unit {unit_num_str}" + (f" — {unit_title}" if unit_title else ""),
                    "page_number": str(page_for_text(sub)),
                }
                chunks.append(Chunk(text=sub, metadata=meta))

    # ── Fallback: page-based chunks if no units detected ───────────────────
    if not chunks:
        logger.warning("No unit structure found — falling back to page-based chunking")
        for page_num, page_text in paged_texts:
            cleaned = clean_text(page_text)
            for sub in _split_text_with_overlap(cleaned):
                if sub.strip():
                    meta = {
                        **base_meta,
                        "unit_number": "0",
                        "unit_name": "Document",
                        "page_number": str(page_num),
                    }
                    chunks.append(Chunk(text=sub, metadata=meta))

    logger.info("Created %d chunks for course_id=%s", len(chunks), course_id)
    return chunks
