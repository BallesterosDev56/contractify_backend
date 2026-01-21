"""Audit module - Pydantic schemas matching OpenAPI spec."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AuditEvent(BaseModel):
    """Audit event."""

    id: str
    eventType: str
    actor: Optional[str] = None
    timestamp: datetime
    ipAddress: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AuditTrail(BaseModel):
    """Audit trail response - matches OpenAPI AuditTrail."""

    contractId: str
    events: List[AuditEvent]
    generatedAt: datetime
