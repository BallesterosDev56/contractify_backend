"""Users module - Database repository."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, UserPreferences, UserSession


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
    ) -> User:
        """Get existing user or create new one."""
        user = await self.get_by_id(user_id)
        if user is None:
            user = await self.create(user_id, email, first_name, last_name)
        return user


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
