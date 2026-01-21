"""Contracts module - Database repository."""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import ActivityLog, Contract, ContractParty, ContractVersion


class ContractRepository:
    """Repository for contract data operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        contract_id: str,
        include_deleted: bool = False,
    ) -> Optional[Contract]:
        """Get contract by ID with relationships."""
        query = (
            select(Contract)
            .options(
                selectinload(Contract.versions),
                selectinload(Contract.parties),
            )
            .where(Contract.id == contract_id)
        )
        if not include_deleted:
            query = query.where(Contract.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_contracts(
        self,
        owner_user_id: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
        template_id: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
    ) -> Tuple[List[Contract], int]:
        """List contracts with filters and pagination."""
        # Base query
        query = select(Contract).where(
            Contract.owner_user_id == owner_user_id,
            Contract.deleted_at.is_(None),
        )

        # Apply filters
        if status:
            query = query.where(Contract.status == status)
        if search:
            query = query.where(
                or_(
                    Contract.title.ilike(f"%{search}%"),
                    Contract.contract_type.ilike(f"%{search}%"),
                )
            )
        if template_id:
            query = query.where(Contract.template_id == template_id)
        if from_date:
            query = query.where(Contract.created_at >= from_date)
        if to_date:
            query = query.where(Contract.created_at <= to_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Sort
        sort_column = {
            "createdAt": Contract.created_at,
            "updatedAt": Contract.updated_at,
            "title": Contract.title,
            "status": Contract.status,
        }.get(sort_by, Contract.created_at)

        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        contracts = list(result.scalars().all())

        return contracts, total

    async def create(
        self,
        title: str,
        template_id: str,
        contract_type: str,
        owner_user_id: str,
    ) -> Contract:
        """Create a new contract."""
        contract = Contract(
            title=title,
            template_id=template_id,
            contract_type=contract_type,
            owner_user_id=owner_user_id,
            status="DRAFT",
        )
        self.db.add(contract)
        await self.db.flush()
        return contract

    async def update(
        self,
        contract_id: str,
        **kwargs: Any,
    ) -> Optional[Contract]:
        """Update contract fields."""
        # Filter out None values
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if updates:
            await self.db.execute(
                update(Contract).where(Contract.id == contract_id).values(**updates)
            )
            await self.db.flush()
        return await self.get_by_id(contract_id)

    async def soft_delete(self, contract_id: str) -> bool:
        """Soft delete a contract."""
        result = await self.db.execute(
            update(Contract)
            .where(Contract.id == contract_id, Contract.deleted_at.is_(None))
            .values(deleted_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def get_stats(self, owner_user_id: str) -> Dict[str, Any]:
        """Get contract statistics."""
        # Total count
        total_query = select(func.count()).where(
            Contract.owner_user_id == owner_user_id,
            Contract.deleted_at.is_(None),
        )
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        # Count by status
        status_query = (
            select(Contract.status, func.count())
            .where(
                Contract.owner_user_id == owner_user_id,
                Contract.deleted_at.is_(None),
            )
            .group_by(Contract.status)
        )
        status_result = await self.db.execute(status_query)
        by_status = {row[0]: row[1] for row in status_result.all()}

        # Pending signatures (contracts in SIGNING status)
        pending = by_status.get("SIGNING", 0)

        # Signed this month
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        signed_query = select(func.count()).where(
            Contract.owner_user_id == owner_user_id,
            Contract.status == "SIGNED",
            Contract.signed_at >= start_of_month,
        )
        signed_result = await self.db.execute(signed_query)
        signed_this_month = signed_result.scalar() or 0

        return {
            "total": total,
            "byStatus": by_status,
            "pendingSignatures": pending,
            "signedThisMonth": signed_this_month,
        }

    async def get_recent(self, owner_user_id: str, limit: int = 10) -> List[Contract]:
        """Get recent contracts."""
        query = (
            select(Contract)
            .where(
                Contract.owner_user_id == owner_user_id,
                Contract.deleted_at.is_(None),
            )
            .order_by(Contract.updated_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_pending(self, owner_user_id: str) -> List[Contract]:
        """Get contracts pending user action."""
        query = (
            select(Contract)
            .where(
                Contract.owner_user_id == owner_user_id,
                Contract.deleted_at.is_(None),
                Contract.status.in_(["DRAFT", "GENERATED", "SIGNING"]),
            )
            .order_by(Contract.updated_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def duplicate(self, contract_id: str, owner_user_id: str) -> Optional[Contract]:
        """Duplicate a contract as new draft."""
        original = await self.get_by_id(contract_id)
        if not original:
            return None

        new_contract = Contract(
            title=f"{original.title} (Copy)",
            template_id=original.template_id,
            contract_type=original.contract_type,
            owner_user_id=owner_user_id,
            status="DRAFT",
            metadata=original.metadata.copy(),
        )
        self.db.add(new_contract)
        await self.db.flush()

        # Copy latest version content if exists
        if original.versions:
            latest = max(original.versions, key=lambda v: v.version)
            new_version = ContractVersion(
                contract_id=new_contract.id,
                version=1,
                content=latest.content,
                source="USER",
                created_by=owner_user_id,
            )
            self.db.add(new_version)
            await self.db.flush()

        return await self.get_by_id(new_contract.id)


class ContractVersionRepository:
    """Repository for contract versions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, contract_id: str) -> List[ContractVersion]:
        """Get all versions for a contract."""
        query = (
            select(ContractVersion)
            .where(ContractVersion.contract_id == contract_id)
            .order_by(ContractVersion.version.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest(self, contract_id: str) -> Optional[ContractVersion]:
        """Get latest version for a contract."""
        query = (
            select(ContractVersion)
            .where(ContractVersion.contract_id == contract_id)
            .order_by(ContractVersion.version.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        contract_id: str,
        content: str,
        source: str,
        created_by: str,
    ) -> ContractVersion:
        """Create new version."""
        # Get next version number
        latest = await self.get_latest(contract_id)
        next_version = (latest.version + 1) if latest else 1

        version = ContractVersion(
            contract_id=contract_id,
            version=next_version,
            content=content,
            source=source,
            created_by=created_by,
        )
        self.db.add(version)
        await self.db.flush()
        return version


class ContractPartyRepository:
    """Repository for contract parties."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, contract_id: str) -> List[ContractParty]:
        """Get all parties for a contract."""
        query = (
            select(ContractParty)
            .where(ContractParty.contract_id == contract_id)
            .order_by(ContractParty.signing_order)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, party_id: str) -> Optional[ContractParty]:
        """Get party by ID."""
        query = select(ContractParty).where(ContractParty.id == party_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        contract_id: str,
        role: str,
        name: str,
        email: str,
        order: int = 1,
    ) -> ContractParty:
        """Create new party."""
        party = ContractParty(
            contract_id=contract_id,
            role=role,
            name=name,
            email=email,
            signing_order=order,
        )
        self.db.add(party)
        await self.db.flush()
        return party

    async def delete(self, party_id: str, contract_id: str) -> bool:
        """Delete a party."""
        result = await self.db.execute(
            delete(ContractParty).where(
                ContractParty.id == party_id,
                ContractParty.contract_id == contract_id,
            )
        )
        return result.rowcount > 0

    async def update_status(
        self,
        party_id: str,
        status: str,
        signed_at: Optional[datetime] = None,
    ) -> Optional[ContractParty]:
        """Update party signature status."""
        updates: Dict[str, Any] = {"signature_status": status}
        if signed_at:
            updates["signed_at"] = signed_at

        await self.db.execute(
            update(ContractParty)
            .where(ContractParty.id == party_id)
            .values(**updates)
        )
        await self.db.flush()
        return await self.get_by_id(party_id)


class ActivityLogRepository:
    """Repository for activity logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, contract_id: str) -> List[ActivityLog]:
        """Get all activity logs for a contract."""
        query = (
            select(ActivityLog)
            .where(ActivityLog.contract_id == contract_id)
            .order_by(ActivityLog.timestamp.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        contract_id: str,
        action: str,
        user_id: str,
        user_name: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> ActivityLog:
        """Create new activity log entry."""
        log = ActivityLog(
            contract_id=contract_id,
            action=action,
            user_id=user_id,
            user_name=user_name,
            details=details or {},
        )
        self.db.add(log)
        await self.db.flush()
        return log
