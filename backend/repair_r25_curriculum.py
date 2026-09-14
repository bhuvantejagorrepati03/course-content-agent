"""Repair the already uploaded R25 curriculum without touching R22.

Usage: py repair_r25_curriculum.py [document_id]
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from app.database import SessionLocal
from app.models.course import Course
from app.models.document import SyllabusDocument
from app.services import vector_store
from app.services.syllabus_processor import process_document


R25_PDF = Path("data/uploads/78478a76f55a0aca.pdf")


def main() -> None:
    document_id = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    db = SessionLocal()
    try:
        document = db.query(SyllabusDocument).filter(SyllabusDocument.id == document_id).first()
        if document is None and R25_PDF.exists():
            document = SyllabusDocument(
                filename=R25_PDF.name,
                original_filename="R25 C25 CSE Course Structure & Syllabus.pdf",
                file_type="pdf",
                file_path=str(R25_PDF),
                file_size=R25_PDF.stat().st_size,
                status="uploaded",
            )
            db.add(document)
            db.flush()
            document_id = document.id
        if document is None:
            raise RuntimeError(f"Document {document_id} not found")
        if not document.original_filename.lower().startswith("r25"):
            raise RuntimeError(f"Document {document_id} is not the R25 curriculum: {document.original_filename}")

        document.course_id = None
        db.flush()
        r25_courses = db.query(Course).filter(Course.regulation == "R25").all()
        invalid_placeholders = (
            db.query(Course)
            .filter(
                Course.regulation == "Unknown",
                Course.course_code == "UNKNOWN",
                Course.source_type == "imported",
            )
            .all()
        )
        for course in [*r25_courses, *invalid_placeholders]:
            vector_store.delete_course_chunks(course.id)
            db.delete(course)
        document.status = "uploaded"
        document.error_message = None
        db.commit()
        print(f"Removed incorrect R25 courses/placeholders: {len(r25_courses) + len(invalid_placeholders)}")

        asyncio.run(process_document(document_id, db))
        db.expire_all()
        remaining = db.query(Course).filter(Course.regulation == "R25").count()
        if remaining == 0:
            raise RuntimeError("R25 processing completed without creating courses")
        print(f"Reprocessed document {document_id}; R25 courses: {remaining}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
