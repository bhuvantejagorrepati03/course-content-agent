"""Pydantic schemas for syllabus upload and processing."""
from datetime import datetime
from pydantic import BaseModel, model_validator


class DocumentUploadOut(BaseModel):
    document_id: int
    status: str
    filename: str
    file_size: int


class DocumentStatusOut(BaseModel):
    document_id: int          # mapped from model.id
    status: str               # uploaded | processing | completed | failed
    original_filename: str
    file_type: str
    file_size: int
    course_id: int | None
    course_name: str | None = None   # filled in by the route if available
    uploaded_at: datetime
    error_message: str | None = None
    extracted_units: int = 0
    extracted_topics: int = 0
    extracted_outcomes: int = 0
    extracted_textbooks: int = 0
    file_hash: str | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_id(cls, data):
        """
        SQLAlchemy model has field `id`; our schema exposes it as `document_id`.
        Works whether data is a dict or an ORM model.
        """
        if hasattr(data, "__dict__"):
            # ORM model instance
            values = {c.key: getattr(data, c.key)
                      for c in data.__mapper__.column_attrs}
        elif isinstance(data, dict):
            values = dict(data)
        else:
            return data
        if "document_id" not in values and "id" in values:
            values["document_id"] = values["id"]
        return values


class ProcessingStats(BaseModel):
    units: int
    topics: int
    course_outcomes: int
    textbooks: int
