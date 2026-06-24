"""Library Schemas"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime


class BookCreate(BaseModel):
    title: str = Field(..., max_length=500)
    author: str = Field(..., max_length=255)
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    category: Optional[str] = None
    total_copies: int = Field(default=1, ge=1)
    shelf_location: Optional[str] = None
    description: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    category: Optional[str] = None
    total_copies: Optional[int] = None
    shelf_location: Optional[str] = None
    description: Optional[str] = None


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    category: Optional[str] = None
    total_copies: int
    available_copies: int
    shelf_location: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class BookIssueCreate(BaseModel):
    book_id: int
    student_id: int
    due_date: date


class BookIssueReturn(BaseModel):
    fine_amount: int = 0
    remarks: Optional[str] = None


class BookIssueResponse(BaseModel):
    id: int
    book_id: int
    book_title: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    issue_date: date
    due_date: date
    return_date: Optional[date] = None
    fine_amount: int = 0
    status: str
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
