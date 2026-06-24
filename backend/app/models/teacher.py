"""
Teacher Model
===============

OOP Concepts: Inheritance, One-to-One, Many-to-One, Many-to-Many
SQLAlchemy: Relationships, Association table (SubjectTeacher)
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Date, Text
from sqlalchemy.orm import relationship

from app.database.base import BaseModel


class Teacher(BaseModel):
    """
    Teacher model — represents a faculty member.

    OOP Concepts:
    ──────────────
    1. ONE-TO-ONE with User (COMPOSITION): Teacher IS-A User
    2. MANY-TO-ONE with Department (AGGREGATION): Teacher belongs to dept
    3. MANY-TO-MANY with Subject (ASSOCIATION): Teacher teaches subjects

    Table: teachers
    ────────────────
    """

    __tablename__ = "teachers"

    # ── Foreign Keys ─────────────────────────────────────────
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    department_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    branch_id = Column(
        Integer,
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ── Teacher-Specific Fields ──────────────────────────────
    faculty_id = Column(String(20), unique=True, nullable=False, index=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    designation = Column(String(100), nullable=True)
    specialization = Column(String(200), nullable=True)
    qualification = Column(String(200), nullable=True)
    joining_date = Column(Date, nullable=True)
    experience_years = Column(Integer, default=0)
    bio = Column(Text, nullable=True)

    # ── RELATIONSHIPS ────────────────────────────────────────
    user = relationship("User", back_populates="teacher", lazy="selectin")
    department = relationship(
        "Department",
        back_populates="teachers",
        foreign_keys=[department_id],
        lazy="selectin",
    )

    branch = relationship(
        "Branch",
        back_populates="faculty",
        lazy="selectin",
    )

    faculty_assignments = relationship(
        "FacultyAssignment",
        back_populates="teacher",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # MANY-TO-MANY: Teacher teaches many subjects via SubjectTeacher
    subject_assignments = relationship(
        "SubjectTeacher",
        back_populates="teacher",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ONE-TO-MANY: Teacher marks attendance
    attendance_records = relationship(
        "Attendance",
        back_populates="teacher",
        lazy="dynamic",
    )

    def __str__(self) -> str:
        return f"Teacher: {self.employee_id}"

    def __repr__(self) -> str:
        return f"<Teacher(id={self.id}, emp_id='{self.employee_id}')>"
