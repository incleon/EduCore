"""
Fee Model
===========

Manages student fee records and payments.
"""

from sqlalchemy import Column, Integer, Float, ForeignKey, String, Date, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database.base import BaseModel


class FeeStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    WAIVED = "waived"


class FeeType(str, enum.Enum):
    TUITION = "tuition"
    EXAM = "exam"
    LIBRARY = "library"
    LABORATORY = "laboratory"
    HOSTEL = "hostel"
    TRANSPORT = "transport"
    OTHER = "other"


class Fee(BaseModel):
    """
    Fee model — tracks student fee payments.

    Relationships:
    - MANY-TO-ONE: Fee → Student
    """

    __tablename__ = "fees"

    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    fee_type = Column(SAEnum(FeeType), nullable=False)
    amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0, nullable=False)
    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)
    status = Column(SAEnum(FeeStatus), default=FeeStatus.PENDING, nullable=False)
    semester = Column(Integer, nullable=False)
    receipt_number = Column(String(50), unique=True, nullable=True)
    payment_method = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)

    # ── RELATIONSHIPS ────────────────────────────────────────
    student = relationship("Student", back_populates="fee_records")

    @property
    def balance(self) -> float:
        """Calculate outstanding balance."""
        return max(0, self.amount - self.paid_amount)

    @property
    def is_fully_paid(self) -> bool:
        return self.paid_amount >= self.amount

    def __repr__(self) -> str:
        return (
            f"<Fee(student={self.student_id}, type={self.fee_type}, "
            f"amount={self.amount}, status={self.status})>"
        )
