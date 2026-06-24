"""
Custom Exception Hierarchy
===========================

OOP Concepts Demonstrated:
--------------------------
1. INHERITANCE: All exceptions inherit from CMSException base class
2. POLYMORPHISM: Each exception overrides attributes (status_code, detail)
3. ENCAPSULATION: Error details are encapsulated within exception objects
4. ABSTRACTION: Callers raise semantic exceptions without knowing HTTP details

Why custom exceptions?
- Decouple business logic from HTTP concerns
- Consistent error response format across the application
- Easier to test (catch specific exception types)
- Follows enterprise error handling patterns

SOLID Principles:
- SRP: Each exception represents one specific error condition
- OCP: New exceptions can be added without modifying existing ones
- LSP: All custom exceptions can be used wherever CMSException is expected
"""

from typing import Optional, Any, Dict


class CMSException(Exception):
    """
    Base exception for the College Management System.

    All application-specific exceptions inherit from this class.
    This demonstrates INHERITANCE as the foundation of the exception hierarchy.

    Attributes:
        status_code: HTTP status code to return
        detail: Human-readable error message
        error_code: Machine-readable error code for frontend handling
        headers: Optional HTTP headers to include in response
    """

    status_code: int = 500
    detail: str = "An unexpected error occurred"
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        CONSTRUCTOR (__init__) demonstrating:
        - Default parameter values (Pythonic method overloading)
        - Optional parameters for flexible instantiation
        - Calling parent constructor with super()
        """
        if detail is not None:
            self.detail = detail
        if error_code is not None:
            self.error_code = error_code
        self.headers = headers
        super().__init__(self.detail)

    # ── MAGIC METHODS ────────────────────────────────────────

    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.error_code}: {self.detail}"

    def __repr__(self) -> str:
        """Developer-friendly representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"status_code={self.status_code}, "
            f"detail='{self.detail}', "
            f"error_code='{self.error_code}')"
        )

    def __eq__(self, other: Any) -> bool:
        """
        MAGIC METHOD (__eq__) for equality comparison.

        Why implement __eq__?
        - Allows comparing exceptions in tests: assert exc == expected_exc
        - Makes exception assertions more readable
        """
        if not isinstance(other, CMSException):
            return NotImplemented
        return (
            self.status_code == other.status_code
            and self.detail == other.detail
            and self.error_code == other.error_code
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to a dictionary for JSON response."""
        return {
            "error": True,
            "error_code": self.error_code,
            "detail": self.detail,
            "status_code": self.status_code,
        }


# ── 400 Bad Request ──────────────────────────────────────────
class BadRequestException(CMSException):
    """Raised when the client sends invalid data."""
    status_code = 400
    detail = "Bad request"
    error_code = "BAD_REQUEST"


# ── 401 Unauthorized ─────────────────────────────────────────
class UnauthorizedException(CMSException):
    """
    Raised when authentication is required but not provided or invalid.

    Demonstrates METHOD OVERRIDING — overrides parent's default values.
    """
    status_code = 401
    detail = "Authentication required"
    error_code = "UNAUTHORIZED"

    def __init__(self, detail: Optional[str] = None, **kwargs):
        super().__init__(
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
            **kwargs,
        )


# ── 403 Forbidden ────────────────────────────────────────────
class ForbiddenException(CMSException):
    """
    Raised when user is authenticated but lacks required permissions.

    This is the key exception for the RBAC system.
    Used by PermissionChecker when user's permissions don't match required ones.
    """
    status_code = 403
    detail = "You do not have permission to perform this action"
    error_code = "FORBIDDEN"


# ── 404 Not Found ────────────────────────────────────────────
class NotFoundException(CMSException):
    """Raised when a requested resource does not exist."""
    status_code = 404
    detail = "Resource not found"
    error_code = "NOT_FOUND"

    def __init__(self, resource: str = "Resource", resource_id: Any = None, **kwargs):
        """
        Demonstrates METHOD OVERLOADING (Pythonic style with default params).

        Can be called as:
        - NotFoundException()  → "Resource not found"
        - NotFoundException("Student")  → "Student not found"
        - NotFoundException("Student", 42)  → "Student with ID 42 not found"
        """
        if resource_id is not None:
            detail = f"{resource} with ID {resource_id} not found"
        else:
            detail = f"{resource} not found"
        super().__init__(detail=detail, **kwargs)


# ── 409 Conflict ─────────────────────────────────────────────
class ConflictException(CMSException):
    """Raised when the operation conflicts with existing data (e.g., duplicate email)."""
    status_code = 409
    detail = "Resource already exists"
    error_code = "CONFLICT"


# ── 422 Validation Error ─────────────────────────────────────
class ValidationException(CMSException):
    """
    Raised when business validation fails.

    Different from Pydantic's ValidationError (which is schema-level).
    This is for domain-level validation (e.g., "Cannot enroll — semester is full").
    """
    status_code = 422
    detail = "Validation failed"
    error_code = "VALIDATION_ERROR"

    def __init__(self, detail: str = "Validation failed", errors: Optional[list] = None, **kwargs):
        """
        Demonstrates COMPOSITION — contains a list of validation errors.
        """
        self.errors = errors or []
        super().__init__(detail=detail, **kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Override parent to include validation errors list."""
        result = super().to_dict()
        if self.errors:
            result["errors"] = self.errors
        return result


# ── 503 Service Unavailable ──────────────────────────────────
class ServiceUnavailableException(CMSException):
    """Raised when an external service or database is unavailable."""
    status_code = 503
    detail = "Service temporarily unavailable"
    error_code = "SERVICE_UNAVAILABLE"
