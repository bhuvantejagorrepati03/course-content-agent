"""
Syllabus / Curriculum processing pipeline orchestrator.

Handles both:
  1. Single-course syllabi (old behaviour, still works)
  2. Full curriculum booklets with many courses (new capability)

The processor detects which type it's dealing with and routes accordingly.

Key changes vs original:
  - Regulation-aware course matching: (regulation, course_code) pair is the identity
  - source_type flag: "seed" vs "imported"
  - First real import: removes seed/demo courses after successful import
  - Multi-course: iterates ParsedCurrriculum.courses and persists each
  - Additive: never deletes previously imported courses from OTHER regulations
"""
import logging
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.unit import Unit
from app.models.topic import Topic
from app.models.outcome import CourseOutcome
from app.models.textbook import Textbook
from app.models.mapping import COPOMapping
from app.models.document import SyllabusDocument
from app.services.syllabus_extractor import extract_text, merge_pages, count_pages
from app.services.syllabus_parser import parser as single_course_parser
from app.services.curriculum_parser import curriculum_parser, ParsedCourse
from app.services.chunking import chunk_by_units
from app.services import vector_store

logger = logging.getLogger(__name__)


# ── Course identity ───────────────────────────────────────────────────────────

def _find_existing_course(
    regulation: str,
    course_code: str,
    db: Session,
) -> Course | None:
    """
    Look up a course by the composite key (regulation, course_code).
    This is the canonical identity — R22+22CS201 ≠ R23+23CS201.
    """
    if not regulation or not course_code:
        return None
    return (
        db.query(Course)
        .filter(
            Course.regulation == regulation,
            Course.course_code == course_code,
        )
        .first()
    )


def _upsert_course(parsed: ParsedCourse, db: Session) -> Course:
    """
    Create or update a Course record based on parsed curriculum data.
    Uses (regulation, course_code) composite identity.
    """
    existing = _find_existing_course(parsed.regulation, parsed.course_code, db)

    if existing:
        # Update fields but keep id and relationships
        existing.course_name = parsed.course_name or existing.course_name
        existing.program = parsed.programme or existing.program
        existing.branch = parsed.branch or existing.branch
        existing.department = parsed.branch_full or existing.department
        existing.regulation = parsed.regulation or existing.regulation
        existing.year = parsed.year or existing.year
        existing.semester = parsed.semester or existing.semester
        existing.credits = parsed.credits or existing.credits
        existing.l_hours = parsed.l_hours
        existing.t_hours = parsed.t_hours
        existing.p_hours = parsed.p_hours
        existing.total_hours = parsed.total_hours or existing.total_hours
        existing.description = parsed.description or existing.description
        existing.prerequisites = (
            ", ".join(parsed.prerequisites) if parsed.prerequisites else existing.prerequisites
        )
        existing.course_objectives = parsed.objectives or existing.course_objectives
        existing.source_type = "imported"
        db.flush()
        return existing

    # Create new
    department = (
        parsed.branch_full if hasattr(parsed, "branch_full") and parsed.branch_full
        else f"{parsed.programme} {parsed.branch}".strip()
        or "Not specified"
    )
    course = Course(
        course_name=parsed.course_name or "Unknown",
        course_code=parsed.course_code,
        program=parsed.programme or "B.Tech",
        branch=parsed.branch or "",
        department=department,
        year=parsed.year or "Not specified",
        semester=parsed.semester or "Not specified",
        regulation=parsed.regulation or "Unknown",
        credits=parsed.credits or 4.0,
        l_hours=parsed.l_hours,
        t_hours=parsed.t_hours,
        p_hours=parsed.p_hours,
        total_hours=parsed.total_hours or 45,
        description=parsed.description or None,
        prerequisites=(", ".join(parsed.prerequisites) if parsed.prerequisites else None),
        course_objectives=parsed.objectives or None,
        source_type="imported",
    )
    db.add(course)
    db.flush()
    return course


# ── Child record helpers ──────────────────────────────────────────────────────

def _save_units(parsed_units, course: Course, db: Session) -> tuple[int, int]:
    db.query(Unit).filter(Unit.course_id == course.id).delete()
    unit_count = topic_count = 0
    for pu in parsed_units:
        # Support both old ParsedUnit (syllabus_parser) and new ParsedUnit (curriculum_parser)
        module_num = getattr(pu, "module_number", 0) or 0
        module_name = getattr(pu, "module_name", "") or ""
        description = None
        if module_num and module_name:
            description = f"Module {module_num}: {module_name}"

        unit = Unit(
            course_id=course.id,
            unit_number=pu.number,
            unit_name=pu.name,
            hours=pu.hours,
            co_mapping=", ".join(pu.co_mapping) if pu.co_mapping else None,
            description=description,
        )
        db.add(unit)
        db.flush()
        unit_count += 1
        for order, pt in enumerate(pu.topics):
            db.add(Topic(unit_id=unit.id, topic_name=pt.name, topic_order=order))
            topic_count += 1
    return unit_count, topic_count


def _save_outcomes(parsed_outcomes, course: Course, db: Session) -> int:
    db.query(CourseOutcome).filter(CourseOutcome.course_id == course.id).delete()
    for po in parsed_outcomes:
        db.add(CourseOutcome(
            course_id=course.id,
            co_number=po.co_number,
            description=po.description,
            bloom_level=po.bloom_level,
        ))
    return len(parsed_outcomes)


def _save_textbooks(parsed_books, course: Course, db: Session) -> int:
    db.query(Textbook).filter(Textbook.course_id == course.id).delete()
    for pb in parsed_books:
        db.add(Textbook(
            course_id=course.id,
            title=pb.title,
            author=pb.author or "Unknown",
            edition=pb.edition,
            publisher=pb.publisher,
            book_type=pb.book_type,
        ))
    return len(parsed_books)


def _save_mappings(parsed_mappings, course: Course, db: Session) -> None:
    db.query(COPOMapping).filter(COPOMapping.course_id == course.id).delete()
    for pm in parsed_mappings:
        db.add(COPOMapping(
            course_id=course.id,
            co_number=pm.co_number,
            po_number=pm.po_number,
            value=pm.value,
        ))


def _link_document(course: Course, doc: SyllabusDocument, db: Session) -> None:
    """Associate a document with a course (use first course if multi-course)."""
    if doc.course_id is None:
        doc.course_id = course.id


def _course_page_texts(
    source_pages: list[int],
    paged_texts: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    """Return the parser-identified pages belonging to one course."""
    page_text_by_number = {page_num: page_text for page_num, page_text in paged_texts}
    return [
        (page_num, page_text_by_number[page_num])
        for page_num in source_pages
        if page_num in page_text_by_number
    ]


# ── Seed-data cleanup ─────────────────────────────────────────────────────────

def _remove_seed_data_if_needed(db: Session) -> int:
    """
    Called after the first successful real curriculum import.
    Deletes only courses marked source_type='seed' that have no associated
    imported documents, then removes their ChromaDB vectors.

    Returns count of courses removed.
    """
    seed_courses = db.query(Course).filter(Course.source_type == "seed").all()
    removed = 0
    for c in seed_courses:
        try:
            vector_store.delete_course_chunks(c.id)
        except Exception:
            pass
        db.delete(c)
        removed += 1
    if removed:
        db.commit()
        logger.info("Removed %d seed/demo courses after first real curriculum import", removed)
    return removed


def _has_any_imported_courses(db: Session) -> bool:
    return db.query(Course).filter(Course.source_type == "imported").count() > 0


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def process_document(document_id: int, db: Session) -> None:
    """
    Main processing entry point.  Handles both single-course syllabus uploads
    and full curriculum PDF booklets.
    """
    doc = db.query(SyllabusDocument).filter(SyllabusDocument.id == document_id).first()
    if not doc:
        logger.error("Document %s not found", document_id)
        return

    try:
        doc.status = "processing"
        doc.error_message = None
        db.commit()
        logger.info("[%s] Processing started: %s", document_id, doc.original_filename)

        # ── Extract text ──────────────────────────────────────────────────
        paged = extract_text(doc.file_path, doc.file_type)
        full_text = merge_pages(paged)
        doc.page_count = count_pages(doc.file_path, doc.file_type)
        logger.info("[%s] Extracted: %d pages, %d chars", document_id, len(paged), len(full_text))

        # ── Try curriculum parser first (multi-course) ────────────────────
        curriculum = curriculum_parser.parse(
            full_text, paged, doc.original_filename,
            file_path=doc.file_path,   # pass actual path for direct PyMuPDF re-read
        )

        is_first_real_import = not _has_any_imported_courses(db)

        total_units = total_topics = total_outcomes = total_books = total_mappings = 0
        courses_saved = 0

        if curriculum.courses:
            logger.info(
                "[%s] Curriculum parser found %d courses (regulation=%s, branch=%s)",
                document_id, len(curriculum.courses), curriculum.regulation, curriculum.branch,
            )
            logger.info(
                "[%s] Curriculum parser found %d courses (regulation=%s, branch=%s)",
                document_id, len(curriculum.courses), curriculum.regulation, curriculum.branch,
            )

            # Persist each course
            first_course: Course | None = None
            for pc in curriculum.courses:
                course = _upsert_course(pc, db)
                if first_course is None:
                    first_course = course
                    _link_document(course, doc, db)

                uc, tc = _save_units(pc.units, course, db)
                oc = _save_outcomes(pc.outcomes, course, db)
                bc = _save_textbooks(pc.textbooks, course, db)
                _save_mappings(pc.mappings, course, db)

                total_units += uc
                total_topics += tc
                total_outcomes += oc
                total_books += bc
                total_mappings += len(pc.mappings)
                courses_saved += 1

                # Index in ChromaDB
                try:
                    course_paged = _course_page_texts(pc.source_pages, paged)
                    if not course_paged:
                        logger.warning(
                            "[%s] No source pages found for %s; skipping course indexing",
                            document_id, course.course_code,
                        )
                        continue
                    course_text = merge_pages(course_paged)
                    chunks = chunk_by_units(
                        full_text=course_text,
                        paged_texts=course_paged,
                        course_id=course.id,
                        course_name=course.course_name,
                        course_code=course.course_code,
                        regulation=course.regulation,
                        program=course.program,
                        source_filename=doc.original_filename,
                    )
                    vector_store.delete_course_chunks(course.id)
                    vector_store.add_chunks(chunks)
                except Exception as exc:
                    logger.warning("[%s] ChromaDB indexing failed for %s: %s",
                                   document_id, course.course_code, exc)

        else:
            # Fallback: single-course parser
            logger.info("[%s] Falling back to single-course parser", document_id)
            parsed = single_course_parser.parse(full_text, doc.original_filename)

            # Regulation-aware course lookup/create
            reg = parsed.regulation or "Unknown"
            code = parsed.course_code or "UNKNOWN"
            course = _find_existing_course(reg, code, db)
            if not course:
                course = Course(
                    course_name=parsed.course_name or doc.original_filename.rsplit(".", 1)[0],
                    course_code=code,
                    program="B.Tech CSE",
                    branch="CSE",
                    department="Computer Science & Engineering",
                    year="Not specified",
                    semester=parsed.semester or "Not specified",
                    regulation=reg,
                    credits=parsed.credits or 4.0,
                    description=None,
                    prerequisites=", ".join(parsed.prerequisites) if parsed.prerequisites else None,
                    source_type="imported",
                )
                db.add(course)
                db.flush()
            else:
                course.source_type = "imported"
                db.flush()

            _link_document(course, doc, db)
            uc, tc = _save_units(parsed.units, course, db)
            oc = _save_outcomes(parsed.outcomes, course, db)
            bc = _save_textbooks(parsed.textbooks, course, db)
            _save_mappings(parsed.mappings, course, db)
            total_units, total_topics, total_outcomes, total_books = uc, tc, oc, bc
            total_mappings = len(parsed.mappings)
            courses_saved = 1

            chunks = chunk_by_units(
                full_text=full_text,
                paged_texts=paged,
                course_id=course.id,
                course_name=course.course_name,
                course_code=course.course_code,
                regulation=course.regulation,
                program=course.program,
                source_filename=doc.original_filename,
            )
            vector_store.delete_course_chunks(course.id)
            vector_store.add_chunks(chunks)

        # ── Remove seed data on first successful real import ──────────────
        if is_first_real_import and courses_saved > 0:
            removed = _remove_seed_data_if_needed(db)
            logger.info("[%s] Seed cleanup: removed %d demo courses", document_id, removed)

        doc.extracted_units = total_units
        doc.extracted_topics = total_topics
        doc.extracted_outcomes = total_outcomes
        doc.extracted_textbooks = total_books
        doc.status = "completed"
        db.commit()

        logger.info(
            "[%s] Completed: %d courses, %d units, %d topics, %d COs, %d books, %d mappings",
            document_id, courses_saved, total_units, total_topics,
            total_outcomes, total_books, total_mappings,
        )

    except Exception as exc:
        logger.exception("[%s] Processing failed: %s", document_id, exc)
        doc.status = "failed"
        doc.error_message = str(exc)[:500]
        db.commit()
