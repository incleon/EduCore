"""
Permission-Based Authorization System
=======================================

OOP Concepts Demonstrated:
--------------------------
1. MAGIC METHOD (__call__): Makes PermissionChecker instances callable
2. COMPOSITION: PermissionChecker composes with get_current_user
3. ENCAPSULATION: Permission logic encapsulated in checker class
4. CALLABLE CLASSES: Instances used as FastAPI dependencies

Why permission-based (not role-based) checks?
─────────────────────────────────────────────
In enterprise RBAC, you check PERMISSIONS, not ROLES:

BAD (hardcoded roles):
    if user.role == "admin":  # What if we add "manager" role?

GOOD (permission-based):
    if "create_student" in user.permissions:  # Any role with this permission works

Benefits:
- Adding new roles doesn't require code changes
- Permissions can be reassigned via admin panel
- Fine-grained access control
- Follows Open/Closed Principle (OCP)

Usage in routes:
    @router.post("/students", dependencies=[Depends(PermissionChecker(["create_student"]))])
    def create_student(...):
        ...
"""

from typing import List, Set
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import ForbiddenException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PermissionChecker:
    """
    Callable class that checks if user has required permissions.

    OOP Concept: MAGIC METHOD (__call__)
    ─────────────────────────────────────
    By implementing __call__, instances of this class can be called
    like functions. This is what makes them usable as FastAPI dependencies.

    How it works:
    1. Created with required permissions: PermissionChecker(["create_student"])
    2. FastAPI calls the instance as a function for each request
    3. __call__ checks the current user's permissions
    4. Raises ForbiddenException if permissions are insufficient

    OOP Concept: COMPOSITION
    ─────────────────────────
    PermissionChecker composes with (depends on) get_current_user.
    It doesn't inherit from anything — it HAS-A dependency on user extraction.
    """

    def __init__(self, required_permissions: List[str]):
        """
        CONSTRUCTOR: Store the required permissions for this endpoint.

        Args:
            required_permissions: List of permission names needed to access endpoint
        """
        self.required_permissions = required_permissions

    def __call__(
        self,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        """
        MAGIC METHOD (__call__): Makes this instance callable.

        When FastAPI sees Depends(PermissionChecker(["create_student"])),
        it calls this __call__ method with the resolved dependencies.

        This is a powerful Python OOP feature:
        - Regular functions are callable
        - Class instances with __call__ are ALSO callable
        - This lets us maintain state (required_permissions) while
          being usable as a function

        Returns:
            The current user if permission check passes

        Raises:
            ForbiddenException: If user lacks required permissions
        """
        # Gather all permissions from all user roles
        user_permissions = self._get_user_permissions(current_user)

        # Check if user has ALL required permissions
        missing = set(self.required_permissions) - user_permissions

        if missing:
            logger.warning(
                f"Permission denied for user {current_user.id} "
                f"({current_user.email}). Missing: {missing}"
            )
            raise ForbiddenException(
                detail=f"Missing permissions: {', '.join(missing)}"
            )

        logger.debug(
            f"Permission granted for user {current_user.id}: "
            f"{self.required_permissions}"
        )
        return current_user

    def _get_user_permissions(self, user) -> Set[str]:
        """
        ENCAPSULATION: Internal method to extract user's permissions.

        Protected method (single underscore) — implementation detail
        that shouldn't be called from outside this class.

        Traverses: User → UserRoles → Role → RolePermissions → Permission
        """
        permissions = set()
        for user_role in user.user_roles:
            role = user_role.role
            if role and role.is_active:
                for role_perm in role.role_permissions:
                    if role_perm.permission:
                        permissions.add(role_perm.permission.name)
        return permissions

    # ── MAGIC METHODS for debugging ──────────────────────────

    def __repr__(self) -> str:
        return f"PermissionChecker(required={self.required_permissions})"

    def __str__(self) -> str:
        return f"Requires: {', '.join(self.required_permissions)}"

    def __len__(self) -> int:
        """
        MAGIC METHOD (__len__): Returns number of required permissions.
        Allows: len(checker) → number of permissions
        """
        return len(self.required_permissions)


class RoleChecker:
    """
    Simpler role-based checker (for cases where role check is sufficient).

    Demonstrates that both role-based AND permission-based checks can coexist.
    Use PermissionChecker for fine-grained control, RoleChecker for broad checks.

    Usage:
        @router.get("/admin", dependencies=[Depends(RoleChecker(["admin"]))])
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user=Depends(get_current_user)):
        user_roles = {
            ur.role.name for ur in current_user.user_roles
            if ur.role and ur.role.is_active
        }

        if not user_roles.intersection(set(self.allowed_roles)):
            raise ForbiddenException(
                detail=f"This action requires one of these roles: "
                       f"{', '.join(self.allowed_roles)}"
            )
        return current_user

    def __repr__(self) -> str:
        return f"RoleChecker(allowed={self.allowed_roles})"
