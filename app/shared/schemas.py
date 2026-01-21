"""Shared Pydantic schemas."""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response matching OpenAPI spec."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class Pagination(BaseModel):
    """Pagination metadata_ matching OpenAPI spec."""

    page: int = Field(ge=1)
    pageSize: int = Field(ge=1, le=100)
    totalPages: int = Field(ge=0)
    totalItems: int = Field(ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    data: List[T]
    pagination: Pagination


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1)
    pageSize: int = Field(default=20, ge=1, le=100)
    sortBy: Optional[str] = None
    sortOrder: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")

    def get_offset(self) -> int:
        """Calculate offset for SQL query."""
        return (self.page - 1) * self.pageSize

    def get_limit(self) -> int:
        """Get limit for SQL query."""
        return self.pageSize
