"""Library Schemas"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime
from app.models.library import MemberType, ReservationStatus, BookCondition

# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    default_rack: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

# --- Author Schemas ---
class AuthorBase(BaseModel):
    name: str = Field(..., max_length=255)
    biography: Optional[str] = None

class AuthorCreate(AuthorBase):
    pass

class AuthorResponse(AuthorBase):
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

# --- Publisher Schemas ---
class PublisherBase(BaseModel):
    name: str = Field(..., max_length=255)
    contact_info: Optional[str] = None

class PublisherCreate(PublisherBase):
    pass

class PublisherResponse(PublisherBase):
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

# --- Member Schemas ---
class MemberBase(BaseModel):
    user_id: int
    member_type: MemberType
    membership_date: date
    expiry_date: Optional[date] = None
    max_books_allowed: int = 5
    is_active: bool = True

class MemberCreate(MemberBase):
    pass

class MemberResponse(MemberBase):
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


# --- Book Schemas ---
class BookBase(BaseModel):
    title: str = Field(..., max_length=500)
    isbn: Optional[str] = None
    edition: Optional[str] = None
    author_id: Optional[int] = None
    publisher_id: Optional[int] = None
    category_id: Optional[int] = None
    total_copies: int = Field(default=1, ge=1)
    shelf_location: Optional[str] = None
    description: Optional[str] = None
    # Enterprise Fields
    purchase_date: Optional[date] = None
    price: Optional[float] = None
    vendor: Optional[str] = None
    language: Optional[str] = "English"
    pages: Optional[int] = None
    cover_image_url: Optional[str] = None
    condition: BookCondition = BookCondition.NEW

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    isbn: Optional[str] = None
    edition: Optional[str] = None
    author_id: Optional[int] = None
    publisher_id: Optional[int] = None
    category_id: Optional[int] = None
    total_copies: Optional[int] = None
    shelf_location: Optional[str] = None
    description: Optional[str] = None
    purchase_date: Optional[date] = None
    price: Optional[float] = None
    vendor: Optional[str] = None
    language: Optional[str] = None
    pages: Optional[int] = None
    cover_image_url: Optional[str] = None
    condition: Optional[BookCondition] = None

class BookResponse(BookBase):
    id: int
    available_copies: int
    status: str
    created_at: datetime
    
    # Nested relations (optional for frontend convenience)
    author: Optional[AuthorResponse] = None
    publisher: Optional[PublisherResponse] = None
    category: Optional[CategoryResponse] = None
    
    model_config = {"from_attributes": True}


# --- Book Issue Schemas ---
class BookIssueCreate(BaseModel):
    book_id: int
    member_id: int
    due_date: date
    condition_on_issue: Optional[BookCondition] = None

class BookIssueReturn(BaseModel):
    fine_amount: int = 0
    remarks: Optional[str] = None
    condition_on_return: Optional[BookCondition] = None
    fine_paid: Optional[bool] = False

class BookIssueResponse(BaseModel):
    id: int
    book_id: int
    member_id: int
    issue_date: date
    due_date: date
    return_date: Optional[date] = None
    fine_amount: int = 0
    status: str
    remarks: Optional[str] = None
    renewals_count: int
    fine_paid: bool
    condition_on_issue: Optional[BookCondition] = None
    condition_on_return: Optional[BookCondition] = None
    created_at: datetime
    
    book: Optional[BookResponse] = None
    member: Optional[MemberResponse] = None
    
    model_config = {"from_attributes": True}


# --- Book Reservation Schemas ---
class ReservationCreate(BaseModel):
    book_id: int
    member_id: int

class ReservationResponse(BaseModel):
    id: int
    book_id: int
    member_id: int
    reservation_date: datetime
    status: ReservationStatus
    notified_date: Optional[datetime] = None
    created_at: datetime
    
    book: Optional[BookResponse] = None
    member: Optional[MemberResponse] = None
    
    model_config = {"from_attributes": True}


# --- Fine Schemas ---
class FineCreate(BaseModel):
    issue_id: Optional[int] = None
    member_id: int
    amount: float
    reason: str

class FineResponse(FineCreate):
    id: int
    is_paid: bool
    payment_date: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}
