"""
Database Base Models & Mixins
===============================

OOP Concepts Demonstrated:
--------------------------
1. INHERITANCE: All models inherit from BaseModel
2. MIXINS (Multiple Inheritance): TimestampMixin, SoftDeleteMixin
3. COMPOSITION: BaseModel composes multiple mixins
4. MAGIC METHODS: __repr__, __str__, __tablename__
5. ENCAPSULATION: Internal fields managed by mixins
6. ABSTRACTION: Models don't need to know about timestamp/soft-delete logic

What are Mixins?
────────────────
Mixins are classes that provide methods/attributes to other classes
through multiple inheritance, WITHOUT being standalone models themselves.

Benefits:
- DRY: timestamp/soft-delete logic written ONCE, used in ALL models
- Separation of Concerns: each mixin handles one concern
- Composable: models can pick and choose which mixins they need

Example:
    class Student(BaseModel):  → Gets id, timestamps, soft-delete, __repr__
        name = Column(String)  → Only defines student-specific fields
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, declared_attr
from typing import Any


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base.

    All ORM models must inherit from this class (directly or indirectly).
    This is required by SQLAlchemy 2.0+ for model registration.
    """
    pass


class TimestampMixin:
    """
    MIXIN: Adds created_at and updated_at timestamps to any model.

    OOP Concept: MIXIN (a form of Multiple Inheritance)
    ─────────────────────────────────────────────────────
    - This class is NOT meant to be instantiated on its own
    - It provides timestamp columns to any model that includes it
    - Multiple models can use this mixin (DRY Principle)

    Why a mixin instead of putting these in BaseModel?
    - Not all tables need timestamps (e.g., association tables)
    - Separation of Concerns: timestamp logic is independent
    - Reusable across different base classes if needed
    """

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Record creation timestamp (UTC)",
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Last update timestamp (UTC)",
    )


class SoftDeleteMixin:
    """
    MIXIN: Adds soft-delete capability to any model.

    OOP Concept: MIXIN + ENCAPSULATION
    ────────────────────────────────────
    Soft delete means marking a record as deleted without physically
    removing it from the database.

    Why soft delete?
    - Data recovery: accidentally deleted records can be restored
    - Audit trail: maintain history of all records
    - Referential integrity: no broken foreign key references
    - Compliance: some regulations require data retention

    The is_deleted flag is ENCAPSULATED in this mixin — models
    using it don't need to know the implementation details.
    """

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Soft delete flag",
    )

    deleted_at = Column(
        DateTime,
        nullable=True,
        doc="Deletion timestamp (UTC)",
    )

    def soft_delete(self) -> None:
        """Mark this record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """
    Abstract base model for all CMS database models.

    OOP Concepts:
    ──────────────
    1. MULTIPLE INHERITANCE: Inherits from Base, TimestampMixin, SoftDeleteMixin
    2. ABSTRACT CLASS: __abstract__ = True means no table is created for this class
    3. MAGIC METHODS: __repr__ and __str__ for debugging
    4. DECLARED_ATTR: Dynamic attribute based on class name

    Method Resolution Order (MRO):
    BaseModel → Base → TimestampMixin → SoftDeleteMixin → object

    All concrete models (Student, Teacher, etc.) inherit from this class,
    getting id, timestamps, and soft-delete FOR FREE (DRY Principle).
    """

    __abstract__ = True  # No table created for this base class

    # Primary key — every model gets this automatically
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        doc="Primary key",
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """
        MAGIC-LIKE METHOD: Automatically generate table name from class name.

        Converts CamelCase class name to snake_case table name:
        - Student → students
        - LibraryBook → library_books
        - BookIssue → book_issues

        This demonstrates ABSTRACTION — subclasses don't need to
        manually specify __tablename__.
        """
        import re
        # Convert CamelCase to snake_case and pluralize
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        # Simple pluralization
        if name.endswith('s') or name.endswith('x') or name.endswith('z'):
            return name + 'es'
        elif name.endswith('y') and name[-2] not in 'aeiou':
            return name[:-1] + 'ies'
        else:
            return name + 's'

    # ── MAGIC METHODS ────────────────────────────────────────

    def __repr__(self) -> str:
        """
        MAGIC METHOD: Developer-friendly representation.

        Called by repr() — shows class name and primary key.
        Useful in debugging and logging.
        """
        return f"<{self.__class__.__name__}(id={self.id})>"

    def __str__(self) -> str:
        """
        MAGIC METHOD: User-friendly string representation.

        Called by str() and print().
        Subclasses should override this for meaningful output.
        """
        return f"{self.__class__.__name__} #{self.id}"

    def __eq__(self, other: Any) -> bool:
        """
        MAGIC METHOD: Equality comparison.

        Two model instances are equal if they have the same class and ID.
        This is important for ORM operations and set membership checks.
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """
        MAGIC METHOD: Hash for use in sets and dict keys.

        Required when __eq__ is defined (Python rule).
        Uses class name + id for uniqueness.
        """
        return hash((self.__class__.__name__, self.id))

    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.

        Useful for serialization, logging, and debugging.
        Excludes SQLAlchemy internal state.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
