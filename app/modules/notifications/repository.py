"""Notifications module - Database repository."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Invitation, Reminder


class InvitationRepository:
    """Repository for invitations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, invitation_id: str) -> Optional[Invitation]:
        """Get invitation by ID."""
        result = await self.db.execute(
            select(Invitation).where(Invitation.id == invitation_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        contract_id: str,
        party_id: str,
        email: str,
        sent_by: str,
        message: Optional[str] = None,
    ) -> Invitation:
        """Create new invitation."""
        invitation = Invitation(
            contract_id=contract_id,
            party_id=party_id,
            email=email,
            message=message,
            sent_by=sent_by,
            status="SENT",
        )
        self.db.add(invitation)
        await self.db.flush()
        return invitation

    async def cancel(self, invitation_id: str) -> bool:
        """Cancel an invitation."""
        result = await self.db.execute(
            update(Invitation)
            .where(Invitation.id == invitation_id, Invitation.status == "SENT")
            .values(status="CANCELLED", cancelled_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def resend(self, invitation_id: str) -> Optional[Invitation]:
        """Resend an invitation."""
        await self.db.execute(
            update(Invitation)
            .where(Invitation.id == invitation_id)
            .values(status="RESENT", sent_at=datetime.utcnow())
        )
        await self.db.flush()
        return await self.get_by_id(invitation_id)


class ReminderRepository:
    """Repository for reminders."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        contract_id: str,
        party_id: str,
        scheduled_at: datetime,
        created_by: str,
    ) -> Reminder:
        """Create new reminder."""
        reminder = Reminder(
            contract_id=contract_id,
            party_id=party_id,
            scheduled_at=scheduled_at,
            created_by=created_by,
        )
        self.db.add(reminder)
        await self.db.flush()
        return reminder

    async def mark_sent(self, reminder_id: str) -> bool:
        """Mark reminder as sent."""
        result = await self.db.execute(
            update(Reminder)
            .where(Reminder.id == reminder_id, Reminder.sent == False)
            .values(sent=True, sent_at=datetime.utcnow())
        )
        return result.rowcount > 0
