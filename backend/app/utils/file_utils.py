"""File handling utilities: safe naming, type detection, size checking."""
import uuid
import mimetypes
from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".ppt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.ms-powerpoint",
}


def safe_filename(original: str) -> str:
    """
    Generate a collision-proof storage filename while keeping the extension.
    Never returns the original filename to prevent path traversal.
    """
    suffix = Path(original).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")
    return f"{uuid.uuid4().hex}{suffix}"


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def is_allowed_file(filename: str) -> bool:
    ext = get_file_extension(filename)
    return ext in ALLOWED_EXTENSIONS


def detect_file_type(filename: str, content_type: str | None = None) -> str:
    """Return 'pdf' or 'docx', raise ValueError for unsupported types."""
    ext = get_file_extension(filename)
    if ext == ".pdf":
        return "pdf"
    if ext == ".docx":
        return "docx"
    # Fall back to MIME type
    if content_type in ALLOWED_MIME_TYPES:
        if "pdf" in content_type:
            return "pdf"
        return "docx"
    raise ValueError(f"Unsupported file: {filename} (type: {content_type})")


def human_readable_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} TB"


def ensure_upload_dir(upload_dir: str) -> Path:
    path = Path(upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path
