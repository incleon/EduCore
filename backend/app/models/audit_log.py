"""
Audit Log Model
=================

Tracks all significant system actions for compliance and debugging.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON

from app.database.base import BaseModel


class AuditLog(BaseModel):
    """
    Audit log — immutable record of system actions.

    Why audit logs?
    - Compliance (who did what, when)
    - Security monitoring
    - Debugging production issues
    - Activity history for users

    Note: Audit logs should NEVER be soft-deleted or modified.
    """

    __tablename__ = "audit_logs"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    action = Column(String(50), nullable=False, index=True)
    resource = Column(String(100), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog(user={self.user_id}, action='{self.action}', "
            f"resource='{self.resource}')>"
        )
