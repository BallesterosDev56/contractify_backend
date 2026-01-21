"""AI module - API routes matching OpenAPI spec."""

from typing import Annotated, Union

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.db import get_db

from .schemas import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIRegenerateRequest,
    AsyncJobResponse,
    AsyncJobStatus,
    ValidateInputRequest,
    ValidateInputResponse,
)
from .service import AIService

router = APIRouter(prefix="/ai", tags=["AI"])


def get_service(db: AsyncSession = Depends(get_db)) -> AIService:
    """Get AI service instance."""
    return AIService(db)


@router.post("/validate-input", response_model=ValidateInputResponse)
async def validate_input(
    data: ValidateInputRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: AIService = Depends(get_service),
) -> ValidateInputResponse:
    """
    Validate form inputs before generation.

    POST /ai/validate-input
    """
    return await service.validate_input(data)


@router.post(
    "/generate-contract",
    response_model=Union[AIGenerateResponse, AsyncJobResponse],
    responses={
        200: {"model": AIGenerateResponse, "description": "Contract generated"},
        202: {"model": AsyncJobResponse, "description": "Generation started (async)"},
    },
)
async def generate_contract(
    data: AIGenerateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: AIService = Depends(get_service),
) -> Union[AIGenerateResponse, AsyncJobResponse]:
    """
    Generate contract content using AI + RAG.

    POST /ai/generate-contract

    Returns 200 with content for sync generation, or 202 with job ID for async.
    """
    # For now, use sync generation
    # To use async, return: await service.generate_contract_async(current_user, data)
    return await service.generate_contract(current_user, data)


@router.post("/regenerate", response_model=AIGenerateResponse)
async def regenerate_contract(
    data: AIRegenerateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: AIService = Depends(get_service),
) -> AIGenerateResponse:
    """
    Regenerate contract with feedback.

    POST /ai/regenerate
    """
    return await service.regenerate_contract(current_user, data)


@router.get("/jobs/{jobId}", response_model=AsyncJobStatus)
async def get_job_status(
    jobId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: AIService = Depends(get_service),
) -> AsyncJobStatus:
    """
    Poll async AI generation job status.

    GET /ai/jobs/{jobId}
    """
    return await service.get_job_status(jobId)
