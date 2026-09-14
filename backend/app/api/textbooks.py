"""Textbook listing and search endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.textbook import Textbook
from app.schemas.common import ApiResponse
from app.schemas.course import TextbookOut

router = APIRouter(prefix="/api/textbooks", tags=["textbooks"])


@router.get("", response_model=ApiResponse)
def list_textbooks(
    course_id: int | None = Query(None),
    book_type: str | None = Query(None, description="textbook or reference"),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Textbook)
    if course_id:
        q = q.filter(Textbook.course_id == course_id)
    if book_type:
        q = q.filter(Textbook.book_type == book_type)
    if search:
        like = f"%{search}%"
        q = q.filter(
            Textbook.title.ilike(like) |
            Textbook.author.ilike(like) |
            Textbook.publisher.ilike(like)
        )
    books = q.order_by(Textbook.title).all()
    return ApiResponse.ok([TextbookOut.model_validate(b) for b in books])
