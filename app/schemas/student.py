"""
Student Schemas
=================
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime


class StudentCreate(BaseModel):
    # User fields
    email: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    # Student fields
    personal_email: str
    department_id: int
    date_of_birth: Optional[date] = None
    admission_date: Optional[date] = None
    semester: int = 1
    section: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    blood_group: Optional[str] = None


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None
    semester: Optional[int] = None
    section: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    blood_group: Optional[str] = None
    status: Optional[str] = None


class StudentResponse(BaseModel):
    id: int
    user_id: int
    enrollment_number: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    personal_email: Optional[str] = None
    phone: Optional[str] = None
    department_name: Optional[str] = None
    department_id: Optional[int] = None
    semester: int = 1
    section: Optional[str] = None
    date_of_birth: Optional[date] = None
    admission_date: Optional[date] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    blood_group: Optional[str] = None
    status: Optional[str] = None
    profile_image: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
