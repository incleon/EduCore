"""
Authentication Schemas
========================

DTOs for login, token response, and password change.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class LoginRequest(BaseModel):
    """Login form data."""
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password")
    captcha_answer: str = Field(..., description="Captcha answer")
    captcha_token: str = Field(..., description="Captcha token")


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str
    roles: List[str] = []


class PasswordChangeRequest(BaseModel):
    """Password change form."""
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
