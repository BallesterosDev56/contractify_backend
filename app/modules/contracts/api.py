"""Contracts module - API routes matching OpenAPI spec."""

from datetime import date
from io import BytesIO
from typing import Annotated, List, Optional
from zipfile import ZipFile

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, get_optional_user
from app.core.db import get_db

from .schemas import (
    ActivityLog,
    AddPartyRequest,
    BulkDownloadRequest,
    Contract,
    ContractDetail,
    ContractListResponse,
    ContractParty,
    ContractStats,
    ContractVersion,
    CreateContractRequest,
    PublicContractView,
    TransitionsResponse,
    UpdateContractRequest,
    UpdateContentRequest,
    UpdateStatusRequest,
)
from .service import ContractService

router = APIRouter(prefix="/contracts", tags=["Contracts"])


def get_service(db: AsyncSession = Depends(get_db)) -> ContractService:
    """Get contract service instance."""
    return ContractService(db)


# ============== List & Stats ==============


@router.get("", response_model=ContractListResponse)
async def list_contracts(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    templateId: Optional[str] = Query(None),
    fromDate: Optional[date] = Query(None),
    toDate: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    sortBy: str = Query("createdAt"),
    sortOrder: str = Query("desc"),
) -> ContractListResponse:
    """
    List contracts with filters and pagination.

    GET /contracts
    """
    return await service.list_contracts(
        current_user=current_user,
        status=status,
        search=search,
        template_id=templateId,
        from_date=fromDate,
        to_date=toDate,
        page=page,
        page_size=pageSize,
        sort_by=sortBy,
        sort_order=sortOrder,
    )


@router.get("/stats", response_model=ContractStats)
async def get_contract_stats(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> ContractStats:
    """
    Get contract statistics for dashboard.

    GET /contracts/stats
    """
    return await service.get_stats(current_user)


@router.get("/recent", response_model=List[Contract])
async def get_recent_contracts(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> List[Contract]:
    """
    Get recent contracts (last 10).

    GET /contracts/recent
    """
    return await service.get_recent(current_user)


@router.get("/pending", response_model=List[Contract])
async def get_pending_contracts(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> List[Contract]:
    """
    Get contracts pending user action.

    GET /contracts/pending
    """
    return await service.get_pending(current_user)


# ============== CRUD ==============


@router.post("", response_model=Contract, status_code=status.HTTP_201_CREATED)
async def create_contract(
    data: CreateContractRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> Contract:
    """
    Create new contract.

    POST /contracts
    """
    return await service.create_contract(current_user, data)


@router.get("/{contractId}", response_model=ContractDetail)
async def get_contract(
    contractId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> ContractDetail:
    """
    Get contract details.

    GET /contracts/{contractId}
    """
    return await service.get_contract(contractId, current_user)


@router.patch("/{contractId}", response_model=Contract)
async def update_contract(
    contractId: str,
    data: UpdateContractRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> Contract:
    """
    Update contract metadata_.

    PATCH /contracts/{contractId}
    """
    return await service.update_contract(contractId, current_user, data)


@router.delete("/{contractId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contractId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> None:
    """
    Delete contract (soft delete).

    DELETE /contracts/{contractId}
    """
    await service.delete_contract(contractId, current_user)


@router.post("/{contractId}/duplicate", response_model=Contract, status_code=status.HTTP_201_CREATED)
async def duplicate_contract(
    contractId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> Contract:
    """
    Duplicate contract as new draft.

    POST /contracts/{contractId}/duplicate
    """
    return await service.duplicate_contract(contractId, current_user)


# ============== Content & Versions ==============


@router.patch("/{contractId}/content", status_code=status.HTTP_200_OK)
async def update_contract_content(
    contractId: str,
    data: UpdateContentRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> dict:
    """
    Update contract content.

    PATCH /contracts/{contractId}/content
    """
    await service.update_content(contractId, current_user, data)
    return {"success": True}


@router.get("/{contractId}/versions", response_model=List[ContractVersion])
async def get_contract_versions(
    contractId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> List[ContractVersion]:
    """
    Get contract version history.

    GET /contracts/{contractId}/versions
    """
    return await service.get_versions(contractId, current_user)


# ============== Status ==============


@router.patch("/{contractId}/status", status_code=status.HTTP_200_OK)
async def update_contract_status(
    contractId: str,
    data: UpdateStatusRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> dict:
    """
    Update contract status.

    PATCH /contracts/{contractId}/status
    """
    await service.update_status(contractId, current_user, data)
    return {"success": True}


@router.get("/{contractId}/transitions", response_model=TransitionsResponse)
async def get_contract_transitions(
    contractId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> TransitionsResponse:
    """
    Get valid status transitions for current state.

    GET /contracts/{contractId}/transitions
    """
    return await service.get_transitions(contractId, current_user)


# ============== History ==============


@router.get("/{contractId}/history", response_model=List[ActivityLog])
async def get_contract_history(
    contractId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> List[ActivityLog]:
    """
    Get contract activity history.

    GET /contracts/{contractId}/history
    """
    return await service.get_history(contractId, current_user)


# ============== Parties ==============


@router.get("/{contractId}/parties", response_model=List[ContractParty])
async def get_contract_parties(
    contractId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> List[ContractParty]:
    """
    Get contract parties/signers.

    GET /contracts/{contractId}/parties
    """
    return await service.get_parties(contractId, current_user)


@router.post("/{contractId}/parties", status_code=status.HTTP_201_CREATED)
async def add_contract_party(
    contractId: str,
    data: AddPartyRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> ContractParty:
    """
    Add party to contract.

    POST /contracts/{contractId}/parties
    """
    return await service.add_party(contractId, current_user, data)


@router.delete("/{contractId}/parties/{partyId}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contract_party(
    contractId: str,
    partyId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> None:
    """
    Remove party from unsigned contract.

    DELETE /contracts/{contractId}/parties/{partyId}
    """
    await service.remove_party(contractId, partyId, current_user)


# ============== Public ==============


@router.get("/{contractId}/public", response_model=PublicContractView)
async def get_public_contract(
    contractId: str,
    token: str = Query(...),
    service: ContractService = Depends(get_service),
) -> PublicContractView:
    """
    Get public view of contract (for guest signing).

    GET /contracts/{contractId}/public
    """
    return await service.get_public_view(contractId, token)


# ============== Bulk Operations ==============


@router.post("/bulk-download")
async def bulk_download_contracts(
    data: BulkDownloadRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: ContractService = Depends(get_service),
) -> StreamingResponse:
    """
    Download multiple contracts as ZIP.

    POST /contracts/bulk-download
    """
    # Create ZIP file in memory
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zip_file:
        for contract_id in data.contractIds:
            try:
                contract = await service.get_contract(contract_id, current_user)
                # Add contract content as HTML file
                content = contract.content or ""
                filename = f"{contract.title.replace('/', '-')[:50]}_{contract_id[:8]}.html"
                zip_file.writestr(filename, content)
            except Exception:
                # Skip contracts that can't be accessed
                continue

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=contracts.zip"},
    )
