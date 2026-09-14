"""
FastAPI application entry point.

Registers all routers, CORS middleware, global exception handlers,
and startup/shutdown events.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_tables

# Routers
from app.api.courses import router as courses_router, regulations_router
from app.api.syllabus import router as syllabus_router
from app.api.chat import router as chat_router
from app.api.textbooks import router as textbooks_router
from app.api.mapping import router as mapping_router
from app.api.analytics import router as analytics_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Course Content Agent Backend")
    logger.info("LLM mode: %s", "OpenAI" if settings.has_llm_key else "Mock/Fallback")
    create_tables()
    logger.info("Database tables ready")
    yield
    logger.info("Shutting down")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Course Content Agent API",
    description="AI-powered university syllabus assistant",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception at %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
    )

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "course-content-agent-backend"}


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(courses_router)
app.include_router(regulations_router)
app.include_router(syllabus_router)
app.include_router(chat_router)
app.include_router(textbooks_router)
app.include_router(mapping_router)
app.include_router(analytics_router)
