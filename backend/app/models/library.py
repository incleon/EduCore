"""
Library Models — Comprehensive Enterprise Architecture
======================================================
Includes Books, Authors, Publishers, Categories, Members, Issues, Reservations, and Fines.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Text, Boolean, Enum as SAEnum, Numeric
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database.base import BaseModel


class BookStatus(str, enum.Enum):
    AVAILABLE = "available"
    ISSUED = "issued"
    RESERVED = "reserved"
    LOST = "lost"
    DAMAGED = "damaged"


class BookCondition(str, enum.Enum):
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DAMAGED = "damaged"


class IssueStatus(str, enum.Enum):
    ISSUED = "issued"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"


class MemberType(str, enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    STAFF = "staff"
    EXTERNAL = "external"


class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


# ── ENTITIES ────────────────────────────────────────

class LibraryAuthor(BaseModel):
    __tablename__ = "library_authors"
    name = Column(String(255), nullable=False, index=True)
    biography = Column(Text, nullable=True)
    books = relationship("LibraryBook", back_populates="author")


class LibraryPublisher(BaseModel):
    __tablename__ = "library_publishers"
    name = Column(String(255), nullable=False, index=True)
    contact_info = Column(Text, nullable=True)
    books = relationship("LibraryBook", back_populates="publisher")


class BookCategory(BaseModel):
    __tablename__ = "book_categories"
    name = Column(String(100), nullable=False, unique=True, index=True)
    default_rack = Column(String(50), nullable=True)
    books = relationship("LibraryBook", back_populates="category")


class LibraryMember(BaseModel):
    """Links any User (Student, Teacher, Admin) to library privileges."""
    __tablename__ = "library_members"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    member_type = Column(SAEnum(MemberType), nullable=False, default=MemberType.STUDENT)
    membership_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    expiry_date = Column(Date, nullable=True)
    max_books_allowed = Column(Integer, default=3, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    user = relationship("User", backref="library_member")
    issues = relationship("BookIssue", back_populates="member", cascade="all, delete-orphan", lazy="dynamic")
    reservations = relationship("BookReservation", back_populates="member", cascade="all, delete-orphan", lazy="dynamic")
    fines = relationship("LibraryFine", back_populates="member", cascade="all, delete-orphan", lazy="dynamic")


class LibraryBook(BaseModel):
    __tablename__ = "library_books"

    title = Column(String(500), nullable=False, index=True)
    isbn = Column(String(20), unique=True, nullable=True)
    edition = Column(String(50), nullable=True)
    
    author_id = Column(Integer, ForeignKey("library_authors.id", ondelete="SET NULL"), nullable=True)
    publisher_id = Column(Integer, ForeignKey("library_publishers.id", ondelete="SET NULL"), nullable=True)
    category_id = Column(Integer, ForeignKey("book_categories.id", ondelete="SET NULL"), nullable=True)
    
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    shelf_location = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(BookStatus), default=BookStatus.AVAILABLE, nullable=False)
    
    purchase_date = Column(Date, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    vendor = Column(String(255), nullable=True)
    language = Column(String(50), nullable=True, default="English")
    pages = Column(Integer, nullable=True)
    cover_image_url = Column(String(1024), nullable=True)
    condition = Column(SAEnum(BookCondition), default=BookCondition.NEW, nullable=False)

    # Relationships
    author = relationship("LibraryAuthor", back_populates="books")
    publisher = relationship("LibraryPublisher", back_populates="books")
    category = relationship("BookCategory", back_populates="books")
    
    issues = relationship("BookIssue", back_populates="book", cascade="all, delete-orphan", lazy="dynamic")
    reservations = relationship("BookReservation", back_populates="book", cascade="all, delete-orphan", lazy="dynamic")


class BookIssue(BaseModel):
    __tablename__ = "book_issues"

    book_id = Column(Integer, ForeignKey("library_books.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("library_members.id", ondelete="CASCADE"), nullable=False, index=True)

    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    fine_amount = Column(Integer, default=0, nullable=False)
    status = Column(SAEnum(IssueStatus), default=IssueStatus.ISSUED, nullable=False)
    remarks = Column(Text, nullable=True)
    
    renewals_count = Column(Integer, default=0, nullable=False)
    fine_paid = Column(Boolean, default=False, nullable=False)
    condition_on_issue = Column(SAEnum(BookCondition), nullable=True)
    condition_on_return = Column(SAEnum(BookCondition), nullable=True)

    book = relationship("LibraryBook", back_populates="issues")
    member = relationship("LibraryMember", back_populates="issues")
    fines = relationship("LibraryFine", back_populates="issue", cascade="all, delete-orphan")


class BookReservation(BaseModel):
    __tablename__ = "book_reservations"
    
    book_id = Column(Integer, ForeignKey("library_books.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("library_members.id", ondelete="CASCADE"), nullable=False, index=True)
    
    reservation_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(SAEnum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False)
    notified_date = Column(DateTime, nullable=True)
    
    book = relationship("LibraryBook", back_populates="reservations")
    member = relationship("LibraryMember", back_populates="reservations")


class LibraryFine(BaseModel):
    __tablename__ = "library_fines"
    
    issue_id = Column(Integer, ForeignKey("book_issues.id", ondelete="CASCADE"), nullable=True)
    member_id = Column(Integer, ForeignKey("library_members.id", ondelete="CASCADE"), nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(255), nullable=False, default="Overdue return")
    is_paid = Column(Boolean, default=False, nullable=False)
    payment_date = Column(DateTime, nullable=True)
    
    issue = relationship("BookIssue", back_populates="fines")
    member = relationship("LibraryMember", back_populates="fines")
