"""Users module - Pydantic schemas matching OpenAPI spec."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str):
    """User role enum."""
    USER = "USER"
    ADMIN = "ADMIN"


class User(BaseModel):
    """User response schema - matches OpenAPI User schema."""

    id: str
    email: EmailStr
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    role: str = "USER"
    preferences: Optional[Dict[str, Any]] = None
    createdAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    """Update user profile - matches OpenAPI UpdateUserRequest."""

    firstName: Optional[str] = None
    lastName: Optional[str] = None


class Session(BaseModel):
    """User session - matches OpenAPI Session schema."""

    id: str
    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    createdAt: datetime
    lastActivityAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    currentPassword: str = Field(min_length=6)
    newPassword: str = Field(min_length=6)


class UserPreferences(BaseModel):
    """User preferences - flexible object."""

    class Config:
        extra = "allow"
