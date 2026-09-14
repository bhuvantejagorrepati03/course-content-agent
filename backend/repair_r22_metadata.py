"""Repair imported R22 curriculum metadata without touching course content.

Usage: py repair_r22_metadata.py [path-to-r22-pdf]
"""
from pathlib import Path
import sys

from app.database import SessionLocal
from app.models.course import Course
from app.models.unit import Unit
from app.models.topic import Topic
from app.services.curriculum_parser import curriculum_parser
from app.services import vector_store
from app.services.syllabus_extractor import extract_text, merge_pages


DEFAULT_PDF = Path("data/uploads/4537971a326d184f.pdf")


def main() -> None:
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
    if not pdf_path.exists():
        raise FileNotFoundError(f"R22 PDF not found: {pdf_path}")

    paged = extract_text(str(pdf_path), "pdf")
    parsed = curriculum_parser.parse(
        merge_pages(paged), paged, pdf_path.name, file_path=str(pdf_path)
    )
    r22_courses = [c for c in parsed.courses if c.regulation == "R22"]
    if not r22_courses:
        raise RuntimeError("Parser found no R22 courses; refusing to modify the database")

    db = SessionLocal()
    try:
        updated = 0
        topics_added = 0
        units_added = 0
        missing: list[str] = []
        for item in r22_courses:
            course = (
                db.query(Course)
                .filter(Course.regulation == "R22", Course.course_code == item.course_code)
                .first()
            )
            if course is None:
                missing.append(item.course_code)
                continue
            course.program = "B.Tech"
            course.branch = "CSE"
            course.department = "Computer Science and Engineering"
            course.regulation = "R22"
            course.year = item.year or course.year
            course.semester = item.semester or course.semester
            course.source_type = "imported"
            updated += 1

            # Repair only missing child content. Existing non-empty units/topics
            # are left untouched so this backfill cannot replace good imports.
            for parsed_unit in item.units:
                unit = (
                    db.query(Unit)
                    .filter(Unit.course_id == course.id, Unit.unit_number == parsed_unit.number)
                    .first()
                )
                if unit is None:
                    unit = Unit(
                        course_id=course.id,
                        unit_number=parsed_unit.number,
                        unit_name=parsed_unit.name,
                        hours=parsed_unit.hours,
                    )
                    db.add(unit)
                    db.flush()
                    units_added += 1
                else:
                    unit.unit_name = parsed_unit.name or unit.unit_name
                    unit.hours = parsed_unit.hours or unit.hours

                existing_topics = db.query(Topic).filter(Topic.unit_id == unit.id).count()
                if existing_topics == 0 and parsed_unit.topics:
                    for order, parsed_topic in enumerate(parsed_unit.topics):
                        db.add(Topic(
                            unit_id=unit.id,
                            topic_name=parsed_topic.name,
                            topic_order=order,
                        ))
                    topics_added += len(parsed_unit.topics)

        if missing:
            raise RuntimeError(f"Refusing partial repair; missing existing courses: {missing}")

        removed_seed = 0
        for course in db.query(Course).filter(Course.source_type == "seed").all():
            vector_store.delete_course_chunks(course.id)
            db.delete(course)
            removed_seed += 1

        db.commit()
        print(f"Parsed R22 courses: {len(r22_courses)}")
        print(f"Updated existing R22 courses: {updated}")
        print(f"Added missing units: {units_added}")
        print(f"Added missing topics: {topics_added}")
        print(f"Removed seed/demo courses and vectors: {removed_seed}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()