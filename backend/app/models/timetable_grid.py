from sqlalchemy import Column, event, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.base import BaseModel


class TimetableVersion(BaseModel):
    """
    TimetableVersion model — represents a weekly timetable for a specific department and semester.
    Status can be: 'draft', 'pending', 'approved', 'rejected'
    """
    __tablename__ = "timetable_versions"

    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"), nullable=True, index=True)
    branch_scope_key = Column(Integer, nullable=False, default=0)
    section_scope_key = Column(Integer, nullable=False, default=0)
    semester = Column(Integer, nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    status = Column(String(20), default="draft", nullable=False)
    
    # Audit tracking
    submitted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Timetables are independently managed for each program/branch/section scope, with versioning
    __table_args__ = (
        UniqueConstraint(
            "course_id", "branch_scope_key", "semester", "section_scope_key", "version_number",
            name="uq_timetable_scope_version",
        ),
    )

    # Relationships
    course = relationship("Course", lazy="selectin")
    department = relationship("Department", lazy="selectin")
    branch = relationship("Branch", lazy="selectin")
    section = relationship("Section", lazy="selectin")
    slots = relationship("TimetableSlot", back_populates="version", cascade="all, delete-orphan")
    
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])


@event.listens_for(TimetableVersion, "before_insert")
@event.listens_for(TimetableVersion, "before_update")
def _sync_timetable_scope(mapper, connection, target):
    target.branch_scope_key = target.branch_id or 0
    target.section_scope_key = target.section_id or 0


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
