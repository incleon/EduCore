"""Fee Schemas"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime


class FeeCreate(BaseModel):
    student_id: int
    fee_type: str
    amount: float = Field(..., gt=0)
    due_date: Optional[date] = None
    semester: int
    remarks: Optional[str] = None


class FeePayment(BaseModel):
    paid_amount: float = Field(..., gt=0)
    payment_method: Optional[str] = "cash"
    remarks: Optional[str] = None


class FeeUpdate(BaseModel):
    amount: Optional[float] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    remarks: Optional[str] = None


class FeeResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    enrollment_number: Optional[str] = None
    fee_type: str
    amount: float
    paid_amount: float = 0
    balance: float = 0
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    status: str
    semester: int
    receipt_number: Optional[str] = None
    payment_method: Optional[str] = None
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
