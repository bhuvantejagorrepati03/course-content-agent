"""
Extract raw text from PDF and DOCX files with page-number tracking.

Returns a list of (page_number, text) tuples so downstream services
can attach accurate page citations to every chunk.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PagedText = list[tuple[int, str]]   # [(page_num, text), ...]


def extract_pdf(file_path: str) -> PagedText:
    """Extract text page-by-page from a PDF using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed — cannot extract PDF text")
        return [(1, "")]

    pages: PagedText = []
    try:
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                pages.append((page_num, text))
        doc.close()
        logger.info("PDF extraction: %d pages from %s", len(pages), file_path)
    except Exception as exc:
        logger.error("PDF extraction failed for %s: %s", file_path, exc)
    return pages


def extract_docx(file_path: str) -> PagedText:
    """
    Extract text from a DOCX file.
    DOCX has no true page boundaries — we assign virtual pages of
    ~50 paragraphs each so citations remain meaningful.
    """
    try:
        from docx import Document
    except ImportError:
        logger.error("python-docx not installed — cannot extract DOCX text")
        return [(1, "")]

    paras: list[str] = []
    try:
        doc = Document(file_path)
        paras = [p.text for p in doc.paragraphs if p.text.strip()]
        logger.info("DOCX extraction: %d paragraphs from %s", len(paras), file_path)
    except Exception as exc:
        logger.error("DOCX extraction failed for %s: %s", file_path, exc)
        return [(1, "")]

    # Group into virtual pages of 50 paragraphs
    page_size = 50
    pages: PagedText = []
    for i in range(0, len(paras), page_size):
        page_num = (i // page_size) + 1
        text = "\n".join(paras[i : i + page_size])
        pages.append((page_num, text))

    return pages if pages else [(1, "")]


def extract_text(file_path: str, file_type: str) -> PagedText:
    """Dispatch to the correct extractor based on file_type."""
    if file_type == "pdf":
        return extract_pdf(file_path)
    if file_type == "docx":
        return extract_docx(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")


def merge_pages(pages: PagedText) -> str:
    """Join all page texts into a single string (for the parser)."""
    return "\n".join(text for _, text in pages)


def count_pages(file_path: str, file_type: str) -> int:
    """Return a quick page/paragraph-group count without full extraction."""
    try:
        if file_type == "pdf":
            import fitz
            with fitz.open(file_path) as doc:
                return doc.page_count
        if file_type == "docx":
            from docx import Document
            doc = Document(file_path)
            return max(1, len(doc.paragraphs) // 50)
    except Exception:
        pass
    return 0
