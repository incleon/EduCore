"""
Subject Model + SubjectTeacher Association
=============================================

OOP Concepts: Many-to-Many (Teacher ↔ Subject), Association table
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database.base import BaseModel


class Subject(BaseModel):
    """
    Subject model (e.g., Data Structures, Calculus).

    Relationships:
    - MANY-TO-ONE: Subject belongs to Department
    - ONE-TO-ONE: Subject may be assigned to a Teacher
    - MANY-TO-MANY: Subject ↔ Teacher via SubjectTeacher
    - ONE-TO-MANY: Subject → Attendance, Marks
    """

    __tablename__ = "subjects"

    name = Column(String(200), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    credits = Column(Integer, default=3, nullable=False)
    semester = Column(Integer, nullable=False)
    type = Column(String(50), default="theory", nullable=False)

    department_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    teacher_id = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── RELATIONSHIPS ────────────────────────────────────────
    department = relationship("Department", back_populates="subjects", lazy="selectin")
    teacher = relationship("Teacher", backref="assigned_subjects", lazy="selectin")

    # MANY-TO-MANY with Teacher
    teacher_assignments = relationship(
        "SubjectTeacher",
        back_populates="subject",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    attendance_records = relationship(
        "Attendance", back_populates="subject", lazy="dynamic"
    )
    marks_records = relationship(
        "Marks", back_populates="subject", lazy="dynamic"
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def __repr__(self) -> str:
        return f"<Subject(id={self.id}, code='{self.code}')>"


class SubjectTeacher(BaseModel):
    """
    Association table: Subject ↔ Teacher (Many-to-Many).

    OOP Concept: ASSOCIATION
    This models the "teaches" relationship between Teacher and Subject.
    """

    __tablename__ = "subject_teachers"

    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    teacher_id = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    section = Column(String(10), nullable=True)

    subject = relationship("Subject", back_populates="teacher_assignments")
    teacher = relationship("Teacher", back_populates="subject_assignments")

    def __repr__(self) -> str:
        return f"<SubjectTeacher(subj={self.subject_id}, teacher={self.teacher_id})>"
