"""Documents module - API routes matching OpenAPI spec."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.db import get_db

from .schemas import (
    AsyncJobResponse,
    AsyncJobStatus,
    DocumentVerification,
    GeneratePDFRequest,
)
from .service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Get document service instance."""
    return DocumentService(db)


@router.post("/generate-pdf", response_model=AsyncJobResponse, status_code=202)
async def generate_pdf(
    data: GeneratePDFRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: DocumentService = Depends(get_service),
) -> AsyncJobResponse:
    """
    Generate PDF from contract content.

    POST /documents/generate-pdf

    Returns 202 with job ID for polling.
    """
    return await service.generate_pdf(current_user, data)


@router.get("/{documentId}/download")
async def download_document(
    documentId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    version: Optional[str] = Query(None),
    service: DocumentService = Depends(get_service),
) -> Response:
    """
    Download contract PDF.

    GET /documents/{documentId}/download
    """
    pdf_bytes = await service.download_document(documentId, version)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=contract_{documentId}.pdf"
        },
    )


@router.post("/{documentId}/verify", response_model=DocumentVerification)
async def verify_document(
    documentId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: DocumentService = Depends(get_service),
) -> DocumentVerification:
    """
    Verify PDF integrity and signatures.

    POST /documents/{documentId}/verify
    """
    return await service.verify_document(documentId)


@router.get("/jobs/{jobId}", response_model=AsyncJobStatus)
async def get_job_status(
    jobId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: DocumentService = Depends(get_service),
) -> AsyncJobStatus:
    """
    Poll PDF generation job status.

    GET /documents/jobs/{jobId}
    """
    return await service.get_job_status(jobId)
