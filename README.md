# Readaloud

Readaloud converts typed text and uploaded documents (PDF, DOCX, TXT/MD) into MP3 audio with a chat-style web UI.

## What this project uses

### Runtime architecture
- **Frontend:** React + Vite + Tailwind CSS, served by Nginx in Docker
- **Backend API:** FastAPI (Python 3.12)
- **Database:** PostgreSQL 16 (pgvector image)
- **TTS providers:**
  - **Piper** (local, default)
  - **ElevenLabs** (optional, premium)
- **Audio tooling:** FFmpeg / ffprobe for MP3 encoding, concat, and duration
- **Storage:**
  - Local volume (`/data/audio`) by default
  - Optional S3 via pre-signed URLs

### Key backend libraries
- `fastapi`, `uvicorn[standard]`
- `sqlalchemy>=2`, `psycopg[binary]`
- `python-multipart` (file uploads)
- `pymupdf` (PDF text extraction)
- `python-docx` (DOCX text extraction)
- `piper-tts` (local speech)
- `httpx` (ElevenLabs API calls)
- `boto3` (S3 upload + signed URL generation)

## How it works

1. User submits text or uploads a supported file.
2. Backend extracts plain text (`PDF/DOCX/TXT/MD`) and validates limits.
3. Text is split into sentence chunks for stable TTS generation.
4. Piper or ElevenLabs generates audio chunks.
5. Chunks are merged into one MP3 via FFmpeg.
6. Job metadata is saved in Postgres.
7. Audio is served from local disk or redirected from S3 signed URL.

## Repository structure

- `/frontend` – React app and Nginx config
- `/backend` – FastAPI app, TTS, extraction, storage, DB model
- `/docker-compose.yml` – full local stack (web + api + db)
- `/.env.example` – environment variable template

## Prerequisites

Choose one of these setup paths:

### Option A: Docker (recommended)
- Docker Engine + Docker Compose plugin

### Option B: Local development without Docker
- Python 3.12+
- Node.js 20+
- npm
- PostgreSQL 16+
- FFmpeg (includes `ffprobe`)

## Environment setup

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` as needed.

### Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `STORAGE` | No | `local` | Audio storage backend (`local` or `s3`) |
| `S3_BUCKET` | If `STORAGE=s3` | empty | S3 bucket for generated audio |
| `S3_REGION` | If `STORAGE=s3` | `us-east-1` | AWS region |
| `ELEVENLABS_API_KEY` | Optional | empty | Enables ElevenLabs provider |
| `ELEVENLABS_VOICE_ID` | Optional | `21m00Tcm4TlvDq8ikWAM` | ElevenLabs default voice |
| `MAX_CHARS` | No | `50000` | Maximum accepted characters per request |
| `DATABASE_URL` | Yes (runtime) | internal default in code | PostgreSQL connection string |
| `PIPER_MODELS` | No | `/models` | Directory containing `.onnx` voice models |
| `LOCAL_DIR` | No | `/data/audio` | Local audio output directory |

### AWS credentials for S3
When `STORAGE=s3`, provide standard AWS credentials in environment:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- (optional) `AWS_SESSION_TOKEN`

## Run with Docker

From repo root:

```bash
docker compose up --build
```

Then open:
- App UI: `http://localhost:8080`
- API via Nginx proxy under `/api/*`

### Docker notes
- Backend downloads default Piper voice model (`en_US-lessac-medium`) during image build.
- PostgreSQL data is persisted in Docker volume `pgdata`.
- Generated audio is persisted in Docker volume `audio`.

## Local development setup (without Docker)

### 1) Start PostgreSQL
Create database and user (example values match compose defaults):

```sql
CREATE USER tts WITH PASSWORD 'tts';
CREATE DATABASE tts OWNER tts;
```

### 2) Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set env vars (example):

```bash
export DATABASE_URL=******localhost:5432/tts
export STORAGE=local
export LOCAL_DIR=/tmp/readaloud-audio
export PIPER_MODELS=/absolute/path/to/models
```

Run API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open Vite URL (usually `http://localhost:5173`).

> `frontend/vite.config.js` proxies `/api` to `http://localhost:8000` in development.

## Piper voice models

The backend expects voice files in `${PIPER_MODELS}`:
- `<voice>.onnx`
- `<voice>.onnx.json`

Default voice name is `en_US-lessac-medium`.

To add more voices, place both files in your models directory. They will appear in `/api/voices` automatically.

## API overview

- `GET /api/voices` – list available voices/providers
- `POST /api/chat` – submit raw text for TTS
- `POST /api/upload` – upload file for extraction + TTS
- `GET /api/messages` – recent generated jobs
- `GET /api/search?q=...` – full-text search in saved jobs
- `GET /api/audio/{job_id}` – stream/download generated audio

## Operational notes

- Search is PostgreSQL full-text search (`to_tsvector` / `plainto_tsquery`).
- `MAX_CHARS` is enforced server-side.
- Frontend only shows ElevenLabs option when API key is configured.
- Long texts are chunked to reduce TTS failures and memory spikes.

## Troubleshooting

- **No voices in UI:** verify Piper models exist in `PIPER_MODELS` and/or ElevenLabs key is valid.
- **`Speech generation failed` errors:** check backend logs for Piper/ElevenLabs/FFmpeg failures.
- **Uploads fail:** ensure file extension is one of `.pdf`, `.docx`, `.txt`, `.md`.
- **No audio playback:** confirm backend can write/read from `LOCAL_DIR` (or S3 config is correct).
