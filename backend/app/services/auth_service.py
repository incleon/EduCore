"""
Authentication Service
========================

Handles login, token generation, and password validation.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.concrete import UserRepository
from app.core.security import PasswordHasher, JWTHandler
from app.core.exceptions import UnauthorizedException, NotFoundException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Authentication service — COMPOSITION with UserRepository.

    OOP Concept: COMPOSITION
    ─────────────────────────
    AuthService HAS-A UserRepository (it doesn't inherit from it).
    The repository is injected via constructor (Dependency Injection).
    """

    def __init__(self, db: Session):
        self._user_repo = UserRepository(db)
        self._db = db

    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with email and password.

        Returns token data on success, raises exception on failure.
        """
        user = self._user_repo.get_by_email(email)

        if user is None:
            logger.warning(f"Login attempt for non-existent email: {email}")
            raise UnauthorizedException(detail="Invalid email or password")

        if not user.is_active:
            logger.warning(f"Login attempt for deactivated user: {email}")
            raise UnauthorizedException(detail="Account is deactivated")

        if not PasswordHasher.verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {email}")
            raise UnauthorizedException(detail="Invalid email or password")

        # Create JWT token with user info + roles + permissions
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "roles": user.roles,
            "permissions": user.permissions,
        }

        access_token = JWTHandler.create_access_token(token_data)

        logger.info(f"User authenticated successfully: {email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
        }

    def get_user_by_id(self, user_id: int):
        """Get user for token validation."""
        user = self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        return user

    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change user's password.
        Validates current password, then hashes and saves the new password.
        """
        user = self.get_user_by_id(user_id)
        
        if not PasswordHasher.verify_password(current_password, user.hashed_password):
            logger.warning(f"Failed password change attempt for user_id: {user_id}")
            raise UnauthorizedException(detail="Incorrect current password")
            
        user.hashed_password = PasswordHasher.hash_password(new_password)
        self._db.commit()
        logger.info(f"Password changed successfully for user_id: {user_id}")
        return True
