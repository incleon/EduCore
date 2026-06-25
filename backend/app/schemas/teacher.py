"""
Teacher Schemas
=================
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime


class TeacherCreate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    full_name: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    employee_id: Optional[str] = None
    department_id: int
    branch_id: Optional[int] = None
    designation: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    joining_date: Optional[date] = None
    experience_years: int = 0
    bio: Optional[str] = None


class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None
    branch_id: Optional[int] = None
    designation: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    bio: Optional[str] = None


class TeacherResponse(BaseModel):
    id: int
    user_id: int
    employee_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department_name: Optional[str] = None
    department_id: Optional[int] = None
    branch_id: Optional[int] = None
    designation: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    joining_date: Optional[date] = None
    experience_years: int = 0
    profile_image: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
