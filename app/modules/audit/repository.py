"""Audit module - Database repository."""

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog


class AuditRepository:
    """Repository for audit logs - append only."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_contract(self, contract_id: str) -> List[AuditLog]:
        """Get all audit logs for a contract."""
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.contract_id == contract_id)
            .order_by(AuditLog.timestamp.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        contract_id: str,
        event_type: str,
        actor: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create new audit log entry (append-only)."""
        log = AuditLog(
            contract_id=contract_id,
            event_type=event_type,
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )
        self.db.add(log)
        await self.db.flush()
        return log
