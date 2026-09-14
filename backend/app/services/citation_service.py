"""
Citation service.

Enriches raw retrieval citations with data from the SQLite database
(unit names, correct page references) and de-duplicates them.
"""
import logging
from sqlalchemy.orm import Session

from app.models.unit import Unit
from app.models.course import Course
from app.models.document import SyllabusDocument
from app.schemas.chat import CitationOut

logger = logging.getLogger(__name__)


def enrich_citations(
    citations: list[CitationOut],
    course_id: int,
    db: Session,
) -> list[CitationOut]:
    """
    Look up unit names from the database to make citations accurate
    even when the vector metadata is incomplete.
    """
    if not citations:
        return []

    # Load units once
    units = db.query(Unit).filter(Unit.course_id == course_id).all()
    unit_map: dict[int, str] = {u.unit_number: u.unit_name for u in units}
    course = db.query(Course).filter(Course.id == course_id).first()
    document = (
        db.query(SyllabusDocument)
        .filter(SyllabusDocument.course_id == course_id, SyllabusDocument.status == "completed")
        .order_by(SyllabusDocument.uploaded_at.desc())
        .first()
    )
    if not document and course and course.regulation:
        regulation_docs = (
            db.query(SyllabusDocument)
            .filter(
                SyllabusDocument.status == "completed",
                SyllabusDocument.original_filename.ilike(f"%{course.regulation}%"),
            )
            .order_by(SyllabusDocument.uploaded_at.desc())
            .all()
        )
        if len(regulation_docs) == 1:
            document = regulation_docs[0]
    if not document:
        candidates = db.query(SyllabusDocument).filter(SyllabusDocument.status == "completed").all()
        if len(candidates) == 1:
            document = candidates[0]

    enriched: list[CitationOut] = []
    for c in citations:
        unit_name = c.unit
        if c.unit_number and c.unit_number in unit_map:
            unit_name = f"Unit {c.unit_number} — {unit_map[c.unit_number]}"
        enriched.append(CitationOut(
            filename=c.filename,
            course_id=course_id,
            course_code=c.course_code,
            course_name=course.course_name if course else None,
            document_id=document.id if document else None,
            page=c.page,
            unit=unit_name,
            unit_number=c.unit_number,
            text=c.text,
        ))
    return enriched


def build_db_citations(
    unit_numbers: list[int],
    course_id: int,
    source_filename: str,
    db: Session,
) -> list[CitationOut]:
    """
    Build citations from DB data when no vector search is available
    (e.g. direct database-backed answers).
    """
    units = (
        db.query(Unit)
        .filter(Unit.course_id == course_id, Unit.unit_number.in_(unit_numbers))
        .all()
    )
    return [
        CitationOut(
            filename=source_filename,
            page=None,
            unit=f"Unit {u.unit_number} — {u.unit_name}",
            unit_number=u.unit_number,
        )
        for u in units
    ]
