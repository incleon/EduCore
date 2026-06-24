"""
Department Model
==================

OOP Concepts: Inheritance, One-to-Many, Aggregation
SQLAlchemy: One-to-Many relationships, back_populates
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import BaseModel


class Department(BaseModel):
    """
    Department model — represents an academic department.

    OOP Concept: AGGREGATION
    ─────────────────────────
    Department HAS students and teachers, but they can exist
    independently (a teacher can be reassigned to another department).
    This is Aggregation, not Composition.

    Relationships:
    - ONE-TO-MANY: Department → Students
    - ONE-TO-MANY: Department → Teachers
    - ONE-TO-MANY: Department → Subjects
    - MANY-TO-ONE: Department → HOD (a teacher who heads the dept)
    """

    __tablename__ = "departments"

    name = Column(String(200), unique=True, nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # HOD is a teacher — MANY-TO-ONE (nullable: dept may not have HOD assigned)
    hod_id = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        doc="Head of Department (teacher ID)",
    )

    # ── RELATIONSHIPS ────────────────────────────────────────
    # ONE-TO-MANY: Department has many students (AGGREGATION)
    students = relationship(
        "Student",
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # ONE-TO-MANY: Department has many teachers (AGGREGATION)
    teachers = relationship(
        "Teacher",
        back_populates="department",
        foreign_keys="Teacher.department_id",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # ONE-TO-MANY: Department offers many subjects
    subjects = relationship(
        "Subject",
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # MANY-TO-ONE: HOD reference
    hod = relationship(
        "Teacher",
        foreign_keys=[hod_id],
        lazy="selectin",
    )
    programs = relationship(
        "Course",
        foreign_keys="Course.department_id",
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, code='{self.code}', name='{self.name}')>"
