"""Course CRUD and query endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.course import Course
from app.models.unit import Unit
from app.models.topic import Topic
from app.models.outcome import CourseOutcome
from app.models.textbook import Textbook
from app.models.mapping import COPOMapping
from app.schemas.common import ApiResponse
from app.schemas.course import (
    CourseCreate, CourseListOut, CourseDetailOut, CourseSummaryOut,
    UnitOut, OutcomeOut, TextbookOut, MappingMatrixOut, MappingRow,
)

router = APIRouter(prefix="/api/courses", tags=["courses"])
logger = logging.getLogger(__name__)


def _course_list_out(course: Course, db: Session) -> CourseListOut:
    unit_count = db.query(func.count(Unit.id)).filter(Unit.course_id == course.id).scalar() or 0
    topic_count = (
        db.query(func.count(Topic.id))
        .join(Unit, Topic.unit_id == Unit.id)
        .filter(Unit.course_id == course.id)
        .scalar() or 0
    )
    co_count = db.query(func.count(CourseOutcome.id)).filter(CourseOutcome.course_id == course.id).scalar() or 0
    tb_count = db.query(func.count(Textbook.id)).filter(Textbook.course_id == course.id).scalar() or 0
    return CourseListOut(
        id=course.id,
        course_name=course.course_name,
        course_code=course.course_code,
        program=course.program,
        branch=course.branch,
        department=course.department,
        year=course.year,
        semester=course.semester,
        regulation=course.regulation,
        credits=course.credits,
        total_hours=course.total_hours,
        description=course.description,
        prerequisites=course.prerequisites,
        created_at=course.created_at,
        unit_count=unit_count,
        topic_count=topic_count,
        co_count=co_count,
        textbook_count=tb_count,
        status="indexed",
    )


# ── Regulations endpoint ──────────────────────────────────────────────────────

regulations_router = APIRouter(prefix="/api/regulations", tags=["regulations"])


@regulations_router.get("", response_model=ApiResponse)
def list_regulations(db: Session = Depends(get_db)):
    """
    Return all distinct regulations present in the database.
    The list is driven entirely by actual course records — never hardcoded.
    """
    rows = (
        db.query(Course.regulation)
        .distinct()
        .order_by(Course.regulation)
        .all()
    )
    regs = [{"code": r[0]} for r in rows if r[0]]
    return ApiResponse.ok(regs)


# ── Course list ───────────────────────────────────────────────────────────────

@router.get("", response_model=ApiResponse)
def list_courses(
    search: str | None = Query(None),
    program: str | None = Query(None),
    branch: str | None = Query(None),
    year: str | None = Query(None),
    regulation: str | None = Query(None),
    semester: str | None = Query(None),
    source_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Course)
    if search:
        like = f"%{search}%"
        q = q.filter(
            Course.course_name.ilike(like) |
            Course.course_code.ilike(like) |
            Course.program.ilike(like)
        )
    if program:
        q = q.filter(Course.program == program)
    if branch:
        q = q.filter(Course.branch == branch)
    if year:
        q = q.filter(Course.year == year)
    if regulation:
        q = q.filter(Course.regulation == regulation)
    if semester:
        q = q.filter(Course.semester == semester)
    if source_type:
        q = q.filter(Course.source_type == source_type)

    courses = q.order_by(Course.regulation, Course.course_name).all()
    data = [_course_list_out(c, db) for c in courses]
    return ApiResponse.ok(data)


@router.get("/{course_id}", response_model=ApiResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    out = CourseDetailOut.model_validate(course)
    return ApiResponse.ok(out)


@router.post("", response_model=ApiResponse, status_code=201)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    # Uniqueness is regulation + course_code (not just course_code alone)
    existing = db.query(Course).filter(
        Course.regulation == payload.regulation,
        Course.course_code == payload.course_code,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Course '{payload.course_code}' already exists under regulation '{payload.regulation}'",
        )
    course = Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    logger.info("Created course: %s (%s / %s)", course.course_name, course.course_code, course.regulation)
    return ApiResponse.ok(_course_list_out(course, db))


@router.delete("/{course_id}", response_model=ApiResponse)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    try:
        from app.services import vector_store
        vector_store.delete_course_chunks(course_id)
    except Exception:
        pass
    db.delete(course)
    db.commit()
    logger.info("Deleted course %s", course_id)
    return ApiResponse.ok({"deleted": True, "course_id": course_id})


@router.get("/{course_id}/units", response_model=ApiResponse)
def get_units(course_id: int, db: Session = Depends(get_db)):
    _require_course(course_id, db)
    units = db.query(Unit).filter(Unit.course_id == course_id).order_by(Unit.unit_number).all()
    return ApiResponse.ok([UnitOut.model_validate(u) for u in units])


@router.get("/{course_id}/outcomes", response_model=ApiResponse)
def get_outcomes(course_id: int, db: Session = Depends(get_db)):
    _require_course(course_id, db)
    cos = db.query(CourseOutcome).filter(CourseOutcome.course_id == course_id).all()
    return ApiResponse.ok([OutcomeOut.model_validate(c) for c in cos])


@router.get("/{course_id}/textbooks", response_model=ApiResponse)
def get_textbooks(course_id: int, db: Session = Depends(get_db)):
    _require_course(course_id, db)
    books = db.query(Textbook).filter(Textbook.course_id == course_id).all()
    return ApiResponse.ok([TextbookOut.model_validate(b) for b in books])


@router.get("/{course_id}/mapping", response_model=ApiResponse)
def get_mapping(course_id: int, db: Session = Depends(get_db)):
    _require_course(course_id, db)
    rows = db.query(COPOMapping).filter(COPOMapping.course_id == course_id).all()

    co_set: dict[str, dict[str, int]] = {}
    col_set: set[str] = set()
    for row in rows:
        co_set.setdefault(row.co_number, {})[row.po_number] = row.value
        col_set.add(row.po_number)

    def col_sort_key(c: str):
        prefix = "A" if c.startswith("PO") else "B"
        num = int(c[2:]) if c[2:].isdigit() else 0
        return (prefix, num)

    columns = sorted(col_set, key=col_sort_key)
    matrix = [
        MappingRow(co=co, values={col: vals.get(col, 0) for col in columns})
        for co, vals in sorted(co_set.items())
    ]
    return ApiResponse.ok(MappingMatrixOut(course_id=course_id, matrix=matrix, columns=columns))


@router.get("/{course_id}/summary", response_model=ApiResponse)
def get_summary(course_id: int, db: Session = Depends(get_db)):
    course = _require_course(course_id, db)
    units = db.query(Unit).filter(Unit.course_id == course_id).all()
    topics = db.query(Topic).join(Unit).filter(Unit.course_id == course_id).all()
    outcomes = db.query(CourseOutcome).filter(CourseOutcome.course_id == course_id).all()
    books = db.query(Textbook).filter(Textbook.course_id == course_id).all()
    prereqs = [p.strip() for p in (course.prerequisites or "").split(",") if p.strip()]
    return ApiResponse.ok(CourseSummaryOut(
        course_id=course.id,
        course_name=course.course_name,
        course_code=course.course_code,
        program=course.program,
        year=course.year,
        regulation=course.regulation,
        total_units=len(units),
        total_topics=len(topics),
        total_outcomes=len(outcomes),
        total_textbooks=len(books),
        description=course.description,
        prerequisites=prereqs,
    ))


def _require_course(course_id: int, db: Session) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
