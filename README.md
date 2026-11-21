# RAG API: ask questions about your documents

A FastAPI backend for Retrieval-Augmented Generation (RAG). Users upload text or PDF documents. The API splits them into chunks, creates embeddings, stores them in PostgreSQL with pgvector, and answers questions using only the user's own documents, with citations.

## Features

- **Document upload**: plain text (JSON) or PDF files
- **Background ingestion**: chunking and embedding run after the response is sent; each document moves from `processing` to `ready`
- **Semantic search**: pgvector cosine similarity finds the chunks closest in meaning to a question
- **Grounded answers**: the LLM answers only from the retrieved chunks, cites its sources, and says so when the answer isn't in the documents
- **Auth**: signup and login with hashed passwords and JWT access tokens
- **Per-user privacy**: users can only see, search and ask about their own documents
- **Automated tests** with pytest against a separate test database

## How it works

```
Upload (text or PDF)
  -> save document (status: processing)
  -> background task: split into overlapping chunks
                      -> embed each chunk (all-MiniLM-L6-v2, 384 dimensions)
                      -> store chunks + vectors in pgvector
                      -> status: ready

POST /ask "Can I return a mattress?"
  -> embed the question
  -> pgvector: find the closest chunks (cosine distance), only from this user's documents
  -> send the chunks + question to the LLM (Groq)
  -> return the answer + the source chunks with similarity scores
```

## Tech stack

| Layer | Tool |
|---|---|
| API | FastAPI, Pydantic |
| Database | PostgreSQL 17 + pgvector (Docker) |
| ORM | SQLAlchemy 2.0 |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, runs locally) |
| LLM | Groq API (Llama 3.3 70B) |
| Auth | PyJWT, pwdlib (Argon2 password hashing) |
| PDF parsing | pypdf |
| Testing | pytest, FastAPI TestClient |

## Project structure

```
app/
├── main.py            # app setup, lifespan (creates tables), routers
├── config.py          # settings loaded from .env
├── database.py        # engine, sessions, get_db dependency
├── models.py          # User, Document, Chunk tables
├── schemas.py         # Pydantic request/response models
├── security.py        # password hashing, JWT create/decode
├── dependencies.py    # get_current_user
├── routers/
│   ├── auth.py        # signup, login
│   ├── documents.py   # CRUD, PDF upload, search
│   └── ask.py         # question answering
├── services/
│   ├── chunking.py    # split text into overlapping chunks
│   ├── embeddings.py  # text -> vectors
│   ├── ingest.py      # chunk + embed + store (background task)
│   ├── retrieval.py   # vector search
│   └── llm.py         # prompt + LLM call
└── tests/
```

## Getting started

### 1. Start PostgreSQL with pgvector

```bash
docker run -d --name rag-db \
  -e POSTGRES_USER=rag -e POSTGRES_PASSWORD=rag -e POSTGRES_DB=rag \
  -p 5432:5432 \
  pgvector/pgvector:pg17
```

### 2. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

- `GROQ_API_KEY`: free key from https://console.groq.com/keys
- `JWT_SECRET`: generate one with `python -c "import secrets; print(secrets.token_hex(32))"`

### 4. Run

```bash
fastapi dev app/main.py
```

Open http://127.0.0.1:8000/docs for interactive API docs. Tables and the pgvector extension are created on startup. The embedding model downloads automatically on first use (about 90 MB).

## API endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/auth/signup` | Create an account | No |
| POST | `/auth/login` | Log in, returns a JWT | No |
| POST | `/documents` | Upload a text document (JSON) | Yes |
| POST | `/documents/upload` | Upload a PDF file | Yes |
| GET | `/documents` | List your documents | Yes |
| GET | `/documents/{id}` | Get one document (with status) | Yes |
| DELETE | `/documents/{id}` | Delete a document and its chunks | Yes |
| GET | `/documents/search?q=...` | Raw semantic search (debugging) | Yes |
| POST | `/ask` | Ask a question, get an answer + sources | Yes |

### Example

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "Can I return a mattress?"}'
```

```json
{
  "answer": "Mattresses cannot be returned for hygiene reasons unless they arrive damaged [1].",
  "sources": [
    { "chunk_id": 3, "document_id": 1, "content": "Returns: Most items can be returned...", "score": 0.71 }
  ]
}
```

Optional fields on `/ask`: `top_k` (1-10, default 4) and `document_id` (search a single document).

## Running tests

Create a separate test database once:

```bash
docker exec -it rag-db psql -U rag -d rag -c "CREATE DATABASE rag_test;"
```

Then run:

```bash
pytest -v
```

Tests cover chunking, signup and login, authentication on protected routes, and that users cannot access each other's documents.

## Design notes

- **Sync routes for blocking work**: the embedding model and LLM client are synchronous, so routes that use them are plain `def` and FastAPI runs them in a thread pool instead of blocking the event loop.
- **Ingestion in the background**: uploads return immediately; a status field shows when a document is ready to query.
- **Grounding**: the system prompt restricts the model to the retrieved context and tells it to say when the answer isn't there, which reduces made-up answers.
- **404 instead of 403** for other users' documents, so the API doesn't reveal that a document exists.
- **Same embedding model for documents and questions**, so their vectors can be compared.

## Possible improvements

- Database migrations with Alembic (tables are currently created with `create_all`)
- OCR for scanned PDFs
- A durable task queue (e.g. RabbitMQ or Celery) instead of in-process background tasks
- Async database driver and LLM client
- Rate limiting on `/ask`
