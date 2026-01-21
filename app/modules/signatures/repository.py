"""Signatures module - Database repository."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Signature, SignatureToken


class SignatureRepository:
    """Repository for signature data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, signature_id: str) -> Optional[Signature]:
        """Get signature by ID."""
        result = await self.db.execute(
            select(Signature).where(Signature.id == signature_id)
        )
        return result.scalar_one_or_none()

    async def get_by_contract(self, contract_id: str) -> List[Signature]:
        """Get all signatures for a contract."""
        result = await self.db.execute(
            select(Signature)
            .where(Signature.contract_id == contract_id)
            .order_by(Signature.signed_at)
        )
        return list(result.scalars().all())

    async def create(
        self,
        contract_id: str,
        party_id: str,
        party_name: Optional[str] = None,
        role: Optional[str] = None,
        document_hash: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        geolocation: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Signature:
        """Create new signature."""
        signature = Signature(
            contract_id=contract_id,
            party_id=party_id,
            party_name=party_name,
            role=role,
            document_hash=document_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            geolocation=geolocation,
            evidence=evidence or {},
        )
        self.db.add(signature)
        await self.db.flush()
        return signature

    async def update_evidence(
        self,
        signature_id: str,
        evidence: Dict[str, Any],
    ) -> Optional[Signature]:
        """Update signature evidence."""
        sig = await self.get_by_id(signature_id)
        if sig:
            merged = {**sig.evidence, **evidence}
            await self.db.execute(
                update(Signature)
                .where(Signature.id == signature_id)
                .values(evidence=merged)
            )
            await self.db.flush()
            return await self.get_by_id(signature_id)
        return None


class SignatureTokenRepository:
    """Repository for signature tokens."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_token(self, token: str) -> Optional[SignatureToken]:
        """Get token record by token string."""
        result = await self.db.execute(
            select(SignatureToken).where(SignatureToken.token == token)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        token: str,
        contract_id: str,
        party_id: str,
        expires_at: datetime,
    ) -> SignatureToken:
        """Create new signature token."""
        token_record = SignatureToken(
            token=token,
            contract_id=contract_id,
            party_id=party_id,
            expires_at=expires_at,
        )
        self.db.add(token_record)
        await self.db.flush()
        return token_record

    async def mark_used(self, token: str) -> bool:
        """Mark token as used."""
        result = await self.db.execute(
            update(SignatureToken)
            .where(
                SignatureToken.token == token,
                SignatureToken.used == False,
            )
            .values(used=True, used_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def validate(self, token: str) -> Optional[SignatureToken]:
        """Validate token and return if valid."""
        token_record = await self.get_by_token(token)
        if not token_record:
            return None
        if token_record.used:
            return None
        if token_record.expires_at < datetime.utcnow():
            return None
        return token_record
