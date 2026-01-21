"""Notifications module - Business logic service."""

from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.shared.exceptions import NotFoundException

from .repository import InvitationRepository, ReminderRepository
from .schemas import (
    NotificationTemplate,
    ReminderRequest,
    SendInvitationRequest,
    SendInvitationResponse,
)

# Static email templates
EMAIL_TEMPLATES: List[NotificationTemplate] = [
    NotificationTemplate(
        id="invitation_default",
        name="Invitación de Firma",
        description="Invitación estándar para firmar un contrato",
    ),
    NotificationTemplate(
        id="reminder_default",
        name="Recordatorio de Firma",
        description="Recordatorio para contratos pendientes de firma",
    ),
    NotificationTemplate(
        id="completion_notice",
        name="Notificación de Completado",
        description="Notificación cuando todos han firmado",
    ),
    NotificationTemplate(
        id="cancellation_notice",
        name="Notificación de Cancelación",
        description="Notificación cuando un contrato es cancelado",
    ),
]


class NotificationService:
    """Service for notification operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.invitation_repo = InvitationRepository(db)
        self.reminder_repo = ReminderRepository(db)

    async def send_invitation(
        self,
        current_user: CurrentUser,
        data: SendInvitationRequest,
    ) -> SendInvitationResponse:
        """
        Send signing invitation to party.

        In production, this would:
        1. Look up party email from contracts service
        2. Generate signing URL with token
        3. Send email via SendGrid/SES
        """
        # Mock email address (in production, get from party record)
        email = "party@example.com"

        invitation = await self.invitation_repo.create(
            contract_id=data.contractId,
            party_id=data.partyId,
            email=email,
            sent_by=current_user.id,
            message=data.message,
        )

        # In production, queue email sending here
        # await self.email_queue.enqueue({
        #     "template": "invitation_default",
        #     "to": email,
        #     "contractId": data.contractId,
        #     "signUrl": f"https://app.contractify.co/sign/{data.contractId}?token=...",
        # })

        return SendInvitationResponse(
            invitationId=invitation.id,
            sentAt=invitation.sent_at,
        )

    async def cancel_invitation(
        self,
        invitation_id: str,
        current_user: CurrentUser,
    ) -> None:
        """Cancel pending invitation."""
        cancelled = await self.invitation_repo.cancel(invitation_id)
        if not cancelled:
            raise NotFoundException(f"Invitation {invitation_id} not found or already cancelled")

    async def resend_invitation(
        self,
        invitation_id: str,
        current_user: CurrentUser,
    ) -> SendInvitationResponse:
        """Resend invitation."""
        invitation = await self.invitation_repo.resend(invitation_id)
        if not invitation:
            raise NotFoundException(f"Invitation {invitation_id} not found")

        # In production, queue email sending here

        return SendInvitationResponse(
            invitationId=invitation.id,
            sentAt=invitation.sent_at,
        )

    def get_templates(self) -> List[NotificationTemplate]:
        """Get available email templates."""
        return EMAIL_TEMPLATES.copy()

    async def schedule_reminder(
        self,
        current_user: CurrentUser,
        data: ReminderRequest,
    ) -> dict:
        """Schedule reminder for unsigned contract."""
        reminder = await self.reminder_repo.create(
            contract_id=data.contractId,
            party_id=data.partyId,
            scheduled_at=data.scheduleAt,
            created_by=current_user.id,
        )

        # In production, this would be picked up by a scheduled job

        return {
            "reminderId": reminder.id,
            "scheduledAt": reminder.scheduled_at.isoformat(),
        }
