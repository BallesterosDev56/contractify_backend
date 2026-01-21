"""Signatures module - SQLAlchemy models."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def generate_uuid() -> str:
    return str(uuid4())


class Signature(Base):
    """Signature record."""

    __tablename__ = "signatures"
    __table_args__ = {"schema": "signatures"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    contract_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    party_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    party_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[Optional[str]] = mapped_column(String(20))

    # Signature data
    document_hash: Mapped[Optional[str]] = mapped_column(String(64))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    geolocation: Mapped[Optional[str]] = mapped_column(String(255))

    # Evidence
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Timestamps
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SignatureToken(Base):
    """Token for guest signing."""

    __tablename__ = "signature_tokens"
    __table_args__ = {"schema": "signatures"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    contract_id: Mapped[str] = mapped_column(String(100), nullable=False)
    party_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Status
    used: Mapped[bool] = mapped_column(default=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
