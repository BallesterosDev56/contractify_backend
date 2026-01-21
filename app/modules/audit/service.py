"""Audit module - Business logic service."""

from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.shared.exceptions import NotFoundException

from .models import AuditLog
from .repository import AuditRepository
from .schemas import AuditEvent, AuditTrail


class AuditService:
    """Service for audit operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_repo = AuditRepository(db)

    def _to_event(self, log: AuditLog) -> AuditEvent:
        """Convert model to schema."""
        return AuditEvent(
            id=log.id,
            eventType=log.event_type,
            actor=log.actor,
            timestamp=log.timestamp,
            ipAddress=log.ip_address,
            details=log.details,
        )

    async def get_trail(
        self,
        contract_id: str,
        current_user: CurrentUser,
    ) -> AuditTrail:
        """Get complete audit trail for contract."""
        logs = await self.audit_repo.get_by_contract(contract_id)

        return AuditTrail(
            contractId=contract_id,
            events=[self._to_event(log) for log in logs],
            generatedAt=datetime.utcnow(),
        )

    async def export_trail(
        self,
        contract_id: str,
        current_user: CurrentUser,
    ) -> bytes:
        """Export audit trail as PDF."""
        logs = await self.audit_repo.get_by_contract(contract_id)

        # Build PDF content
        events_text = "\n".join([
            f"- {log.timestamp.isoformat()}: {log.event_type} by {log.actor or 'System'}"
            for log in logs
        ])

        # Mock PDF
        pdf_content = f"""
%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 500 >>
stream
BT
/F1 16 Tf
100 750 Td
(AUDIT TRAIL) Tj
0 -30 Td
/F1 12 Tf
(Contract ID: {contract_id}) Tj
0 -20 Td
(Generated: {datetime.utcnow().isoformat()}) Tj
0 -20 Td
(Total Events: {len(logs)}) Tj
0 -30 Td
/F1 10 Tf
(Events:) Tj
0 -15 Td
({events_text[:200]}...) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000206 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
800
%%EOF
"""
        return pdf_content.encode()

    async def log_event(
        self,
        contract_id: str,
        event_type: str,
        actor: str,
        ip_address: str = None,
        details: dict = None,
    ) -> None:
        """Log an audit event."""
        await self.audit_repo.create(
            contract_id=contract_id,
            event_type=event_type,
            actor=actor,
            ip_address=ip_address,
            details=details,
        )
