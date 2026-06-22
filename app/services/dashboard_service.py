"""
Dashboard Service — Role-Based Dashboard Data
================================================

OOP Concepts Demonstrated:
--------------------------
1. FACTORY PATTERN: DashboardFactory creates role-specific dashboard objects
2. POLYMORPHISM: Each dashboard type overrides get_stats()
3. INHERITANCE: All dashboards inherit from BaseDashboard
4. ABSTRACTION: BaseDashboard is abstract (uses ABC)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.student import Student
from app.models.teacher import Teacher
from app.models.department import Department
from app.models.subject import Subject, SubjectTeacher
from app.models.fee import Fee
from app.models.library import LibraryBook, BookIssue
from app.models.attendance import Attendance
from app.models.marks import Marks
from app.repositories.concrete import (
    StudentRepository, TeacherRepository, DepartmentRepository,
    FeeRepository, LibraryBookRepository, BookIssueRepository,
    AttendanceRepository, SubjectRepository,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class BaseDashboard(ABC):
    """
    Abstract base dashboard — defines interface for all dashboards.

    OOP Concept: ABSTRACT BASE CLASS
    ─────────────────────────────────
    - Cannot be instantiated directly
    - All concrete dashboards MUST implement get_stats()
    - Enforces a consistent dashboard API
    """

    def __init__(self, db: Session, user=None):
        self._db = db
        self._user = user

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics. Must be implemented by subclasses."""
        pass


class AdminDashboard(BaseDashboard):
    """
    Admin dashboard — OVERRIDES get_stats() with admin-specific data.

    Demonstrates METHOD OVERRIDING (Polymorphism).
    """

    def get_stats(self) -> Dict[str, Any]:
        from app.models.user import User
        from app.models.audit_log import AuditLog
        
        total_students = self._db.query(Student).filter(Student.is_deleted == False).count()
        total_teachers = self._db.query(Teacher).filter(Teacher.is_deleted == False).count()
        total_departments = self._db.query(Department).filter(Department.is_deleted == False).count()
        total_subjects = self._db.query(Subject).filter(Subject.is_deleted == False).count()
        total_users = self._db.query(User).filter(User.is_deleted == False).count()

        pending_fees = (
            self._db.query(func.coalesce(func.sum(Fee.amount - Fee.paid_amount), 0))
            .filter(Fee.status.in_(["pending", "partial", "overdue"]), Fee.is_deleted == False)
            .scalar()
        ) or 0

        recent_students = (
            self._db.query(Student)
            .filter(Student.is_deleted == False)
            .order_by(Student.created_at.desc())
            .limit(5)
            .all()
        )
        
        # Fetch actual system activities
        recent_activities = (
            self._db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(10)
            .all()
        )
        
        activities_data = []
        for act in recent_activities:
            # We construct a human-readable text
            if act.details:
                text = act.details
            else:
                text = f"Action <strong>{act.action}</strong> performed on {act.resource}."
                
            activities_data.append({
                "time": act.created_at.strftime("%I:%M %p, %b %d") if act.created_at else "Just now",
                "text": text,
                "color": "#4f46e5" if act.action == "CREATE" else "#10b981" if act.action == "UPDATE" else "#f59e0b"
            })

        # ── TREND DATA CALCULATION (Last 6 Months) ──
        from datetime import datetime
        import calendar
        from sqlalchemy import extract

        today = datetime.now()
        months_labels = []
        enrollment_data = []
        revenue_data = []

        for i in range(5, -1, -1):
            y, m = today.year, today.month
            m -= i
            while m <= 0:
                y -= 1
                m += 12
            
            months_labels.append(calendar.month_abbr[m])
            
            enrollments = self._db.query(Student).filter(
                Student.is_deleted == False,
                extract('year', Student.created_at) == y,
                extract('month', Student.created_at) == m
            ).count()
            enrollment_data.append(enrollments)
            
            revenue = self._db.query(func.coalesce(func.sum(Fee.paid_amount), 0)).filter(
                Fee.is_deleted == False,
                extract('year', Fee.updated_at) == y,
                extract('month', Fee.updated_at) == m
            ).scalar() or 0
            revenue_data.append(float(revenue))

        return {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_departments": total_departments,
            "total_subjects": total_subjects,
            "total_users": total_users,
            "pending_fees": float(pending_fees),
            "recent_students": recent_students,
            "recent_activities": activities_data,
            "trend_labels": months_labels,
            "trend_enrollments": enrollment_data,
            "trend_revenue": revenue_data,
            "stats": [
                {"label": "Total Students", "value": total_students, "icon": "bi-people", "color": "primary"},
                {"label": "Total Teachers", "value": total_teachers, "icon": "bi-person-badge", "color": "success"},
                {"label": "Departments", "value": total_departments, "icon": "bi-building", "color": "info"},
                {"label": "Total Subjects", "value": total_subjects, "icon": "bi-book", "color": "info"},
                {"label": "Total Users", "value": total_users, "icon": "bi-person-gear", "color": "dark"},
                {"label": "Pending Fees", "value": f"₹{pending_fees:,.0f}", "icon": "bi-cash-stack", "color": "warning"},
            ],
        }


class TeacherDashboard(BaseDashboard):
    """Teacher dashboard — shows assigned subjects and attendance data."""

    def get_stats(self) -> Dict[str, Any]:
        teacher = None
        if self._user and self._user.teacher:
            teacher = self._user.teacher

        assigned_subjects = 0
        subjects = []
        
        if teacher:
            # Get subjects directly assigned to this teacher via teacher_id
            assigned_subject_records = (
                self._db.query(Subject)
                .filter(Subject.teacher_id == teacher.id, Subject.is_deleted == False)
                .all()
            )
            assigned_subjects = len(assigned_subject_records)
            
            for subject in assigned_subject_records:
                subjects.append({
                    "id": subject.id,
                    "name": subject.name,
                    "code": subject.code,
                    "semester": subject.semester,
                    "department_name": subject.department.name if subject.department else "N/A",
                })

        return {
            "assigned_subjects": assigned_subjects,
            "subjects": subjects,
            "stats": [
                {"label": "Assigned Subjects", "value": assigned_subjects, "icon": "bi-book", "color": "primary"},
            ],
        }


class StudentDashboard(BaseDashboard):
    """Student dashboard — shows personal academic data."""

    def get_stats(self) -> Dict[str, Any]:
        student = None
        if self._user and self._user.student:
            student = self._user.student

        attendance_pct = 0.0
        total_subjects = 0
        pending_fees = 0.0

        if student:
            att_repo = AttendanceRepository(self._db)
            stats = att_repo.get_student_attendance_stats(student.id)
            attendance_pct = stats["percentage"]

            pending_fees = (
                self._db.query(func.coalesce(func.sum(Fee.amount - Fee.paid_amount), 0))
                .filter(
                    Fee.student_id == student.id,
                    Fee.status.in_(["pending", "partial", "overdue"]),
                    Fee.is_deleted == False,
                )
                .scalar()
            ) or 0

        return {
            "attendance_percentage": attendance_pct,
            "total_subjects": total_subjects,
            "pending_fees": float(pending_fees),
            "stats": [
                {"label": "Attendance", "value": f"{attendance_pct}%", "icon": "bi-calendar-check", "color": "primary"},
                {"label": "Pending Fees", "value": f"₹{pending_fees:,.0f}", "icon": "bi-cash", "color": "warning"},
            ],
        }


class AccountantDashboard(BaseDashboard):
    def get_stats(self) -> Dict[str, Any]:
        fee_repo = FeeRepository(self._db)
        total_pending = fee_repo.get_total_pending()
        total_collected = fee_repo.get_total_collected()

        return {
            "total_collected": total_collected,
            "pending_fees": total_pending,
            "stats": [
                {"label": "Collected", "value": f"₹{total_collected:,.0f}", "icon": "bi-cash-stack", "color": "success"},
                {"label": "Pending", "value": f"₹{total_pending:,.0f}", "icon": "bi-exclamation-triangle", "color": "danger"},
            ],
        }


class HODDashboard(BaseDashboard):
    def get_stats(self) -> Dict[str, Any]:
        dept = None
        if self._user and self._user.teacher and self._user.teacher.department:
            dept = self._user.teacher.department

        dept_name = dept.name if dept else "N/A"
        teacher_count = 0
        student_count = 0

        if dept:
            teacher_count = self._db.query(Teacher).filter(
                Teacher.department_id == dept.id, Teacher.is_deleted == False
            ).count()
            student_count = self._db.query(Student).filter(
                Student.department_id == dept.id, Student.is_deleted == False
            ).count()

        return {
            "department_name": dept_name,
            "total_teachers": teacher_count,
            "total_students": student_count,
            "stats": [
                {"label": "Department", "value": dept_name, "icon": "bi-building", "color": "info"},
                {"label": "Teachers", "value": teacher_count, "icon": "bi-person-badge", "color": "success"},
                {"label": "Students", "value": student_count, "icon": "bi-people", "color": "primary"},
            ],
        }


class LibrarianDashboard(BaseDashboard):
    def get_stats(self) -> Dict[str, Any]:
        total_books = self._db.query(LibraryBook).filter(LibraryBook.is_deleted == False).count()
        issued = self._db.query(BookIssue).filter(BookIssue.status == "issued", BookIssue.is_deleted == False).count()
        overdue = BookIssueRepository(self._db).get_overdue_count()

        return {
            "total_books": total_books,
            "issued_books": issued,
            "overdue_books": overdue,
            "stats": [
                {"label": "Total Books", "value": total_books, "icon": "bi-book", "color": "primary"},
                {"label": "Issued", "value": issued, "icon": "bi-bookmark", "color": "info"},
                {"label": "Overdue", "value": overdue, "icon": "bi-exclamation-circle", "color": "danger"},
            ],
        }




# ══════════════════════════════════════════════════════════════
# DASHBOARD FACTORY
# ══════════════════════════════════════════════════════════════

class DashboardFactory:
    """
    FACTORY PATTERN: Creates role-specific dashboard objects.

    Why Factory Pattern?
    - Client code doesn't need to know concrete dashboard classes
    - New dashboard types can be added without modifying client code (OCP)
    - Centralizes dashboard creation logic

    POLYMORPHISM in action:
    - DashboardFactory.create("admin", db) → AdminDashboard
    - DashboardFactory.create("student", db) → StudentDashboard
    - Both return BaseDashboard, but get_stats() behaves differently
    """

    _dashboards = {
        "admin": AdminDashboard,
        "teacher": TeacherDashboard,
        "student": StudentDashboard,
        "accountant": AccountantDashboard,
        "hod": HODDashboard,
        "librarian": LibrarianDashboard,
    }

    @classmethod
    def create(cls, role: str, db: Session, user=None) -> BaseDashboard:
        """
        CLASS METHOD + FACTORY: Create dashboard by role name.

        Args:
            role: Role name (e.g., "admin", "student")
            db: Database session
            user: Current user (needed for student/teacher dashboards)

        Returns:
            Concrete BaseDashboard subclass instance
        """
        dashboard_class = cls._dashboards.get(role, AdminDashboard)
        return dashboard_class(db, user)

    @classmethod
    def get_available_roles(cls) -> list:
        """Get list of roles with dashboards."""
        return list(cls._dashboards.keys())
