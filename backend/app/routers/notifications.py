"""Authenticated notification endpoints for the React client."""

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.repositories.concrete import NotificationRepository


router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("")
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    records = NotificationRepository(db).get_user_notifications(current_user.id, unread_only)
    return {"items": jsonable_encoder(records, sqlalchemy_safe=True), "unread": sum(not item.is_read for item in records)}


@router.post("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    updated = NotificationRepository(db).mark_all_read(current_user.id)
    return {"message": "Notifications marked as read", "updated": updated}
