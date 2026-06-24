"""
Notification Model
====================

System notifications for users.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database.base import BaseModel


class NotificationType(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"
    ERROR = "error"


class Notification(BaseModel):
    """
    Notification model — system messages to users.

    Relationships:
    - MANY-TO-ONE: Notification → User
    """

    __tablename__ = "notifications"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(
        SAEnum(NotificationType),
        default=NotificationType.INFO,
        nullable=False,
    )
    is_read = Column(Boolean, default=False, nullable=False)
    link = Column(String(500), nullable=True)

    # ── RELATIONSHIPS ────────────────────────────────────────
    user = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(user={self.user_id}, title='{self.title}', read={self.is_read})>"
