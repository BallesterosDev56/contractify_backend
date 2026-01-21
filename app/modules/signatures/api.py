"""Signatures module - API routes matching OpenAPI spec."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.db import get_db

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
from .service import SignatureService

router = APIRouter(tags=["Signatures"])


def get_service(db: AsyncSession = Depends(get_db)) -> SignatureService:
    """Get signature service instance."""
    return SignatureService(db)


@router.post("/signatures/create-token", response_model=SignatureTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_token(
    data: CreateTokenRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: SignatureService = Depends(get_service),
) -> SignatureTokenResponse:
    """
    Create signature token for party.

    POST /signatures/create-token
    """
    return await service.create_token(current_user, data)


@router.get("/signatures/validate-token", response_model=ValidateTokenResponse)
async def validate_token(
    token: str = Query(...),
    service: SignatureService = Depends(get_service),
) -> ValidateTokenResponse:
    """
    Validate signature token (public endpoint).

    GET /signatures/validate-token
    """
    return await service.validate_token(token)


@router.post("/signatures/sign", response_model=SignatureResponse)
async def sign_contract(
    data: SignRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: SignatureService = Depends(get_service),
) -> SignatureResponse:
    """
    Sign contract (authenticated user).

    POST /signatures/sign
    """
    return await service.sign(current_user, data)


@router.post("/signatures/sign-guest", response_model=SignatureResponse)
async def sign_guest(
    data: GuestSignRequest,
    service: SignatureService = Depends(get_service),
) -> SignatureResponse:
    """
    Sign contract as guest (public with token).

    POST /signatures/sign-guest
    """
    return await service.sign_guest(data)


@router.get("/contracts/{contractId}/signatures", response_model=List[Signature])
async def get_contract_signatures(
    contractId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: SignatureService = Depends(get_service),
) -> List[Signature]:
    """
    Get all signatures for contract.

    GET /contracts/{contractId}/signatures
    """
    return await service.get_contract_signatures(contractId, current_user)


@router.post("/signatures/{signatureId}/evidence", status_code=status.HTTP_201_CREATED)
async def store_evidence(
    signatureId: str,
    data: SignatureEvidence,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: SignatureService = Depends(get_service),
) -> dict:
    """
    Store signature evidence (IP, timestamp, etc.).

    POST /signatures/{signatureId}/evidence
    """
    await service.store_evidence(signatureId, data, current_user)
    return {"success": True}


@router.get("/signatures/{signatureId}/certificate")
async def get_certificate(
    signatureId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: SignatureService = Depends(get_service),
) -> Response:
    """
    Download signature certificate.

    GET /signatures/{signatureId}/certificate
    """
    pdf_bytes = await service.get_certificate(signatureId)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=certificate_{signatureId}.pdf"
        },
    )
