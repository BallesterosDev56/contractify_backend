"""Notifications module - SQLAlchemy models."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def generate_uuid() -> str:
    return str(uuid4())


class Invitation(Base):
    """Email invitation for contract signing."""

    __tablename__ = "invitations"
    __table_args__ = {"schema": "notifications"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    contract_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    party_id: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="SENT")  # SENT, CANCELLED, RESENT
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Tracking
    sent_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Reminder(Base):
    """Scheduled reminder for unsigned contracts."""

    __tablename__ = "reminders"
    __table_args__ = {"schema": "notifications"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    contract_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    party_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Schedule
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Tracking
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
