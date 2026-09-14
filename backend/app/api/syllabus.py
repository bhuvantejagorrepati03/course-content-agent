"""
Syllabus upload, listing, download and deletion endpoints.

Endpoints
---------
GET    /api/syllabus                   list all documents  (any role)
POST   /api/syllabus/upload            upload + process    (faculty only)
GET    /api/syllabus/{id}             document details    (any role)
GET    /api/syllabus/{id}/status      polling status      (any role)
GET    /api/syllabus/{id}/download    serve the file      (any role)
DELETE /api/syllabus/{id}             delete + clear AI   (faculty only)
"""
import hashlib
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.document import SyllabusDocument
from app.models.course import Course
from app.schemas.common import ApiResponse
from app.schemas.syllabus import DocumentUploadOut, DocumentStatusOut
from app.utils.file_utils import is_allowed_file
from app.auth.roles import require_faculty

router = APIRouter(prefix="/api/syllabus", tags=["syllabus"])
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".ppt"}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _enrich(doc: SyllabusDocument, db: Session) -> dict:
    """Add course_name to the raw document dict before validation."""
    course_name = None
    if doc.course_id:
        course = db.query(Course).filter(Course.id == doc.course_id).first()
        if course:
            course_name = course.course_name
    d = DocumentStatusOut.model_validate(doc).model_dump()
    d["course_name"] = course_name
    return d


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=ApiResponse)
def list_documents(
    course_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(SyllabusDocument)
    if course_id is not None:
        q = q.filter(SyllabusDocument.course_id == course_id)
    docs = q.order_by(SyllabusDocument.uploaded_at.desc()).all()
    return ApiResponse.ok([_enrich(d, db) for d in docs])


# ── Upload ────────────────────────────────────────────────────────────────────

def _is_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@router.post("/upload", response_model=ApiResponse, status_code=202)
async def upload_syllabus(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    course_id: int | None = Form(None),
    db: Session = Depends(get_db),
    _role: str = Depends(require_faculty),   # ← 403 for students
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    if not _is_allowed(file.filename):
        raise HTTPException(
            status_code=415,
            detail="Supported types: PDF, DOCX, PPTX. Other types are not accepted.",
        )

    content = await file.read()

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
        )
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # ── Duplicate detection via SHA-256 ──────────────────────────────────
    file_hash = _sha256(content)
    existing = (
        db.query(SyllabusDocument)
        .filter(SyllabusDocument.file_hash == file_hash)
    )
    if course_id is not None:
        existing = existing.filter(SyllabusDocument.course_id == course_id)
    dup = existing.first()
    if dup:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This file already exists"
                + (f" for this course" if course_id else "")
                + f" (document id {dup.id})."
            ),
        )

    # ── Detect type (PDF / DOCX; PPTX stored as-is, no text extraction yet)
    ext = Path(file.filename).suffix.lower()
    file_type = "pdf" if ext == ".pdf" else "docx" if ext == ".docx" else "pptx"

    # ── Save file with collision-proof name ───────────────────────────────
    stored_name = f"{file_hash[:16]}{ext}"   # deterministic → same content = same name
    upload_path = Path(settings.upload_dir) / stored_name
    upload_path.write_bytes(content)
    logger.info("Saved upload: %s → %s (%d bytes)", file.filename, stored_name, len(content))

    # ── Persist record ────────────────────────────────────────────────────
    doc = SyllabusDocument(
        course_id=course_id,
        filename=stored_name,
        original_filename=file.filename,
        file_type=file_type,
        file_path=str(upload_path),
        file_size=len(content),
        file_hash=file_hash,
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    logger.info("Created document record id=%s for '%s'", doc.id, file.filename)

    # ── Background processing (PDF/DOCX only) ────────────────────────────
    if file_type in ("pdf", "docx"):
        background_tasks.add_task(_process_in_background, doc.id)

    return ApiResponse.ok(DocumentUploadOut(
        document_id=doc.id,
        status=doc.status,
        filename=doc.original_filename,
        file_size=doc.file_size,
    ))


def _process_in_background(document_id: int):
    import asyncio
    from app.database import SessionLocal
    from app.services.syllabus_processor import process_document

    db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_document(document_id, db))
        loop.close()
    except Exception as exc:
        logger.error("Background processing failed for doc %s: %s", document_id, exc)
    finally:
        db.close()


# ── Get / Status ──────────────────────────────────────────────────────────────

@router.get("/{document_id}/status", response_model=ApiResponse)
def get_status(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(SyllabusDocument).filter(SyllabusDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return ApiResponse.ok(_enrich(doc, db))


@router.get("/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)):
    """Serve the file for browser download / inline viewing."""
    doc = db.query(SyllabusDocument).filter(SyllabusDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    path = Path(doc.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    media_type = media_types.get(doc.file_type, "application/octet-stream")

    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=doc.original_filename,
        headers={"Content-Disposition": f'inline; filename="{doc.original_filename}"'},
    )


@router.get("/{document_id}", response_model=ApiResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(SyllabusDocument).filter(SyllabusDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return ApiResponse.ok(_enrich(doc, db))


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{document_id}", response_model=ApiResponse)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _role: str = Depends(require_faculty),   # ← 403 for students
):
    doc = db.query(SyllabusDocument).filter(SyllabusDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    course_id = doc.course_id

    # 1. Remove file from disk
    try:
        Path(doc.file_path).unlink(missing_ok=True)
        logger.info("Deleted file: %s", doc.file_path)
    except Exception as exc:
        logger.warning("Could not delete file %s: %s", doc.file_path, exc)

    # 2. Remove vectorised content from ChromaDB so the AI stops using it
    if course_id:
        try:
            from app.services import vector_store
            # Delete only chunks that originated from this specific document
            collection = vector_store._get_collection()
            collection.delete(where={
                "$and": [
                    {"course_id": str(course_id)},
                    {"source_filename": doc.original_filename},
                ]
            })
            logger.info("Removed vector chunks for doc id=%s (course %s, file '%s')",
                        document_id, course_id, doc.original_filename)
        except Exception as exc:
            logger.warning("Could not remove vector chunks for doc %s: %s", document_id, exc)

    # 3. Delete DB record
    db.delete(doc)
    db.commit()

    return ApiResponse.ok({
        "deleted": True,
        "document_id": document_id,
        "vectors_cleared": course_id is not None,
    })
