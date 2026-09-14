"""AI chat endpoint."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.course import Course
from app.schemas.common import ApiResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ApiResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # An explicitly supplied course ID is authoritative. Validate it here so
    # invalid IDs retain the API's normal 404 behavior instead of falling into
    # general/curriculum chat handling.
    if payload.course_id is not None:
        course = db.query(Course).filter(Course.id == payload.course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail=f"Course {payload.course_id} not found")

    logger.info(
        "Chat request — course_id=%s regulation=%s history_turns=%d msg='%s'",
        payload.course_id,
        payload.regulation,
        len(payload.history),
        payload.message[:80],
    )

    response = await handle_chat(
        course_id=payload.course_id,
        question=payload.message,
        db=db,
        history=payload.history,
        regulation=payload.regulation,
        program=payload.program,
        branch=payload.branch,
    )
    return ApiResponse.ok(response)
