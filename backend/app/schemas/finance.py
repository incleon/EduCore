"""Finance Schemas"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime
from app.models.finance import FeeStatus, PaymentMethod, PaymentStatus

# ----------------- ExpenseCategory -----------------

class ExpenseCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass

class ExpenseCategoryResponse(ExpenseCategoryBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}

# ----------------- Expense -----------------

class ExpenseBase(BaseModel):
    title: str
    amount: float = Field(..., gt=0)
    expense_date: date
    category_id: Optional[int] = None
    receipt_url: Optional[str] = None
    remarks: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int
    recorded_by: Optional[int] = None
    created_at: datetime
    model_config = {"from_attributes": True}

# ----------------- FeeStructure -----------------

class FeeStructureBase(BaseModel):
    name: str
    amount: float = Field(..., gt=0)
    course_id: int
    academic_year: str
    semester: int
    description: Optional[str] = None

class FeeStructureCreate(FeeStructureBase):
    pass

class FeeStructureResponse(FeeStructureBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}

# ----------------- Payment -----------------

class PaymentBase(BaseModel):
    amount: float = Field(..., gt=0)
    payment_date: date
    payment_method: PaymentMethod
    transaction_reference: Optional[str] = None
    remarks: Optional[str] = None

class PaymentCreate(PaymentBase):
    student_fee_id: int

class PaymentResponse(PaymentBase):
    id: int
    student_fee_id: int
    status: PaymentStatus
    created_at: datetime
    model_config = {"from_attributes": True}

# ----------------- StudentFee (Invoice) -----------------

class StudentFeeBase(BaseModel):
    student_id: int
    fee_structure_id: Optional[int] = None
    title: str
    amount: float = Field(..., gt=0)
    due_date: Optional[date] = None
    remarks: Optional[str] = None

class StudentFeeCreate(StudentFeeBase):
    pass

class StudentFeeResponse(StudentFeeBase):
    id: int
    status: FeeStatus
    paid_amount: float = 0.0
    balance: float = 0.0
    payments: List[PaymentResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}

# ----------------- StaffSalary -----------------

class StaffSalaryBase(BaseModel):
    user_id: int
    amount: float = Field(..., gt=0)
    payment_date: date
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., gt=2000)
    payment_method: PaymentMethod
    transaction_reference: Optional[str] = None
    remarks: Optional[str] = None

class StaffSalaryCreate(StaffSalaryBase):
    pass

class StaffSalaryResponse(StaffSalaryBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}
