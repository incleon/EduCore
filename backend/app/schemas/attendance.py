"""Attendance Schemas"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime


class AttendanceCreate(BaseModel):
    student_id: int
    subject_id: int
    date: date
    status: str = "present"
    remarks: Optional[str] = None
    section_id: Optional[int] = None
    faculty_assignment_id: Optional[int] = None


class AttendanceBulkCreate(BaseModel):
    """Bulk attendance marking for a class."""
    subject_id: int
    date: date
    section_id: Optional[int] = None
    faculty_assignment_id: Optional[int] = None
    records: List[dict]  # [{"student_id": 1, "status": "present"}, ...]


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    subject_id: int
    subject_name: Optional[str] = None
    teacher_id: Optional[int] = None
    section_id: Optional[int] = None
    faculty_assignment_id: Optional[int] = None
    date: date
    status: str
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class AttendanceUpdate(BaseModel):
    status: Optional[str] = None
    remarks: Optional[str] = None
    section_id: Optional[int] = None
    faculty_assignment_id: Optional[int] = None


class AttendanceSummary(BaseModel):
    student_id: int
    student_name: str
    total_classes: int = 0
    present: int = 0
    absent: int = 0
    percentage: float = 0.0
