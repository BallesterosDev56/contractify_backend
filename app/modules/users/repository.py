"""Users module - Database repository."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, UserPreferences, UserSession

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user data operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """Create a new user."""
        user = User(
            id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role="USER",
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update(
        self,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Optional[User]:
        """Update user profile."""
        updates = {}
        if first_name is not None:
            updates["first_name"] = first_name
        if last_name is not None:
            updates["last_name"] = last_name

        if updates:
            await self.db.execute(
                update(User).where(User.id == user_id).values(**updates)
            )
            await self.db.flush()

        return await self.get_by_id(user_id)

    async def get_or_create(
        self,
        user_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        max_retries: int = 3,
    ) -> User:
        """
        Get existing user or create new one with race condition handling.

        This method implements auto-provisioning for Firebase-authenticated users.
        When a valid Firebase user doesn't exist in the database, it will be
        created automatically with the provided information.

        Race Condition Handling:
        - Multiple simultaneous requests with the same user_id/email are handled
          gracefully using database constraints and retry logic
        - If a unique constraint violation occurs during creation, we assume
          another request successfully created the user and retry the GET operation

        Args:
            user_id: Firebase UID (primary key)
            email: User's email address (must be unique)
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            max_retries: Maximum number of retry attempts for race condition handling

        Returns:
            User: The existing or newly created user object

        Raises:
            Exception: If user creation fails after all retries or for unexpected errors

        Future Extensibility:
        - Additional fields (profile picture, phone, etc.) can be added as optional params
        - Role assignment logic can be injected here
        - Welcome email or onboarding triggers can be added after creation
        """
        # Step 1: Try to get existing user by Firebase UID
        user = await self.get_by_id(user_id)

        if user is not None:
            # User already exists - return immediately
            logger.debug(f"User {user_id} already exists in database")
            return user

        # Step 2: User doesn't exist - attempt to create with retry logic
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Auto-provisioning new user: user_id={user_id}, "
                    f"email={email}, attempt={attempt + 1}/{max_retries}"
                )

                # Attempt to create the user
                user = await self.create(
                    user_id=user_id,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                )

                # Commit the transaction to persist the user
                await self.db.commit()

                logger.info(
                    f"Successfully auto-provisioned user {user_id} with email {email}"
                )
                return user

            except IntegrityError as e:
                # Race condition detected: Another request created the user simultaneously
                # This can happen if:
                # 1. Two requests check for user existence at the same time
                # 2. Both find the user doesn't exist
                # 3. Both try to create the user
                # 4. One succeeds, one fails with IntegrityError

                logger.warning(
                    f"IntegrityError during user creation (attempt {attempt + 1}/{max_retries}): "
                    f"user_id={user_id}, error={str(e)}"
                )

                # Rollback the failed transaction
                await self.db.rollback()

                # Retry: Try to get the user that was created by the other request
                user = await self.get_by_id(user_id)

                if user is not None:
                    # Success! The other request created the user
                    logger.info(
                        f"User {user_id} was created by concurrent request, "
                        f"retrieved successfully"
                    )
                    return user

                # User still doesn't exist - might be a different integrity error
                # (e.g., email constraint) or timing issue. Retry if we have attempts left.
                if attempt < max_retries - 1:
                    logger.warning(
                        f"User {user_id} still not found after IntegrityError, "
                        f"retrying... ({attempt + 2}/{max_retries})"
                    )
                    continue
                else:
                    # Out of retries - log and raise
                    logger.error(
                        f"Failed to create or retrieve user {user_id} after "
                        f"{max_retries} attempts. Last error: {str(e)}"
                    )
                    raise Exception(
                        f"Failed to auto-provision user {user_id}. "
                        f"This might indicate a database constraint issue with email={email}. "
                        f"Please contact support if this persists."
                    ) from e

            except Exception as e:
                # Unexpected error during user creation
                logger.error(
                    f"Unexpected error creating user {user_id}: {type(e).__name__}: {str(e)}"
                )
                await self.db.rollback()
                raise Exception(
                    f"Failed to auto-provision user: {str(e)}"
                ) from e

        # This should never be reached due to the exception in the loop,
        # but include as a safety fallback
        raise Exception(
            f"Failed to auto-provision user {user_id} after {max_retries} attempts"
        )


class UserPreferencesRepository:
    """Repository for user preferences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences."""
        result = await self.db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update(self, user_id: str, preferences: Dict[str, Any]) -> UserPreferences:
        """Update or create user preferences."""
        existing = await self.get(user_id)
        if existing:
            # Merge preferences
            merged = {**existing.preferences, **preferences}
            await self.db.execute(
                update(UserPreferences)
                .where(UserPreferences.user_id == user_id)
                .values(preferences=merged)
            )
            await self.db.flush()
            return await self.get(user_id)  # type: ignore
        else:
            prefs = UserPreferences(user_id=user_id, preferences=preferences)
            self.db.add(prefs)
            await self.db.flush()
            return prefs


class UserSessionRepository:
    """Repository for user sessions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, user_id: str) -> List[UserSession]:
        """Get all sessions for user."""
        result = await self.db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.last_activity_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserSession:
        """Create new session."""
        session = UserSession(
            id=str(uuid4()),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def delete(self, session_id: str, user_id: str) -> bool:
        """Delete a session (only if owned by user)."""
        result = await self.db.execute(
            delete(UserSession).where(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
            )
        )
        return result.rowcount > 0

    async def update_activity(self, session_id: str) -> None:
        """Update last activity timestamp."""
        await self.db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(last_activity_at=datetime.utcnow())
        )
