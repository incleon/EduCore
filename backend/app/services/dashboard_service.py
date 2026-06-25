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
from app.models.finance import StudentFee, Payment
from app.models.library import LibraryBook, BookIssue
from app.models.attendance import Attendance
from app.models.marks import Marks
from app.repositories.concrete import (
    StudentRepository, TeacherRepository, DepartmentRepository,
    LibraryBookRepository, BookIssueRepository,
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

        total_fee = self._db.query(func.sum(StudentFee.amount)).filter(StudentFee.status.in_(["pending", "partial", "overdue"]), StudentFee.is_deleted == False).scalar() or 0
        total_paid = self._db.query(func.sum(Payment.amount)).join(StudentFee).filter(StudentFee.status.in_(["pending", "partial", "overdue"]), StudentFee.is_deleted == False, Payment.status == "success", Payment.is_deleted == False).scalar() or 0
        pending_fees = total_fee - total_paid

        recent_students_records = (
            self._db.query(Student)
            .filter(Student.is_deleted == False)
            .order_by(Student.created_at.desc())
            .limit(5)
            .all()
        )
        recent_students = [
            {"id": s.id, "student_id": s.student_id}
            for s in recent_students_records
        ]
        
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
            if m == 12:
                next_y, next_m = y + 1, 1
            else:
                next_y, next_m = y, m + 1
                
            start_date = datetime(y, m, 1)
            end_date = datetime(next_y, next_m, 1)
            
            enrollments = self._db.query(Student).filter(
                Student.is_deleted == False,
                Student.created_at >= start_date,
                Student.created_at < end_date
            ).count()
            enrollment_data.append(enrollments)
            
            revenue = self._db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
                Payment.is_deleted == False,
                Payment.status == "success",
                Payment.payment_date >= start_date.date(),
                Payment.payment_date < end_date.date()
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
            "system_alerts": [alert for alert in [
                {"type": "warning", "message": "Attendance reporting is incomplete for 3 departments today."} if total_teachers > 0 else None,
                {"type": "danger", "message": f"High pending fee ratio: ₹{pending_fees:,.0f} outstanding."} if pending_fees > 10000 else None
            ] if alert],
            "student_staff_ratio": round(total_students / total_teachers, 1) if total_teachers > 0 else 0,
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
            "week_at_a_glance": [
                {"day": "Today", "time": "10:00 AM", "subject": "Data Structures", "room": "Room 101"},
                {"day": "Today", "time": "01:00 PM", "subject": "Algorithms", "room": "Room 102"}
            ],
            "at_risk_students": [
                {"name": "John Doe", "reason": "Low Attendance (45%)", "id": 1},
                {"name": "Jane Smith", "reason": "Failed Midterm", "id": 2}
            ]
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

        # Build enrollment info from the student's own records
        enrollment = {}
        if student:
            att_repo = AttendanceRepository(self._db)
            stats = att_repo.get_student_attendance_stats(student.id)
            attendance_pct = stats["percentage"]

            total_student_fee = self._db.query(func.sum(StudentFee.amount)).filter(StudentFee.student_id == student.id, StudentFee.status.in_(["pending", "partial", "overdue"]), StudentFee.is_deleted == False).scalar() or 0
            total_student_paid = self._db.query(func.sum(Payment.amount)).join(StudentFee).filter(StudentFee.student_id == student.id, StudentFee.status.in_(["pending", "partial", "overdue"]), StudentFee.is_deleted == False, Payment.status == "success", Payment.is_deleted == False).scalar() or 0
            pending_fees = total_student_fee - total_student_paid

            enrollment = {
                "student_id": student.student_id,
                "enrollment_number": student.enrollment_number,
                "department": student.department.name if student.department else None,
                "course": student.course.name if student.course else None,
                "branch": student.branch.name if student.branch else None,
                "curriculum_version": student.curriculum_version.title if student.curriculum_version else None,
                "current_semester": student.current_semester,
                "section": student.academic_section.code if student.academic_section else student.section,
                "admission_year": student.admission_year,
                "status": student.status.value if student.status else None,
            }

        return {
            "attendance_percentage": attendance_pct,
            "total_subjects": total_subjects,
            "pending_fees": float(pending_fees),
            "enrollment": enrollment,
            "stats": [
                {"label": "Attendance", "value": f"{attendance_pct}%", "icon": "bi-calendar-check", "color": "primary"},
                {"label": "Pending Fees", "value": f"₹{pending_fees:,.0f}", "icon": "bi-cash", "color": "warning"},
            ],
            "deadline_tracker": [
                {"task": "Midterm Exam", "date": "Oct 15", "urgency": "high"},
                {"task": "Physics Lab Report", "date": "Oct 18", "urgency": "medium"}
            ],
            "real_time_schedule": [
                {"time": "09:00 AM", "subject": "Physics 101", "room": "Lab 3"},
                {"time": "11:00 AM", "subject": "Calculus", "room": "Room 402"}
            ]
        }


class AccountantDashboard(BaseDashboard):
    def get_stats(self) -> Dict[str, Any]:
        total_fee = self._db.query(func.sum(StudentFee.amount)).filter(StudentFee.status.in_(["pending", "partial", "overdue"]), StudentFee.is_deleted == False).scalar() or 0
        total_paid_for_pending = self._db.query(func.sum(Payment.amount)).join(StudentFee).filter(StudentFee.status.in_(["pending", "partial", "overdue"]), StudentFee.is_deleted == False, Payment.status == "success", Payment.is_deleted == False).scalar() or 0
        total_pending = total_fee - total_paid_for_pending
        
        total_collected = self._db.query(func.sum(Payment.amount)).filter(Payment.status == "success", Payment.is_deleted == False).scalar() or 0

        return {
            "total_collected": total_collected,
            "pending_fees": total_pending,
            "stats": [
                {"label": "Collected", "value": f"₹{total_collected:,.0f}", "icon": "bi-cash-stack", "color": "success"},
                {"label": "Pending", "value": f"₹{total_pending:,.0f}", "icon": "bi-exclamation-triangle", "color": "danger"},
            ],
            "high_risk_defaulters": [
                {"name": "Mike Ross", "amount": 45000, "days_overdue": 120},
                {"name": "Harvey Specter", "amount": 32000, "days_overdue": 90}
            ],
            "revenue_breakdown": [
                {"category": "Tuition", "amount": float(total_collected) * 0.8},
                {"category": "Library Fines", "amount": float(total_collected) * 0.05},
                {"category": "Transport", "amount": float(total_collected) * 0.15}
            ]
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
            "at_risk_subjects": [
                {"name": "Advanced Math", "issue": "High Failure Rate (30%)"},
                {"name": "Operating Systems", "issue": "Low Attendance Avg (65%)"}
            ],
            "workload_distribution": [
                {"teacher": "Dr. Smith", "hours": 18},
                {"teacher": "Prof. Alan", "hours": 24},
                {"teacher": "Dr. Clara", "hours": 12}
            ]
        }


class LibrarianDashboard(BaseDashboard):
    def get_stats(self) -> Dict[str, Any]:
        from datetime import datetime
        import calendar
        from sqlalchemy import extract
        from app.models.student import Student
        from app.models.user import User
        
        total_books = self._db.query(LibraryBook).filter(LibraryBook.is_deleted == False).count()
        issued = self._db.query(BookIssue).filter(BookIssue.status == "issued", BookIssue.is_deleted == False).count()
        overdue = BookIssueRepository(self._db).get_overdue_count()
        
        total_fines = (
            self._db.query(func.coalesce(func.sum(BookIssue.fine_amount), 0))
            .filter(BookIssue.is_deleted == False, BookIssue.fine_paid == True)
            .scalar()
        ) or 0

        # ── TREND DATA CALCULATION (Last 6 Months) ──
        today = datetime.now()
        months_labels = []
        issues_data = []
        returns_data = []

        for i in range(5, -1, -1):
            y, m = today.year, today.month
            m -= i
            while m <= 0:
                y -= 1
                m += 12
            
            months_labels.append(calendar.month_abbr[m])
            if m == 12:
                next_y, next_m = y + 1, 1
            else:
                next_y, next_m = y, m + 1
                
            start_date = datetime(y, m, 1)
            end_date = datetime(next_y, next_m, 1)
            
            monthly_issues = self._db.query(BookIssue).filter(
                BookIssue.is_deleted == False,
                BookIssue.issue_date >= start_date.date(),
                BookIssue.issue_date < end_date.date()
            ).count()
            issues_data.append(monthly_issues)
            
            monthly_returns = self._db.query(BookIssue).filter(
                BookIssue.is_deleted == False,
                BookIssue.return_date >= start_date.date(),
                BookIssue.return_date < end_date.date(),
                BookIssue.status == "returned"
            ).count()
            returns_data.append(monthly_returns)

        # ── RECENT ACTIVITY ──
        recent_issues = (
            self._db.query(BookIssue)
            .filter(BookIssue.is_deleted == False)
            .order_by(BookIssue.created_at.desc())
            .limit(5)
            .all()
        )
        activities_data = []
        for act in recent_issues:
            action_type = "issued" if act.status == "issued" else act.status
            student_name = act.student.user.full_name if (act.student and act.student.user) else "a student"
            book_title = act.book.title if act.book else "a book"
            
            text = f"Book <strong>{book_title}</strong> was {action_type} to <strong>{student_name}</strong>."
            activities_data.append({
                "time": act.created_at.strftime("%I:%M %p, %b %d") if act.created_at else "Just now",
                "text": text,
                "color": "#10b981" if act.status == "returned" else "#4f46e5" if act.status == "issued" else "#f59e0b"
            })

        return {
            "total_books": total_books,
            "issued_books": issued,
            "overdue_books": overdue,
            "trend_labels": months_labels,
            "trend_issues": issues_data,
            "trend_returns": returns_data,
            "recent_activities": activities_data,
            "stats": [
                {"label": "Total Books", "value": total_books, "icon": "bi-book", "color": "primary"},
                {"label": "Active Issues", "value": issued, "icon": "bi-bookmark", "color": "info"},
                {"label": "Overdue", "value": overdue, "icon": "bi-exclamation-circle", "color": "danger"},
                {"label": "Fines Collected", "value": f"₹{total_fines:,.0f}", "icon": "bi-cash", "color": "success"},
            ],
            "low_stock_alerts": [
                {"title": "Introduction to Algorithms", "available": 0, "requests": 15},
                {"title": "Clean Code", "available": 1, "requests": 8}
            ],
            "overdue_actions": [
                {"student": "Rachel Zane", "book": "Design Patterns", "days_overdue": 14},
                {"student": "Louis Litt", "book": "Constitutional Law", "days_overdue": 21}
            ]
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
