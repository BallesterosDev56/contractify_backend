"""Contracts module - Business logic service."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.shared.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)

from .models import Contract, ContractParty, ContractVersion, ActivityLog
from .repository import (
    ActivityLogRepository,
    ContractPartyRepository,
    ContractRepository,
    ContractVersionRepository,
)
from .schemas import (
    ActivityLog as ActivityLogSchema,
    AddPartyRequest,
    Contract as ContractSchema,
    ContractDetail,
    ContractListResponse,
    ContractParty as ContractPartySchema,
    ContractStats,
    ContractStatus,
    ContractVersion as ContractVersionSchema,
    CreateContractRequest,
    Pagination,
    PublicContractView,
    Signature,
    TransitionsResponse,
    UpdateContractRequest,
    UpdateContentRequest,
    UpdateStatusRequest,
)

# Valid status transitions
STATUS_TRANSITIONS = {
    "DRAFT": ["GENERATED", "CANCELLED"],
    "GENERATED": ["DRAFT", "SIGNING", "CANCELLED"],
    "SIGNING": ["SIGNED", "CANCELLED", "EXPIRED"],
    "SIGNED": [],  # Terminal state
    "CANCELLED": [],  # Terminal state
    "EXPIRED": [],  # Terminal state
}


class ContractService:
    """Service for contract operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.contract_repo = ContractRepository(db)
        self.version_repo = ContractVersionRepository(db)
        self.party_repo = ContractPartyRepository(db)
        self.activity_repo = ActivityLogRepository(db)

    def _to_schema(self, contract: Contract) -> ContractSchema:
        """Convert model to schema."""
        return ContractSchema(
            id=contract.id,
            title=contract.title,
            status=ContractStatus(contract.status),
            templateId=contract.template_id,
            contractType=contract.contract_type,
            ownerUserId=contract.owner_user_id,
            createdAt=contract.created_at,
            updatedAt=contract.updated_at,
            signedAt=contract.signed_at,
        )

    def _to_detail_schema(self, contract: Contract) -> ContractDetail:
        """Convert model to detail schema."""
        # Get latest version content
        content = None
        if contract.versions:
            latest = max(contract.versions, key=lambda v: v.version)
            content = latest.content

        parties = [
            ContractPartySchema(
                id=p.id,
                role=p.role,
                name=p.name,
                email=p.email,
                signatureStatus=p.signature_status,
                signedAt=p.signed_at,
                order=p.signing_order,
            )
            for p in contract.parties
        ]

        return ContractDetail(
            id=contract.id,
            title=contract.title,
            status=ContractStatus(contract.status),
            templateId=contract.template_id,
            contractType=contract.contract_type,
            ownerUserId=contract.owner_user_id,
            createdAt=contract.created_at,
            updatedAt=contract.updated_at,
            signedAt=contract.signed_at,
            content=content,
            parties=parties,
            signatures=[],  # Signatures come from signatures module
            documentUrl=contract.metadata.get("documentUrl"),
            documentHash=contract.metadata.get("documentHash"),
        )

    async def _check_ownership(
        self,
        contract: Contract,
        current_user: CurrentUser,
    ) -> None:
        """Check if user owns the contract."""
        if contract.owner_user_id != current_user.id:
            raise ForbiddenException("You do not have access to this contract")

    async def _log_activity(
        self,
        contract_id: str,
        action: str,
        user: CurrentUser,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log activity."""
        await self.activity_repo.create(
            contract_id=contract_id,
            action=action,
            user_id=user.id,
            user_name=user.name or user.email,
            details=details,
        )

    # ============== Contract CRUD ==============

    async def list_contracts(
        self,
        current_user: CurrentUser,
        status: Optional[str] = None,
        search: Optional[str] = None,
        template_id: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
    ) -> ContractListResponse:
        """List contracts with filters and pagination."""
        contracts, total = await self.contract_repo.list_contracts(
            owner_user_id=current_user.id,
            status=status,
            search=search,
            template_id=template_id,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        total_pages = (total + page_size - 1) // page_size

        return ContractListResponse(
            data=[self._to_schema(c) for c in contracts],
            pagination=Pagination(
                page=page,
                pageSize=page_size,
                totalPages=total_pages,
                totalItems=total,
            ),
        )

    async def create_contract(
        self,
        current_user: CurrentUser,
        data: CreateContractRequest,
    ) -> ContractSchema:
        """Create a new contract."""
        contract = await self.contract_repo.create(
            title=data.title,
            template_id=data.templateId,
            contract_type=data.contractType,
            owner_user_id=current_user.id,
        )

        await self._log_activity(contract.id, "CREATED", current_user)

        return self._to_schema(contract)

    async def get_contract(
        self,
        contract_id: str,
        current_user: CurrentUser,
    ) -> ContractDetail:
        """Get contract details."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        return self._to_detail_schema(contract)

    async def update_contract(
        self,
        contract_id: str,
        current_user: CurrentUser,
        data: UpdateContractRequest,
    ) -> ContractSchema:
        """Update contract metadata."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        updates = {}
        if data.title is not None:
            updates["title"] = data.title

        if updates:
            contract = await self.contract_repo.update(contract_id, **updates)
            await self._log_activity(
                contract_id, "UPDATED", current_user, {"fields": list(updates.keys())}
            )

        return self._to_schema(contract)  # type: ignore

    async def delete_contract(
        self,
        contract_id: str,
        current_user: CurrentUser,
    ) -> None:
        """Soft delete a contract."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        if contract.status == "SIGNED":
            raise ConflictException("Cannot delete signed contract")

        await self.contract_repo.soft_delete(contract_id)

    async def duplicate_contract(
        self,
        contract_id: str,
        current_user: CurrentUser,
    ) -> ContractSchema:
        """Duplicate a contract as new draft."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        new_contract = await self.contract_repo.duplicate(contract_id, current_user.id)
        if not new_contract:
            raise NotFoundException("Failed to duplicate contract")

        await self._log_activity(
            new_contract.id, "CREATED", current_user, {"duplicatedFrom": contract_id}
        )

        return self._to_schema(new_contract)

    # ============== Content & Versions ==============

    async def update_content(
        self,
        contract_id: str,
        current_user: CurrentUser,
        data: UpdateContentRequest,
    ) -> None:
        """Update contract content (creates new version)."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        if contract.status in ["SIGNED", "CANCELLED", "EXPIRED"]:
            raise ConflictException(f"Cannot update content of {contract.status} contract")

        await self.version_repo.create(
            contract_id=contract_id,
            content=data.content,
            source=data.source.value if data.source else "USER",
            created_by=current_user.id,
        )

        # Update status to GENERATED if was DRAFT and content added via AI
        if contract.status == "DRAFT" and data.source and data.source.value == "AI":
            await self.contract_repo.update(contract_id, status="GENERATED")
            await self._log_activity(
                contract_id, "GENERATED", current_user
            )
        else:
            await self._log_activity(
                contract_id, "UPDATED", current_user, {"field": "content"}
            )

    async def get_versions(
        self,
        contract_id: str,
        current_user: CurrentUser,
    ) -> List[ContractVersionSchema]:
        """Get contract version history."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        versions = await self.version_repo.get_all(contract_id)
        return [
            ContractVersionSchema(
                version=v.version,
                content=v.content,
                source=v.source,
                createdAt=v.created_at,
                createdBy=v.created_by,
            )
            for v in versions
        ]

    # ============== Status ==============

    async def update_status(
        self,
        contract_id: str,
        current_user: CurrentUser,
        data: UpdateStatusRequest,
    ) -> None:
        """Update contract status."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        new_status = data.status.value
        allowed = STATUS_TRANSITIONS.get(contract.status, [])

        if new_status not in allowed:
            raise BadRequestException(
                f"Cannot transition from {contract.status} to {new_status}"
            )

        if new_status == "CANCELLED" and not data.reason:
            raise BadRequestException("Reason required for cancellation")

        updates: Dict[str, Any] = {"status": new_status}
        if new_status == "SIGNED":
            updates["signed_at"] = datetime.utcnow()

        await self.contract_repo.update(contract_id, **updates)

        action = "CANCELLED" if new_status == "CANCELLED" else "UPDATED"
        await self._log_activity(
            contract_id,
            action,
            current_user,
            {"oldStatus": contract.status, "newStatus": new_status, "reason": data.reason},
        )

    async def get_transitions(
        self,
        contract_id: str,
        current_user: CurrentUser,
    ) -> TransitionsResponse:
        """Get valid status transitions."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        return TransitionsResponse(
            currentStatus=contract.status,
            allowedTransitions=STATUS_TRANSITIONS.get(contract.status, []),
        )

    # ============== Activity History ==============

    async def get_history(
        self,
        contract_id: str,
        current_user: CurrentUser,
    ) -> List[ActivityLogSchema]:
        """Get contract activity history."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        logs = await self.activity_repo.get_all(contract_id)
        return [
            ActivityLogSchema(
                id=log.id,
                action=log.action,
                userId=log.user_id,
                userName=log.user_name,
                details=log.details,
                timestamp=log.timestamp,
            )
            for log in logs
        ]

    # ============== Stats & Lists ==============

    async def get_stats(self, current_user: CurrentUser) -> ContractStats:
        """Get contract statistics for dashboard."""
        stats = await self.contract_repo.get_stats(current_user.id)
        return ContractStats(**stats)

    async def get_recent(self, current_user: CurrentUser) -> List[ContractSchema]:
        """Get recent contracts."""
        contracts = await self.contract_repo.get_recent(current_user.id)
        return [self._to_schema(c) for c in contracts]

    async def get_pending(self, current_user: CurrentUser) -> List[ContractSchema]:
        """Get contracts pending user action."""
        contracts = await self.contract_repo.get_pending(current_user.id)
        return [self._to_schema(c) for c in contracts]

    # ============== Parties ==============

    async def get_parties(
        self,
        contract_id: str,
        current_user: CurrentUser,
    ) -> List[ContractPartySchema]:
        """Get contract parties."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        parties = await self.party_repo.get_all(contract_id)
        return [
            ContractPartySchema(
                id=p.id,
                role=p.role,
                name=p.name,
                email=p.email,
                signatureStatus=p.signature_status,
                signedAt=p.signed_at,
                order=p.signing_order,
            )
            for p in parties
        ]

    async def add_party(
        self,
        contract_id: str,
        current_user: CurrentUser,
        data: AddPartyRequest,
    ) -> ContractPartySchema:
        """Add party to contract."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        if contract.status in ["SIGNED", "CANCELLED", "EXPIRED"]:
            raise ConflictException(f"Cannot add party to {contract.status} contract")

        party = await self.party_repo.create(
            contract_id=contract_id,
            role=data.role.value,
            name=data.name,
            email=data.email,
            order=data.order or 1,
        )

        return ContractPartySchema(
            id=party.id,
            role=party.role,
            name=party.name,
            email=party.email,
            signatureStatus=party.signature_status,
            signedAt=party.signed_at,
            order=party.signing_order,
        )

    async def remove_party(
        self,
        contract_id: str,
        party_id: str,
        current_user: CurrentUser,
    ) -> None:
        """Remove party from contract."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        await self._check_ownership(contract, current_user)

        party = await self.party_repo.get_by_id(party_id)
        if not party or party.contract_id != contract_id:
            raise NotFoundException("Party not found")

        if party.signature_status == "SIGNED":
            raise ConflictException("Cannot remove party that has already signed")

        await self.party_repo.delete(party_id, contract_id)

    # ============== Public View ==============

    async def get_public_view(
        self,
        contract_id: str,
        token: str,
    ) -> PublicContractView:
        """Get public contract view for guest signing."""
        # Token validation would be handled by signatures module
        # For now, just return basic contract info
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise NotFoundException("Contract not found")

        # Get content from latest version
        content = None
        if contract.versions:
            latest = max(contract.versions, key=lambda v: v.version)
            content = latest.content

        return PublicContractView(
            id=contract.id,
            title=contract.title,
            content=content,
            documentUrl=contract.metadata.get("documentUrl"),
        )
