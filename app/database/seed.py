"""
Seed Data — Pre-populate database with demo data
====================================================

Creates roles, permissions, role-permission mappings, and demo users.
"""

from sqlalchemy.orm import Session
from app.models.user import User, Role, Permission, UserRole, RolePermission
from app.models.department import Department
from app.models.subject import Subject
from app.models.student import Student
from app.models.teacher import Teacher
from app.core.security import PasswordHasher
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# ── PERMISSION DEFINITIONS ───────────────────────────────────

PERMISSIONS = [
    # User management
    ("manage_users", "user", "manage", "Full user management"),
    ("manage_roles", "role", "manage", "Manage roles and permissions"),
    # Department
    ("view_departments", "department", "read", "View departments"),
    ("manage_departments", "department", "manage", "Manage departments"),
    # Student
    ("view_students", "student", "read", "View students"),
    ("manage_students", "student", "manage", "Create/edit/delete students"),
    # Teacher
    ("view_teachers", "teacher", "read", "View teachers"),
    ("manage_teachers", "teacher", "manage", "Manage teachers"),
    # Subject
    ("view_subjects", "subject", "read", "View subjects"),
    ("manage_subjects", "subject", "manage", "Manage subjects"),
    # Attendance
    ("view_attendance", "attendance", "read", "View attendance"),
    ("mark_attendance", "attendance", "manage", "Mark attendance"),
    # Marks
    ("view_marks", "marks", "read", "View marks"),
    ("upload_marks", "marks", "manage", "Upload marks"),
    # Fees
    ("view_fees", "fee", "read", "View fees"),
    ("manage_fees", "fee", "manage", "Manage fees"),
    # Library
    ("view_library", "library", "read", "View library"),
    ("manage_library", "library", "manage", "Manage library"),
    # Reports
    ("view_reports", "report", "read", "View reports"),
    # Dashboard
    ("view_dashboard", "dashboard", "read", "View dashboard"),
    # Profile
    ("manage_profile", "profile", "manage", "Manage own profile"),
]

# ── ROLE DEFINITIONS WITH PERMISSIONS ────────────────────────

ROLE_PERMISSIONS = {
    "admin": [p[0] for p in PERMISSIONS],  # ALL permissions
    "hod": [
        "view_departments", "manage_departments", "view_students",
        "manage_students", "view_teachers",
        "view_subjects", "manage_subjects", "view_attendance", "view_marks",
        "view_reports", "view_dashboard", "manage_profile",
    ],
    "teacher": [
        "view_students", "view_subjects", "view_attendance",
        "mark_attendance", "view_marks", "upload_marks",
        "view_library", "view_dashboard", "manage_profile",
    ],
    "student": [
        "view_attendance", "view_marks", "view_fees",
        "view_library", "view_dashboard", "manage_profile",
    ],
    "accountant": [
        "view_fees", "manage_fees", "view_students",
        "view_reports", "view_dashboard", "manage_profile",
    ],
    "librarian": [
        "view_library", "manage_library",
        "view_students", "view_dashboard", "manage_profile",
    ],
}

ROLES = [
    ("admin", "Administrator"),
    ("hod", "Head of Department"),
    ("teacher", "Teacher"),
    ("student", "Student"),
    ("accountant", "Accountant"),
    ("librarian", "Librarian"),
]


def seed_database(db: Session) -> None:
    """Seed the database with initial data if empty."""

    # Check if already seeded
    if db.query(Role).first():
        logger.info("Database already seeded — skipping")
        return

    logger.info("Seeding database with initial data...")

    # ── 1. Create Permissions ────────────────────────────────
    perm_map = {}
    for name, resource, action, description in PERMISSIONS:
        perm = Permission(name=name, resource=resource, action=action, description=description)
        db.add(perm)
        db.flush()
        perm_map[name] = perm.id

    # ── 2. Create Roles ──────────────────────────────────────
    role_map = {}
    for name, display_name in ROLES:
        role = Role(name=name, display_name=display_name, description=f"{display_name} role")
        db.add(role)
        db.flush()
        role_map[name] = role.id

    # ── 3. Assign Permissions to Roles ───────────────────────
    for role_name, perm_names in ROLE_PERMISSIONS.items():
        role_id = role_map[role_name]
        for perm_name in perm_names:
            if perm_name in perm_map:
                rp = RolePermission(role_id=role_id, permission_id=perm_map[perm_name])
                db.add(rp)

    db.flush()

    # ── 4. Create Demo Users ─────────────────────────────────
    demo_password = PasswordHasher.hash_password("admin123")

    # Admin
    admin = User(
        email="admin@cms.edu", username="admin",
        hashed_password=demo_password, full_name="System Administrator",
    )
    db.add(admin)
    db.flush()
    db.add(UserRole(user_id=admin.id, role_id=role_map["admin"]))

    # Accountant
    accountant = User(
        email="accountant@cms.edu", username="accountant",
        hashed_password=demo_password, full_name="John Accountant",
    )
    db.add(accountant)
    db.flush()
    db.add(UserRole(user_id=accountant.id, role_id=role_map["accountant"]))

    # Librarian
    librarian = User(
        email="librarian@cms.edu", username="librarian",
        hashed_password=demo_password, full_name="Lisa Librarian",
    )
    db.add(librarian)
    db.flush()
    db.add(UserRole(user_id=librarian.id, role_id=role_map["librarian"]))

    # ── 4.5 Create Courses ───────────────────────────────────
    from app.models.course import Course
    btech = Course(name="B.TECH", code="B.TECH", description="Bachelor of Technology", duration_years="4 years")
    mba = Course(name="MBA", code="MBA", description="Master of Business Administration", duration_years="2 years")
    bpharma = Course(name="B.PHARMA", code="B.PHARMA", description="Bachelor of Pharmacy", duration_years="4 years")
    bcom = Course(name="B.COM", code="B.COM", description="Bachelor of Commerce", duration_years="3 years")
    db.add_all([btech, mba, bpharma, bcom])
    db.flush()

    # ── 5. Create Departments ────────────────────────────────
    cs_dept = Department(name="Computer Science", code="CS", description="Department of Computer Science", course_id=btech.id)
    ee_dept = Department(name="Electrical Engineering", code="EE", description="Department of Electrical Engineering", course_id=btech.id)
    me_dept = Department(name="Mechanical Engineering", code="ME", description="Department of Mechanical Engineering", course_id=btech.id)
    finance_dept = Department(name="Finance", code="FIN", description="Department of Finance", course_id=mba.id)
    db.add_all([cs_dept, ee_dept, me_dept, finance_dept])
    db.flush()

    # ── 6. Create Subjects ───────────────────────────────────
    subjects_data = [
        ("Data Structures", "CS201", 3, 3, cs_dept.id),
        ("Algorithms", "CS301", 3, 5, cs_dept.id),
        ("Database Systems", "CS302", 3, 5, cs_dept.id),
        ("Operating Systems", "CS303", 3, 5, cs_dept.id),
        ("Circuit Theory", "EE201", 4, 3, ee_dept.id),
    ]
    for name, code, credits, sem, dept_id in subjects_data:
        db.add(Subject(name=name, code=code, credits=credits, semester=sem, department_id=dept_id))
    db.flush()

    # ── 7. Create Demo Teacher ───────────────────────────────
    teacher_user = User(
        email="teacher@cms.edu", username="teacher",
        hashed_password=demo_password, full_name="Dr. Priya Sharma",
    )
    db.add(teacher_user)
    db.flush()
    db.add(UserRole(user_id=teacher_user.id, role_id=role_map["teacher"]))

    teacher = Teacher(
        user_id=teacher_user.id, department_id=cs_dept.id,
        employee_id="T001", designation="Assistant Professor",
        specialization="Data Science", qualification="Ph.D.",
    )
    db.add(teacher)
    db.flush()

    # HOD user
    hod_user = User(
        email="hod@cms.edu", username="hod",
        hashed_password=demo_password, full_name="Dr. Rajesh Kumar",
    )
    db.add(hod_user)
    db.flush()
    db.add(UserRole(user_id=hod_user.id, role_id=role_map["hod"]))
    db.add(UserRole(user_id=hod_user.id, role_id=role_map["teacher"]))

    hod_teacher = Teacher(
        user_id=hod_user.id, department_id=cs_dept.id,
        employee_id="T000", designation="Professor & HOD",
        specialization="Artificial Intelligence", qualification="Ph.D.",
    )
    db.add(hod_teacher)
    db.flush()

    # Set HOD
    cs_dept.hod_id = hod_teacher.id

    # ── 8. Create Demo Students ──────────────────────────────
    for i in range(1, 6):
        stu_user = User(
            email=f"student{i}@cms.edu", username=f"student{i}",
            hashed_password=demo_password,
            full_name=f"Student {i}",
        )
        db.add(stu_user)
        db.flush()
        db.add(UserRole(user_id=stu_user.id, role_id=role_map["student"]))

        student = Student(
            user_id=stu_user.id, department_id=cs_dept.id,
            enrollment_number=f"2024CS{i:03d}",
            semester=3, section="A",
        )
        db.add(student)

    db.commit()
    logger.info("Database seeded successfully with demo data!")
    logger.info("Demo credentials: any demo user with password 'admin123'")
    logger.info("Users: admin@cms.edu, teacher@cms.edu, student1@cms.edu, etc.")
