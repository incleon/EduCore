"""
Course Model
==============

OOP Concepts: Inheritance, One-to-Many
SQLAlchemy: One-to-Many relationships, back_populates
"""

"""
Course Model
==============

OOP Concepts: Inheritance, One-to-Many
SQLAlchemy: One-to-Many relationships, back_populates
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database.base import BaseModel


class Course(BaseModel):
    """
    Course model — represents academic programs/courses.

    Examples: B.TECH, MBA, B.PHARMA, B.COM

    OOP Concept: AGGREGATION
    ──────────────────────────
    Course HAS departments, but they can exist independently.

    Relationships:
    - ONE-TO-MANY: Course → Departments
    """

    __tablename__ = "courses"

    name = Column(String(200), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    duration_years = Column(String(50), nullable=True, doc="Duration e.g., '4 years'")
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=True, index=True)

    # ── RELATIONSHIPS ────────────────────────────────────────
    department = relationship("Department", foreign_keys=[department_id], back_populates="programs", lazy="selectin")
    branches = relationship("Branch", back_populates="course", cascade="all, delete-orphan")
    curricula = relationship("Curriculum", back_populates="course", cascade="all, delete-orphan")
    sections = relationship("Section", back_populates="course", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, code='{self.code}', name='{self.name}')>"
