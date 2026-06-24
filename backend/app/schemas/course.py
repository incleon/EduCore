"""
Course Schemas
==============
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CourseCreate(BaseModel):
    department_id: int
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    duration_years: Optional[str] = None


class CourseUpdate(BaseModel):
    department_id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    duration_years: Optional[str] = None


class CourseResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    duration_years: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
