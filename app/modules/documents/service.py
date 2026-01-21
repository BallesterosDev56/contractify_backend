"""Documents module - Business logic service for PDF generation."""

import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.shared.exceptions import NotFoundException

from app.modules.ai.models import AsyncJob
from app.modules.ai.repository import AsyncJobRepository

from .schemas import (
    AsyncJobResponse,
    AsyncJobStatus,
    DocumentVerification,
    GeneratePDFRequest,
    JobStatus,
    SignatureVerification,
)

# Mock document storage (in production would be Azure Blob)
MOCK_DOCUMENTS: Dict[str, Dict[str, Any]] = {}


class DocumentService:
    """Service for document operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_repo = AsyncJobRepository(db)

    def _generate_document_hash(self, content: str) -> str:
        """Generate SHA-256 hash of document content."""
        return hashlib.sha256(content.encode()).hexdigest()

    async def generate_pdf(
        self,
        current_user: CurrentUser,
        data: GeneratePDFRequest,
    ) -> AsyncJobResponse:
        """
        Start async PDF generation.

        Returns job ID for polling.
        """
        # Create job
        job = await self.job_repo.create(
            job_type="PDF_GENERATE",
            user_id=current_user.id,
            input_data={
                "contractId": data.contractId,
                "includeAuditPage": data.includeAuditPage,
            },
        )

        # In production, this would trigger a background task
        # For now, we simulate completion
        try:
            await self.job_repo.mark_processing(job.id)

            # Mock PDF generation result
            document_id = str(uuid4())
            document_hash = self._generate_document_hash(f"contract_{data.contractId}")

            # Store mock document
            MOCK_DOCUMENTS[document_id] = {
                "contractId": data.contractId,
                "hash": document_hash,
                "createdAt": datetime.utcnow().isoformat(),
                "createdBy": current_user.id,
            }

            await self.job_repo.mark_completed(
                job.id,
                {
                    "documentId": document_id,
                    "documentHash": document_hash,
                    "downloadUrl": f"/api/documents/{document_id}/download",
                },
            )
        except Exception as e:
            await self.job_repo.mark_failed(job.id, str(e))

        return AsyncJobResponse(
            jobId=job.id,
            status=JobStatus.PENDING,
            pollUrl=f"/api/documents/jobs/{job.id}",
        )

    async def get_job_status(self, job_id: str) -> AsyncJobStatus:
        """Get async job status."""
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundException(f"Job {job_id} not found")

        return AsyncJobStatus(
            jobId=job.id,
            status=JobStatus(job.status),
            progress=job.progress,
            result=job.result,
            error=job.error,
            createdAt=job.created_at,
            completedAt=job.completed_at,
        )

    async def download_document(
        self,
        document_id: str,
        version: Optional[str] = None,
    ) -> bytes:
        """
        Download document PDF.

        In production, this would fetch from Azure Blob Storage.
        """
        doc = MOCK_DOCUMENTS.get(document_id)
        if not doc:
            raise NotFoundException(f"Document {document_id} not found")

        # Return mock PDF content
        # In production, this would be actual PDF bytes
        mock_pdf = f"""
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
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Contract Document - ID: {document_id}) Tj
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
300
%%EOF
"""
        return mock_pdf.encode()

    async def verify_document(
        self,
        document_id: str,
    ) -> DocumentVerification:
        """
        Verify document integrity and signatures.

        In production, this would verify SHA-256 hash and PAdES signatures.
        """
        doc = MOCK_DOCUMENTS.get(document_id)
        if not doc:
            raise NotFoundException(f"Document {document_id} not found")

        # Mock verification
        return DocumentVerification(
            valid=True,
            documentHash=doc.get("hash"),
            signatures=[],  # Would include actual signature verifications
            verifiedAt=datetime.utcnow(),
        )
