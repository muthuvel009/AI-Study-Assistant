# AI Study Assistant — Personal Academic Learning Companion

A college-level, source-grounded learning platform powered by **FastAPI**, **PostgreSQL with pgvector**, **Google Gemini**, and a modern **React + Vite** frontend.

---

## 1. Problem Statement & Overview

Students in rigorous university programs frequently struggle with information overload, hallucinated answers from generic AI models, and passive reading habits that do not lead to long-term memory retention.

**AI Study Assistant** solves this by providing:
- **Zero-Hallucination Grounded Tutor**: Answers strictly derived from student-uploaded course notes, slides, and textbooks with page-level and chunk-level citations.
- **Adaptive Semantic Quizzes**: Multiple-choice assessments generated via pgvector cosine similarity search over relevant study material.
- **Authoritative Server-Side Grading**: Answers are never exposed before submission, with detailed question-level explanations returned upon completion.
- **Long-Term Topic Mastery**: Exponential moving average tracking of concept accuracy across study sessions.
- **Data-Driven Study Plans**: Intelligent recommendations that detect low mastery, recent incorrect answers, and neglected topics.

---

## 2. System Architecture

```
React / Vite (SPA)
       ↓  (HTTPS / JWT Bearer)
FastAPI Backend (Port 8000)
       ↓
SQLAlchemy ORM + Alembic Migrations
       ↓
PostgreSQL 17 + pgvector Extension (Port 5433)
       ↓
Google Gemini API (text-embedding-004 + gemini-2.5-flash)
```

### Retrieval & Learning Pipeline
```mermaid
graph TD
    A[Student Uploads PDF] --> B[FastAPI /api/documents/upload]
    B -->|201 Processing| C[Background Worker]
    C -->|pypdf| D[Text Extraction & Page Tracking]
    C -->|Recursive Chunker| E[1000 Char Chunks / 200 Overlap]
    C -->|text-embedding-004| F[768-dim Vector Embeddings]
    F -->|Store| G[(PostgreSQL pgvector)]
    C -->|Transition| H[Document Ready]

    I[Student Question / Quiz Request] --> J[Topic Embedding 768-dim]
    J -->|Cosine Distance Search <->| G
    G -->|Multi-Tenant Filter: user_id == current_user.id| K[Top K Relevant Chunks]
    K -->|Strict Grounding System Prompt| L[Gemini 2.5 Flash]
    L -->|Grounded Answer + Citations / Validated Quiz| M[Authoritative Result]
```

---

## 3. Technology Stack

- **Frontend**: React 19, Vite, Tailwind CSS, Lucide React, Recharts, React Router v6.
- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2, python-jose (JWT), passlib (bcrypt).
- **Database**: PostgreSQL 17 with `pgvector 0.8.6` extension.
- **ORM & Migrations**: SQLAlchemy 2.0, Alembic.
- **Document Processing**: `pypdf` (multi-page parsing, whitespace cleaning, 1-indexed page tracking).
- **Artificial Intelligence**: Google GenAI SDK (`google-genai`), `models/text-embedding-004` (768 dimensions), `gemini-2.5-flash` with strict grounding and deterministic offline testing fallbacks.

---

## 4. Project Structure

```
AI-Study-Assistant/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── bad45ffcc776_initial_phase2_schema.py
│   │   │   ├── 821a53af3025_add_embedding_to_document_chunks.py
│   │   │   └── c19a53bf9100_add_phase4_learning_models.py
│   │   └── env.py
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py             # Settings, CORS, AI configuration
│   │   │   ├── dependencies.py       # Current user JWT resolution
│   │   │   └── security.py           # Bcrypt hashing & JWT issuance
│   │   ├── db/
│   │   │   ├── database.py           # Engine & SessionLocal
│   │   │   └── models.py             # 10 SQLAlchemy tables with pgvector
│   │   ├── routers/
│   │   │   ├── auth.py               # /api/auth (register, login, me)
│   │   │   ├── chats.py              # /api/chat (grounded RAG, history)
│   │   │   ├── documents.py          # /api/documents (upload, status, delete)
│   │   │   ├── progress.py           # /api/progress (summary, topic, activity)
│   │   │   ├── quizzes.py            # /api/quizzes (generate, submit, results)
│   │   │   └── recommendations.py    # /api/recommendations (study plans)
│   │   ├── schemas/                  # Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── ai_service.py         # Gemini embeddings & grounded RAG
│   │   │   ├── chunking_service.py   # Recursive text splitting
│   │   │   ├── pdf_service.py        # PDF extraction & cleaning
│   │   │   ├── processing_service.py # Background asynchronous worker
│   │   │   ├── quiz_service.py       # True semantic quiz RAG & scoring
│   │   │   └── recommendation_service.py # Learning analytics & study plans
│   │   └── main.py                   # FastAPI application & exception handlers
│   ├── scripts/
│   │   ├── verify_phase3_live.py     # Live RAG pipeline verification
│   │   └── verify_phase4_e2e.py      # Complete 30-step end-to-end integration test
│   ├── tests/
│   │   ├── test_api.py               # Phase 2 test suite (13 tests)
│   │   ├── test_phase3.py            # Phase 3 RAG test suite (12 tests)
│   │   └── test_phase4.py            # Phase 4 quiz & learning test suite (18 tests)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/               # Cards, Badges, Modals, Spinners, Layout
│   │   ├── context/                  # AuthContext, ToastContext
│   │   ├── pages/                    # Dashboard, Documents, Chat, Quiz, Progress, Recommendations
│   │   └── services/                 # API client & resource services
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 5. Environment Variables Configuration

### Backend (`backend/.env`)
```bash
# Database (PostgreSQL 17 with pgvector)
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/ai_study_assistant

# Authentication
JWT_SECRET_KEY=change_this_to_a_secure_random_secret_key_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# File Uploads
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=25

# CORS Configuration (Explicit comma-separated origins)
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_DIMENSION=768
GEMINI_MODEL=gemini-2.5-flash
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=5
```

### Frontend (`frontend/.env`)
```bash
VITE_API_URL=http://localhost:8000
```

---

## 6. Setup & Execution Guide

### Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- PostgreSQL 17 with `pgvector` extension

### Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Running Backend Automated Tests
```bash
cd backend
.\.venv\Scripts\pytest.exe -v
# Result: 43 passed in ~10 seconds
```

### Running Complete 30-Step End-to-End Workflow Verification
```bash
cd backend
.\.venv\Scripts\python.exe scripts/verify_phase4_e2e.py
```

---

## 7. Key Features & Algorithms

### True Semantic Quiz RAG
Quizzes are generated by embedding the student's selected topic via `models/text-embedding-004`, finding nearest neighbor chunks in PostgreSQL with `DocumentChunk.embedding.cosine_distance(topic_vector)` strictly joined on `Document.user_id == current_user.id` and `Document.id == requested_document_id`.

### Authoritative Server-Side Scoring & Moving Average Mastery
- Correct answer keys are never sent to the client during quiz taking.
- Upon submission, the server compares user selections against database records.
- Topic mastery is updated using a weighted moving average formula:
  $$\text{Mastery}_{\text{new}} = 0.7 \times \text{CurrentScore} + 0.3 \times \text{PreviousMastery}$$
- Tracks `quiz_attempts`, `questions_attempted`, `questions_correct`, `latest_score`, and `average_score`.

### Multi-Tenant Data Isolation
Every database query explicitly enforces user ownership:
- Documents: `Document.user_id == current_user.id`
- Chunks: `DocumentChunk.document.has(Document.user_id == current_user.id)`
- Chats: `Chat.user_id == current_user.id`
- Quizzes: `Quiz.user_id == current_user.id`
- Progress: `Progress.user_id == current_user.id`
- Recommendations: `Recommendation.user_id == current_user.id`
A student can never read, query, score, or delete another student's materials.

---

## 8. Deployment Preparation

1. **Database**: Use a managed PostgreSQL instance (e.g. Google Cloud SQL for PostgreSQL or AWS RDS) with the `vector` extension enabled.
2. **Persistent Storage**: Mount a persistent block volume or configure an object storage adapter (Google Cloud Storage / AWS S3) for uploaded PDF notes instead of local disk.
3. **Secrets**: Set `JWT_SECRET_KEY` and `GEMINI_API_KEY` via production environment secrets managers.
4. **CORS**: Configure `ALLOWED_ORIGINS` with your production domain (e.g., `https://study.university.edu`).
5. **Frontend Build**: Serve the pre-compiled production bundle generated via `npm run build` (`dist/` directory) via Nginx, Cloudflare Pages, or AWS CloudFront.

---

## 9. Known Limitations

1. **Complex Multi-Column PDFs**: Scanned image-only PDFs without OCR text layers or highly complex multi-column scientific layouts may extract out of order.
2. **External API Quota**: Real-time Gemini responses depend on upstream API availability; the system provides a deterministic fallback to prevent application crashes during test execution or offline environments.
3. **Storage Persistence**: In containerized deployments, local `./uploads` must be backed by persistent storage volumes to ensure files persist across container restarts.
