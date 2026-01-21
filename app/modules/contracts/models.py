"""Contracts module - SQLAlchemy models based on script_contracts.sql."""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def generate_uuid() -> str:
    return str(uuid4())


class Contract(Base):
    """Contract model - main contracts table."""

    __tablename__ = "contracts"
    __table_args__ = (
        CheckConstraint(
            "char_length(title) >= 3",
            name="contracts_title_min_length",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'GENERATED', 'SIGNING', 'SIGNED', 'CANCELLED', 'EXPIRED')",
            name="contracts_status_valid",
        ),
        {"schema": "contracts"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(100), nullable=False)
    template_id: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    versions: Mapped[List["ContractVersion"]] = relationship(
        "ContractVersion", back_populates="contract", cascade="all, delete-orphan"
    )
    parties: Mapped[List["ContractParty"]] = relationship(
        "ContractParty", back_populates="contract", cascade="all, delete-orphan"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="contract", cascade="all, delete-orphan"
    )


class ContractVersion(Base):
    """Contract version model - stores content history."""

    __tablename__ = "contract_versions"
    __table_args__ = (
        CheckConstraint("version > 0", name="version_number_positive"),
        CheckConstraint("source IN ('AI', 'USER')", name="version_source_valid"),
        UniqueConstraint("contract_id", "version", name="version_unique_per_contract"),
        {"schema": "contracts"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    contract_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("contracts.contracts.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    contract: Mapped["Contract"] = relationship("Contract", back_populates="versions")


class ContractParty(Base):
    """Contract party model - signers and witnesses."""

    __tablename__ = "contract_parties"
    __table_args__ = (
        CheckConstraint("role IN ('HOST', 'GUEST', 'WITNESS')", name="party_role_valid"),
        CheckConstraint(
            "signature_status IN ('PENDING', 'INVITED', 'SIGNED')",
            name="party_signature_status_valid",
        ),
        CheckConstraint("signing_order > 0", name="party_signing_order_positive"),
        UniqueConstraint("contract_id", "email", name="party_email_unique_per_contract"),
        {"schema": "contracts"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    contract_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("contracts.contracts.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    signature_status: Mapped[str] = mapped_column(String(10), default="PENDING", nullable=False)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    signing_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    contract: Mapped["Contract"] = relationship("Contract", back_populates="parties")


class ActivityLog(Base):
    """Activity log model - contract history."""

    __tablename__ = "activity_logs"
    __table_args__ = (
        CheckConstraint(
            "action IN ('CREATED', 'UPDATED', 'GENERATED', 'SIGNED', 'SENT', 'CANCELLED')",
            name="activity_action_valid",
        ),
        {"schema": "contracts"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    contract_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("contracts.contracts.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    contract: Mapped["Contract"] = relationship("Contract", back_populates="activity_logs")
