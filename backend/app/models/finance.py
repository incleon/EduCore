"""
Finance Models
==============
Handles Fee Structures, Invoices (Student Fees), Payments, Expenses, and Staff Salaries.
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


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CHEQUE = "cheque"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    ONLINE = "online"


class PaymentStatus(str, enum.Enum):
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"
    REFUNDED = "refunded"


class FeeStructure(BaseModel):
    """Template for fees assigned to courses."""
    __tablename__ = "fee_structures"

    name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    academic_year = Column(String(20), nullable=False)
    semester = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)


class StudentFee(BaseModel):
    """An invoice/demand issued to a student."""
    __tablename__ = "student_fees"

    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    fee_structure_id = Column(
        Integer, ForeignKey("fee_structures.id", ondelete="SET NULL"),
        nullable=True
    )

    title = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(SAEnum(FeeStatus), default=FeeStatus.PENDING, nullable=False)
    remarks = Column(Text, nullable=True)

    # ── RELATIONSHIPS ────────────────────────────────────────
    student = relationship("Student", back_populates="fee_records")
    payments = relationship("Payment", back_populates="student_fee", cascade="all, delete-orphan", lazy="selectin")

    @property
    def paid_amount(self) -> float:
        return sum(p.amount for p in self.payments if p.status == PaymentStatus.SUCCESS)

    @property
    def balance(self) -> float:
        return max(0, self.amount - self.paid_amount)


class Payment(BaseModel):
    """Individual payment installment for a StudentFee."""
    __tablename__ = "payments"

    student_fee_id = Column(
        Integer, ForeignKey("student_fees.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(SAEnum(PaymentMethod), nullable=False)
    transaction_reference = Column(String(100), nullable=True, unique=True)
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.SUCCESS, nullable=False)
    remarks = Column(Text, nullable=True)

    student_fee = relationship("StudentFee", back_populates="payments")


class ExpenseCategory(BaseModel):
    """Categorization for expenses."""
    __tablename__ = "expense_categories"

    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)


class Expense(BaseModel):
    """Operational expenses of the school/college."""
    __tablename__ = "expenses"

    title = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    expense_date = Column(Date, nullable=False)
    category_id = Column(
        Integer, ForeignKey("expense_categories.id", ondelete="SET NULL"),
        nullable=True
    )
    receipt_url = Column(String(500), nullable=True)
    recorded_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    remarks = Column(Text, nullable=True)


class StaffSalary(BaseModel):
    """Flat salary payout records for staff/teachers."""
    __tablename__ = "staff_salaries"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    payment_method = Column(SAEnum(PaymentMethod), nullable=False)
    transaction_reference = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
