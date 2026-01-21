"""Audit module - API routes matching OpenAPI spec."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.db import get_db

from .schemas import AuditTrail
from .service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


def get_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    """Get audit service instance."""
    return AuditService(db)


@router.get("/contracts/{contractId}/trail", response_model=AuditTrail)
async def get_audit_trail(
    contractId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: AuditService = Depends(get_service),
) -> AuditTrail:
    """
    Get complete audit trail for contract.

    GET /audit/contracts/{contractId}/trail
    """
    return await service.get_trail(contractId, current_user)


@router.get("/contracts/{contractId}/export")
async def export_audit_trail(
    contractId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: AuditService = Depends(get_service),
) -> Response:
    """
    Export audit trail as PDF.

    GET /audit/contracts/{contractId}/export
    """
    pdf_bytes = await service.export_trail(contractId, current_user)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=audit_{contractId}.pdf"
        },
    )
