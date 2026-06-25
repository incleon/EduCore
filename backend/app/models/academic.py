"""Normalized academic structure, curriculum, elective and allocation models."""

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, event, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import BaseModel


SUBJECT_TYPE_CODES = (
    "COMMON", "SPECIALIZATION", "ELECTIVE", "OPEN_ELECTIVE",
    "LAB", "PROJECT", "INTERNSHIP",
)


class Branch(BaseModel):
    """Optional specialization/branch inside an academic program."""

    __tablename__ = "branches"
    __table_args__ = (
        UniqueConstraint("course_id", "code", name="uq_branch_course_code"),
        Index("ix_branch_course_active", "course_id", "is_deleted"),
    )

    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(30), nullable=False)
    description = Column(Text, nullable=True)
    hod_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    course = relationship("Course", back_populates="branches", lazy="selectin")
    curricula = relationship("Curriculum", back_populates="branch")
    students = relationship("Student", back_populates="branch", lazy="dynamic")
    faculty = relationship("Teacher", foreign_keys="Teacher.branch_id", back_populates="branch", lazy="dynamic")
    hod = relationship("Teacher", foreign_keys=[hod_id], back_populates="branch_hod", lazy="selectin")


class SubjectType(BaseModel):
    """Controlled subject classification required by the academic domain."""

    __tablename__ = "subject_types"
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    subjects = relationship("Subject", back_populates="subject_type", lazy="dynamic")


class Curriculum(BaseModel):
    """Stable curriculum identity for a program and optional branch."""

    __tablename__ = "curricula"
    __table_args__ = (
        UniqueConstraint("code", name="uq_curriculum_code"),
        Index("ix_curriculum_program_branch", "course_id", "branch_id"),
    )

    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True, index=True)
    code = Column(String(60), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    course = relationship("Course", back_populates="curricula", lazy="selectin")
    branch = relationship("Branch", back_populates="curricula", lazy="selectin")
    versions = relationship("CurriculumVersion", back_populates="curriculum", cascade="all, delete-orphan")


class CurriculumVersion(BaseModel):
    """Immutable regulation/version assigned to students by admission batch."""

    __tablename__ = "curriculum_versions"
    __table_args__ = (
        UniqueConstraint("curriculum_id", "version_code", name="uq_curriculum_version_code"),
        CheckConstraint("applicable_batch_end IS NULL OR applicable_batch_end >= applicable_batch_start", name="ck_curriculum_batch_range"),
        Index("ix_curriculum_version_effective", "curriculum_id", "effective_year", "is_active"),
    )

    curriculum_id = Column(Integer, ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False, index=True)
    version_code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    effective_year = Column(Integer, nullable=False, index=True)
    applicable_batch_start = Column(Integer, nullable=False, index=True)
    applicable_batch_end = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    published_at = Column(DateTime, nullable=True)

    curriculum = relationship("Curriculum", back_populates="versions", lazy="selectin")
    semesters = relationship("AcademicSemester", back_populates="curriculum_version", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="curriculum_version", lazy="dynamic")


class AcademicSemester(BaseModel):
    """Semester definition within one curriculum version."""

    __tablename__ = "academic_semesters"
    __table_args__ = (
        UniqueConstraint("curriculum_version_id", "number", name="uq_curriculum_semester_number"),
        CheckConstraint("number > 0", name="ck_semester_positive"),
    )

    curriculum_version_id = Column(Integer, ForeignKey("curriculum_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)
    minimum_credits = Column(Integer, nullable=False, default=0)
    maximum_credits = Column(Integer, nullable=True)

    curriculum_version = relationship("CurriculumVersion", back_populates="semesters", lazy="selectin")
    curriculum_subjects = relationship("CurriculumSubject", back_populates="semester", cascade="all, delete-orphan")
    elective_groups = relationship("ElectiveGroup", back_populates="semester", cascade="all, delete-orphan")


class Section(BaseModel):
    """A section for one program/branch/semester and academic year."""

    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("course_id", "branch_scope_key", "semester_number", "academic_year", "code", name="uq_section_scope_code"),
        CheckConstraint("branch_scope_key = COALESCE(branch_id, 0)", name="ck_section_branch_scope"),
        CheckConstraint("semester_number > 0", name="ck_section_semester_positive"),
        CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_section_capacity_positive"),
        Index("ix_section_lookup", "course_id", "branch_id", "semester_number", "academic_year"),
    )

    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True, index=True)
    branch_scope_key = Column(Integer, nullable=False, default=0)
    curriculum_version_id = Column(Integer, ForeignKey("curriculum_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    semester_number = Column(Integer, nullable=False)
    code = Column(String(20), nullable=False)
    academic_year = Column(String(20), nullable=False, index=True)
    capacity = Column(Integer, nullable=True)

    course = relationship("Course", back_populates="sections", lazy="selectin")
    branch = relationship("Branch", lazy="selectin")
    curriculum_version = relationship("CurriculumVersion", lazy="selectin")
    students = relationship("Student", back_populates="academic_section", lazy="dynamic")
    faculty_assignments = relationship("FacultyAssignment", back_populates="section")


class ElectiveGroup(BaseModel):
    """A set of elective options with selection cardinality rules."""

    __tablename__ = "elective_groups"
    __table_args__ = (
        UniqueConstraint("semester_id", "code", name="uq_elective_group_semester_code"),
        CheckConstraint("minimum_choices >= 0", name="ck_elective_minimum"),
        CheckConstraint("maximum_choices >= minimum_choices", name="ck_elective_maximum"),
    )

    semester_id = Column(Integer, ForeignKey("academic_semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    minimum_choices = Column(Integer, nullable=False, default=0)
    maximum_choices = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)

    semester = relationship("AcademicSemester", back_populates="elective_groups")
    curriculum_subjects = relationship("CurriculumSubject", back_populates="elective_group")


class CurriculumSubject(BaseModel):
    """Maps one subject into a versioned semester without duplicating the subject."""

    __tablename__ = "curriculum_subjects"
    __table_args__ = (
        UniqueConstraint("semester_id", "subject_id", "branch_scope_key", name="uq_curriculum_subject_scope"),
        CheckConstraint("branch_scope_key = COALESCE(branch_id, 0)", name="ck_curriculum_subject_branch_scope"),
        CheckConstraint("credits_override IS NULL OR credits_override >= 0", name="ck_curriculum_subject_credits"),
        Index("ix_curriculum_subject_resolution", "semester_id", "branch_id", "subject_id"),
    )

    semester_id = Column(Integer, ForeignKey("academic_semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True, index=True)
    branch_scope_key = Column(Integer, nullable=False, default=0)
    elective_group_id = Column(Integer, ForeignKey("elective_groups.id", ondelete="SET NULL"), nullable=True, index=True)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    credits_override = Column(Integer, nullable=True)
    display_order = Column(Integer, nullable=False, default=0)

    semester = relationship("AcademicSemester", back_populates="curriculum_subjects")
    subject = relationship("Subject", back_populates="curriculum_mappings", lazy="selectin")
    branch = relationship("Branch", lazy="selectin")
    elective_group = relationship("ElectiveGroup", back_populates="curriculum_subjects")
    student_elections = relationship("StudentElective", back_populates="curriculum_subject", cascade="all, delete-orphan")
    faculty_assignments = relationship("FacultyAssignment", back_populates="curriculum_subject", cascade="all, delete-orphan")


class StudentElective(BaseModel):
    """A student's explicit elective choice in their locked curriculum version."""

    __tablename__ = "student_electives"
    __table_args__ = (
        UniqueConstraint("student_id", "curriculum_subject_id", name="uq_student_elective_choice"),
        Index("ix_student_elective_lookup", "student_id", "status"),
    )

    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    curriculum_subject_id = Column(Integer, ForeignKey("curriculum_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="selected")
    selected_at = Column(DateTime, nullable=False, server_default=func.now())

    student = relationship("Student", back_populates="elective_selections")
    curriculum_subject = relationship("CurriculumSubject", back_populates="student_elections", lazy="selectin")


class FacultyAssignment(BaseModel):
    """Faculty allocation to a curriculum subject, optionally scoped to a section."""

    __tablename__ = "faculty_assignments"
    __table_args__ = (
        UniqueConstraint("teacher_id", "curriculum_subject_id", "section_scope_key", "academic_year", name="uq_faculty_assignment_scope"),
        CheckConstraint("section_scope_key = COALESCE(section_id, 0)", name="ck_faculty_assignment_section_scope"),
        Index("ix_faculty_assignment_lookup", "curriculum_subject_id", "section_id", "academic_year"),
    )

    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    curriculum_subject_id = Column(Integer, ForeignKey("curriculum_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=True, index=True)
    section_scope_key = Column(Integer, nullable=False, default=0)
    academic_year = Column(String(20), nullable=False, index=True)
    role = Column(String(30), nullable=False, default="primary")

    teacher = relationship("Teacher", back_populates="faculty_assignments", lazy="selectin")
    curriculum_subject = relationship("CurriculumSubject", back_populates="faculty_assignments", lazy="selectin")
    section = relationship("Section", back_populates="faculty_assignments", lazy="selectin")
    assignments = relationship(
        "Assignment", back_populates="faculty_assignment",
        cascade="all, delete-orphan", passive_deletes=True,
    )


@event.listens_for(Section, "before_insert")
@event.listens_for(Section, "before_update")
def _sync_section_scope(mapper, connection, target):
    target.branch_scope_key = target.branch_id or 0


@event.listens_for(CurriculumSubject, "before_insert")
@event.listens_for(CurriculumSubject, "before_update")
def _sync_curriculum_subject_scope(mapper, connection, target):
    target.branch_scope_key = target.branch_id or 0


@event.listens_for(FacultyAssignment, "before_insert")
@event.listens_for(FacultyAssignment, "before_update")
def _sync_faculty_assignment_scope(mapper, connection, target):
    target.section_scope_key = target.section_id or 0


class Assignment(BaseModel):
    """Homework/Task assigned to a section by a faculty member."""
    __tablename__ = "assignments"

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    faculty_assignment_id = Column(Integer, ForeignKey("faculty_assignments.id", ondelete="CASCADE"), nullable=False, index=True)

    faculty_assignment = relationship("FacultyAssignment", back_populates="assignments", lazy="selectin")
    submissions = relationship(
        "AssignmentSubmission", back_populates="assignment",
        cascade="all, delete-orphan", passive_deletes=True,
    )


class AssignmentSubmission(BaseModel):
    """A student's submission for an assignment."""
    __tablename__ = "assignment_submissions"

    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending") # pending, submitted, accepted, rejected
    content = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)

    assignment = relationship("Assignment", back_populates="submissions", lazy="selectin")
    student = relationship("Student", lazy="selectin")

