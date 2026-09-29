import uuid, datetime as dt
from sqlalchemy import create_engine, String, Text, Float, DateTime, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

class Job(Base):
    """One text-to-audio conversion: the text in, the audio out."""
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String, default="chat")   # "chat" or the uploaded filename
    provider: Mapped[str] = mapped_column(String)                 # piper | elevenlabs
    voice: Mapped[str] = mapped_column(String)
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    audio_key: Mapped[str] = mapped_column(String)
    duration: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    # Full-text search now. For pgvector later: add `embedding = mapped_column(Vector(384))`
    # plus an hnsw index, and rank by cosine distance in the /api/search route.
    __table_args__ = (Index("ix_jobs_fts", func.to_tsvector("english", text), postgresql_using="gin"),)

def init_db():
    Base.metadata.create_all(engine)
