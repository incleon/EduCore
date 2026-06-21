"""
Student Model
===============

OOP Concepts: Inheritance, One-to-One, Many-to-One, One-to-Many, Composition
SQLAlchemy: Relationships, Foreign Keys, Cascade Delete
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Date, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database.base import BaseModel


class EnrollmentStatus(str, enum.Enum):
    """Student enrollment status."""
    ACTIVE = "active"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"
    DROPPED = "dropped"


class Student(BaseModel):
    """
    Student model — represents a student enrolled in the college.

    OOP Concepts:
    ──────────────
    1. INHERITANCE: extends BaseModel
    2. ONE-TO-ONE with User (COMPOSITION):
       A Student IS-A User. If the User is deleted, the Student is also deleted.
       This is Composition — Student cannot exist without User.
    3. MANY-TO-ONE with Department (AGGREGATION):
       A Student belongs to a Department, but the department exists independently.
    4. ONE-TO-MANY with Attendance, Marks, Fees (COMPOSITION):
       Attendance/Marks/Fees belong to a student.

    Table: students
    ────────────────
    Linked to users table via user_id (ONE-TO-ONE).
    Linked to departments table via department_id (MANY-TO-ONE).
    """

    __tablename__ = "students"

    # ── Foreign Keys ─────────────────────────────────────────
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        doc="Link to user account (ONE-TO-ONE)",
    )
    department_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Department (MANY-TO-ONE)",
    )

    # ── Student-Specific Fields ──────────────────────────────
    student_id = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        doc="Auto-generated student ID (Format: YYBBSSS)",
    )
    enrollment_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique enrollment/registration number",
    )
    date_of_birth = Column(Date, nullable=True)
    admission_date = Column(Date, nullable=True)
    semester = Column(Integer, default=1, nullable=False)
    section = Column(String(10), nullable=True)
    guardian_name = Column(String(255), nullable=True)
    guardian_phone = Column(String(20), nullable=True)
    father_name = Column(String(255), nullable=True)
    mother_name = Column(String(255), nullable=True)
    blood_group = Column(String(5), nullable=True)
    personal_email = Column(String(255), nullable=True, doc="Student's personal email for notifications")
    initial_password = Column(String(255), nullable=True)
    status = Column(
        SAEnum(EnrollmentStatus),
        default=EnrollmentStatus.ACTIVE,
        nullable=False,
    )

    # ── RELATIONSHIPS ────────────────────────────────────────
    # ONE-TO-ONE: Student belongs to a User (COMPOSITION)
    user = relationship(
        "User",
        back_populates="student",
        lazy="selectin",
    )

    # MANY-TO-ONE: Student belongs to a Department (AGGREGATION)
    department = relationship(
        "Department",
        back_populates="students",
        lazy="selectin",
    )

    # ONE-TO-MANY: Student has many attendance records
    attendance_records = relationship(
        "Attendance",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # ONE-TO-MANY: Student has many marks records
    marks_records = relationship(
        "Marks",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # ONE-TO-MANY: Student has many fee records
    fee_records = relationship(
        "Fee",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # ONE-TO-MANY: Student has many book issues
    book_issues = relationship(
        "BookIssue",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __str__(self) -> str:
        return f"Student: {self.enrollment_number}"

    def __repr__(self) -> str:
        return (
            f"<Student(id={self.id}, enrollment='{self.enrollment_number}', "
            f"dept_id={self.department_id})>"
        )
