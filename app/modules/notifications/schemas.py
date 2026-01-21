"""Notifications module - Pydantic schemas matching OpenAPI spec."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SendInvitationRequest(BaseModel):
    """Send invitation request - matches OpenAPI SendInvitationRequest."""

    contractId: str
    partyId: str
    message: Optional[str] = None


class SendInvitationResponse(BaseModel):
    """Send invitation response."""

    invitationId: str
    sentAt: datetime


class NotificationTemplate(BaseModel):
    """Email template."""

    id: str
    name: str
    description: Optional[str] = None


class ReminderRequest(BaseModel):
    """Schedule reminder request."""

    contractId: str
    partyId: str
    scheduleAt: datetime
