"""
Common Schemas — Pagination, Filtering, Sorting
==================================================

Reusable schemas used across all modules (DRY Principle).
"""

from typing import Optional, List, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


class SortParams(BaseModel):
    """Query parameters for sorting."""
    sort_by: str = Field(default="id", description="Field to sort by")
    sort_order: str = Field(default="desc", description="asc or desc")


class FilterParams(BaseModel):
    """Query parameters for search/filter."""
    search: Optional[str] = Field(default=None, description="Search query")
    status: Optional[str] = Field(default=None, description="Status filter")


class PaginatedResponse(BaseModel):
    """
    Generic paginated response wrapper.

    Demonstrates GENERICS in Pydantic (conceptual — Pydantic v2 supports it).
    """
    items: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0

    @classmethod
    def create(cls, items: list, total: int, page: int, page_size: int):
        """Factory method for creating paginated responses."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: bool = True
    error_code: str
    detail: str
    status_code: int
