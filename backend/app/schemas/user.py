"""
User, Role & Permission Schemas
==================================
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ── User Schemas ─────────────────────────────────────────────

class UserBase(BaseModel):
    """Base user fields (DRY — shared between Create and Update)."""
    email: str = Field(..., description="Email address")
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user (includes password)."""
    password: str = Field(..., min_length=8, description="Plain-text password")
    role_ids: List[int] = Field(default=[], description="Role IDs to assign")


class UserUpdate(BaseModel):
    """Schema for updating a user (all fields optional)."""
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[int]] = None


class UserResponse(BaseModel):
    """User response (NEVER includes password)."""
    id: int
    email: str
    username: str
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None
    profile_image: Optional[str] = None
    is_active: bool
    roles: List[str] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """User list item (minimal fields)."""
    id: int
    email: str
    full_name: str
    is_active: bool
    roles: List[str] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Role Schemas ─────────────────────────────────────────────

class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    display_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    is_active: bool
    permissions: List[str] = []

    model_config = {"from_attributes": True}


# ── Permission Schemas ───────────────────────────────────────

class PermissionCreate(BaseModel):
    name: str
    resource: str
    action: str
    description: Optional[str] = None


class PermissionResponse(BaseModel):
    id: int
    name: str
    resource: str
    action: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}
