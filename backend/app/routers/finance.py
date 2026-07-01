"""
Finance API Endpoints
=====================
CRUD operations for Accountant dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.core.dependencies import get_db
from app.core.permissions import PermissionChecker, RoleChecker
from app.models.user import User
from app.models.finance import (
    FeeStructure, StudentFee, Payment, Expense, ExpenseCategory, StaffSalary,
    FeeStatus, PaymentStatus
)
from app.models.student import Student
from app.schemas import finance as schemas
router = APIRouter()
legacy_router = APIRouter(prefix="/api/fees", tags=["Finance compatibility"])


def _course_brief(course):
    return {"id": course.id, "name": course.name, "code": course.code} if course else None


def _user_brief(user):
    return {"id": user.id, "full_name": user.full_name, "email": user.email} if user else None


def _fee_structure(record):
    return {
        "id": record.id, "name": record.name, "amount": record.amount,
        "course_id": record.course_id, "course": _course_brief(record.course),
        "academic_year": record.academic_year, "semester": record.semester,
        "description": record.description, "created_at": record.created_at,
    }


def _student_fee(record):
    student = record.student
    return {
        "id": record.id, "student_id": record.student_id,
        "student": ({"id": student.id, "student_id": student.student_id, "user": _user_brief(student.user)} if student else None),
        "fee_structure_id": record.fee_structure_id, "title": record.title,
        "amount": record.amount, "due_date": record.due_date, "status": record.status,
        "remarks": record.remarks, "paid_amount": record.paid_amount,
        "balance": record.balance, "created_at": record.created_at,
    }


def _payment(record):
    invoice = record.student_fee
    return {
        "id": record.id, "student_fee_id": record.student_fee_id,
        "student_fee": _student_fee(invoice) if invoice else None,
        "amount": record.amount, "payment_date": record.payment_date,
        "payment_method": record.payment_method,
        "transaction_reference": record.transaction_reference,
        "status": record.status, "remarks": record.remarks, "created_at": record.created_at,
    }


def _expense(record):
    return {
        "id": record.id, "title": record.title, "amount": record.amount,
        "expense_date": record.expense_date, "category_id": record.category_id,
        "category": ({"id": record.category.id, "name": record.category.name} if record.category else None),
        "receipt_url": record.receipt_url, "recorded_by": record.recorded_by,
        "recorded_by_user": _user_brief(record.recorded_by_user),
        "remarks": record.remarks, "created_at": record.created_at,
    }


def _salary(record):
    return {
        "id": record.id, "user_id": record.user_id, "user": _user_brief(record.user),
        "amount": record.amount, "payment_date": record.payment_date,
        "month": record.month, "year": record.year,
        "payment_method": record.payment_method,
        "transaction_reference": record.transaction_reference,
        "status": "paid", "remarks": record.remarks, "created_at": record.created_at,
    }


def _update(db, model, record_id, values):
    record = db.query(model).filter(model.id == record_id, model.is_deleted.is_(False)).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    for key, value in values.items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


def _delete(db, model, record_id):
    record = db.query(model).filter(model.id == record_id, model.is_deleted.is_(False)).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    record.soft_delete()
    db.commit()
    return {"message": f"{model.__name__} deleted successfully"}


def _page(query, page, page_size, serializer):
    total = query.order_by(None).count()
    records = query.order_by(query.column_descriptions[0]["entity"].id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [serializer(item) for item in records],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

# ----------------- Dashboard -----------------

@router.get("/dashboard-stats")
def get_finance_dashboard_stats(db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
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
def create_fee_structure(schema: schemas.FeeStructureCreate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    db_obj = FeeStructure(**schema.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/fee-structures")
def list_fee_structures(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    query = db.query(FeeStructure).options(selectinload(FeeStructure.course)).filter(FeeStructure.is_deleted.is_(False))
    return _page(query, page, page_size, _fee_structure)

@router.put("/fee-structures/{record_id}")
def update_fee_structure(record_id: int, schema: schemas.FeeStructureUpdate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _fee_structure(_update(db, FeeStructure, record_id, schema.model_dump(exclude_unset=True)))

@router.delete("/fee-structures/{record_id}")
def delete_fee_structure(record_id: int, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _delete(db, FeeStructure, record_id)

# ----------------- Student Fees (Invoices) -----------------

@router.post("/student-fees", response_model=schemas.StudentFeeResponse)
def create_student_fee(schema: schemas.StudentFeeCreate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    db_obj = StudentFee(**schema.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/student-fees")
def list_student_fees(student_id: Optional[int] = None, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_fees"]))):
    query = db.query(StudentFee).options(
        selectinload(StudentFee.student).selectinload(Student.user),
        selectinload(StudentFee.payments),
    ).filter(StudentFee.is_deleted.is_(False))
    if current_user.student:
        student_id = current_user.student.id
    if student_id:
        query = query.filter(StudentFee.student_id == student_id)
    return _page(query, page, page_size, _student_fee)

@router.put("/student-fees/{record_id}")
def update_student_fee(record_id: int, schema: schemas.StudentFeeUpdate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _student_fee(_update(db, StudentFee, record_id, schema.model_dump(exclude_unset=True)))

@router.delete("/student-fees/{record_id}")
def delete_student_fee(record_id: int, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _delete(db, StudentFee, record_id)

# ----------------- Payments -----------------

@router.post("/payments", response_model=schemas.PaymentResponse)
def create_payment(schema: schemas.PaymentCreate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    db_obj = Payment(**schema.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/payments")
def list_payments(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_fees"]))):
    query = db.query(Payment).options(
        selectinload(Payment.student_fee).selectinload(StudentFee.student),
        selectinload(Payment.student_fee).selectinload(StudentFee.payments),
    ).filter(Payment.is_deleted.is_(False))
    if current_user.student:
        query = query.join(StudentFee).filter(StudentFee.student_id == current_user.student.id)
    return _page(query, page, page_size, _payment)

@router.put("/payments/{record_id}")
def update_payment(record_id: int, schema: schemas.PaymentUpdate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _payment(_update(db, Payment, record_id, schema.model_dump(exclude_unset=True)))

@router.delete("/payments/{record_id}")
def delete_payment(record_id: int, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _delete(db, Payment, record_id)

# ----------------- Expense Categories -----------------

@router.post("/expense-categories", response_model=schemas.ExpenseCategoryResponse)
def create_expense_category(schema: schemas.ExpenseCategoryCreate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    db_obj = ExpenseCategory(**schema.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/expense-categories", response_model=List[schemas.ExpenseCategoryResponse])
def list_expense_categories(db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return db.query(ExpenseCategory).all()

# ----------------- Expenses -----------------

@router.post("/expenses", response_model=schemas.ExpenseResponse)
def create_expense(
    schema: schemas.ExpenseCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(RoleChecker(["admin", "accountant"]))
):
    db_obj = Expense(**schema.model_dump())
    db_obj.recorded_by = current_user.id
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/expenses")
def list_expenses(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    query = db.query(Expense).options(selectinload(Expense.category), selectinload(Expense.recorded_by_user)).filter(Expense.is_deleted.is_(False))
    return _page(query, page, page_size, _expense)

@router.put("/expenses/{record_id}")
def update_expense(record_id: int, schema: schemas.ExpenseUpdate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _expense(_update(db, Expense, record_id, schema.model_dump(exclude_unset=True)))

@router.delete("/expenses/{record_id}")
def delete_expense(record_id: int, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _delete(db, Expense, record_id)

# ----------------- Staff Salaries -----------------

@router.post("/staff-salaries", response_model=schemas.StaffSalaryResponse)
def create_staff_salary(schema: schemas.StaffSalaryCreate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    db_obj = StaffSalary(**schema.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/staff-salaries")
def list_staff_salaries(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    query = db.query(StaffSalary).options(selectinload(StaffSalary.user)).filter(StaffSalary.is_deleted.is_(False))
    return _page(query, page, page_size, _salary)

@router.put("/staff-salaries/{record_id}")
def update_staff_salary(record_id: int, schema: schemas.StaffSalaryUpdate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _salary(_update(db, StaffSalary, record_id, schema.model_dump(exclude_unset=True)))

@router.delete("/staff-salaries/{record_id}")
def delete_staff_salary(record_id: int, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _delete(db, StaffSalary, record_id)

@router.get("/salaries")
def list_salaries(db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return list_staff_salaries(1, 100, db, current_user)


@legacy_router.post("", status_code=201)
def create_legacy_fee(schema: schemas.LegacyFeeCreate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    record = StudentFee(
        student_id=schema.student_id,
        title=schema.fee_type.replace("_", " ").title(),
        amount=schema.amount,
        due_date=schema.due_date,
        status=FeeStatus.PENDING,
        remarks=schema.remarks,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _student_fee(record)


@legacy_router.put("/{fee_id}")
def update_legacy_fee(fee_id: int, schema: schemas.LegacyFeeUpdate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    values = schema.model_dump(exclude_unset=True)
    if "fee_type" in values:
        values["title"] = values.pop("fee_type").replace("_", " ").title()
    return _student_fee(_update(db, StudentFee, fee_id, values))


@legacy_router.delete("/{fee_id}")
def delete_legacy_fee(fee_id: int, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    return _delete(db, StudentFee, fee_id)


@legacy_router.post("/{fee_id}/pay", status_code=201)
def pay_legacy_fee(fee_id: int, schema: schemas.LegacyFeePayment, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin", "accountant"]))):
    invoice = db.query(StudentFee).filter(StudentFee.id == fee_id, StudentFee.is_deleted.is_(False)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="StudentFee not found")
    payment = Payment(
        student_fee_id=invoice.id,
        amount=schema.paid_amount,
        payment_date=datetime.utcnow().date(),
        payment_method=schema.payment_method,
        transaction_reference=schema.transaction_reference,
        status=PaymentStatus.SUCCESS,
    )
    db.add(payment)
    db.flush()
    total_paid = sum(item.amount for item in invoice.payments if item.status == PaymentStatus.SUCCESS) + schema.paid_amount
    invoice.status = FeeStatus.PAID if total_paid >= invoice.amount else FeeStatus.PARTIAL
    db.commit()
    db.refresh(payment)
    return _payment(payment)
