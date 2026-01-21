"""AI module - Pydantic schemas matching OpenAPI spec."""

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


class AIGenerateRequest(BaseModel):
    """AI generate request - matches OpenAPI AIGenerateRequest."""

    contractId: str
    templateId: str
    contractType: str
    jurisdiction: str = Field(default="CO")
    inputs: Dict[str, Any] = {}


class AIGenerateMetadata(BaseModel):
    """AI generation metadata."""

    model: Optional[str] = None
    promptVersion: Optional[str] = None
    confidenceScore: Optional[float] = None


class AIGenerateResponse(BaseModel):
    """AI generate response - matches OpenAPI AIGenerateResponse."""

    content: str = Field(description="Generated HTML content")
    placeholders: Dict[str, str] = {}
    metadata: Optional[AIGenerateMetadata] = None


class AIRegenerateRequest(BaseModel):
    """AI regenerate request."""

    contractId: str
    feedback: str
    preserveStructure: bool = True


class ValidateInputRequest(BaseModel):
    """Validate input request."""

    contractType: str
    inputs: Dict[str, Any] = {}


class ValidateInputResponse(BaseModel):
    """Validate input response."""

    valid: bool
    warnings: List[str] = []
    errors: List[str] = []


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
