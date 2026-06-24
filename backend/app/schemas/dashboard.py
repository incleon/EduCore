"""Dashboard Schemas — role-specific dashboard data."""
from typing import Optional, List
from pydantic import BaseModel


class DashboardStat(BaseModel):
    label: str
    value: int | float | str
    icon: str = "bi-info-circle"
    color: str = "primary"
    link: Optional[str] = None


class AdminDashboardData(BaseModel):
    total_students: int = 0
    total_teachers: int = 0
    total_departments: int = 0
    total_subjects: int = 0
    pending_fees: float = 0
    recent_students: list = []
    stats: List[DashboardStat] = []


class TeacherDashboardData(BaseModel):
    assigned_subjects: int = 0
    total_students: int = 0
    attendance_today: int = 0
    subjects: list = []
    stats: List[DashboardStat] = []


class StudentDashboardData(BaseModel):
    attendance_percentage: float = 0.0
    total_subjects: int = 0
    pending_fees: float = 0
    recent_marks: list = []
    stats: List[DashboardStat] = []


class AccountantDashboardData(BaseModel):
    total_fees: float = 0
    collected_fees: float = 0
    pending_fees: float = 0
    recent_payments: list = []
    stats: List[DashboardStat] = []


class HODDashboardData(BaseModel):
    department_name: str = ""
    total_teachers: int = 0
    total_students: int = 0
    total_subjects: int = 0
    stats: List[DashboardStat] = []


class LibrarianDashboardData(BaseModel):
    total_books: int = 0
    issued_books: int = 0
    overdue_books: int = 0
    stats: List[DashboardStat] = []
