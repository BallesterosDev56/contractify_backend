"""Documents module - Pydantic schemas matching OpenAPI spec."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Async job status enum."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GeneratePDFRequest(BaseModel):
    """Generate PDF request - matches OpenAPI GeneratePDFRequest."""

    contractId: str
    includeAuditPage: bool = True


class AsyncJobResponse(BaseModel):
    """Async job response - matches OpenAPI AsyncJobResponse."""

    jobId: str
    status: JobStatus
    pollUrl: Optional[str] = None


class AsyncJobStatus(BaseModel):
    """Async job status - matches OpenAPI AsyncJobStatus."""

    jobId: str
    status: JobStatus
    progress: int = Field(ge=0, le=100, default=0)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    createdAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None


class SignatureVerification(BaseModel):
    """Signature verification result."""

    signerId: str
    valid: bool
    signedAt: Optional[datetime] = None


class DocumentVerification(BaseModel):
    """Document verification response - matches OpenAPI DocumentVerification."""

    valid: bool
    documentHash: Optional[str] = None
    signatures: List[SignatureVerification] = []
    verifiedAt: Optional[datetime] = None
