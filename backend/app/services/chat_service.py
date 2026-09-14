"""
Chat service — true RAG + LLM pipeline.

Every question goes through this flow, with NO keyword/intent matching:

  1.  Load full structured course data from SQLite  (always available)
  2.  Perform semantic retrieval from ChromaDB       (when syllabus is indexed)
  3.  Build a rich context block containing:
        - course metadata
        - all units + topics
        - course outcomes
        - textbooks
        - CO-PO mapping summary
        - semantically retrieved syllabus chunks
  4.  Prepend conversation history so the LLM can resolve follow-up questions
  5.  Call the LLM (OpenAI Responses API or fallback)
  6.  Detect textbook resources mentioned in the answer
  7.  Return answer + citations + optional resource actions
"""
import logging
import re
from typing import Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.unit import Unit
from app.models.topic import Topic
from app.models.outcome import CourseOutcome
from app.models.textbook import Textbook
from app.models.mapping import COPOMapping
from app.models.document import SyllabusDocument
from app.schemas.chat import ChatResponse, CitationOut, ResourceOut, HistoryMessage
from app.services import retriever
from app.services.llm_service import get_llm_provider, SYSTEM_PROMPT
from app.services.citation_service import enrich_citations

logger = logging.getLogger(__name__)

SUGGESTED_QUESTIONS = [
    "What is Unit 3 about?",
    "Explain binary trees in simple words.",
    "Compare stacks and queues.",
    "Which textbook should I use for trees?",
    "What are the course outcomes?",
    "Give me a study plan for this course.",
]

_YEAR_ALIASES = {
    "first": "I Year", "1st": "I Year", "one": "I Year", "1": "I Year", "i": "I Year",
    "second": "II Year", "2nd": "II Year", "two": "II Year", "2": "II Year", "ii": "II Year",
    "third": "III Year", "3rd": "III Year", "three": "III Year", "3": "III Year", "iii": "III Year",
    "fourth": "IV Year", "4th": "IV Year", "four": "IV Year", "4": "IV Year", "iv": "IV Year",
}
_YEAR_TOKEN = r"first|1st|one|1|i|second|2nd|two|2|ii|third|3rd|three|3|iii|fourth|4th|four|4|iv"
_YEAR_RE = re.compile(
    rf"\byear\s+(?P<reverse>{_YEAR_TOKEN})\b|\b(?P<forward>{_YEAR_TOKEN})\s+years?\b",
    re.IGNORECASE,
)
_SEMESTER_RE = re.compile(r"\b(first|1st|one|i|second|2nd|two|ii)\s+semester\b", re.IGNORECASE)
_COURSE_CODE_RE = re.compile(r"\b\d{2}[A-Z]{2,4}\d{3}[A-Z]?\b", re.IGNORECASE)
_UNIT_RE = re.compile(r"\bunit\s*(?P<number>[1-9]\d*)\b", re.IGNORECASE)
_ORDINAL_UNIT_RE = re.compile(r"\b(?P<ordinal>first|1st|second|2nd|third|3rd|fourth|4th)\s+unit\b", re.IGNORECASE)
_TOPIC_RE = re.compile(r"\btopic\s*(?P<number>[1-9]\d*)\b", re.IGNORECASE)
_ORDINAL_TOPIC_RE = re.compile(
    r"\b(?P<ordinal>first|1st|second|2nd|third|3rd|fourth|4th)\s+topic\b",
    re.IGNORECASE,
)
_TOPIC_FOLLOWUP_RE = re.compile(
    r"\b(?:the\s+)?(?:\d+|one|two|three|four|all|those|these|them|each)?\s*topics?\b"
    r"|\b(?:explain|describe|teach|tell me about)\s+(?:them|those)\b",
    re.IGNORECASE,
)


def _normalise_curriculum_period(question: str) -> tuple[str | None, str | None]:
    year_match = _YEAR_RE.search(question)
    semester_match = _SEMESTER_RE.search(question)
    year_token = (year_match.group("reverse") or year_match.group("forward")) if year_match else None
    year = _YEAR_ALIASES.get(year_token.lower()) if year_token else None
    semester = None
    if semester_match:
        semester = "I Semester" if semester_match.group(1).lower() in {"first", "1st", "one", "i"} else "II Semester"
    return year, semester


def _is_curriculum_question(question: str) -> bool:
    lower = question.lower()
    year, semester = _normalise_curriculum_period(question)
    asks_across_courses = bool(re.search(r"\b(subjects?|courses?)\b", lower))
    asks_curriculum_scope = bool(re.search(
        r"\b(curriculum|programme|program|regulation|all|how many|list|show)\b|\br\d{2,4}\b|\bcse\b",
        lower,
    ))
    return asks_across_courses and (bool(year or semester) or asks_curriculum_scope)


def _question_with_curriculum_history(question: str, history: list[HistoryMessage]) -> str:
    """Carry the prior curriculum period into short follow-up questions."""
    if _normalise_curriculum_period(question) != (None, None):
        return question
    if not re.search(r"\b(subjects?|courses?|those|them|these)\b", question, re.IGNORECASE):
        return question
    for message in reversed(history[-6:]):
        if _normalise_curriculum_period(message.content) != (None, None):
            return f"{question} ({message.content})"
    return question


def _question_with_unit_history(question: str, history: list[HistoryMessage]) -> str:
    if not _TOPIC_RE.search(question) and not _ORDINAL_TOPIC_RE.search(question) and not _TOPIC_FOLLOWUP_RE.search(question):
        return question
    if _UNIT_RE.search(question) or _ORDINAL_UNIT_RE.search(question):
        return question
    for message in reversed(history[-6:]):
        unit_number = _requested_unit_number(message.content)
        if unit_number is not None:
            return f"{question} (Unit {unit_number})"
        unit_match = re.search(r"\bUnit\s+([1-9]\d*)\b", message.content, re.IGNORECASE)
        if unit_match:
            return f"{question} (Unit {unit_match.group(1)})"
    return question


def _normalise_course_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _resolve_course(
    question: str,
    db: Session,
    selected_course_id: int | None,
    regulation: str | None,
    history: list[HistoryMessage],
) -> tuple[Course | None, bool]:
    """Resolve an explicitly named course without using vector similarity."""
    # A valid caller-selected course wins over name/regulation heuristics. This
    # preserves legacy seed-course requests while keeping explicit named-course
    # resolution available when no course ID was selected.
    if selected_course_id is not None:
        selected = db.query(Course).filter(Course.id == selected_course_id).first()
        if selected:
            return selected, False

    imported = db.query(Course).filter(Course.source_type == "imported").all()
    if regulation:
        imported = [course for course in imported if course.regulation == regulation]
    normalized_question = _normalise_course_text(question)

    # Course codes are unambiguous and have highest priority.
    code_match = _COURSE_CODE_RE.search(question)
    if code_match:
        code = code_match.group(0).upper()
        matches = [course for course in imported if course.course_code.upper() == code]
        if len(matches) == 1:
            return matches[0], False
        if len(matches) > 1:
            return None, True

    normalized_names = {
        course.id: _normalise_course_text(course.course_name)
        for course in imported
    }
    exact = [course for course in imported if normalized_names[course.id] == normalized_question]
    if len(exact) == 1:
        return exact[0], False
    if len(exact) > 1:
        return None, True

    # A course name can be surrounded by natural-language wording.
    contained = [
        course for course in imported
        if normalized_names[course.id] and normalized_names[course.id] in normalized_question
    ]
    if len(contained) == 1:
        return contained[0], False
    if len(contained) > 1:
        longest = max(len(normalized_names[course.id]) for course in contained)
        longest_matches = [course for course in contained if len(normalized_names[course.id]) == longest]
        if len(longest_matches) == 1:
            return longest_matches[0], False
        return None, True

    # Support a unique partial-name request such as "how many units in cryptography".
    query_tokens = set(normalized_question.split())
    partial = [
        course for course in imported
        if query_tokens & set(normalized_names[course.id].split())
        and any(token in normalized_names[course.id].split() for token in query_tokens if len(token) > 4)
    ]
    if len(partial) == 1:
        return partial[0], False
    if len(partial) > 1:
        return None, True

    # Short follow-ups inherit the course named in the previous conversation.
    for message in reversed(history[-6:]):
        if message.role != "user":
            continue
        resolved, ambiguous = _resolve_course(message.content, db, selected_course_id, regulation, [])
        if resolved or ambiguous:
            return resolved, ambiguous
    return None, False


def _course_metadata_answer(question: str, course: Course, db: Session) -> str | None:
    """Answer exact course metadata questions directly from SQLite."""
    lower = question.lower()
    units = db.query(Unit).filter(Unit.course_id == course.id).order_by(Unit.unit_number).all()
    if re.search(r"\bhow many\b.*\b(units?|topics?)\b", lower):
        if "topic" in lower:
            count = db.query(Topic).join(Unit).filter(Unit.course_id == course.id).count()
            return f"**{course.course_name} ({course.course_code})** has **{count} topics**."
        return f"**{course.course_name} ({course.course_code})** has **{len(units)} units**."
    if re.search(r"\b(list|what are|show).*(units?)\b", lower):
        lines = [
            f"{index}. **Unit {unit.unit_number}: {unit.unit_name}** ({unit.hours} hours)"
            for index, unit in enumerate(units, 1)
        ]
        return f"**{course.course_name} ({course.course_code})** has {len(units)} units:\n\n" + "\n".join(lines)
    if re.search(r"\b(textbooks?|references?|books?)\b", lower):
        books = db.query(Textbook).filter(Textbook.course_id == course.id).all()
        if not books:
            return f"No textbooks or references are recorded for **{course.course_name} ({course.course_code})**."
        lines = [f"- **{book.title}** by {book.author} ({book.book_type})" for book in books]
        return f"Books for **{course.course_name} ({course.course_code})**:\n\n" + "\n".join(lines)
    if re.search(r"\b(show|what are|list).*(COs?|outcomes?)\b", lower):
        outcomes = db.query(CourseOutcome).filter(CourseOutcome.course_id == course.id).all()
        lines = [f"- **{outcome.co_number}**: {outcome.description}" for outcome in outcomes]
        return f"Course outcomes for **{course.course_name} ({course.course_code})**:\n\n" + "\n".join(lines)
    return None


def _requested_unit_number(question: str) -> int | None:
    match = _UNIT_RE.search(question) or _ORDINAL_UNIT_RE.search(question)
    if not match:
        return None
    if match.lastgroup == "number":
        return int(match.group("number"))
    return {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4}[match.group("ordinal").lower()]


def _unit_source_answer(question: str, course: Course, db: Session) -> tuple[str, Unit] | None:
    """Return a unit-only, source-faithful answer for syllabus questions."""
    unit_number = _requested_unit_number(question)
    if unit_number is None:
        return None
    unit = (
        db.query(Unit)
        .filter(Unit.course_id == course.id, Unit.unit_number == unit_number)
        .first()
    )
    if not unit:
        return None
    topics = db.query(Topic).filter(Topic.unit_id == unit.id).order_by(Topic.topic_order).all()
    topic_match = _TOPIC_RE.search(question)
    ordinal_topic_match = _ORDINAL_TOPIC_RE.search(question)
    if topic_match or ordinal_topic_match:
        topic_number = (
            int(topic_match.group("number"))
            if topic_match
            else {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4}[ordinal_topic_match.group("ordinal").lower()]
        )
        topic = topics[topic_number - 1] if 0 < topic_number <= len(topics) else None
        if topic:
            return (
                f"**{course.course_code} — {course.course_name}**\n\n"
                f"**Unit {unit.unit_number} — {unit.unit_name}**\n\n"
                f"**Topic {topic_number}:** {topic.topic_name}\n\n"
                "This topic is listed in the imported syllabus for this unit. "
                "The syllabus does not provide additional detail here.",
                unit,
            )
        return (
            f"**{course.course_code} — {course.course_name}**\n\n"
            f"Unit {unit.unit_number} — {unit.unit_name} has **{len(topics)} syllabus topics**. "
            f"Topic {topic_number} is not available in this unit.",
            unit,
        )
    normalized_question = _normalise_course_text(question)
    named_topics = [
        topic for topic in topics
        if _normalise_course_text(topic.topic_name) in normalized_question
    ]
    if named_topics and re.search(r"\b(explain|what is|describe)\b", question, re.IGNORECASE):
        topic = max(named_topics, key=lambda item: len(_normalise_course_text(item.topic_name)))
        return (
            f"**{course.course_code} — {course.course_name}**\n\n"
            f"**Unit {unit.unit_number} — {unit.unit_name}**\n\n"
            f"**Syllabus topic:** {topic.topic_name}\n\n"
            "**Simple explanation:** This topic is included in the imported syllabus for this unit. "
            "The syllabus record does not provide additional detail beyond this topic label.",
            unit,
        )
    topic_lines = "\n".join(f"{index}. {topic.topic_name}" for index, topic in enumerate(topics, 1))
    header = f"**{course.course_code} — {course.course_name}**\n\n**Unit {unit.unit_number} — {unit.unit_name}**\n**{unit.hours} Hours**\n\n"
    if re.search(r"\bhow many\b.*\bhours?\b", question, re.IGNORECASE):
        return header.rstrip(), unit
    if re.search(r"\bhow many\b.*\btopics?\b", question, re.IGNORECASE):
        return f"{header}This unit has **{len(topics)} syllabus topics**.", unit
    if re.search(r"\b(explain|teach)\b", question, re.IGNORECASE):
        answer = (
            f"{header}"
            "### Syllabus topics\n"
            f"{topic_lines or 'No topics are recorded for this unit.'}\n\n"
            "### Simple explanation\n"
            "This section is a concise explanation of the syllabus structure above. "
            "The topic list is taken directly from the imported R22 syllabus; no additional syllabus topics are being added."
        )
        return answer, unit
    return f"{header}### Topics\n{topic_lines or 'No topics are recorded for this unit.'}", unit


def _curriculum_courses(
    question: str,
    db: Session,
    selected_course_id: int | None,
    regulation: str | None,
    program: str | None,
    branch: str | None,
) -> tuple[list[Course], str | None, str | None, str | None, str | None]:
    selected = db.query(Course).filter(Course.id == selected_course_id).first() if selected_course_id else None
    resolved_regulation = regulation or (selected.regulation if selected else None)
    resolved_program = program or (selected.program if selected else None)
    resolved_branch = branch or (selected.branch if selected else None)
    year, semester = _normalise_curriculum_period(question)

    if not resolved_regulation:
        regulations = [r[0] for r in db.query(Course.regulation).filter(Course.source_type == "imported").distinct().all() if r[0]]
        if len(regulations) == 1:
            resolved_regulation = regulations[0]
    if not resolved_program:
            program_row = (
                db.query(Course.program)
                .filter(Course.source_type == "imported", Course.regulation == resolved_regulation)
                .group_by(Course.program)
                .order_by(func.count(Course.id).desc())
                .first()
            )
            resolved_program = program_row[0] if program_row else None
    if not resolved_branch:
        branch_row = (
            db.query(Course.branch)
            .filter(Course.source_type == "imported", Course.regulation == resolved_regulation, Course.branch != "")
            .group_by(Course.branch)
            .order_by(func.count(Course.id).desc())
            .first()
        )
        resolved_branch = branch_row[0] if branch_row else None

    query = db.query(Course).filter(
        Course.source_type == "imported",
        Course.regulation == resolved_regulation,
        Course.program == resolved_program,
        Course.branch == resolved_branch,
    )
    if year:
        query = query.filter(Course.year == year)
    if semester:
        query = query.filter(Course.semester == semester)
    return query.order_by(Course.year, Course.semester, Course.course_code).all(), resolved_regulation, resolved_program, resolved_branch, year


def _curriculum_answer(
    question: str,
    courses: list[Course],
    regulation: str | None,
    program: str | None,
    branch: str | None,
    year: str | None,
) -> str:
    semester = _normalise_curriculum_period(question)[1]
    scope = " ".join(value for value in (regulation, program, branch, year, semester) if value)
    if not courses:
        return f"I could not find imported courses for {scope or 'that curriculum scope'}."
    heading = f"For {regulation} {program} {branch}"
    if year:
        heading += f", {year}"
    if semester:
        heading += f", {semester}"
    answer = f"{heading} has **{len(courses)} subjects**.\n\n"
    answer += "\n".join(f"{index}. **{course.course_code}** - {course.course_name}" for index, course in enumerate(courses, 1))
    return answer

# ── Course context builder ─────────────────────────────────────────────────────

def _build_structured_context(course_id: int, db: Session) -> tuple[str, list[Textbook]]:
    """
    Build a complete, structured text representation of the entire course from
    the SQLite database.  This is always passed to the LLM regardless of whether
    the vector store has any chunks, so the LLM always has factual course data.

    Returns (context_text, textbooks_list).
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return "", []

    units = (
        db.query(Unit)
        .filter(Unit.course_id == course_id)
        .order_by(Unit.unit_number)
        .all()
    )
    outcomes = db.query(CourseOutcome).filter(CourseOutcome.course_id == course_id).all()
    textbooks = db.query(Textbook).filter(Textbook.course_id == course_id).all()
    mappings = db.query(COPOMapping).filter(COPOMapping.course_id == course_id).all()

    prereqs = [p.strip() for p in (course.prerequisites or "").split(",") if p.strip()]

    lines: list[str] = []

    # ── Course header ──────────────────────────────────────────────────────
    lines.append(f"COURSE: {course.course_name} ({course.course_code})")
    lines.append(f"Program: {course.program} | Year: {course.year} | Semester: {course.semester}")
    lines.append(f"Regulation: {course.regulation} | Credits: {course.credits} | Total Hours: {course.total_hours}")
    if course.description:
        lines.append(f"Description: {course.description}")
    if prereqs:
        lines.append(f"Prerequisites: {', '.join(prereqs)}")
    lines.append("")

    # ── Units and topics ──────────────────────────────────────────────────
    lines.append("UNITS AND TOPICS:")
    for unit in units:
        co_str = unit.co_mapping or "—"
        lines.append(f"\nUnit {unit.unit_number}: {unit.unit_name}  [{unit.hours} hrs]  [CO mapping: {co_str}]")
        if unit.description:
            lines.append(f"  Overview: {unit.description}")
        topics = (
            db.query(Topic)
            .filter(Topic.unit_id == unit.id)
            .order_by(Topic.topic_order)
            .all()
        )
        for i, t in enumerate(topics, 1):
            lines.append(f"  {i}. {t.topic_name}")
    lines.append("")

    # ── Course outcomes ───────────────────────────────────────────────────
    if outcomes:
        lines.append("COURSE OUTCOMES:")
        for o in outcomes:
            bloom = f" [{o.bloom_level}]" if o.bloom_level else ""
            lines.append(f"  {o.co_number}: {o.description}{bloom}")
        lines.append("")

    # ── CO-PO mapping summary ─────────────────────────────────────────────
    if mappings:
        lines.append("CO-PO MAPPING (scale 1-3, 3=high correlation):")
        co_map: dict[str, list[str]] = {}
        for m in mappings:
            if m.value > 0:
                co_map.setdefault(m.co_number, []).append(f"{m.po_number}={m.value}")
        for co, po_list in sorted(co_map.items()):
            lines.append(f"  {co}: {', '.join(po_list)}")
        lines.append("")

    # ── Textbooks ─────────────────────────────────────────────────────────
    prescribed = [b for b in textbooks if b.book_type == "textbook"]
    references = [b for b in textbooks if b.book_type == "reference"]
    if prescribed:
        lines.append("PRESCRIBED TEXTBOOKS:")
        for i, b in enumerate(prescribed, 1):
            parts = [f'"{b.title}"', f"by {b.author}"]
            if b.edition:
                parts.append(b.edition)
            if b.publisher:
                parts.append(b.publisher)
            lines.append(f"  {i}. {', '.join(parts)}")
        lines.append("")
    if references:
        lines.append("REFERENCE BOOKS:")
        for i, b in enumerate(references, 1):
            parts = [f'"{b.title}"', f"by {b.author}"]
            if b.edition:
                parts.append(b.edition)
            if b.publisher:
                parts.append(b.publisher)
            lines.append(f"  {i}. {', '.join(parts)}")
        lines.append("")

    return "\n".join(lines), textbooks


def _get_source_filename(course_id: int, db: Session) -> str:
    doc = _get_source_document(course_id, db)
    if doc:
        return doc.original_filename
    course = db.query(Course).filter(Course.id == course_id).first()
    if course:
        return f"{course.course_code}_{course.regulation}.pdf"
    return "course_syllabus.pdf"


def _get_source_document(course_id: int, db: Session) -> SyllabusDocument | None:
    course = db.query(Course).filter(Course.id == course_id).first()
    doc = (
        db.query(SyllabusDocument)
        .filter(SyllabusDocument.course_id == course_id, SyllabusDocument.status == "completed")
        .order_by(SyllabusDocument.uploaded_at.desc())
        .first()
    )
    if doc:
        return doc
    if course and course.regulation:
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
            return regulation_docs[0]
    completed = db.query(SyllabusDocument).filter(SyllabusDocument.status == "completed").all()
    return completed[0] if len(completed) == 1 else None


# ── Citation builder ──────────────────────────────────────────────────────────

def _build_db_citations(course_id: int, db: Session) -> list[CitationOut]:
    filename = _get_source_filename(course_id, db)
    course = db.query(Course).filter(Course.id == course_id).first()
    document = _get_source_document(course_id, db)
    return [CitationOut(
        filename=filename,
        course_id=course_id,
        course_code=course.course_code if course else None,
        course_name=course.course_name if course else None,
        document_id=document.id if document else None,
        page=None,
        unit="Course Syllabus",
    )]


def _build_course_metadata_citations(course_id: int, db: Session) -> list[CitationOut]:
    filename = _get_source_filename(course_id, db)
    units = db.query(Unit).filter(Unit.course_id == course_id).order_by(Unit.unit_number).all()
    if not units:
        return _build_db_citations(course_id, db)
    return [
        CitationOut(
            filename=filename,
            course_id=course_id,
            course_code=db.query(Course.course_code).filter(Course.id == course_id).scalar(),
            course_name=db.query(Course.course_name).filter(Course.id == course_id).scalar(),
            document_id=(_get_source_document(course_id, db).id
                if _get_source_document(course_id, db) else None),
            page=None,
            unit=f"Unit {unit.unit_number} — {unit.unit_name}",
            unit_number=unit.unit_number,
        )
        for unit in units
    ]


def _build_unit_citation(course: Course, unit: Unit, db: Session) -> CitationOut:
    document = _get_source_document(course.id, db)
    return CitationOut(
        filename=_get_source_filename(course.id, db),
        course_id=course.id,
        course_code=course.course_code,
        course_name=course.course_name,
        document_id=document.id if document else None,
        page=None,
        unit=f"Unit {unit.unit_number} — {unit.unit_name}",
        unit_number=unit.unit_number,
    )


# ── Resource detector ─────────────────────────────────────────────────────────

def _detect_textbook_resources(
    answer: str,
    question: str,
    textbooks: list[Textbook],
) -> list[ResourceOut]:
    """
    If the answer or question references a textbook by name or the user asked
    to 'open' something, surface that book as an actionable resource.
    Only returns books that actually exist in the course data.
    """
    resources: list[ResourceOut] = []
    combined = (answer + " " + question).lower()

    for book in textbooks:
        title_lower = book.title.lower()
        # Check if book title words appear in the answer/question
        title_words = [w for w in title_lower.split() if len(w) > 4]
        if any(w in combined for w in title_words):
            resources.append(ResourceOut(
                resource_type=book.book_type,
                title=book.title,
                author=book.author,
                url=None,   # We never invent URLs; would be populated from DB if available
            ))

    return resources[:2]  # surface at most 2 books


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_conversation(
    question: str,
    structured_context: str,
    retrieved_context: str,
    history: list[HistoryMessage],
) -> list[dict]:
    """
    Build the full conversation list to send to the LLM.

    Structure:
      [past_turn_1, past_turn_2, ..., current_user_turn_with_context]

    The current user turn embeds all course context so the LLM always has it.
    Retrieved chunks are appended only when available (syllabus indexed).
    """
    messages: list[dict] = []

    # Include up to the last 6 turns of conversation history
    for msg in history[-6:]:
        messages.append({"role": msg.role, "content": msg.content})

    # Build the current user message with full context
    ctx_parts = [
        "<course_context>",
        structured_context,
    ]
    if retrieved_context.strip():
        ctx_parts.append("\n--- ADDITIONAL SYLLABUS CONTENT (from uploaded documents) ---")
        ctx_parts.append(retrieved_context)
    ctx_parts.append("</course_context>")
    ctx_parts.append("")
    ctx_parts.append(f"<question>{question}</question>")

    messages.append({"role": "user", "content": "\n".join(ctx_parts)})
    return messages


# ── Main entry point ──────────────────────────────────────────────────────────

async def handle_chat(
    course_id: int | None,
    question: str,
    db: Session,
    history: list[HistoryMessage] | None = None,
    regulation: str | None = None,
    program: str | None = None,
    branch: str | None = None,
) -> ChatResponse:
    """
    Full RAG + LLM pipeline. No keyword matching. Every question goes to the LLM.
    """
    if history is None:
        history = []

    effective_question = _question_with_curriculum_history(question, history)
    effective_course_question = _question_with_unit_history(question, history)

    logger.info(
        "Chat: course_id=%s regulation=%s history_turns=%d question='%s'",
        course_id,
        regulation,
        len(history),
        question[:100],
    )

    resolved_course, ambiguous_course = _resolve_course(
        effective_course_question, db, course_id, regulation, history
    )
    if ambiguous_course:
        return ChatResponse(
            course_id=None,
            message=question,
            answer="Which course do you mean? Please provide the course name or code.",
            citations=[],
            resources=[],
            suggested_questions=SUGGESTED_QUESTIONS,
        )
    if not resolved_course and course_id is not None and not _is_curriculum_question(effective_question):
        resolved_course = db.query(Course).filter(Course.id == course_id).first()
    if resolved_course:
        course_id = resolved_course.id
        logger.info(
            "Course resolver: question='%s' resolved to %s (%s) id=%s",
            question[:100], resolved_course.course_code, resolved_course.course_name, course_id,
        )
        unit_answer = _unit_source_answer(effective_course_question, resolved_course, db)
        if unit_answer:
            answer, unit = unit_answer
            return ChatResponse(
                course_id=course_id,
                message=question,
                answer=answer,
                citations=[_build_unit_citation(resolved_course, unit, db)],
                resources=[],
                suggested_questions=SUGGESTED_QUESTIONS,
            )
        metadata_answer = _course_metadata_answer(question, resolved_course, db)
        if metadata_answer:
            textbooks = db.query(Textbook).filter(Textbook.course_id == course_id).all()
            return ChatResponse(
                course_id=course_id,
                message=question,
                answer=metadata_answer,
                citations=_build_course_metadata_citations(course_id, db),
                resources=_detect_textbook_resources(metadata_answer, question, textbooks),
                suggested_questions=SUGGESTED_QUESTIONS,
            )

    # Curriculum questions are answered from imported SQL metadata. This branch
    # deliberately never calls Chroma, so another selected course cannot leak
    # unrelated chunks into a cross-course answer.
    if _is_curriculum_question(effective_question):
        courses, resolved_regulation, resolved_program, resolved_branch, year = _curriculum_courses(
            effective_question, db, course_id, regulation, program, branch
        )
        if not resolved_regulation:
            return ChatResponse(
                course_id=None,
                message=question,
                answer="There are multiple imported regulations. Please select a regulation before asking about subjects.",
                citations=[],
                resources=[],
                suggested_questions=SUGGESTED_QUESTIONS,
            )

        answer = _curriculum_answer(
            effective_question, courses, resolved_regulation, resolved_program, resolved_branch, year
        )
        resources: list[ResourceOut] = []
        if re.search(r"\btextbooks?|references?|books?\b", effective_question, re.IGNORECASE):
            books = (
                db.query(Textbook)
                .filter(Textbook.course_id.in_([course.id for course in courses]))
                .order_by(Textbook.course_id, Textbook.book_type, Textbook.title)
                .all()
            )
            if books:
                answer += "\n\n**Books used:**\n" + "\n".join(
                    f"- {course.course_code}: {book.title} by {book.author}"
                    for course in courses
                    for book in books
                    if book.course_id == course.id
                )
                resources = [
                    ResourceOut(resource_type=book.book_type, title=book.title, author=book.author)
                    for book in books[:2]
                ]
        return ChatResponse(
            course_id=None,
            message=question,
            answer=answer,
            citations=[CitationOut(filename="R22 CSE Curriculum", unit="Curriculum metadata")],
            resources=resources,
            suggested_questions=SUGGESTED_QUESTIONS,
        )

    if course_id is None:
        return ChatResponse(
            course_id=None,
            message=question,
            answer="Please select a course before asking a course-specific question.",
            citations=[],
            resources=[],
            suggested_questions=SUGGESTED_QUESTIONS,
        )

    # ── 1. Load structured course data from DB ────────────────────────────
    structured_context, textbooks = _build_structured_context(course_id, db)

    if not structured_context:
        return ChatResponse(
            course_id=course_id,
            message=question,
            answer="This course does not exist or has no data yet. Please upload a syllabus first.",
            citations=[],
            resources=[],
            suggested_questions=SUGGESTED_QUESTIONS,
        )

    # ── 2. Semantic retrieval from vector store ───────────────────────────
    retrieved_context: str = ""
    vector_citations: list[CitationOut] = []
    try:
        retrieved_context, raw_citations = retriever.retrieve(question, course_id, n_results=8)
        if raw_citations:
            vector_citations = enrich_citations(raw_citations, course_id, db)
            logger.info("Vector retrieval: %d chunks, %d citations", len(raw_citations), len(vector_citations))
    except Exception as exc:
        logger.warning("Vector retrieval failed (continuing without): %s", exc)

    # ── 3. Build citations (prefer vector; fall back to DB-level) ─────────
    citations = vector_citations if vector_citations else _build_db_citations(course_id, db)

    # ── 4. Build conversation for LLM ────────────────────────────────────
    conversation = _build_conversation(
        question=question,
        structured_context=structured_context,
        retrieved_context=retrieved_context,
        history=history,
    )

    # ── 5. Call the LLM ───────────────────────────────────────────────────
    try:
        llm = get_llm_provider()
        answer = await llm.complete(SYSTEM_PROMPT, conversation)
        logger.info("LLM response: %d chars", len(answer))
    except Exception as exc:
        logger.error("LLM call failed: %s", exc, exc_info=True)
        answer = (
            "I encountered an error generating a response. "
            "Please check the backend logs or try again."
        )

    # ── 6. Detect textbook resources ──────────────────────────────────────
    resources = _detect_textbook_resources(answer, question, textbooks)

    return ChatResponse(
        course_id=course_id,
        message=question,
        answer=answer,
        citations=citations,
        resources=resources,
        suggested_questions=SUGGESTED_QUESTIONS,
    )
