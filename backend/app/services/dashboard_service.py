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
from collections import defaultdict
from datetime import date, datetime
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
from app.models.academic import Assignment, AssignmentSubmission, FacultyAssignment
from app.models.timetable_grid import TimetableSlot, TimetableVersion
from app.core.portfolio import get_faculty_portfolio
from app.services.academic_service import AcademicStructureService
from app.services.crud_services import TimetableGridService
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
                {
                    "type": "warning",
                    "title": "Attendance reporting",
                    "message": "Today’s reporting is incomplete for 3 departments.",
                    "action": "Review attendance",
                    "href": "/attendance",
                } if total_teachers > 0 else None,
                {
                    "type": "danger",
                    "title": "Outstanding fee balance",
                    "message": f"₹{pending_fees:,.0f} remains pending across student invoices.",
                    "action": "Review invoices",
                    "href": "/student-fees",
                } if pending_fees > 10000 else None
            ] if alert],
            "student_staff_ratio": round(total_students / total_teachers, 1) if total_teachers > 0 else 0,
        }


class TeacherDashboard(BaseDashboard):
    """Teacher dashboard — shows assigned subjects and attendance data."""

    def get_stats(self) -> Dict[str, Any]:
        teacher = self._user.teacher if self._user and self._user.teacher else None
        subjects = []
        week_at_a_glance = []
        at_risk_students = []

        if teacher:
            assignments = (
                self._db.query(FacultyAssignment)
                .filter(
                    FacultyAssignment.teacher_id == teacher.id,
                    FacultyAssignment.is_deleted.is_(False),
                )
                .order_by(FacultyAssignment.id)
                .all()
            )
            seen_subjects = set()
            for assignment in assignments:
                subject = assignment.curriculum_subject.subject
                if subject.id in seen_subjects:
                    continue
                seen_subjects.add(subject.id)
                subjects.append({
                    "id": subject.id,
                    "name": subject.name,
                    "code": subject.code,
                    "semester": assignment.curriculum_subject.semester.number,
                    "department_name": subject.department.name if subject.department else None,
                })

            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            period_times = ["09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM"]
            schedule = sorted(
                TimetableGridService(self._db).get_teacher_schedule(teacher.id),
                key=lambda item: (item.day_of_week, item.slot_index),
            )
            for slot in schedule[:8]:
                version = slot.version
                scope = [
                    f"Sem {version.semester}",
                    version.branch.code if version.branch else None,
                    f"Sec {version.section.code}" if version.section else None,
                ]
                week_at_a_glance.append({
                    "day": day_names[slot.day_of_week - 1] if 1 <= slot.day_of_week <= 6 else f"Day {slot.day_of_week}",
                    "time": period_times[slot.slot_index - 1] if 1 <= slot.slot_index <= 8 else f"Period {slot.slot_index}",
                    "subject": slot.subject.name if slot.subject else "Unassigned",
                    "room": " · ".join(part for part in scope if part),
                })

            portfolio = get_faculty_portfolio(self._db, teacher.id)
            if portfolio.student_ids:
                attendance_rows = (
                    self._db.query(Attendance)
                    .filter(
                        Attendance.student_id.in_(portfolio.student_ids),
                        Attendance.subject_id.in_(portfolio.subject_ids),
                        Attendance.is_deleted.is_(False),
                    )
                    .all()
                )
                totals = defaultdict(int)
                attended = defaultdict(int)
                for record in attendance_rows:
                    totals[record.student_id] += 1
                    status = record.status.value if hasattr(record.status, "value") else str(record.status)
                    if status in {"present", "late"}:
                        attended[record.student_id] += 1

                risk = []
                for student_id, total in totals.items():
                    percentage = round((attended[student_id] / total) * 100, 1) if total else 0
                    if percentage < 75:
                        risk.append((percentage, student_id))
                risk.sort()
                student_map = {
                    item.id: item for item in self._db.query(Student).filter(
                        Student.id.in_([student_id for _, student_id in risk[:5]]),
                        Student.is_deleted.is_(False),
                    ).all()
                } if risk else {}
                at_risk_students = [{
                    "name": student_map[student_id].user.full_name,
                    "reason": f"Attendance {percentage:.1f}%",
                    "id": student_id,
                } for percentage, student_id in risk[:5] if student_id in student_map]

        return {
            "assigned_subjects": len(subjects),
            "subjects": subjects,
            "stats": [
                {"label": "Assigned Subjects", "value": len(subjects), "icon": "bi-book", "color": "primary"},
                {"label": "Weekly Classes", "value": len(week_at_a_glance), "icon": "bi-calendar-week", "color": "info"},
                {"label": "Attendance Alerts", "value": len(at_risk_students), "icon": "bi-exclamation-triangle", "color": "warning"},
            ],
            "week_at_a_glance": week_at_a_glance,
            "at_risk_students": at_risk_students,
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
        deadline_tracker = []
        real_time_schedule = []

        # Build enrollment info from the student's own records
        enrollment = {}
        if student:
            att_repo = AttendanceRepository(self._db)
            stats = att_repo.get_student_attendance_stats(student.id)
            attendance_pct = stats["percentage"]

            total_student_fee = self._db.query(func.sum(StudentFee.amount)).filter(StudentFee.student_id == student.id, StudentFee.status.in_(["pending", "partial", "overdue"]), StudentFee.is_deleted == False).scalar() or 0
            total_student_paid = self._db.query(func.sum(Payment.amount)).join(StudentFee).filter(StudentFee.student_id == student.id, StudentFee.status.in_(["pending", "partial", "overdue"]), StudentFee.is_deleted == False, Payment.status == "success", Payment.is_deleted == False).scalar() or 0
            pending_fees = total_student_fee - total_student_paid
            total_subjects = len(
                AcademicStructureService(self._db).resolve_student_subjects(
                    student.id, student.current_semester
                )
            )

            submissions = (
                self._db.query(AssignmentSubmission)
                .join(Assignment, AssignmentSubmission.assignment_id == Assignment.id)
                .filter(
                    AssignmentSubmission.student_id == student.id,
                    AssignmentSubmission.status.in_(["pending", "submitted"]),
                    AssignmentSubmission.is_deleted.is_(False),
                    Assignment.is_deleted.is_(False),
                )
                .order_by(Assignment.due_date)
                .limit(6)
                .all()
            )
            now = datetime.now()
            for submission in submissions:
                due = submission.assignment.due_date
                days_left = (due.date() - now.date()).days
                urgency = "high" if days_left <= 2 else "medium" if days_left <= 7 else "low"
                deadline_tracker.append({
                    "task": submission.assignment.title,
                    "date": due.strftime("%b %d"),
                    "urgency": urgency,
                    "status": submission.status,
                })

            version = (
                self._db.query(TimetableVersion)
                .filter(
                    TimetableVersion.department_id == student.department_id,
                    TimetableVersion.course_id == student.course_id,
                    TimetableVersion.branch_id == student.branch_id,
                    TimetableVersion.section_id == student.section_id,
                    TimetableVersion.semester == student.current_semester,
                    TimetableVersion.status == "approved",
                    TimetableVersion.is_deleted.is_(False),
                )
                .order_by(TimetableVersion.version_number.desc())
                .first()
            )
            today_number = date.today().isoweekday()
            if version and today_number <= 6:
                period_times = ["09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM"]
                slots = (
                    self._db.query(TimetableSlot)
                    .filter(
                        TimetableSlot.version_id == version.id,
                        TimetableSlot.day_of_week == today_number,
                        TimetableSlot.is_deleted.is_(False),
                    )
                    .order_by(TimetableSlot.slot_index)
                    .all()
                )
                for slot in slots:
                    if not slot.subject:
                        continue
                    real_time_schedule.append({
                        "time": period_times[slot.slot_index - 1] if 1 <= slot.slot_index <= 8 else f"Period {slot.slot_index}",
                        "subject": slot.subject.name,
                        "room": f"Sem {version.semester} · Sec {version.section.code if version.section else student.section}",
                    })

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
                {"label": "Current Subjects", "value": total_subjects, "icon": "bi-book", "color": "info"},
                {"label": "Pending Fees", "value": f"₹{pending_fees:,.0f}", "icon": "bi-cash", "color": "warning"},
            ],
            "deadline_tracker": deadline_tracker,
            "real_time_schedule": real_time_schedule,
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
