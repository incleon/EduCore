"""
Finance API Endpoints
=====================
CRUD operations for Accountant dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.core.dependencies import get_db
from app.models.user import User
from app.models.finance import (
    FeeStructure, StudentFee, Payment, Expense, ExpenseCategory, StaffSalary,
    PaymentStatus
)
from app.schemas import finance as schemas
from app.routers.auth import get_current_user

router = APIRouter()

# ----------------- Dashboard -----------------

@router.get("/dashboard-stats")
def get_finance_dashboard_stats(db: Session = Depends(get_db)):
    # Total revenue from SUCCESS payments
    total_revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == PaymentStatus.SUCCESS).scalar() or 0.0
    # Total expenses
    total_expenses = db.query(func.sum(Expense.amount)).scalar() or 0.0
    # Total salary payouts
    total_salaries = db.query(func.sum(StaffSalary.amount)).scalar() or 0.0
    
    total_outflow = total_expenses + total_salaries
    net_balance = total_revenue - total_outflow
    
    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "total_salaries": total_salaries,
        "net_balance": net_balance
    }

# ----------------- Fee Structures -----------------

@router.post("/fee-structures", response_model=schemas.FeeStructureResponse)
def create_fee_structure(schema: schemas.FeeStructureCreate, db: Session = Depends(get_db)):
    db_obj = FeeStructure(**schema.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/fee-structures", response_model=List[schemas.FeeStructureResponse])
def list_fee_structures(db: Session = Depends(get_db)):
    return db.query(FeeStructure).all()

# ----------------- Student Fees (Invoices) -----------------

@router.post("/student-fees", response_model=schemas.StudentFeeResponse)
def create_student_fee(schema: schemas.StudentFeeCreate, db: Session = Depends(get_db)):
    db_obj = StudentFee(**schema.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/student-fees", response_model=List[schemas.StudentFeeResponse])
def list_student_fees(student_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(StudentFee)
    if student_id:
        query = query.filter(StudentFee.student_id == student_id)
    return query.all()

# ----------------- Payments -----------------

@router.post("/payments", response_model=schemas.PaymentResponse)
def create_payment(schema: schemas.PaymentCreate, db: Session = Depends(get_db)):
    db_obj = Payment(**schema.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# ----------------- Expense Categories -----------------

@router.post("/expense-categories", response_model=schemas.ExpenseCategoryResponse)
def create_expense_category(schema: schemas.ExpenseCategoryCreate, db: Session = Depends(get_db)):
    db_obj = ExpenseCategory(**schema.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/expense-categories", response_model=List[schemas.ExpenseCategoryResponse])
def list_expense_categories(db: Session = Depends(get_db)):
    return db.query(ExpenseCategory).all()

# ----------------- Expenses -----------------

@router.post("/expenses", response_model=schemas.ExpenseResponse)
def create_expense(
    schema: schemas.ExpenseCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    db_obj = Expense(**schema.model_dump())
    db_obj.recorded_by = current_user.id
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/expenses", response_model=List[schemas.ExpenseResponse])
def list_expenses(db: Session = Depends(get_db)):
    return db.query(Expense).all()

# ----------------- Staff Salaries -----------------

@router.post("/staff-salaries", response_model=schemas.StaffSalaryResponse)
def create_staff_salary(schema: schemas.StaffSalaryCreate, db: Session = Depends(get_db)):
    db_obj = StaffSalary(**schema.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/staff-salaries", response_model=List[schemas.StaffSalaryResponse])
def list_staff_salaries(db: Session = Depends(get_db)):
    return db.query(StaffSalary).all()
