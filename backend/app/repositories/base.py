"""
Base Repository — Generic CRUD Operations
============================================

OOP Concepts Demonstrated:
--------------------------
1. GENERICS (TypeVar): BaseRepository[T] works with ANY model type
2. ABSTRACTION: Provides a clean interface hiding SQL details
3. INHERITANCE: Concrete repos inherit and optionally override
4. ENCAPSULATION: Database session (_db) is protected
5. METHOD OVERRIDING: Subclasses override for custom queries
6. DRY PRINCIPLE: CRUD logic written ONCE, reused by ALL repositories
7. TEMPLATE METHOD PATTERN: Defines algorithm skeleton, subclasses customize steps

Why Repository Pattern?
────────────────────────
- Isolates data access from business logic
- Services don't know about SQLAlchemy queries
- Easy to swap data source (e.g., from SQL to NoSQL)
- Easy to test (mock the repository)
- Single place to add query optimizations

SOLID Principles:
- SRP: Each repo handles data access for one model
- OCP: New queries added without modifying base
- LSP: Any concrete repo works wherever BaseRepository is expected
- DIP: Services depend on repository abstraction, not concrete queries
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_

from app.database.base import BaseModel
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# TypeVar for generic typing — T can be any SQLAlchemy model
T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Generic base repository providing CRUD operations for any model.

    OOP Concept: GENERICS
    ──────────────────────
    BaseRepository[T] is parameterized by model type T.
    StudentRepository(BaseRepository[Student]) → all methods return Student objects.

    Usage:
        class StudentRepository(BaseRepository[Student]):
            def __init__(self, db: Session):
                super().__init__(Student, db)

            # Optionally override methods for custom queries
            def find_by_enrollment(self, enrollment: str) -> Optional[Student]:
                return self._db.query(self._model).filter(
                    self._model.enrollment_number == enrollment
                ).first()
    """

    def __init__(self, model: Type[T], db: Session):
        """
        CONSTRUCTOR: Initialize with model class and database session.

        ENCAPSULATION: _model and _db are protected (single underscore).
        They should be accessed by subclasses but not by external code.
        """
        self._model = model  # Protected: the SQLAlchemy model class
        self._db = db        # Protected: database session

    # ── CREATE ───────────────────────────────────────────────

    def create(self, obj_data: Dict[str, Any]) -> T:
        """
        Create a new record in the database.

        Args:
            obj_data: Dictionary of field values

        Returns:
            The created model instance with generated ID
        """
        db_obj = self._model(**obj_data)
        self._db.add(db_obj)
        self._db.commit()
        self._db.refresh(db_obj)
        logger.info(f"Created {self._model.__name__} with id={db_obj.id}")
        return db_obj

    # ── READ ─────────────────────────────────────────────────

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[T]:
        """Get a single record by primary key."""
        query = self._db.query(self._model).filter(self._model.id == id)
        if not include_deleted and hasattr(self._model, 'is_deleted'):
            query = query.filter(self._model.is_deleted == False)
        return query.first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "id",
        sort_order: str = "desc",
        include_deleted: bool = False,
    ) -> List[T]:
        """
        Get all records with pagination and sorting.

        METHOD OVERLOADING (Pythonic style):
        - get_all() → default pagination
        - get_all(skip=10, limit=5) → custom pagination
        - get_all(sort_by="name", sort_order="asc") → custom sorting
        """
        query = self._db.query(self._model)

        if not include_deleted and hasattr(self._model, 'is_deleted'):
            query = query.filter(self._model.is_deleted == False)

        # Dynamic sorting
        if hasattr(self._model, sort_by):
            sort_column = getattr(self._model, sort_by)
            query = query.order_by(
                desc(sort_column) if sort_order == "desc" else asc(sort_column)
            )

        return query.offset(skip).limit(limit).all()

    def count(self, include_deleted: bool = False) -> int:
        """Count total records."""
        query = self._db.query(self._model)
        if not include_deleted and hasattr(self._model, 'is_deleted'):
            query = query.filter(self._model.is_deleted == False)
        return query.count()

    def search(
        self,
        search_fields: List[str],
        search_value: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[T]:
        """
        Search across multiple fields.

        Demonstrates POLYMORPHISM — search behavior adapts
        based on the model and its fields.
        """
        query = self._db.query(self._model)

        if hasattr(self._model, 'is_deleted'):
            query = query.filter(self._model.is_deleted == False)

        if search_value and search_fields:
            conditions = []
            for field in search_fields:
                if hasattr(self._model, field):
                    column = getattr(self._model, field)
                    conditions.append(column.ilike(f"%{search_value}%"))
            if conditions:
                query = query.filter(or_(*conditions))

        return query.offset(skip).limit(limit).all()

    def search_count(self, search_fields: List[str], search_value: str) -> int:
        """Count search results."""
        query = self._db.query(self._model)
        if hasattr(self._model, 'is_deleted'):
            query = query.filter(self._model.is_deleted == False)
        if search_value and search_fields:
            conditions = []
            for field in search_fields:
                if hasattr(self._model, field):
                    column = getattr(self._model, field)
                    conditions.append(column.ilike(f"%{search_value}%"))
            if conditions:
                query = query.filter(or_(*conditions))
        return query.count()

    # ── UPDATE ───────────────────────────────────────────────

    def update(self, id: int, obj_data: Dict[str, Any]) -> Optional[T]:
        """Update a record by ID."""
        db_obj = self.get_by_id(id)
        if db_obj is None:
            return None

        for key, value in obj_data.items():
            if value is not None and hasattr(db_obj, key):
                setattr(db_obj, key, value)

        self._db.commit()
        self._db.refresh(db_obj)
        logger.info(f"Updated {self._model.__name__} with id={id}")
        return db_obj

    # ── DELETE ───────────────────────────────────────────────

    def soft_delete(self, id: int) -> bool:
        """Compatibility entry point for the application's permanent-delete policy."""
        db_obj = self.get_by_id(id)
        if db_obj is None:
            return False

        self._db.delete(db_obj)
        self._db.commit()
        logger.info(f"Deleted {self._model.__name__} with id={id}")
        return True

    def hard_delete(self, id: int) -> bool:
        """Permanently remove record from database."""
        db_obj = self._db.query(self._model).filter(self._model.id == id).first()
        if db_obj is None:
            return False

        self._db.delete(db_obj)
        self._db.commit()
        logger.info(f"Hard deleted {self._model.__name__} with id={id}")
        return True

    def restore(self, id: int) -> Optional[T]:
        """Restore a soft-deleted record."""
        db_obj = self.get_by_id(id, include_deleted=True)
        if db_obj is None:
            return None

        db_obj.is_deleted = False
        db_obj.deleted_at = None
        self._db.commit()
        self._db.refresh(db_obj)
        logger.info(f"Restored {self._model.__name__} with id={id}")
        return db_obj

    # ── MAGIC METHODS ────────────────────────────────────────

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(model={self._model.__name__})>"

    def __len__(self) -> int:
        """Returns total record count. Allows: len(repository)"""
        return self.count()
