"""AI module - SQLAlchemy models for async jobs."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def generate_uuid() -> str:
    return str(uuid4())


class AsyncJob(Base):
    """Async job tracking for AI generation."""

    __tablename__ = "async_jobs"
    __table_args__ = {"schema": "ai"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)  # AI_GENERATE, PDF_GENERATE, etc.
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0)

    # Input data
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Result data
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
    error: Mapped[Optional[str]] = mapped_column(Text)

    # User tracking
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class AICache(Base):
    """Cache for AI-generated content to avoid re-generation."""

    __tablename__ = "ai_cache"
    __table_args__ = {"schema": "ai"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
