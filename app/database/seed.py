"""
Seed Data — Pre-populate database with demo data
====================================================

Creates roles, permissions, role-permission mappings, and demo users.
"""

import datetime

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
        "view_students",
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

    # Check if roles already exist. If so, skip role/permission/user seeding
    # but continue to ensure courses and departments are present.
    roles_exist = bool(db.query(Role).first())
    if roles_exist:
        logger.info("Basic roles exist — skipping role/user seeding, continuing with courses/departments")

    logger.info("Seeding database with initial data...")

    # ── 1-4. Create Permissions, Roles and Demo Users (only if missing)
    perm_map = {}
    role_map = {}
    # ensure demo password is available for any user creation below
    demo_password = PasswordHasher.hash_password("admin123")
    if not roles_exist:
        # 1. Create Permissions
        for name, resource, action, description in PERMISSIONS:
            # avoid duplicate perms
            perm = db.query(Permission).filter_by(name=name).first()
            if not perm:
                perm = Permission(name=name, resource=resource, action=action, description=description)
                db.add(perm)
                db.flush()
            perm_map[name] = perm.id

        # 2. Create Roles
        for name, display_name in ROLES:
            role = db.query(Role).filter_by(name=name).first()
            if not role:
                role = Role(name=name, display_name=display_name, description=f"{display_name} role")
                db.add(role)
                db.flush()
            role_map[name] = role.id

        # 3. Assign Permissions to Roles
        for role_name, perm_names in ROLE_PERMISSIONS.items():
            role_id = role_map[role_name]
            for perm_name in perm_names:
                if perm_name in perm_map:
                    exists = db.query(RolePermission).filter_by(role_id=role_id, permission_id=perm_map[perm_name]).first()
                    if not exists:
                        rp = RolePermission(role_id=role_id, permission_id=perm_map[perm_name])
                        db.add(rp)

        db.flush()

        # 4. Create Demo Users
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
    else:
        # roles already exist; ensure role_map contains ids for later use when needed
        for name, _ in ROLES:
            role = db.query(Role).filter_by(name=name).first()
            if role:
                role_map[name] = role.id

    # ── 4.5 Create Courses (only if missing) ────────────────
    from app.models.course import Course
    def get_or_create_course(code, name, description, duration):
        c = db.query(Course).filter_by(code=code).first()
        if c:
            return c
        c = Course(name=name, code=code, description=description, duration_years=duration)
        db.add(c)
        db.flush()
        return c

    btech = get_or_create_course("B.TECH", "B.TECH", "Bachelor of Technology", "4 years")
    mba = get_or_create_course("MBA", "MBA", "Master of Business Administration", "2 years")
    bpharma = get_or_create_course("B.PHARMA", "B.PHARMA", "Bachelor of Pharmacy", "4 years")
    bcom = get_or_create_course("B.COM", "B.COM", "Bachelor of Commerce", "3 years")

    # ── 5. Create Departments (5 per course) ─────────────────
    # B.TECH departments
    btech_departments = [
        ("Computer Science", "CS"),
        ("Electrical Engineering", "EE"),
        ("Mechanical Engineering", "ME"),
        ("Civil Engineering", "CE"),
        ("Chemical Engineering", "CH"),
    ]

    # MBA departments
    mba_departments = [
        ("Finance", "FN"),
        ("Marketing", "MK"),
        ("Human Resources", "HR"),
        ("Operations Management", "OM"),
        ("Information Technology", "IT"),
    ]

    # B.PHARMA departments
    bpharma_departments = [
        ("Pharmaceutics", "PH"),
        ("Pharmacology", "PK"),
        ("Pharmaceutical Chemistry", "PC"),
        ("Quality Assurance", "QA"),
        ("Regulatory Science", "RS"),
    ]

    # B.COM departments
    bcom_departments = [
        ("Accounting", "AC"),
        ("Business Management", "BM"),
        ("Financial Management", "FM"),
        ("Taxation", "TX"),
        ("International Business", "IB"),
    ]

    # Create departments only if they do not already exist for the course
    dept_objs = []
    def ensure_dept(name, code, course_obj):
        # Check global uniqueness: department name or code may already exist
        d = db.query(Department).filter((Department.code == code) | (Department.name == name)).first()
        if d:
            # If an existing department belongs to a different course, return it (avoid duplicates)
            return d
        # Otherwise create new department under the given course
        d = Department(name=name, code=code, description=f"Department of {name}", course_id=course_obj.id)
        db.add(d)
        db.flush()
        return d

    for name, code in btech_departments:
        dept_objs.append(ensure_dept(name, code, btech))
    for name, code in mba_departments:
        dept_objs.append(ensure_dept(name, code, mba))
    for name, code in bpharma_departments:
        dept_objs.append(ensure_dept(name, code, bpharma))
    for name, code in bcom_departments:
        dept_objs.append(ensure_dept(name, code, bcom))

    # Keep convenient references for usage later in the seed script
    cs_dept = next((d for d in dept_objs if d.code == "CS"), None)
    ee_dept = next((d for d in dept_objs if d.code == "EE"), None)
    me_dept = next((d for d in dept_objs if d.code == "ME"), None)
    finance_dept = next((d for d in dept_objs if d.code == "FN"), None)
    # Persist departments now so later failures won't rollback these inserts
    db.commit()
    # refresh dept objects from DB to ensure ids are present
    dept_objs = [db.query(Department).filter_by(code=d.code).first() for d in dept_objs]

    # ── 6. Create Subjects ───────────────────────────────────
    subjects_data = [
        ("Data Structures", "CS201", 3, 3, cs_dept.id),
        ("Algorithms", "CS301", 3, 5, cs_dept.id),
        ("Database Systems", "CS302", 3, 5, cs_dept.id),
        ("Operating Systems", "CS303", 3, 5, cs_dept.id),
        ("Circuit Theory", "EE201", 4, 3, ee_dept.id),
    ]
    for name, code, credits, sem, dept_id in subjects_data:
        # avoid duplicate subjects by code
        existing = db.query(Subject).filter_by(code=code).first()
        if not existing:
            db.add(Subject(name=name, code=code, credits=credits, semester=sem, department_id=dept_id))
    db.flush()

    # ── 7. Create Demo Teacher ───────────────────────────────
    # Create demo teacher user only if not exists
    teacher_user = db.query(User).filter_by(email="teacher@cms.edu").first()
    if not teacher_user:
        teacher_user = User(
            email="teacher@cms.edu", username="teacher",
            hashed_password=demo_password, full_name="Dr. Priya Sharma",
        )
        db.add(teacher_user)
        db.flush()
        db.add(UserRole(user_id=teacher_user.id, role_id=role_map.get("teacher")))

    # Create Teacher record only if not present for this user
    existing_teacher = db.query(Teacher).filter_by(user_id=teacher_user.id).first()
    if not existing_teacher:
        teacher = Teacher(
            user_id=teacher_user.id, department_id=cs_dept.id,
            faculty_id=f"FC{datetime.datetime.now().year % 100:02d}000001",
            employee_id="T001", designation="Assistant Professor",
            specialization="Data Science", qualification="Ph.D.",
        )
        db.add(teacher)
        db.flush()

    # HOD user
    # HOD user (create only if missing)
    hod_user = db.query(User).filter_by(email="hod@cms.edu").first()
    if not hod_user:
        hod_user = User(
            email="hod@cms.edu", username="hod",
            hashed_password=demo_password, full_name="Dr. Rajesh Kumar",
        )
        db.add(hod_user)
        db.flush()
        db.add(UserRole(user_id=hod_user.id, role_id=role_map.get("hod")))
        db.add(UserRole(user_id=hod_user.id, role_id=role_map.get("teacher")))

    # Create HOD teacher record only if not present
    existing_hod_teacher = db.query(Teacher).filter_by(user_id=hod_user.id).first()
    if not existing_hod_teacher:
        hod_teacher = Teacher(
            user_id=hod_user.id, department_id=cs_dept.id,
            faculty_id=f"FC{datetime.datetime.now().year % 100:02d}000002",
            employee_id="T000", designation="Professor & HOD",
            specialization="Artificial Intelligence", qualification="Ph.D.",
        )
        db.add(hod_teacher)
        db.flush()
        # Set HOD
        cs_dept.hod_id = hod_teacher.id
    else:
        cs_dept.hod_id = existing_hod_teacher.id

    # ── 8. Create Demo Students ──────────────────────────────
    for i in range(1, 6):
        email = f"student{i}@cms.edu"
        stu_user = db.query(User).filter_by(email=email).first()
        if not stu_user:
            stu_user = User(
                email=email, username=f"student{i}",
                hashed_password=demo_password,
                full_name=f"Student {i}",
            )
            db.add(stu_user)
            db.flush()
            db.add(UserRole(user_id=stu_user.id, role_id=role_map.get("student")))

        student_id = f"24CS{i:03d}"
        existing_student = db.query(Student).filter_by(student_id=student_id).first()
        if not existing_student:
            student = Student(
                user_id=stu_user.id, department_id=cs_dept.id,
                student_id=student_id,
                enrollment_number=f"ENR-24CS{i:03d}",
                semester=3, section="A",
            )
            db.add(student)

    db.commit()
    logger.info("Database seeded successfully with demo data!")
    logger.info("Demo credentials: any demo user with password 'admin123'")
    logger.info("Users: admin@cms.edu, teacher@cms.edu, student1@cms.edu, etc.")
