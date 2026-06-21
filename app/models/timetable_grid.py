from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.base import BaseModel


class TimetableVersion(BaseModel):
    """
    TimetableVersion model — represents a weekly timetable for a specific department and semester.
    Status can be: 'draft', 'pending', 'approved', 'rejected'
    """
    __tablename__ = "timetable_versions"

    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    semester = Column(Integer, nullable=False)
    status = Column(String(20), default="draft", nullable=False)
    
    # Audit tracking
    submitted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # A department can only have one timetable per semester
    __table_args__ = (
        UniqueConstraint("department_id", "semester", name="uq_department_semester"),
    )

    # Relationships
    course = relationship("Course", lazy="selectin")
    department = relationship("Department", lazy="selectin")
    slots = relationship("TimetableSlot", back_populates="version", cascade="all, delete-orphan", lazy="selectin")
    
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])


class TimetableSlot(BaseModel):
    """
    TimetableSlot model — represents a single cell in the timetable grid.
    day_of_week: 1 (Monday) to 6 (Saturday)
    slot_index: 1 to 8 (excluding lunch break which is fixed visually)
    """
    __tablename__ = "timetable_slots"

    version_id = Column(Integer, ForeignKey("timetable_versions.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    slot_index = Column(Integer, nullable=False)
    
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        UniqueConstraint("version_id", "day_of_week", "slot_index", name="uq_version_day_slot"),
    )

    # Relationships
    version = relationship("TimetableVersion", back_populates="slots")
    subject = relationship("Subject", lazy="selectin")
    teacher = relationship("Teacher", lazy="selectin")
