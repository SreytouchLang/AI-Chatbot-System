# AI Chatbot System

Document and media-aware chatbot built with a polished frontend plus a FastAPI, LangGraph, Redis, and Chroma backend.

Developed by **Sreytouch Lang (Jessica)**.

## UI Preview

<p align="center">
  <img src="docs/images/ui-dashboard-preview.svg" alt="AI Chatbot System dashboard preview" width="100%" />
</p>

<p align="center">
  <img src="docs/images/ui-workspace-preview.svg" alt="AI Chatbot System workspace preview" width="100%" />
</p>

## Highlights

- branded project identity and API metadata
- custom frontend at `/` with ingest, chat, health, summary, and evidence panels
- demo mode fallback so PDF and DOCX workflows still work without an OpenAI key
- safer startup checks with no dummy vector data inserted
- centralized configuration for cleaner maintenance
- stronger request validation and typed API responses
- user-based chat sessions instead of a hardcoded user id
- chat responses now include answer, summary, and source snippets
- local or URL-based document, voice, and video ingestion with duplicate detection, cleanup, transcription, and timeouts
- audio and video transcription powered by OpenAI, with `ffmpeg` conversion for compatible media formats
- `/health` and `/about` endpoints for service visibility
- `.env.example` added for easier setup

## Client Experience

- one-page dashboard with a branded landing section and live service status
- friendly setup banner that explains whether the app is in full mode or demo mode
- flexible ingestion from URL or local upload for PDF, DOCX, audio, and video
- conversational chat experience with persistent user sessions
- evidence sidebar that shows retrieved source snippets for every answer
- rolling conversation summary so longer sessions stay easier to follow
- responsive layout that still presents well on smaller screens

## Backend Features

- FastAPI service layer with typed request and response schemas
- LangGraph workflow for memory loading, retrieval, answer generation, summarization, and storage
- Redis-backed chat memory with recent-message windows and rolling summaries
- Chroma vector storage for retrieval-augmented answers
- local hash-embedding and answer fallback when OpenAI is not configured
- hash-based duplicate detection to avoid re-ingesting the same file content
- document parsing for PDF and DOCX plus media transcription for voice and video
- startup health checks and operational endpoints for visibility

## Tech Stack

- FastAPI
- LangGraph
- Redis
- ChromaDB
- optional OpenAI APIs for upgraded chat, embeddings, and transcription
- local fallback embeddings and answer generation for demo-friendly PDF and DOCX workflows
- HTML, CSS, and vanilla JavaScript frontend

## Architecture

```text
Client
  -> FastAPI controllers
  -> service layer
  -> LangGraph workflow
      -> load memory from Redis
      -> retrieve context from Chroma
      -> generate answer with LLM
      -> summarize conversation
      -> store memory in Redis
```

## Project Structure

```text
AI-Chatbot-System/
|-- controllers/     # FastAPI route handlers
|-- core/            # settings and app-level exceptions
|-- db/              # Redis and Chroma helpers
|-- graph/           # LangGraph state and nodes
|-- ingest/          # document and media ingestion pipeline
|-- schemas/         # request and response models
|-- services/        # chat, ingest, and health orchestration
|-- utils/           # model and embedding adapters
|-- .env.example     # sample configuration
`-- main.py          # FastAPI app entrypoint
```

## Requirements

- Python 3.10+
- Redis
- OpenAI API key only if you want upgraded OpenAI answers or audio/video transcription
- `ffmpeg` only for some audio/video conversion paths

## Install

```bash
pip install -r requirements.txt
```

## Environment

Start from the sample config:

```bash
cp .env.example .env
```

Key branding defaults:

```bash
APP_NAME=AI Chatbot System
DEVELOPER_DISPLAY_NAME=Sreytouch Lang (Jessica)
```

Optional OpenAI setup:

```bash
OPENAI_API_KEY=your_api_key
```

Recommended local default for quieter logs:

```bash
LANGSMITH_TRACING=false
```

Transcription defaults for audio and video:

```bash
TRANSCRIPTION_PROVIDER=openai
TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
```

## Modes

- `Demo Mode`: no valid `OPENAI_API_KEY` is set. PDF and DOCX ingestion still work, retrieval still works, and the chat stays grounded in uploaded file content.
- `Full Mode`: a valid `OPENAI_API_KEY` is set. OpenAI-powered answers, embeddings, and audio/video transcription are enabled.

## Run

```bash
uvicorn main:app --reload
```

If your global Python does not have the project dependencies, use the repo venv instead:

```bash
source .venv/bin/activate
python -m uvicorn main:app --reload
```

Or start it in one command:

```bash
./run.sh
```

If `OPENAI_API_KEY` is still a placeholder, the app starts in `Demo Mode` instead of failing.

App:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Supported Files

- documents: `.pdf`, `.docx`
- audio: `.mp3`, `.m4a`, `.wav`, `.ogg`, `.flac`, `.mpeg`, `.mpga`
- convertible audio: `.aac`, `.aif`, `.aiff`, `.caf`, `.wma`
- video: `.mp4`, `.mov`, `.m4v`, `.avi`, `.mkv`, `.webm`

## API

### `GET /`

Serves the frontend dashboard UI.

### `GET /about`

Returns branded project metadata plus setup mode information.

### `GET /api/info`

Returns the app name, version, and developer credit as JSON.

### `GET /health`

Checks setup state, Redis, and vector store readiness.

### `POST /api/ingest`

Ingest a remote supported file into the vector store.

Request:

```json
{
  "file_name": "terms_conditions",
  "source_url": "https://example.com/terms.pdf"
}
```

`source_url` also accepts the legacy key `s3_url`.

Supported file types are listed above in **Supported Files**.

### `POST /api/ingest/upload`

Upload a local supported document, audio, or video file directly from the UI or with multipart form data.

Example:

```bash
curl -X POST "http://127.0.0.1:8000/api/ingest/upload" \
  -F "file=@/path/to/meeting.mov" \
  -F "file_name=meeting_notes"
```

### `POST /api/chat`

Ask a question using memory plus retrieved document context.

In `Demo Mode`, this endpoint still works for PDF and DOCX-backed retrieval without requiring OpenAI.

Request:

```json
{
  "user_id": "customer-42",
  "q": "What is the return policy?",
  "top_k": 3
}
```

Response shape:

```json
{
  "status": "success",
  "data": {
    "user_id": "customer-42",
    "answer": "You can return items within 30 days...",
    "summary": "Customer is asking about returns and refunds.",
    "sources": [
      {
        "source_file": "terms_conditions",
        "page_number": 2,
        "excerpt": "Returns are accepted within 30 days..."
      }
    ]
  }
}
```

## Notes

- If the uploaded files do not contain the answer, the assistant is instructed to say that clearly instead of inventing facts.
- Conversation history is stored in Redis with both recent messages and a rolling summary.
- Duplicate ingestion is detected by file hash.
- `Demo Mode` is intended for local demos and document-grounded workflows when no real OpenAI key is configured.
- Audio and video ingestion rely on transcription, so a valid `OPENAI_API_KEY` is required for those file types.
- The UI shows a `Demo Mode` banner when OpenAI features are unavailable, instead of blocking the whole app.
- Some media formats are converted with `ffmpeg` before transcription.
- The visible project branding now credits **Sreytouch Lang (Jessica)** by default.
