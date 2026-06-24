"""Marks Schemas"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MarksCreate(BaseModel):
    student_id: int
    subject_id: int
    exam_type: str
    marks_obtained: float = Field(..., ge=0)
    max_marks: float = Field(default=100, ge=0)
    semester: int
    remarks: Optional[str] = None


class MarksUpdate(BaseModel):
    marks_obtained: Optional[float] = None
    max_marks: Optional[float] = None
    remarks: Optional[str] = None


class MarksResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    subject_id: int
    subject_name: Optional[str] = None
    exam_type: str
    marks_obtained: float
    max_marks: float
    percentage: float = 0.0
    grade: str = ""
    semester: int
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
