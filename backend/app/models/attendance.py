"""
Attendance Model
==================

Tracks daily student attendance per subject.
"""

from sqlalchemy import Column, Integer, ForeignKey, Date, Boolean, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database.base import BaseModel


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class Attendance(BaseModel):
    """
    Attendance model — tracks student presence per subject per day.

    Relationships:
    - MANY-TO-ONE: Attendance → Student
    - MANY-TO-ONE: Attendance → Subject
    - MANY-TO-ONE: Attendance → Teacher (who marked it)
    """

    __tablename__ = "attendances"

    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    subject_id = Column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    teacher_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"), nullable=True, index=True)
    faculty_assignment_id = Column(Integer, ForeignKey("faculty_assignments.id", ondelete="SET NULL"), nullable=True, index=True)

    date = Column(Date, nullable=False, index=True)
    status = Column(
        SAEnum(AttendanceStatus),
        default=AttendanceStatus.PRESENT,
        nullable=False,
    )
    remarks = Column(Text, nullable=True)

    # ── RELATIONSHIPS ────────────────────────────────────────
    student = relationship("Student", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")
    teacher = relationship("Teacher", back_populates="attendance_records")
    section = relationship("Section", lazy="selectin")
    faculty_assignment = relationship("FacultyAssignment", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<Attendance(student={self.student_id}, subject={self.subject_id}, "
            f"date={self.date}, status={self.status})>"
        )
