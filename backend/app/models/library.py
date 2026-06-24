"""
Library Models — Book and BookIssue
======================================

Two models in one file demonstrating related entities.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database.base import BaseModel


class BookStatus(str, enum.Enum):
    AVAILABLE = "available"
    ISSUED = "issued"
    RESERVED = "reserved"
    LOST = "lost"
    DAMAGED = "damaged"


class IssueStatus(str, enum.Enum):
    ISSUED = "issued"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"


class LibraryBook(BaseModel):
    """
    Library book catalog entry.

    Relationships:
    - ONE-TO-MANY: Book → BookIssue records
    """

    __tablename__ = "library_books"

    title = Column(String(500), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    isbn = Column(String(20), unique=True, nullable=True)
    publisher = Column(String(255), nullable=True)
    edition = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    shelf_location = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(BookStatus), default=BookStatus.AVAILABLE, nullable=False)

    # ── RELATIONSHIPS ────────────────────────────────────────
    issues = relationship(
        "BookIssue", back_populates="book",
        cascade="all, delete-orphan", lazy="dynamic",
    )

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"

    def __repr__(self) -> str:
        return f"<LibraryBook(id={self.id}, title='{self.title}')>"


class BookIssue(BaseModel):
    """
    Book issue/checkout record.

    Relationships:
    - MANY-TO-ONE: BookIssue → LibraryBook
    - MANY-TO-ONE: BookIssue → Student
    """

    __tablename__ = "book_issues"

    book_id = Column(
        Integer, ForeignKey("library_books.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    fine_amount = Column(Integer, default=0, nullable=False)
    status = Column(SAEnum(IssueStatus), default=IssueStatus.ISSUED, nullable=False)
    remarks = Column(Text, nullable=True)

    # ── RELATIONSHIPS ────────────────────────────────────────
    book = relationship("LibraryBook", back_populates="issues")
    student = relationship("Student", back_populates="book_issues")

    def __repr__(self) -> str:
        return f"<BookIssue(book={self.book_id}, student={self.student_id}, status={self.status})>"
