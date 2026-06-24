"""Role-aware dashboard API consumed by the React application."""

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.services.dashboard_service import DashboardFactory


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
ROLE_HIERARCHY = ("admin", "hod", "accountant", "librarian", "teacher", "student")


@router.get("")
def dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the same role-specific data previously passed to Jinja views."""
    role = next((name for name in ROLE_HIERARCHY if name in current_user.roles), "student")
    data = DashboardFactory.create(role, db, current_user).get_stats()
    return {"role": role, "data": jsonable_encoder(data, sqlalchemy_safe=True)}
