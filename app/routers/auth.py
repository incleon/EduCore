"""
Authentication Router — Login/Logout Endpoints
=================================================
"""

from fastapi import APIRouter, Depends, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Authenticate user and set JWT cookie.

    Flow:
    1. Receive email + password
    2. AuthService validates credentials
    3. JWT token is created
    4. Token is set as HTTP-only cookie
    5. Return user info
    """
    auth_service = AuthService(db)
    result = auth_service.authenticate(data.email, data.password)

    # Set HTTP-only cookie (secure against XSS)
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        max_age=3600,
        samesite="lax",
        secure=False,  # Set True in production with HTTPS
    )

    return result


@router.post("/logout")
def logout(response: Response):
    """Clear the authentication cookie."""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current authenticated user's info."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "roles": current_user.roles,
        "permissions": current_user.permissions,
    }


from app.schemas.auth import PasswordChangeRequest

@router.put("/change-password")
def change_password(
    data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Change the current user's password."""
    auth_service = AuthService(db)
    auth_service.change_password(
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password
    )
    return {"message": "Password updated successfully"}
