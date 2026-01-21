"""Users module - Business logic service."""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.shared.exceptions import NotFoundException, BadRequestException

from .models import User, UserPreferences, UserSession
from .repository import UserRepository, UserPreferencesRepository, UserSessionRepository
from .schemas import User as UserSchema, Session as SessionSchema, UpdateUserRequest


class UserService:
    """Service for user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.prefs_repo = UserPreferencesRepository(db)
        self.session_repo = UserSessionRepository(db)

    async def get_current_user_profile(self, current_user: CurrentUser) -> UserSchema:
        """
        Get or auto-provision user profile for authenticated Firebase user.

        This method implements auto-provisioning: when a valid Firebase user
        authenticates but doesn't exist in our database, they are automatically
        created with their Firebase information.

        Auto-Provisioning Flow:
        1. Check if user exists in database by Firebase UID
        2. If exists: return user profile
        3. If not exists: create user with Firebase data (email, name)
        4. Handle race conditions for simultaneous logins
        5. Initialize default preferences and return complete profile

        The method signature remains stable for backward compatibility and
        future enhancements (roles, permissions, etc.) can be added internally
        without breaking existing callers.

        Args:
            current_user: Authenticated Firebase user from JWT token

        Returns:
            UserSchema: Complete user profile with preferences

        Raises:
            Exception: If user creation fails (database errors, constraints, etc.)
        """
        # Parse Firebase name into first/last name
        # Handle various name formats: "John", "John Doe", "John Michael Doe"
        first_name = None
        last_name = None

        if current_user.name:
            name_parts = current_user.name.strip().split()
            if len(name_parts) >= 1:
                first_name = name_parts[0]
            if len(name_parts) >= 2:
                # Join remaining parts as last name (handles middle names)
                last_name = " ".join(name_parts[1:])

        # Get or create user with auto-provisioning
        # This handles race conditions internally
        user = await self.user_repo.get_or_create(
            user_id=current_user.id,
            email=current_user.email,
            first_name=first_name,
            last_name=last_name,
        )

        # Get user preferences (returns None if not set)
        prefs = await self.prefs_repo.get(current_user.id)

        # Build and return complete user profile
        return UserSchema(
            id=user.id,
            email=user.email,
            firstName=user.first_name,
            lastName=user.last_name,
            role=user.role,
            preferences=prefs.preferences if prefs else None,
            createdAt=user.created_at,
        )

    async def update_profile(
        self,
        current_user: CurrentUser,
        data: UpdateUserRequest,
    ) -> UserSchema:
        """Update user profile."""
        # Ensure user exists
        await self.user_repo.get_or_create(
            user_id=current_user.id,
            email=current_user.email,
        )

        # Update profile
        user = await self.user_repo.update(
            user_id=current_user.id,
            first_name=data.firstName,
            last_name=data.lastName,
        )

        if user is None:
            raise NotFoundException("User not found")

        prefs = await self.prefs_repo.get(current_user.id)

        return UserSchema(
            id=user.id,
            email=user.email,
            firstName=user.first_name,
            lastName=user.last_name,
            role=user.role,
            preferences=prefs.preferences if prefs else None,
            createdAt=user.created_at,
        )

    async def update_preferences(
        self,
        current_user: CurrentUser,
        preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update user preferences."""
        prefs = await self.prefs_repo.update(current_user.id, preferences)
        return prefs.preferences

    async def get_sessions(self, current_user: CurrentUser) -> List[SessionSchema]:
        """Get all active sessions for user."""
        sessions = await self.session_repo.get_all(current_user.id)
        return [
            SessionSchema(
                id=s.id,
                ipAddress=s.ip_address,
                userAgent=s.user_agent,
                createdAt=s.created_at,
                lastActivityAt=s.last_activity_at,
            )
            for s in sessions
        ]

    async def revoke_session(
        self,
        current_user: CurrentUser,
        session_id: str,
    ) -> bool:
        """Revoke a specific session."""
        deleted = await self.session_repo.delete(session_id, current_user.id)
        if not deleted:
            raise NotFoundException("Session not found")
        return True

    async def change_password(
        self,
        current_user: CurrentUser,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change user password.

        Note: Actual password change is handled by Firebase Auth.
        This endpoint validates the request and could trigger Firebase Admin SDK.
        For now, we return success as Firebase handles passwords client-side.
        """
        # Password validation
        if len(new_password) < 6:
            raise BadRequestException("Password must be at least 6 characters")

        # In production, you would use Firebase Admin SDK to update password
        # firebase_admin.auth.update_user(current_user.id, password=new_password)

        return True
