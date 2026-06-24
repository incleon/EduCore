"""
Base Service — Abstract Interface
====================================

OOP Concepts Demonstrated:
--------------------------
1. ABSTRACT BASE CLASS (ABC): Defines interface that all services must implement
2. ABSTRACTION: Hides implementation behind a contract
3. INTERFACE: Python doesn't have interfaces; ABC is the closest equivalent

Why ABC?
- Forces all services to implement the same methods
- Guarantees consistent API across modules
- Enables polymorphism (any service can be used interchangeably)
- Makes code self-documenting (you can read the interface to understand capabilities)

SOLID — ISP (Interface Segregation):
- This interface is small and focused
- Services implement only what they need
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IService(ABC):
    """
    Abstract interface for all CRUD services.

    OOP Concept: ABSTRACT BASE CLASS
    ─────────────────────────────────
    - Cannot be instantiated directly
    - Subclasses MUST implement all @abstractmethod methods
    - Trying to instantiate without implementing all methods raises TypeError

    Usage:
        class StudentService(IService):
            def get(self, id): ...       # Must implement
            def list(self, ...): ...     # Must implement
            def create(self, data): ...  # Must implement
            def update(self, ...): ...   # Must implement
            def delete(self, id): ...    # Must implement
    """

    @abstractmethod
    def get(self, id: int) -> Optional[Any]:
        """Get a single resource by ID."""
        pass

    @abstractmethod
    def list(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        sort_by: str = "id",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """List resources with pagination, search, sorting."""
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Any:
        """Create a new resource."""
        pass

    @abstractmethod
    def update(self, id: int, data: Dict[str, Any]) -> Optional[Any]:
        """Update an existing resource."""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete a resource (soft delete)."""
        pass
