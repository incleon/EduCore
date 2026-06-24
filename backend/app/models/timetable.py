"""
Timetable Document Model
=================

PDF Timetables uploaded by Admins.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime

from app.database.base import BaseModel


class TimetableDocument(BaseModel):
    """
    Timetable entry — a PDF document representing the weekly schedule.
    """

    __tablename__ = "timetable_documents"

    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    department_id = Column(
        Integer, ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    semester = Column(Integer, nullable=False)
    
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    uploaded_by_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── RELATIONSHIPS ────────────────────────────────────────
    course = relationship("Course", lazy="selectin")
    department = relationship("Department", lazy="selectin")
    uploaded_by = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<TimetableDocument(course={self.course_id}, dept={self.department_id}, sem={self.semester})>"
