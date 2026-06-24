"""
Models Package
===============
Import all models here so that:
1. Alembic can discover them for migrations
2. SQLAlchemy's Base.metadata has all tables registered
3. Relationships between models are properly resolved

This demonstrates the PACKAGE PATTERN — grouping related
modules and providing a clean public API.
"""

# Import all models to register them with SQLAlchemy
from app.models.user import User, Role, Permission, UserRole, RolePermission  # noqa
from app.models.course import Course  # noqa
from app.models.department import Department  # noqa
from app.models.student import Student, StudentSequence  # noqa
from app.models.teacher import Teacher  # noqa
from app.models.subject import Subject, SubjectTeacher  # noqa
from app.models.academic import (  # noqa
    Branch, SubjectType, Curriculum, CurriculumVersion, AcademicSemester,
    Section, ElectiveGroup, CurriculumSubject, StudentElective, FacultyAssignment,
)
from app.models.attendance import Attendance  # noqa
from app.models.marks import Marks  # noqa
from app.models.fee import Fee  # noqa
from app.models.library import LibraryBook, BookIssue  # noqa
from app.models.timetable_grid import TimetableVersion, TimetableSlot  # noqa
from app.models.notification import Notification  # noqa
from app.models.audit_log import AuditLog  # noqa
