from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: datetime
    faculty_assignment_id: int

class AssignmentCreate(AssignmentBase):
    pass

class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class AssignmentResponse(AssignmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AssignmentSubmissionBase(BaseModel):
    assignment_id: int
    student_id: int
    status: str
    content: Optional[str] = None
    feedback: Optional[str] = None
    submitted_at: Optional[datetime] = None

class AssignmentSubmissionCreate(BaseModel):
    # Only used for updating the submission content by student
    content: str = Field(..., min_length=1)

class AssignmentSubmissionReview(BaseModel):
    # Used by faculty to accept/reject
    status: str = Field(..., description="accepted or rejected")
    feedback: Optional[str] = None

class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    assignment: AssignmentResponse

    class Config:
        from_attributes = True
