"""Pydantic schemas for the AI chat endpoint."""
from pydantic import BaseModel, Field


class HistoryMessage(BaseModel):
    role: str           # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    course_id: int | None = None
    regulation: str | None = None
    program: str | None = None
    branch: str | None = None
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[HistoryMessage] = Field(default_factory=list)


class CitationOut(BaseModel):
    filename: str
    course_id: int | None = None
    course_code: str | None = None
    course_name: str | None = None
    document_id: int | None = None
    page: int | None = None
    unit: str | None = None
    unit_number: int | None = None
    topic_id: int | None = None
    topic_name: str | None = None
    text: str | None = None


class ResourceOut(BaseModel):
    """An actionable resource the frontend can offer to open."""
    resource_type: str        # "textbook" | "reference" | "url"
    title: str
    author: str | None = None
    url: str | None = None    # only present when a real URL exists in the DB


class ChatResponse(BaseModel):
    course_id: int | None
    message: str
    answer: str
    citations: list[CitationOut] = []
    resources: list[ResourceOut] = []
    suggested_questions: list[str] = []
