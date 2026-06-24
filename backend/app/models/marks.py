"""
Marks Model
=============

Tracks student exam scores per subject.
"""

from sqlalchemy import Column, Integer, Float, ForeignKey, String, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database.base import BaseModel


class ExamType(str, enum.Enum):
    MIDTERM = "midterm"
    FINAL = "final"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    PRACTICAL = "practical"
    INTERNAL = "internal"


class Marks(BaseModel):
    """
    Marks model — stores exam scores.

    Relationships:
    - MANY-TO-ONE: Marks → Student
    - MANY-TO-ONE: Marks → Subject
    """

    __tablename__ = "markss"  # will be overridden below

    # Override auto-generated tablename
    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    __tablename__ = "marks"

    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    subject_id = Column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    exam_type = Column(SAEnum(ExamType), nullable=False)
    marks_obtained = Column(Float, nullable=False)
    max_marks = Column(Float, nullable=False, default=100)
    semester = Column(Integer, nullable=False)
    remarks = Column(Text, nullable=True)

    # ── RELATIONSHIPS ────────────────────────────────────────
    student = relationship("Student", back_populates="marks_records")
    subject = relationship("Subject", back_populates="marks_records")

    @property
    def percentage(self) -> float:
        """Calculate percentage score."""
        if self.max_marks and self.max_marks > 0:
            return round((self.marks_obtained / self.max_marks) * 100, 2)
        return 0.0

    @property
    def grade(self) -> str:
        """Calculate letter grade based on percentage."""
        pct = self.percentage
        if pct >= 90: return "A+"
        if pct >= 80: return "A"
        if pct >= 70: return "B+"
        if pct >= 60: return "B"
        if pct >= 50: return "C"
        if pct >= 40: return "D"
        return "F"

    def __repr__(self) -> str:
        return (
            f"<Marks(student={self.student_id}, subject={self.subject_id}, "
            f"type={self.exam_type}, score={self.marks_obtained}/{self.max_marks})>"
        )
