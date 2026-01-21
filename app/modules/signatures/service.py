"""Signatures module - Business logic service."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.config import settings
from app.shared.exceptions import BadRequestException, ConflictException, NotFoundException

from .models import Signature as SignatureModel
from .repository import SignatureRepository, SignatureTokenRepository
from .schemas import (
    CreateTokenRequest,
    GuestSignRequest,
    Signature,
    SignatureEvidence,
    SignatureResponse,
    SignatureTokenResponse,
    SignRequest,
    ValidateTokenResponse,
)


class SignatureService:
    """Service for signature operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sig_repo = SignatureRepository(db)
        self.token_repo = SignatureTokenRepository(db)

    def _generate_token(self) -> str:
        """Generate secure random token."""
        return secrets.token_urlsafe(32)

    def _generate_document_hash(self, contract_id: str, party_id: str) -> str:
        """Generate document hash for signature."""
        data = f"{contract_id}:{party_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _to_schema(self, sig: SignatureModel) -> Signature:
        """Convert model to schema."""
        return Signature(
            id=sig.id,
            partyId=sig.party_id,
            partyName=sig.party_name,
            role=sig.role,
            signedAt=sig.signed_at,
            ipAddress=sig.ip_address,
            documentHash=sig.document_hash,
        )

    async def create_token(
        self,
        current_user: CurrentUser,
        data: CreateTokenRequest,
    ) -> SignatureTokenResponse:
        """Create signature token for party."""
        token = self._generate_token()
        expires_at = datetime.utcnow() + timedelta(minutes=data.expiresInMinutes)

        await self.token_repo.create(
            token=token,
            contract_id=data.contractId,
            party_id=data.partyId,
            expires_at=expires_at,
        )

        # Build sign URL
        base_url = "http://localhost:5173"  # Frontend URL
        sign_url = f"{base_url}/sign/{data.contractId}?token={token}"

        return SignatureTokenResponse(
            token=token,
            signUrl=sign_url,
            expiresAt=expires_at,
        )

    async def validate_token(self, token: str) -> ValidateTokenResponse:
        """Validate signature token."""
        token_record = await self.token_repo.validate(token)

        if not token_record:
            return ValidateTokenResponse(valid=False)

        return ValidateTokenResponse(
            valid=True,
            contractId=token_record.contract_id,
            partyId=token_record.party_id,
            expiresAt=token_record.expires_at,
        )

    async def sign(
        self,
        current_user: CurrentUser,
        data: SignRequest,
    ) -> SignatureResponse:
        """Sign contract as authenticated user."""
        # Generate document hash
        document_hash = self._generate_document_hash(data.contractId, data.partyId)

        # Extract evidence
        evidence_dict = {}
        ip_address = None
        user_agent = None
        geolocation = None

        if data.evidence:
            ip_address = data.evidence.ipAddress
            user_agent = data.evidence.userAgent
            geolocation = data.evidence.geolocation
            evidence_dict = {
                "ipAddress": ip_address,
                "userAgent": user_agent,
                "geolocation": geolocation,
                "signedAt": datetime.utcnow().isoformat(),
                "signedBy": current_user.email,
            }

        # Create signature
        signature = await self.sig_repo.create(
            contract_id=data.contractId,
            party_id=data.partyId,
            party_name=current_user.name or current_user.email,
            document_hash=document_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            geolocation=geolocation,
            evidence=evidence_dict,
        )

        return SignatureResponse(
            signatureId=signature.id,
            documentHash=document_hash,
            signedAt=signature.signed_at,
            certificateUrl=f"/api/signatures/{signature.id}/certificate",
        )

    async def sign_guest(
        self,
        data: GuestSignRequest,
    ) -> SignatureResponse:
        """Sign contract as guest using token."""
        # Validate token
        token_record = await self.token_repo.validate(data.token)
        if not token_record:
            raise BadRequestException("Invalid or expired token")

        # Generate document hash
        document_hash = self._generate_document_hash(
            token_record.contract_id,
            token_record.party_id,
        )

        # Extract evidence
        evidence_dict = {"signedAt": datetime.utcnow().isoformat()}
        ip_address = None
        user_agent = None
        geolocation = None

        if data.evidence:
            ip_address = data.evidence.ipAddress
            user_agent = data.evidence.userAgent
            geolocation = data.evidence.geolocation
            evidence_dict.update({
                "ipAddress": ip_address,
                "userAgent": user_agent,
                "geolocation": geolocation,
            })

        # Create signature
        signature = await self.sig_repo.create(
            contract_id=token_record.contract_id,
            party_id=token_record.party_id,
            document_hash=document_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            geolocation=geolocation,
            evidence=evidence_dict,
        )

        # Mark token as used
        await self.token_repo.mark_used(data.token)

        return SignatureResponse(
            signatureId=signature.id,
            documentHash=document_hash,
            signedAt=signature.signed_at,
            certificateUrl=f"/api/signatures/{signature.id}/certificate",
        )

    async def get_contract_signatures(
        self,
        contract_id: str,
        current_user: CurrentUser,
    ) -> List[Signature]:
        """Get all signatures for a contract."""
        signatures = await self.sig_repo.get_by_contract(contract_id)
        return [self._to_schema(s) for s in signatures]

    async def store_evidence(
        self,
        signature_id: str,
        evidence: SignatureEvidence,
        current_user: CurrentUser,
    ) -> None:
        """Store additional signature evidence."""
        sig = await self.sig_repo.get_by_id(signature_id)
        if not sig:
            raise NotFoundException(f"Signature {signature_id} not found")

        evidence_dict = {
            "ipAddress": evidence.ipAddress,
            "userAgent": evidence.userAgent,
            "geolocation": evidence.geolocation,
            "signedAt": evidence.signedAt.isoformat() if evidence.signedAt else None,
            "storedBy": current_user.email,
            "storedAt": datetime.utcnow().isoformat(),
        }

        await self.sig_repo.update_evidence(signature_id, evidence_dict)

    async def get_certificate(self, signature_id: str) -> bytes:
        """
        Get signature certificate PDF.

        In production, this would generate a proper certificate.
        """
        sig = await self.sig_repo.get_by_id(signature_id)
        if not sig:
            raise NotFoundException(f"Signature {signature_id} not found")

        # Mock certificate PDF
        certificate = f"""
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
<< /Length 200 >>
stream
BT
/F1 16 Tf
100 700 Td
(SIGNATURE CERTIFICATE) Tj
0 -30 Td
/F1 12 Tf
(Signature ID: {sig.id}) Tj
0 -20 Td
(Document Hash: {sig.document_hash}) Tj
0 -20 Td
(Signed At: {sig.signed_at.isoformat() if sig.signed_at else 'N/A'}) Tj
0 -20 Td
(Party: {sig.party_name or 'N/A'}) Tj
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
500
%%EOF
"""
        return certificate.encode()
