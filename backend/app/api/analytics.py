"""Analytics / statistics endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.course import Course
from app.models.unit import Unit
from app.models.topic import Topic
from app.models.outcome import CourseOutcome
from app.models.textbook import Textbook
from app.models.document import SyllabusDocument
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=ApiResponse)
def get_analytics(db: Session = Depends(get_db)):
    total_courses = db.query(func.count(Course.id)).scalar() or 0
    total_documents = db.query(func.count(SyllabusDocument.id)).scalar() or 0
    total_units = db.query(func.count(Unit.id)).scalar() or 0
    total_topics = db.query(func.count(Topic.id)).scalar() or 0
    total_outcomes = db.query(func.count(CourseOutcome.id)).scalar() or 0
    total_textbooks = db.query(func.count(Textbook.id)).scalar() or 0

    # Courses by program
    program_counts = (
        db.query(Course.program, func.count(Course.id).label("count"))
        .group_by(Course.program)
        .all()
    )

    # Topics per course
    topics_per_course = (
        db.query(Course.course_name, func.count(Topic.id).label("count"))
        .join(Unit, Unit.course_id == Course.id)
        .join(Topic, Topic.unit_id == Unit.id)
        .group_by(Course.id)
        .order_by(func.count(Topic.id).desc())
        .limit(10)
        .all()
    )

    # CO distribution by bloom level
    co_bloom = (
        db.query(CourseOutcome.bloom_level, func.count(CourseOutcome.id).label("count"))
        .group_by(CourseOutcome.bloom_level)
        .all()
    )

    return ApiResponse.ok({
        "total_courses": total_courses,
        "total_documents": total_documents,
        "total_units": total_units,
        "total_topics": total_topics,
        "total_outcomes": total_outcomes,
        "total_textbooks": total_textbooks,
        "courses_by_program": [{"program": p, "count": c} for p, c in program_counts],
        "topics_per_course": [{"course": name, "topics": c} for name, c in topics_per_course],
        "co_distribution": [
            {"level": lvl or "Unspecified", "count": c} for lvl, c in co_bloom
        ],
    })
