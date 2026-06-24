"""Contracts for normalized academic structure and curriculum management."""

from typing import Optional
from pydantic import BaseModel, Field, model_validator


class BranchCreate(BaseModel):
    course_id: int
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=1, max_length=30)
    description: Optional[str] = None


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class CurriculumCreate(BaseModel):
    course_id: int
    branch_id: Optional[int] = None
    code: str = Field(..., min_length=2, max_length=60)
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class CurriculumUpdate(BaseModel):
    branch_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None


class CurriculumVersionCreate(BaseModel):
    curriculum_id: int
    version_code: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=2, max_length=255)
    effective_year: int = Field(..., ge=1900, le=2200)
    applicable_batch_start: int = Field(..., ge=1900, le=2200)
    applicable_batch_end: Optional[int] = Field(None, ge=1900, le=2200)
    status: str = "draft"
    is_active: bool = False

    @model_validator(mode="after")
    def validate_batch_range(self):
        if self.applicable_batch_end is not None and self.applicable_batch_end < self.applicable_batch_start:
            raise ValueError("Applicable batch end cannot be before batch start")
        return self


class CurriculumVersionUpdate(BaseModel):
    title: Optional[str] = None
    effective_year: Optional[int] = Field(None, ge=1900, le=2200)
    applicable_batch_start: Optional[int] = Field(None, ge=1900, le=2200)
    applicable_batch_end: Optional[int] = Field(None, ge=1900, le=2200)
    status: Optional[str] = None
    is_active: Optional[bool] = None


class SemesterCreate(BaseModel):
    curriculum_version_id: int
    number: int = Field(..., ge=1, le=20)
    name: Optional[str] = None
    minimum_credits: int = Field(0, ge=0)
    maximum_credits: Optional[int] = Field(None, ge=0)


class SemesterUpdate(BaseModel):
    name: Optional[str] = None
    minimum_credits: Optional[int] = Field(None, ge=0)
    maximum_credits: Optional[int] = Field(None, ge=0)


class SectionCreate(BaseModel):
    course_id: int
    branch_id: Optional[int] = None
    curriculum_version_id: Optional[int] = None
    semester_number: int = Field(..., ge=1, le=20)
    code: str = Field(..., min_length=1, max_length=20)
    academic_year: str = Field(..., min_length=4, max_length=20)
    capacity: Optional[int] = Field(None, gt=0)


class SectionUpdate(BaseModel):
    branch_id: Optional[int] = None
    curriculum_version_id: Optional[int] = None
    code: Optional[str] = None
    academic_year: Optional[str] = None
    capacity: Optional[int] = Field(None, gt=0)


class ElectiveGroupCreate(BaseModel):
    semester_id: int
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    minimum_choices: int = Field(0, ge=0)
    maximum_choices: int = Field(1, ge=1)
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_choices(self):
        if self.maximum_choices < self.minimum_choices:
            raise ValueError("Maximum choices cannot be lower than minimum choices")
        return self


class ElectiveGroupUpdate(BaseModel):
    name: Optional[str] = None
    minimum_choices: Optional[int] = Field(None, ge=0)
    maximum_choices: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None


class CurriculumSubjectCreate(BaseModel):
    semester_id: int
    subject_id: int
    branch_id: Optional[int] = None
    elective_group_id: Optional[int] = None
    is_mandatory: bool = True
    credits_override: Optional[int] = Field(None, ge=0)
    display_order: int = Field(0, ge=0)


class CurriculumSubjectUpdate(BaseModel):
    branch_id: Optional[int] = None
    elective_group_id: Optional[int] = None
    is_mandatory: Optional[bool] = None
    credits_override: Optional[int] = Field(None, ge=0)
    display_order: Optional[int] = Field(None, ge=0)


class FacultyAssignmentCreate(BaseModel):
    teacher_id: int
    curriculum_subject_id: int
    section_id: Optional[int] = None
    academic_year: str = Field(..., min_length=4, max_length=20)
    role: str = "primary"


class FacultyAssignmentUpdate(BaseModel):
    section_id: Optional[int] = None
    academic_year: Optional[str] = Field(None, min_length=4, max_length=20)
    role: Optional[str] = None


class StudentAcademicMappingUpdate(BaseModel):
    department_id: int
    course_id: int
    branch_id: Optional[int] = None
    admission_year: int = Field(..., ge=1900, le=2200)
    current_semester: int = Field(..., ge=1, le=20)
    section_id: Optional[int] = None
    curriculum_version_id: Optional[int] = None
    academic_status: Optional[str] = None


class StudentElectiveCreate(BaseModel):
    curriculum_subject_id: int
