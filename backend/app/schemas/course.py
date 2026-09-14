"""Pydantic schemas for courses, units, topics, outcomes, textbooks, and mappings."""
from datetime import datetime
from pydantic import BaseModel, Field


# ── Topic ─────────────────────────────────────────────────────────────────────

class TopicBase(BaseModel):
    topic_name: str
    topic_order: int = 0
    description: str | None = None


class TopicCreate(TopicBase):
    pass


class TopicOut(TopicBase):
    id: int
    unit_id: int

    model_config = {"from_attributes": True}


# ── Unit ──────────────────────────────────────────────────────────────────────

class UnitBase(BaseModel):
    unit_number: int
    unit_name: str
    hours: int = 8
    co_mapping: str | None = None
    description: str | None = None


class UnitCreate(UnitBase):
    topics: list[TopicCreate] = []


class UnitOut(UnitBase):
    id: int
    course_id: int
    topics: list[TopicOut] = []

    model_config = {"from_attributes": True}


# ── Course Outcome ─────────────────────────────────────────────────────────────

class OutcomeBase(BaseModel):
    co_number: str
    description: str
    bloom_level: str | None = None


class OutcomeCreate(OutcomeBase):
    pass


class OutcomeOut(OutcomeBase):
    id: int
    course_id: int

    model_config = {"from_attributes": True}


# ── Textbook ──────────────────────────────────────────────────────────────────

class TextbookBase(BaseModel):
    title: str
    author: str
    edition: str | None = None
    publisher: str | None = None
    year: str | None = None
    isbn: str | None = None
    book_type: str = "textbook"


class TextbookCreate(TextbookBase):
    pass


class TextbookOut(TextbookBase):
    id: int
    course_id: int

    model_config = {"from_attributes": True}


# ── CO–PO Mapping ─────────────────────────────────────────────────────────────

class MappingEntry(BaseModel):
    co_number: str
    po_number: str
    value: int = Field(ge=0, le=3)


class MappingRow(BaseModel):
    """One CO row with all PO/PSO values as a dict."""
    co: str
    values: dict[str, int]


class MappingMatrixOut(BaseModel):
    course_id: int
    matrix: list[MappingRow]
    columns: list[str]


# ── Course ────────────────────────────────────────────────────────────────────

class CourseBase(BaseModel):
    course_name: str
    course_code: str
    program: str
    branch: str = ""
    department: str
    year: str
    semester: str
    regulation: str
    credits: float = 4.0
    l_hours: int = 0
    t_hours: int = 0
    p_hours: int = 0
    total_hours: int = 45
    description: str | None = None
    course_objectives: str | None = None
    prerequisites: str | None = None
    source_type: str = "seed"


class CourseCreate(CourseBase):
    pass


class CourseListOut(CourseBase):
    id: int
    created_at: datetime
    unit_count: int = 0
    topic_count: int = 0
    co_count: int = 0
    textbook_count: int = 0
    status: str = "indexed"

    model_config = {"from_attributes": True}


class CourseDetailOut(CourseBase):
    id: int
    created_at: datetime
    units: list[UnitOut] = []
    outcomes: list[OutcomeOut] = []
    textbooks: list[TextbookOut] = []

    model_config = {"from_attributes": True}


class CourseSummaryOut(BaseModel):
    course_id: int
    course_name: str
    course_code: str
    program: str
    year: str
    regulation: str
    total_units: int
    total_topics: int
    total_outcomes: int
    total_textbooks: int
    description: str | None
    prerequisites: list[str]
