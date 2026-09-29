import os, tempfile, uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from . import config as c, tts, storage
from .db import Session, Job, init_db
from .extract import extract

@asynccontextmanager
async def lifespan(_):
    init_db(); yield

app = FastAPI(title="Readaloud", lifespan=lifespan)

def out(j: Job) -> dict:
    return {"id": j.id, "text": j.text[:400], "chars": len(j.text), "source": j.source,
            "provider": j.provider, "voice": j.voice, "speed": j.speed, "duration": j.duration,
            "audio_url": f"/api/audio/{j.id}", "created_at": j.created_at.isoformat()}

def make_job(text: str, source: str, provider: str, voice: str, speed: float) -> dict:
    text = text.strip()
    if not text: raise HTTPException(400, "No text to read.")
    if len(text) > c.MAX_CHARS: raise HTTPException(413, f"Text is over the {c.MAX_CHARS}-character limit.")
    if provider not in ("piper", "elevenlabs"): raise HTTPException(400, "Unknown provider.")
    jid = uuid.uuid4().hex
    job = Job(id=jid, text=text, source=source, provider=provider, voice=voice,
              speed=speed, audio_key=f"{jid}.mp3")
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "out.mp3")
        try:
            job.duration = tts.synthesize(text, provider, voice, speed, path)
        except Exception as e:
            raise HTTPException(502, f"Speech generation failed: {e}")
        storage.put(job.audio_key, path)
    with Session() as s:
        s.add(job); s.commit()
        job.created_at = job.created_at  # loaded by default on commit
    return out(job)

class ChatIn(BaseModel):
    text: str
    provider: str = "piper"
    voice: str = "en_US-lessac-medium"
    speed: float = 1.0

@app.get("/api/voices")
def get_voices(): return tts.voices()

@app.post("/api/chat")
def chat(b: ChatIn): return make_job(b.text, "chat", b.provider, b.voice, b.speed)

@app.post("/api/upload")
def upload(file: UploadFile = File(...), provider: str = Form("piper"),
           voice: str = Form("en_US-lessac-medium"), speed: float = Form(1.0)):
    try: text = extract(file.filename or "", file.file.read())
    except ValueError as e: raise HTTPException(415, str(e))
    return make_job(text, file.filename, provider, voice, speed)

@app.get("/api/messages")
def messages(limit: int = 50):
    with Session() as s:
        rows = s.scalars(select(Job).order_by(Job.created_at.desc()).limit(limit)).all()
    return [out(j) for j in reversed(rows)]

@app.get("/api/search")
def search(q: str):
    ts = func.to_tsvector("english", Job.text)
    with Session() as s:
        rows = s.scalars(select(Job).where(ts.op("@@")(func.plainto_tsquery("english", q)))
                         .order_by(Job.created_at.desc()).limit(50)).all()
    return [out(j) for j in rows]

@app.get("/api/audio/{job_id}")
def audio(job_id: str):
    with Session() as s:
        j = s.get(Job, job_id)
    if not j: raise HTTPException(404, "Audio not found.")
    return storage.serve(j.audio_key)
