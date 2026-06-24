"""
Authentication Router — Login/Logout Endpoints
=================================================
"""

from fastapi import APIRouter, Depends, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import UnauthorizedException
from app.core.security import CaptchaHandler
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest
from app.core.config import settings

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
    if not CaptchaHandler.verify(data.captcha_token, data.captcha_answer):
        raise UnauthorizedException(detail="Invalid captcha. Please try again.")

    auth_service = AuthService(db)
    result = auth_service.authenticate(data.email, data.password)

    # Set HTTP-only cookie (secure against XSS)
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        max_age=3600,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
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


@router.get("/profile")
def get_profile(current_user=Depends(get_current_user)):
    """Return the signed-in account plus its role-specific, non-sensitive profile."""
    payload = {
        "id": current_user.id, "email": current_user.email,
        "username": current_user.username, "full_name": current_user.full_name,
        "phone": current_user.phone, "gender": current_user.gender.value if current_user.gender else None,
        "address": current_user.address, "profile_image": current_user.profile_image,
        "roles": current_user.roles, "permissions": current_user.permissions,
        "created_at": current_user.created_at,
    }
    if current_user.student:
        s = current_user.student
        payload["student"] = {
            "id": s.id, "student_id": s.student_id, "enrollment_number": s.enrollment_number,
            "personal_email": s.personal_email, "department": s.department.name if s.department else None,
            "course": s.course.name if s.course else None, "branch": s.branch.name if s.branch else None,
            "admission_year": s.admission_year, "current_semester": s.current_semester,
            "section": s.academic_section.code if s.academic_section else s.section,
            "date_of_birth": s.date_of_birth, "admission_date": s.admission_date,
            "guardian_name": s.guardian_name, "guardian_phone": s.guardian_phone,
            "father_name": s.father_name, "mother_name": s.mother_name,
            "blood_group": s.blood_group, "status": s.status.value if s.status else None,
        }
    if current_user.teacher:
        t = current_user.teacher
        payload["teacher"] = {
            "id": t.id, "faculty_id": t.faculty_id, "employee_id": t.employee_id,
            "department": t.department.name if t.department else None,
            "course": t.branch.course.name if t.branch and t.branch.course else None,
            "branch": t.branch.name if t.branch else None, "designation": t.designation,
            "specialization": t.specialization, "qualification": t.qualification,
            "joining_date": t.joining_date, "experience_years": t.experience_years, "bio": t.bio,
        }
    return payload


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
