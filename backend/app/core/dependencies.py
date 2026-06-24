"""
Dependency Injection Module
=============================

OOP Concepts Demonstrated:
--------------------------
1. DEPENDENCY INJECTION: FastAPI's Depends() system
2. FACTORY PATTERN: get_db() is a factory that yields database sessions
3. COMPOSITION: get_current_user composes JWT decoding + DB lookup

Why Dependency Injection?
- Loose coupling between components
- Easy to swap implementations (e.g., mock DB in tests)
- FastAPI manages lifecycle (creation, cleanup)
- Each request gets its own DB session (isolation)

SOLID Principles:
- DIP (Dependency Inversion): Routes depend on abstractions (get_db),
  not concrete database implementations
- SRP: Each dependency has one responsibility
"""

from typing import Optional
from fastapi import Depends, Request, Cookie
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.core.security import JWTHandler
from app.core.exceptions import UnauthorizedException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def get_db():
    """
    FACTORY + DEPENDENCY INJECTION: Yield a database session.

    Why 'yield' instead of 'return'?
    ─────────────────────────────────
    - 'yield' makes this a generator — FastAPI handles cleanup automatically
    - The session is created at the start of a request
    - After the route handler finishes, code after 'yield' runs (cleanup)
    - This guarantees the session is always closed, even if an error occurs
    - Same pattern as Python's context managers (with statement)

    Usage in routes:
        @router.get("/students")
        def list_students(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """
    Extract and validate the current user from JWT token.

    COMPOSITION: This dependency composes multiple operations:
    1. Extract token from cookie (or Authorization header)
    2. Decode JWT token (delegates to JWTHandler)
    3. Load user from database
    4. Return user object

    Why a cookie-based approach?
    - HTTP-only cookies are more secure than localStorage
    - Automatically sent with every request
    - Protected against XSS attacks
    - CSRF protection can be added via SameSite attribute
    """
    # Import here to avoid circular imports
    from app.models.user import User

    # Try cookie first, then Authorization header
    token = access_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise UnauthorizedException(detail="Not authenticated. Please log in.")

    # Decode the JWT token
    payload = JWTHandler.decode_token(token)
    user_id: Optional[int] = payload.get("sub")

    if user_id is None:
        raise UnauthorizedException(detail="Invalid token payload")

    # Load user from database
    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise UnauthorizedException(detail="User not found")

    if not user.is_active:
        raise UnauthorizedException(detail="User account is deactivated")

    return user


def get_current_active_user(current_user=Depends(get_current_user)):
    """
    Ensure the current user is active.

    DEPENDENCY CHAINING: This depends on get_current_user,
    which depends on get_db. FastAPI resolves the entire chain.

    This demonstrates the DECORATOR PATTERN conceptually —
    it adds a check on top of the base dependency.
    """
    if not current_user.is_active:
        raise UnauthorizedException(detail="Inactive user account")
    return current_user


def get_optional_user(
    request: Request,
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """
    Get current user if authenticated, None otherwise.

    Used for pages that work both for authenticated and anonymous users
    (e.g., login page should redirect if already logged in).
    """
    from app.models.user import User

    token = access_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        return None

    try:
        payload = JWTHandler.decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user if user and user.is_active else None
    except Exception:
        return None
