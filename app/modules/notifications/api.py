"""Notifications module - API routes matching OpenAPI spec."""

from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.db import get_db

from .schemas import (
    NotificationTemplate,
    ReminderRequest,
    SendInvitationRequest,
    SendInvitationResponse,
)
from .service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    """Get notification service instance."""
    return NotificationService(db)


@router.post("/send-invitation", response_model=SendInvitationResponse)
async def send_invitation(
    data: SendInvitationRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: NotificationService = Depends(get_service),
) -> SendInvitationResponse:
    """
    Send signing invitation to party.

    POST /notifications/send-invitation
    """
    return await service.send_invitation(current_user, data)


@router.post("/invitations/{invitationId}/cancel", status_code=status.HTTP_200_OK)
async def cancel_invitation(
    invitationId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: NotificationService = Depends(get_service),
) -> Dict[str, bool]:
    """
    Cancel pending invitation.

    POST /notifications/invitations/{invitationId}/cancel
    """
    await service.cancel_invitation(invitationId, current_user)
    return {"success": True}


@router.post("/invitations/{invitationId}/resend", response_model=SendInvitationResponse)
async def resend_invitation(
    invitationId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: NotificationService = Depends(get_service),
) -> SendInvitationResponse:
    """
    Resend invitation.

    POST /notifications/invitations/{invitationId}/resend
    """
    return await service.resend_invitation(invitationId, current_user)


@router.get("/templates", response_model=List[NotificationTemplate])
async def get_templates(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: NotificationService = Depends(get_service),
) -> List[NotificationTemplate]:
    """
    Get available email templates.

    GET /notifications/templates
    """
    return service.get_templates()


@router.post("/reminders", status_code=status.HTTP_201_CREATED)
async def schedule_reminder(
    data: ReminderRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: NotificationService = Depends(get_service),
) -> Dict[str, Any]:
    """
    Configure reminder for unsigned contract.

    POST /notifications/reminders
    """
    return await service.schedule_reminder(current_user, data)
