"""
Tests for user auto-provisioning functionality.

This module tests the critical auto-provisioning feature that automatically
creates users in the database when they authenticate with Firebase for the first time.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


class TestUserRepositoryAutoProvisioning:
    """Test suite for UserRepository.get_or_create method."""

    @pytest.mark.asyncio
    async def test_get_or_create_new_user(self, db_session: AsyncSession):
        """Test creating a new user when they don't exist."""
        repo = UserRepository(db_session)

        user_id = "firebase_uid_123"
        email = "newuser@example.com"
        first_name = "John"
        last_name = "Doe"

        # Create user
        user = await repo.get_or_create(
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        # Assertions
        assert user is not None
        assert user.id == user_id
        assert user.email == email
        assert user.first_name == first_name
        assert user.last_name == last_name
        assert user.role == "USER"
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_get_or_create_existing_user(self, db_session: AsyncSession):
        """Test retrieving an existing user without creating a duplicate."""
        repo = UserRepository(db_session)

        user_id = "firebase_uid_456"
        email = "existing@example.com"

        # Create user first time
        user1 = await repo.get_or_create(
            user_id=user_id,
            email=email,
            first_name="Jane",
            last_name="Smith",
        )

        # Try to create same user again
        user2 = await repo.get_or_create(
            user_id=user_id,
            email="different@example.com",  # Different email should be ignored
            first_name="Different",
            last_name="Name",
        )

        # Should return the same user without modification
        assert user1.id == user2.id
        assert user2.email == email  # Original email preserved
        assert user2.first_name == "Jane"  # Original name preserved

    @pytest.mark.asyncio
    async def test_get_or_create_without_names(self, db_session: AsyncSession):
        """Test creating a user with only required fields (email)."""
        repo = UserRepository(db_session)

        user_id = "firebase_uid_789"
        email = "minimal@example.com"

        user = await repo.get_or_create(
            user_id=user_id,
            email=email,
        )

        assert user is not None
        assert user.id == user_id
        assert user.email == email
        assert user.first_name is None
        assert user.last_name is None

    @pytest.mark.asyncio
    async def test_get_or_create_race_condition_simulation(self, db_session: AsyncSession):
        """
        Test handling of race condition when two requests try to create the same user.

        This simulates the scenario where:
        1. Request A checks if user exists (not found)
        2. Request B checks if user exists (not found)
        3. Request A creates the user
        4. Request B tries to create the user and gets IntegrityError
        5. Request B should retry and get the user created by Request A
        """
        repo = UserRepository(db_session)

        user_id = "race_condition_uid"
        email = "race@example.com"

        # Mock the create method to simulate race condition on first call
        original_create = repo.create
        create_call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal create_call_count
            create_call_count += 1

            if create_call_count == 1:
                # First call: simulate another request creating the user
                # by actually creating it, then raising IntegrityError
                await original_create(*args, **kwargs)
                raise IntegrityError("duplicate key", None, None)
            else:
                # Subsequent calls: normal behavior
                return await original_create(*args, **kwargs)

        with patch.object(repo, 'create', side_effect=mock_create):
            # This should handle the IntegrityError and retry
            user = await repo.get_or_create(
                user_id=user_id,
                email=email,
                first_name="Race",
                last_name="Test",
            )

        # Should successfully retrieve the user
        assert user is not None
        assert user.id == user_id
        assert user.email == email

    @pytest.mark.asyncio
    async def test_get_or_create_max_retries_exceeded(self, db_session: AsyncSession):
        """Test that appropriate error is raised when max retries are exceeded."""
        repo = UserRepository(db_session)

        user_id = "max_retries_uid"
        email = "retries@example.com"

        # Mock create to always raise IntegrityError
        with patch.object(
            repo,
            'create',
            side_effect=IntegrityError("persistent error", None, None)
        ):
            # Mock get_by_id to always return None (user never created)
            with patch.object(repo, 'get_by_id', return_value=None):
                with pytest.raises(Exception) as exc_info:
                    await repo.get_or_create(
                        user_id=user_id,
                        email=email,
                        max_retries=3,
                    )

                # Verify error message is descriptive
                assert "Failed to auto-provision user" in str(exc_info.value)
                assert email in str(exc_info.value)


class TestUserServiceAutoProvisioning:
    """Test suite for UserService.get_current_user_profile with auto-provisioning."""

    @pytest.mark.asyncio
    async def test_get_profile_creates_new_user(self, db_session: AsyncSession):
        """Test that getting profile auto-provisions a new user."""
        service = UserService(db_session)

        current_user = CurrentUser(
            id="new_firebase_user",
            email="newuser@example.com",
            email_verified=True,
            name="Alice Johnson",
        )

        profile = await service.get_current_user_profile(current_user)

        assert profile is not None
        assert profile.id == "new_firebase_user"
        assert profile.email == "newuser@example.com"
        assert profile.firstName == "Alice"
        assert profile.lastName == "Johnson"
        assert profile.role == "USER"

    @pytest.mark.asyncio
    async def test_get_profile_returns_existing_user(self, db_session: AsyncSession):
        """Test that getting profile returns existing user without modification."""
        service = UserService(db_session)

        current_user = CurrentUser(
            id="existing_firebase_user",
            email="existing@example.com",
            email_verified=True,
            name="Bob Smith",
        )

        # Create profile first time
        profile1 = await service.get_current_user_profile(current_user)

        # Get profile second time (simulating another login)
        current_user_second_login = CurrentUser(
            id="existing_firebase_user",
            email="existing@example.com",
            email_verified=True,
            name="Bob Smith Updated",  # Name changed in Firebase
        )

        profile2 = await service.get_current_user_profile(current_user_second_login)

        # Should return same user (name not updated)
        assert profile1.id == profile2.id
        assert profile2.firstName == "Bob"  # Original name preserved
        assert profile2.lastName == "Smith"

    @pytest.mark.asyncio
    async def test_get_profile_handles_single_name(self, db_session: AsyncSession):
        """Test name parsing when user has only one name."""
        service = UserService(db_session)

        current_user = CurrentUser(
            id="single_name_user",
            email="singlename@example.com",
            email_verified=True,
            name="Madonna",
        )

        profile = await service.get_current_user_profile(current_user)

        assert profile.firstName == "Madonna"
        assert profile.lastName is None

    @pytest.mark.asyncio
    async def test_get_profile_handles_multiple_names(self, db_session: AsyncSession):
        """Test name parsing when user has multiple middle names."""
        service = UserService(db_session)

        current_user = CurrentUser(
            id="multiple_names_user",
            email="multiple@example.com",
            email_verified=True,
            name="John Michael Patrick Doe",
        )

        profile = await service.get_current_user_profile(current_user)

        assert profile.firstName == "John"
        assert profile.lastName == "Michael Patrick Doe"

    @pytest.mark.asyncio
    async def test_get_profile_handles_no_name(self, db_session: AsyncSession):
        """Test auto-provisioning when Firebase user has no name."""
        service = UserService(db_session)

        current_user = CurrentUser(
            id="no_name_user",
            email="noname@example.com",
            email_verified=True,
            name=None,
        )

        profile = await service.get_current_user_profile(current_user)

        assert profile.email == "noname@example.com"
        assert profile.firstName is None
        assert profile.lastName is None

    @pytest.mark.asyncio
    async def test_get_profile_handles_whitespace_name(self, db_session: AsyncSession):
        """Test name parsing with extra whitespace."""
        service = UserService(db_session)

        current_user = CurrentUser(
            id="whitespace_user",
            email="whitespace@example.com",
            email_verified=True,
            name="  John   Doe  ",
        )

        profile = await service.get_current_user_profile(current_user)

        assert profile.firstName == "John"
        assert profile.lastName == "Doe"

    @pytest.mark.asyncio
    async def test_concurrent_login_requests(self, db_session: AsyncSession):
        """
        Test multiple concurrent requests for the same new user.

        This simulates real-world scenario where a user opens multiple tabs
        or refreshes the page multiple times during login.
        """
        service = UserService(db_session)

        current_user = CurrentUser(
            id="concurrent_user",
            email="concurrent@example.com",
            email_verified=True,
            name="Concurrent User",
        )

        # Simulate 5 concurrent requests
        tasks = [
            service.get_current_user_profile(current_user)
            for _ in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should succeed
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 5

        # All should return the same user
        user_ids = [r.id for r in successful_results]
        assert all(uid == "concurrent_user" for uid in user_ids)


class TestAutoProvisioningEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_database_error_during_creation(self, db_session: AsyncSession):
        """Test handling of unexpected database errors."""
        service = UserService(db_session)

        current_user = CurrentUser(
            id="db_error_user",
            email="dberror@example.com",
            email_verified=True,
            name="DB Error",
        )

        # Mock the repository to raise unexpected error
        with patch.object(
            service.user_repo,
            'get_or_create',
            side_effect=Exception("Database connection lost")
        ):
            with pytest.raises(Exception) as exc_info:
                await service.get_current_user_profile(current_user)

            assert "Database connection lost" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_email_handling(self, db_session: AsyncSession):
        """Test that empty email is handled properly."""
        repo = UserRepository(db_session)

        # This should work but might raise validation error in production
        # depending on database constraints
        user = await repo.get_or_create(
            user_id="empty_email_user",
            email="",
        )

        assert user.id == "empty_email_user"
        assert user.email == ""
