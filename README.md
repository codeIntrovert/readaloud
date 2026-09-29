# Readaloud
Text, PDF and DOCX to audio. React + Tailwind, FastAPI, Piper (ElevenLabs optional), PostgreSQL, FFmpeg.

    docker compose up --build      # then open http://localhost:8080

- Premium voices: set ELEVENLABS_API_KEY in .env.
- S3: set STORAGE=s3, S3_BUCKET and AWS credentials in .env.
- More Piper voices: add .onnx and .onnx.json files to /models (see backend/Dockerfile).
- Search is Postgres full-text today; the db image already ships pgvector for semantic search later.
- Dev without Docker: `uvicorn app.main:app --reload` in backend/, `npm run dev` in frontend/.
