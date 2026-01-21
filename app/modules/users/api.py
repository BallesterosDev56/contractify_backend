"""Users module - API routes matching OpenAPI spec."""

from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.db import get_db

from .schemas import (
    ChangePasswordRequest,
    Session,
    UpdateUserRequest,
    User,
)
from .service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service instance."""
    return UserService(db)


@router.get("/me", response_model=User)
async def get_current_user_profile(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: UserService = Depends(get_service),
) -> User:
    """
    Get current user profile.

    GET /users/me
    """
    return await service.get_current_user_profile(current_user)


@router.patch("/me", response_model=User)
async def update_user_profile(
    data: UpdateUserRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: UserService = Depends(get_service),
) -> User:
    """
    Update user profile.

    PATCH /users/me
    """
    return await service.update_profile(current_user, data)


@router.patch("/me/preferences", status_code=status.HTTP_200_OK)
async def update_user_preferences(
    preferences: Dict[str, Any],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: UserService = Depends(get_service),
) -> Dict[str, Any]:
    """
    Update user preferences.

    PATCH /users/me/preferences
    """
    return await service.update_preferences(current_user, preferences)


@router.get("/me/sessions", response_model=List[Session])
async def list_sessions(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: UserService = Depends(get_service),
) -> List[Session]:
    """
    List active sessions.

    GET /users/me/sessions
    """
    return await service.get_sessions(current_user)


@router.delete("/me/sessions/{sessionId}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    sessionId: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: UserService = Depends(get_service),
) -> None:
    """
    Revoke session.

    DELETE /users/me/sessions/{sessionId}
    """
    await service.revoke_session(current_user, sessionId)


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    data: ChangePasswordRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: UserService = Depends(get_service),
) -> Dict[str, bool]:
    """
    Change password.

    POST /users/change-password
    """
    await service.change_password(
        current_user,
        data.currentPassword,
        data.newPassword,
    )
    return {"success": True}
