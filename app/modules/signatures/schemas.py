"""Signatures module - Pydantic schemas matching OpenAPI spec."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SignatureEvidence(BaseModel):
    """Signature evidence - matches OpenAPI SignatureEvidence."""

    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    geolocation: Optional[str] = None
    signedAt: Optional[datetime] = None


class SignRequest(BaseModel):
    """Sign request - matches OpenAPI SignRequest."""

    contractId: str
    partyId: str
    evidence: Optional[SignatureEvidence] = None


class GuestSignRequest(BaseModel):
    """Guest sign request - matches OpenAPI GuestSignRequest."""

    token: str
    evidence: Optional[SignatureEvidence] = None


class SignatureResponse(BaseModel):
    """Signature response - matches OpenAPI SignatureResponse."""

    signatureId: str
    documentHash: Optional[str] = None
    signedAt: datetime
    certificateUrl: Optional[str] = None


class Signature(BaseModel):
    """Signature - matches OpenAPI Signature."""

    id: str
    partyId: str
    partyName: Optional[str] = None
    role: Optional[str] = None
    signedAt: Optional[datetime] = None
    ipAddress: Optional[str] = None
    documentHash: Optional[str] = None

    class Config:
        from_attributes = True


class CreateTokenRequest(BaseModel):
    """Create token request."""

    contractId: str
    partyId: str
    expiresInMinutes: int = Field(default=1440, description="Default 24 hours")


class SignatureTokenResponse(BaseModel):
    """Signature token response - matches OpenAPI SignatureTokenResponse."""

    token: str
    signUrl: str
    expiresAt: datetime


class ValidateTokenResponse(BaseModel):
    """Validate token response."""

    valid: bool
    contractId: Optional[str] = None
    partyId: Optional[str] = None
    expiresAt: Optional[datetime] = None
