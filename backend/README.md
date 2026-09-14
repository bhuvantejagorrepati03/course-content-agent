# Course Content Agent — Backend

AI-powered FastAPI backend for the Course Content Agent.  
Accepts university syllabus uploads, extracts structured course data, indexes it in ChromaDB, and answers natural-language questions via RAG.

---

## Architecture

```
course-content-agent-backend/
├── app/
│   ├── main.py               # FastAPI app, CORS, routers, lifespan
│   ├── config.py             # Pydantic settings loaded from .env
│   ├── database.py           # SQLAlchemy engine + session factory
│   ├── models/               # SQLAlchemy ORM models (SQLite)
│   ├── schemas/              # Pydantic request/response schemas
│   ├── api/                  # FastAPI route handlers
│   │   ├── courses.py        # CRUD + queries
│   │   ├── syllabus.py       # File upload + processing
│   │   ├── chat.py           # AI chat endpoint
│   │   ├── textbooks.py      # Textbook listing
│   │   ├── mapping.py        # CO-PO-PSO matrix
│   │   └── analytics.py      # Stats
│   ├── services/
│   │   ├── syllabus_parser.py    # Rule-based syllabus parser
│   │   ├── syllabus_extractor.py # PDF/DOCX text extraction
│   │   ├── syllabus_processor.py # Full processing pipeline
│   │   ├── chunking.py           # Text → overlapping chunks
│   │   ├── vector_store.py       # ChromaDB wrapper
│   │   ├── retriever.py          # Semantic search + citation building
│   │   ├── llm_service.py        # OpenAI adapter + mock fallback
│   │   ├── chat_service.py       # RAG orchestration
│   │   └── citation_service.py   # Citation enrichment
│   ├── utils/
│   │   ├── text_cleaner.py       # Unicode, whitespace normalization
│   │   └── file_utils.py         # Safe filenames, type detection
│   └── seed.py               # Database seeder (5 courses)
├── data/
│   ├── uploads/              # Uploaded syllabus files
│   ├── chroma/               # ChromaDB persistent storage
│   └── app.db                # SQLite database
├── tests/                    # pytest test suite
├── .env                      # Local environment (not committed)
├── .env.example              # Template
├── requirements.txt
└── run.py                    # Convenience uvicorn launcher
```

---

## Requirements

- Python 3.11+
- pip

---

## Installation

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate (Windows)
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
copy .env.example .env
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_API_KEY` | *(empty)* | OpenAI API key. Leave blank for mock mode. |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS allowed origin |
| `DATABASE_URL` | `sqlite:///./data/app.db` | SQLite connection string |
| `CHROMA_PATH` | `data/chroma` | ChromaDB storage directory |
| `UPLOAD_DIR` | `data/uploads` | File upload directory |
| `MAX_UPLOAD_SIZE_MB` | `20` | Max file size |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

**Mock mode**: Leave `LLM_API_KEY` empty. The backend answers questions using structured DB queries and a deterministic fallback — no external API call needed.

---

## Running

```bash
# Seed the database (first time only)
python -m app.seed

# Start the server
uvicorn app.main:app --reload --port 8000

# Or use the convenience launcher
python run.py
```

- API: http://localhost:8000  
- Swagger docs: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  
- Health: http://localhost:8000/health

---

## API Endpoints

### Health
```
GET /health
```

### Courses
```
GET    /api/courses                   # List / search / filter
GET    /api/courses/{id}              # Full course with units, topics, COs
POST   /api/courses                   # Create course
DELETE /api/courses/{id}              # Delete course
GET    /api/courses/{id}/units        # Units for a course
GET    /api/courses/{id}/outcomes     # Course outcomes
GET    /api/courses/{id}/textbooks    # Textbooks
GET    /api/courses/{id}/mapping      # CO-PO-PSO matrix
GET    /api/courses/{id}/summary      # Course summary stats
```

### Syllabus Upload
```
POST   /api/syllabus/upload           # Upload PDF/DOCX (background processing)
GET    /api/syllabus/{id}             # Document details
GET    /api/syllabus/{id}/status      # Polling endpoint (uploaded|processing|completed|failed)
DELETE /api/syllabus/{id}             # Delete document
```

### Chat (RAG)
```
POST /api/chat
Body: { "course_id": 1, "message": "What are the topics in Unit 3?" }
```

### Textbooks
```
GET /api/textbooks?course_id=1&book_type=textbook&search=...
```

### Mapping
```
GET /api/mapping/{course_id}
```

### Analytics
```
GET /api/analytics
```

---

## RAG Pipeline

```
User question + course_id
    │
    ├─ Structured DB answers (fast, no LLM)
    │   • Unit topics query
    │   • Textbook listing
    │   • Course outcomes
    │   • Summary / prerequisites
    │
    └─ RAG (when no structured match)
        │
        ├─ ChromaDB semantic search (filtered by course_id)
        ├─ Retrieve top-6 relevant chunks
        ├─ Build context string with unit/page metadata
        ├─ LLM completion (or mock fallback)
        └─ Return answer + citations
```

---

## Example API Calls

### Chat — Unit topics
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"course_id": 1, "message": "What are the topics in Unit 3?"}'
```

### Response
```json
{
  "success": true,
  "data": {
    "course_id": 1,
    "message": "What are the topics in Unit 3?",
    "answer": "**Unit 3 — Trees** (10 hours)\n\n1. Binary Trees...",
    "citations": [
      { "filename": "CS201_R23.pdf", "page": null, "unit": "Unit 3 — Trees", "unit_number": 3 }
    ],
    "suggested_questions": [...]
  }
}
```

### Upload syllabus
```bash
curl -X POST http://localhost:8000/api/syllabus/upload \
  -F "file=@DataStructures_R23.pdf" \
  -F "course_id=1"
```

### Poll status
```bash
curl http://localhost:8000/api/syllabus/1/status
```

---

## Tests

```bash
pytest tests/ -v
```

---

## Frontend Integration

The React frontend runs at `http://localhost:5173`.  
CORS is pre-configured to allow it.

Update `src/services/` in the frontend to point to `http://localhost:8000/api/...` instead of returning mock data.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: fitz` | `pip install pymupdf` |
| `ModuleNotFoundError: docx` | `pip install python-docx` |
| `chromadb` import error | `pip install chromadb` |
| `sentence-transformers` slow first load | Normal — downloads embedding model once |
| No answers in chat | Check that seed ran: `python -m app.seed` |
| CORS error from frontend | Verify `FRONTEND_ORIGIN` in `.env` matches your dev server port |
