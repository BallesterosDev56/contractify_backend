"""Contracts module - Pydantic schemas matching OpenAPI spec."""

from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class ContractStatus(str, Enum):
    """Contract status enum matching OpenAPI."""

    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    SIGNING = "SIGNING"
    SIGNED = "SIGNED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class PartyRole(str, Enum):
    """Party role enum matching OpenAPI."""

    HOST = "HOST"
    GUEST = "GUEST"
    WITNESS = "WITNESS"


class SignatureStatus(str, Enum):
    """Signature status enum matching OpenAPI."""

    PENDING = "PENDING"
    INVITED = "INVITED"
    SIGNED = "SIGNED"


class ActivityAction(str, Enum):
    """Activity log action enum matching OpenAPI."""

    CREATED = "CREATED"
    UPDATED = "UPDATED"
    GENERATED = "GENERATED"
    SIGNED = "SIGNED"
    SENT = "SENT"
    CANCELLED = "CANCELLED"


class VersionSource(str, Enum):
    """Version source enum matching OpenAPI."""

    AI = "AI"
    USER = "USER"


# ============== Contract Schemas ==============


class Contract(BaseModel):
    """Contract base schema - matches OpenAPI Contract."""

    id: str
    title: str
    status: ContractStatus
    templateId: Optional[str] = None
    contractType: Optional[str] = None
    ownerUserId: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    signedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContractParty(BaseModel):
    """Contract party schema - matches OpenAPI ContractParty."""

    id: str
    role: PartyRole
    name: str
    email: EmailStr
    signatureStatus: SignatureStatus = SignatureStatus.PENDING
    signedAt: Optional[datetime] = None
    order: Optional[int] = Field(default=1, description="Signing order (1-based)")

    class Config:
        from_attributes = True


class Signature(BaseModel):
    """Signature schema - matches OpenAPI Signature."""

    id: str
    partyId: str
    partyName: Optional[str] = None
    role: Optional[str] = None
    signedAt: Optional[datetime] = None
    ipAddress: Optional[str] = None
    documentHash: Optional[str] = None

    class Config:
        from_attributes = True


class ContractDetail(Contract):
    """Contract detail schema - matches OpenAPI ContractDetail."""

    content: Optional[str] = None
    parties: List[ContractParty] = []
    signatures: List[Signature] = []
    documentUrl: Optional[str] = None
    documentHash: Optional[str] = None


class CreateContractRequest(BaseModel):
    """Create contract request - matches OpenAPI CreateContractRequest."""

    title: str = Field(min_length=3)
    templateId: str
    contractType: str


class UpdateContractRequest(BaseModel):
    """Update contract metadata_ - matches OpenAPI UpdateContractRequest."""

    title: Optional[str] = None


class UpdateContentRequest(BaseModel):
    """Update contract content request."""

    content: str = Field(description="HTML or Markdown content")
    source: Optional[VersionSource] = VersionSource.USER


class UpdateStatusRequest(BaseModel):
    """Update contract status request."""

    status: ContractStatus
    reason: Optional[str] = Field(default=None, description="Required for CANCELLED status")


class AddPartyRequest(BaseModel):
    """Add party request - matches OpenAPI AddPartyRequest."""

    role: PartyRole
    name: str
    email: EmailStr
    order: Optional[int] = 1


# ============== Response Schemas ==============


class Pagination(BaseModel):
    """Pagination metadata_ - matches OpenAPI Pagination."""

    page: int
    pageSize: int
    totalPages: int
    totalItems: int


class ContractListResponse(BaseModel):
    """Contract list response - matches OpenAPI ContractListResponse."""

    data: List[Contract]
    pagination: Pagination


class ContractStats(BaseModel):
    """Contract statistics - matches OpenAPI ContractStats."""

    total: int
    byStatus: Dict[str, int]
    pendingSignatures: int
    signedThisMonth: int


class ContractVersion(BaseModel):
    """Contract version - matches OpenAPI ContractVersion."""

    version: int
    content: str
    source: VersionSource
    createdAt: datetime
    createdBy: str

    class Config:
        from_attributes = True


class ActivityLog(BaseModel):
    """Activity log - matches OpenAPI ActivityLog."""

    id: str
    action: ActivityAction
    userId: str
    userName: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class TransitionsResponse(BaseModel):
    """Valid status transitions response."""

    currentStatus: str
    allowedTransitions: List[str]


class PublicContractView(BaseModel):
    """Public contract view - matches OpenAPI PublicContractView."""

    id: str
    title: str
    content: Optional[str] = None
    party: Optional[ContractParty] = None
    documentUrl: Optional[str] = None


class BulkDownloadRequest(BaseModel):
    """Bulk download request."""

    contractIds: List[str]
