"""
User, Role & Permission Models — RBAC System
===============================================

OOP Concepts Demonstrated:
--------------------------
1. INHERITANCE: All models inherit from BaseModel
2. ASSOCIATION: Many-to-Many via association tables (UserRole, RolePermission)
3. COMPOSITION: User HAS roles (strong ownership — user doesn't exist without account)
4. AGGREGATION: Role HAS permissions (permissions can exist without roles)
5. ENCAPSULATION: hashed_password is never exposed directly
6. MAGIC METHODS: __repr__, __str__

Database Design:
────────────────
This implements the standard enterprise RBAC pattern:
- Users can have multiple Roles (many-to-many via user_roles)
- Roles can have multiple Permissions (many-to-many via role_permissions)
- Authorization checks permissions, NOT roles
- New roles can be created and assigned permissions without code changes

Normalization:
- users, roles, permissions → 3NF (no transitive dependencies)
- user_roles, role_permissions → join tables for M:N relationships
"""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database.base import BaseModel


# ── ENUM for Gender ──────────────────────────────────────────
class GenderEnum(str, enum.Enum):
    """
    Python Enum integrated with SQLAlchemy.

    Why Enum instead of plain strings?
    - Type safety at the Python level
    - Database constraint (only valid values allowed)
    - IDE autocomplete
    - Self-documenting code
    """
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class User(BaseModel):
    """
    User model — central to the authentication and RBAC system.

    OOP Concepts:
    - INHERITANCE: extends BaseModel (gets id, timestamps, soft-delete)
    - ENCAPSULATION: hashed_password is stored, never the plain password
    - COMPOSITION: User HAS-A list of UserRole objects
    - ONE-TO-ONE: User ↔ Student, User ↔ Teacher (a user IS a student/teacher)

    Table: users
    ─────────────
    Primary entity for authentication. Every person in the system
    (student, teacher, admin) has a User record.
    """

    __tablename__ = "users"

    # ── Authentication Fields ────────────────────────────────
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique email address for login",
    )
    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique username",
    )
    hashed_password = Column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password — NEVER store plain text",
    )

    # ── Profile Fields ───────────────────────────────────────
    full_name = Column(String(255), nullable=False, doc="Full display name")
    phone = Column(String(20), nullable=True, doc="Contact phone number")
    address = Column(Text, nullable=True, doc="Postal address")
    profile_image = Column(String(500), nullable=True, doc="Profile image file path")
    gender = Column(SAEnum(GenderEnum), nullable=True, doc="Gender")

    # ── Status ───────────────────────────────────────────────
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Account active status",
    )

    # ── RELATIONSHIPS ────────────────────────────────────────
    # ONE-TO-MANY: User has many UserRole records (COMPOSITION)
    user_roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="User's role assignments",
    )

    # ONE-TO-ONE: User may be linked to a Student record
    student = relationship(
        "Student",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        doc="Associated student profile (if user is a student)",
    )

    # ONE-TO-ONE: User may be linked to a Teacher record
    teacher = relationship(
        "Teacher",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        doc="Associated teacher profile (if user is a teacher)",
    )

    # ONE-TO-MANY: User has many notifications
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # ── HELPER METHODS ───────────────────────────────────────

    @property
    def roles(self):
        """
        PROPERTY: Encapsulate role access behind a clean API.

        Instead of: user.user_roles[0].role.name
        Use: user.roles → ["admin", "teacher"]
        """
        return [
            ur.role.name for ur in self.user_roles
            if ur.role and ur.role.is_active
        ]

    @property
    def permissions(self):
        """
        PROPERTY: Get all permissions across all roles.

        Traverses the RBAC graph:
        User → UserRole → Role → RolePermission → Permission
        """
        perms = set()
        for ur in self.user_roles:
            if ur.role and ur.role.is_active:
                for rp in ur.role.role_permissions:
                    if rp.permission:
                        perms.add(rp.permission.name)
        return list(perms)

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        return permission_name in self.permissions

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return role_name in self.roles

    @classmethod
    def create_user(cls, email: str, username: str, hashed_password: str,
                    full_name: str, **kwargs) -> "User":
        """
        CLASS METHOD: Alternative constructor for creating users.

        Why class method?
        - Validates data before creating instance
        - Can include business logic (e.g., default values)
        - Returns typed instance (cls, not User — supports subclassing)
        """
        return cls(
            email=email.lower().strip(),
            username=username.lower().strip(),
            hashed_password=hashed_password,
            full_name=full_name.strip(),
            **kwargs,
        )

    # ── MAGIC METHODS ────────────────────────────────────────

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', roles={self.roles})>"


class Role(BaseModel):
    """
    Role model — defines a named role in the system.

    OOP Concepts:
    - INHERITANCE: extends BaseModel
    - AGGREGATION: Role HAS permissions (permissions exist independently)
    - MANY-TO-MANY: Role ↔ Permission via role_permissions table

    Table: roles
    ─────────────
    Predefined roles: admin, hod, teacher, student, accountant, librarian
    """

    __tablename__ = "roles"

    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Role identifier (e.g., 'admin', 'teacher')",
    )
    display_name = Column(
        String(100),
        nullable=False,
        doc="Human-readable role name (e.g., 'System Administrator')",
    )
    description = Column(
        Text,
        nullable=True,
        doc="Role description",
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this role is currently active",
    )

    # ── RELATIONSHIPS ────────────────────────────────────────
    # MANY-TO-MANY: Role has many permissions (AGGREGATION)
    role_permissions = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # MANY-TO-MANY back-reference: Role is assigned to many users
    user_roles = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    @property
    def permission_names(self):
        """Get list of permission names for this role."""
        return [
            rp.permission.name for rp in self.role_permissions
            if rp.permission
        ]

    def __str__(self) -> str:
        return self.display_name

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"


class Permission(BaseModel):
    """
    Permission model — defines a granular permission in the system.

    OOP Concepts:
    - INHERITANCE: extends BaseModel
    - ENCAPSULATION: Permission details (resource, action) are self-contained

    Table: permissions
    ───────────────────
    Format: "{action}_{resource}" (e.g., "create_student", "view_marks")

    Why granular permissions?
    - Fine-grained access control
    - Permissions are assignable to ANY role
    - Adding new roles doesn't require code changes (OCP)
    """

    __tablename__ = "permissions"

    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Permission identifier (e.g., 'create_student')",
    )
    resource = Column(
        String(50),
        nullable=False,
        doc="Resource this permission applies to (e.g., 'student')",
    )
    action = Column(
        String(50),
        nullable=False,
        doc="Action type (e.g., 'create', 'read', 'update', 'delete')",
    )
    description = Column(
        Text,
        nullable=True,
        doc="Human-readable description of what this permission allows",
    )

    # ── RELATIONSHIPS ────────────────────────────────────────
    role_permissions = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        return f"{self.action}:{self.resource}"

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name='{self.name}')>"


class UserRole(BaseModel):
    """
    Association table: User ↔ Role (Many-to-Many).

    OOP Concept: ASSOCIATION
    ─────────────────────────
    This is the standard pattern for many-to-many relationships in RDBMS.
    A user can have multiple roles, and a role can be assigned to multiple users.

    Table: user_roles
    ──────────────────
    Columns: user_id (FK), role_id (FK)
    """

    __tablename__ = "user_roles"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── RELATIONSHIPS ────────────────────────────────────────
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class RolePermission(BaseModel):
    """
    Association table: Role ↔ Permission (Many-to-Many).

    OOP Concept: ASSOCIATION + AGGREGATION
    ───────────────────────────────────────
    A role can have many permissions, a permission can belong to many roles.
    Permissions exist independently of roles (AGGREGATION, not COMPOSITION).

    Table: role_permissions
    ────────────────────────
    Columns: role_id (FK), permission_id (FK)
    """

    __tablename__ = "role_permissions"

    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id = Column(
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── RELATIONSHIPS ────────────────────────────────────────
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    def __repr__(self) -> str:
        return f"<RolePermission(role_id={self.role_id}, perm_id={self.permission_id})>"
