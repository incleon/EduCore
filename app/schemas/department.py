"""
Department Schemas
====================
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=20)
    description: Optional[str] = None
    course_id: int
    hod_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    hod_id: Optional[int] = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    hod_id: Optional[int] = None
    hod_name: Optional[str] = None
    student_count: int = 0
    teacher_count: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
