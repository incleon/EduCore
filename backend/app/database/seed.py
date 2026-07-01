"""Comprehensive, deterministic EduCore demonstration data.

Run ``python -m app.database.seed`` to replace business data with a complete
odd-semester campus dataset. Authorization metadata and the current
administrator are preserved. Run with ``--clean`` to keep only those records,
or ``--system`` to reconcile authorization metadata without demo data.
"""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, inspect, text
from sqlalchemy.orm import Session, noload

from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.security import PasswordHasher
from app.database.session import SessionLocal, init_db
from app.models.academic import (
    SUBJECT_TYPE_CODES,
    AcademicSemester,
    Assignment,
    AssignmentSubmission,
    Branch,
    Curriculum,
    CurriculumSubject,
    CurriculumVersion,
    ElectiveGroup,
    FacultyAssignment,
    Section,
    StudentElective,
    SubjectType,
)
from app.models.attendance import Attendance, AttendanceStatus
from app.models.course import Course
from app.models.department import Department
from app.models.finance import (
    Expense,
    ExpenseCategory,
    FeeStatus,
    FeeStructure,
    Payment,
    PaymentMethod,
    PaymentStatus,
    StaffSalary,
    StudentFee,
)
from app.models.library import (
    BookCategory,
    BookCondition,
    BookIssue,
    BookReservation,
    BookStatus,
    IssueStatus,
    LibraryAuthor,
    LibraryBook,
    LibraryFine,
    LibraryMember,
    LibraryPublisher,
    MemberType,
    ReservationStatus,
)
from app.models.marks import ExamType, Marks
from app.models.notification import Notification, NotificationType
from app.models.student import Student
from app.models.subject import Subject, SubjectTeacher
from app.models.teacher import Teacher
from app.models.timetable_grid import TimetableSlot, TimetableVersion
from app.models.user import Permission, Role, RolePermission, User, UserRole


logger = get_logger(__name__)

DEPARTMENT_DATA = (
    ("Department of Engineering", "ENG", "Engineering education, research, design, and innovation."),
    ("Department of Management", "MGT", "Business leadership, entrepreneurship, finance, and organizational studies."),
    ("Department of Pharmacy", "PHA", "Pharmaceutical sciences, clinical practice, formulation, and drug research."),
    ("Department of Computer Applications", "CA", "Applied computing, software development, analytics, and information systems."),
)

# department code, course name, course code, duration, regulator, branches
PROGRAM_DATA = (
    ("ENG", "Bachelor of Technology", "BT", 4, "AICTE", (
        ("Computer Science and Engineering", "CS"),
        ("Mechanical Engineering", "ME"),
        ("Civil Engineering", "CE"),
    )),
    ("ENG", "Master of Technology", "MT", 2, "AICTE", (
        ("Computer Science and Engineering", "CS"),
    )),
    ("MGT", "Bachelor of Business Administration", "BBA", 3, "UGC", (
        ("General Management", "GM"),
    )),
    ("MGT", "Master of Business Administration", "MBA", 2, "AICTE", (
        ("Finance", "FIN"),
        ("Human Resource Management", "HR"),
        ("Marketing Management", "MKT"),
    )),
    ("PHA", "Bachelor of Pharmacy", "BP", 4, "PCI", (
        ("Pharmacy", "PH"),
    )),
    ("PHA", "Master of Pharmacy", "MP", 2, "PCI", (
        ("Pharmaceutics", "PHT"),
    )),
    ("PHA", "Diploma in Pharmacy", "DP", 2, "PCI", (
        ("Pharmacy", "PH"),
    )),
    ("CA", "Bachelor of Computer Applications", "BCA", 3, "UGC", (
        ("Computer Applications", "CA"),
    )),
    ("CA", "Master of Computer Applications", "MCA", 2, "AICTE", (
        ("Computer Applications", "CA"),
    )),
)

PERMISSIONS = [
    ("manage_users", "user", "manage", "Full user management"),
    ("manage_roles", "role", "manage", "Manage roles and permissions"),
    ("view_departments", "department", "read", "View departments"),
    ("manage_departments", "department", "manage", "Manage departments"),
    ("view_students", "student", "read", "View students"),
    ("manage_students", "student", "manage", "Create/edit/delete students"),
    ("view_teachers", "teacher", "read", "View teachers"),
    ("manage_teachers", "teacher", "manage", "Manage teachers"),
    ("view_subjects", "subject", "read", "View subjects"),
    ("manage_subjects", "subject", "manage", "Manage subjects"),
    ("view_attendance", "attendance", "read", "View attendance"),
    ("mark_attendance", "attendance", "manage", "Mark attendance"),
    ("view_marks", "marks", "read", "View marks"),
    ("upload_marks", "marks", "manage", "Upload marks"),
    ("view_fees", "fee", "read", "View fees"),
    ("manage_fees", "fee", "manage", "Manage fees"),
    ("view_library", "library", "read", "View library"),
    ("manage_library", "library", "manage", "Manage library"),
    ("view_reports", "report", "read", "View reports"),
    ("view_dashboard", "dashboard", "read", "View dashboard"),
    ("manage_profile", "profile", "manage", "Manage own profile"),
    ("manage_timetable", "timetable", "manage", "Create and approve timetables"),
    ("view_academic_structure", "academic_structure", "read", "View academic structure"),
    ("manage_academic_structure", "academic_structure", "manage", "Manage academic structure"),
    ("manage_curriculum", "curriculum", "manage", "Manage curricula"),
    ("manage_assignments", "assignment", "manage", "Create and review assignments"),
    ("select_electives", "elective", "select", "Select eligible electives"),
]

ROLE_PERMISSIONS = {
    "admin": [item[0] for item in PERMISSIONS],
    "hod": ["view_students", "manage_students", "view_subjects", "manage_subjects", "view_attendance", "view_marks", "view_reports", "view_dashboard", "manage_profile", "manage_timetable", "view_academic_structure", "manage_curriculum"],
    "teacher": ["view_students", "view_subjects", "view_attendance", "mark_attendance", "view_marks", "upload_marks", "view_library", "view_dashboard", "manage_profile", "view_academic_structure", "manage_assignments"],
    "student": ["view_attendance", "view_marks", "view_fees", "view_library", "view_dashboard", "manage_profile", "select_electives"],
    "accountant": ["view_fees", "manage_fees", "view_students", "view_reports", "view_dashboard", "manage_profile", "view_academic_structure"],
    "librarian": ["view_library", "manage_library", "view_students", "view_dashboard", "manage_profile", "view_academic_structure"],
}

ROLE_NAMES = {
    "admin": "Administrator",
    "hod": "Head of Department",
    "teacher": "Teacher",
    "student": "Student",
    "accountant": "Accountant",
    "librarian": "Librarian",
}

MALE_NAMES = (
    "Aarav", "Vivaan", "Aditya", "Arjun", "Reyansh", "Krishna", "Ishaan", "Kabir",
    "Rohan", "Atharv", "Dhruv", "Siddharth", "Nikhil", "Kunal", "Manav", "Yash",
    "Rahul", "Abhinav", "Harsh", "Varun", "Dev", "Aryan", "Pranav", "Sameer",
    "Vikram", "Anirudh", "Ritvik", "Arnav", "Mohit", "Shaurya",
)
FEMALE_NAMES = (
    "Aanya", "Diya", "Ananya", "Ira", "Meera", "Kavya", "Ishita", "Nisha",
    "Sara", "Myra", "Riya", "Aditi", "Sneha", "Priya", "Tanvi", "Avni",
    "Saanvi", "Neha", "Pooja", "Radhika", "Nandini", "Simran", "Anika", "Zoya",
    "Shruti", "Mira", "Navya", "Tara", "Kiara", "Ayesha",
)
LAST_NAMES = (
    "Sharma", "Patel", "Singh", "Gupta", "Iyer", "Nair", "Mehta", "Verma",
    "Reddy", "Joshi", "Khan", "Kapoor", "Menon", "Das", "Chatterjee", "Rao",
    "Malhotra", "Bose", "Mishra", "Kulkarni", "Bhat", "Saxena", "Agarwal",
    "Pillai", "Jain", "Desai", "Banerjee", "Chauhan", "Sethi", "Thomas",
)

SUBJECT_CATALOG = {
    "BT": {
        1: ("Engineering Mathematics I", "Engineering Physics", "Programming for Problem Solving", "Engineering Graphics", "Indian Constitution", "Environmental Sustainability"),
        3: ("Engineering Mathematics III", "Data Structures and Algorithms", "Digital Systems", "Object-Oriented Programming", "Innovation and Design Thinking", "Technical Communication"),
        5: ("Database Management Systems", "Computer Networks", "Theory of Computation", "Software Engineering", "Cloud Computing", "Machine Learning Foundations"),
        7: ("Distributed Systems", "Professional Ethics", "Major Project Phase I", "Industrial Engineering", "Cyber Security", "Internet of Things"),
    },
    "MT": {
        1: ("Advanced Algorithms", "Research Methodology", "Advanced Computer Architecture", "Mathematical Foundations of Computing", "Natural Language Processing", "Secure Systems Engineering"),
        3: ("Dissertation Phase I", "Seminar and Technical Writing", "Distributed Computing", "Research Colloquium", "Deep Learning", "Cloud Native Architecture"),
    },
    "BBA": {
        1: ("Principles of Management", "Business Economics", "Financial Accounting", "Business Mathematics", "Indian Business Environment", "Digital Productivity"),
        3: ("Marketing Management", "Human Resource Management", "Cost Accounting", "Business Statistics", "Consumer Behaviour", "Entrepreneurship Development"),
        5: ("Strategic Management", "Financial Management", "Operations Management", "Business Law", "Retail Management", "International Business"),
    },
    "MBA": {
        1: ("Managerial Economics", "Accounting for Managers", "Organizational Behaviour", "Quantitative Methods", "Business Analytics", "Design Thinking for Managers"),
        3: ("Strategic Management", "Operations and Supply Chain", "Business Research Methods", "Corporate Governance", "Investment Analysis", "Digital Marketing Strategy"),
    },
    "BP": {
        1: ("Human Anatomy and Physiology I", "Pharmaceutical Analysis I", "Pharmaceutics I", "Pharmaceutical Inorganic Chemistry", "Remedial Biology", "Communication Skills"),
        3: ("Pharmaceutical Organic Chemistry II", "Physical Pharmaceutics I", "Pharmaceutical Microbiology", "Pharmaceutical Engineering", "Biostatistics", "Computer Applications in Pharmacy"),
        5: ("Medicinal Chemistry II", "Industrial Pharmacy I", "Pharmacology II", "Pharmacognosy II", "Herbal Drug Technology", "Pharmaceutical Regulatory Science"),
        7: ("Instrumental Methods of Analysis", "Industrial Pharmacy II", "Pharmacy Practice", "Novel Drug Delivery Systems", "Cosmetic Science", "Pharmacovigilance"),
    },
    "MP": {
        1: ("Modern Pharmaceutical Analytical Techniques", "Drug Delivery Systems", "Modern Pharmaceutics", "Regulatory Affairs", "Biopharmaceutics", "Quality by Design"),
        3: ("Research Methodology and Biostatistics", "Journal Club", "Dissertation Phase I", "Advanced Formulation Laboratory", "Nanopharmaceutics", "Intellectual Property Rights"),
    },
    "DP": {
        1: ("Pharmaceutics", "Pharmaceutical Chemistry", "Pharmacognosy", "Human Anatomy and Physiology", "Social Pharmacy", "Health Education"),
        3: ("Pharmacology", "Community Pharmacy and Management", "Biochemistry and Clinical Pathology", "Pharmacotherapeutics", "Hospital Pharmacy", "Pharmacy Law and Ethics"),
    },
    "BCA": {
        1: ("Fundamentals of Computers", "Programming in C", "Mathematics for Computing", "Digital Logic", "Office Automation", "Communication Skills"),
        3: ("Data Structures", "Object-Oriented Programming with Java", "Database Management Systems", "Operating Systems", "Web Design", "Open Source Technologies"),
        5: ("Software Engineering", "Computer Networks", "Python Programming", "Cloud Computing", "Data Analytics", "Mobile Application Development"),
    },
    "MCA": {
        1: ("Advanced Data Structures", "Advanced Database Systems", "Object-Oriented Software Engineering", "Discrete Mathematics", "Full Stack Development", "Python for Data Science"),
        3: ("Cloud Computing", "Machine Learning", "Information Security", "Major Project Phase I", "DevOps Engineering", "Natural Language Processing"),
    },
}


def seed_system_data(db: Session) -> None:
    """Reconcile permanent RBAC/type metadata and ensure one administrator."""
    permissions = {}
    for name, resource, action, description in PERMISSIONS:
        record = db.query(Permission).options(noload("*")).filter(Permission.name == name).first()
        if not record:
            record = Permission(name=name, resource=resource, action=action, description=description)
            db.add(record)
            db.flush()
        permissions[name] = record

    roles = {}
    for name, display_name in ROLE_NAMES.items():
        role = db.query(Role).options(noload("*")).filter(Role.name == name).first()
        if not role:
            role = Role(name=name, display_name=display_name, description=f"{display_name} role")
            db.add(role)
            db.flush()
        roles[name] = role

    for role_name, names in ROLE_PERMISSIONS.items():
        allowed_permission_ids = {permissions[name].id for name in names}
        db.query(RolePermission).filter(
            RolePermission.role_id == roles[role_name].id,
            ~RolePermission.permission_id.in_(allowed_permission_ids),
        ).delete(synchronize_session=False)
        for permission_name in names:
            exists = db.query(RolePermission).options(noload("*")).filter_by(
                role_id=roles[role_name].id,
                permission_id=permissions[permission_name].id,
            ).first()
            if not exists:
                db.add(RolePermission(role_id=roles[role_name].id, permission_id=permissions[permission_name].id))

    descriptions = {
        "COMMON": "Required for all students in the program",
        "SPECIALIZATION": "Restricted to a branch or specialization",
        "ELECTIVE": "Selected from a program elective group",
        "OPEN_ELECTIVE": "Selectable across departments",
        "LAB": "Practical or laboratory subject",
        "PROJECT": "Project work",
        "INTERNSHIP": "Industry internship credits",
    }
    for code in SUBJECT_TYPE_CODES:
        if not db.query(SubjectType).options(noload("*")).filter(SubjectType.code == code).first():
            db.add(SubjectType(code=code, name=code.replace("_", " ").title(), description=descriptions[code]))
    db.flush()

    admin = (
        db.query(User).options(noload("*")).join(UserRole).join(Role)
        .filter(Role.name == "admin", User.is_deleted.is_(False)).order_by(User.id).first()
    )
    if not admin:
        admin = User(
            email=settings.ADMIN_EMAIL,
            username=settings.ADMIN_USERNAME,
            hashed_password=PasswordHasher.hash_password(settings.ADMIN_PASSWORD),
            full_name="System Administrator",
        )
        db.add(admin)
        db.flush()
        db.add(UserRole(user_id=admin.id, role_id=roles["admin"].id))
    db.commit()


def _assign_role(db: Session, user: User, role_name: str) -> None:
    role = db.query(Role).options(noload("*")).filter(Role.name == role_name).one()
    if not db.query(UserRole).options(noload("*")).filter_by(user_id=user.id, role_id=role.id).first():
        db.add(UserRole(user_id=user.id, role_id=role.id))


def _user(db: Session, email: str, username: str, name: str, password_hash: str, role: str) -> User:
    record = db.query(User).options(noload("*")).filter(User.email == email).first()
    if not record:
        record = User(
            email=email,
            username=username,
            full_name=name,
            hashed_password=password_hash,
        )
        db.add(record)
        db.flush()
    _assign_role(db, record, role)
    return record


def _odd_semesters(duration: int) -> tuple[int, ...]:
    return tuple(number for number in (1, 3, 5, 7) if number <= duration * 2)


def _seed_is_current(db: Session, academic_year: str) -> bool:
    expected_departments = {item[0] for item in DEPARTMENT_DATA}
    actual_departments = {name for (name,) in db.query(Department.name).filter(Department.is_deleted.is_(False)).all()}
    if actual_departments != expected_departments:
        return False
    sections = db.query(Section).options(noload("*")).filter(
        Section.academic_year == academic_year,
        Section.is_deleted.is_(False),
    ).all()
    if not sections or any(
        db.query(func.count(Student.id)).filter(Student.section_id == section.id, Student.is_deleted.is_(False)).scalar() != 50
        for section in sections
    ):
        return False
    branches = db.query(Branch).options(noload("*")).filter(Branch.is_deleted.is_(False)).all()
    if len(branches) != sum(len(item[5]) for item in PROGRAM_DATA):
        return False
    if any(
        db.query(func.count(Teacher.id)).filter(Teacher.branch_id == branch.id, Teacher.is_deleted.is_(False)).scalar() != 6
        for branch in branches
    ):
        return False
    return (
        db.query(Assignment).filter(Assignment.is_deleted.is_(False)).count() >= len(sections)
        and db.query(Payment).filter(Payment.is_deleted.is_(False)).count() >= len(sections) * 50
        and db.query(LibraryBook).filter(LibraryBook.is_deleted.is_(False)).count() >= 30
        and db.query(TimetableVersion).filter(TimetableVersion.is_deleted.is_(False)).count() == len(sections)
    )


def _teacher_name(index: int) -> tuple[str, str]:
    first_pool = MALE_NAMES + FEMALE_NAMES
    return first_pool[(index * 7 + 3) % len(first_pool)], LAST_NAMES[(index * 11 + 5) % len(LAST_NAMES)]


def _student_name(section_index: int, student_index: int) -> tuple[str, str, str]:
    female = student_index % 2 == 1
    pool = FEMALE_NAMES if female else MALE_NAMES
    first = pool[(student_index + section_index * 3) % len(pool)]
    last = LAST_NAMES[(student_index * 7 + section_index * 5) % len(LAST_NAMES)]
    return first, last, "female" if female else "male"


def _seed_academic_hierarchy(db: Session, year: int):
    departments = {}
    for name, code, description in DEPARTMENT_DATA:
        record = Department(name=name, code=code, description=description, hod_id=None)
        db.add(record)
        departments[code] = record
    db.flush()

    courses, branches = {}, []
    program_meta = {}
    for department_code, name, code, duration, regulator, branch_data in PROGRAM_DATA:
        course = Course(
            name=name,
            code=code,
            duration_years=str(duration),
            department_id=departments[department_code].id,
            description=f"{duration}-year {name} program approved under {regulator} academic norms.",
        )
        db.add(course)
        db.flush()
        courses[code] = course
        program_meta[course.id] = {"duration": duration, "regulator": regulator}
        for branch_name, branch_code in branch_data:
            branch = Branch(
                course_id=course.id,
                name=branch_name,
                code=branch_code,
                description=f"{branch_name} pathway within the {name} program.",
                hod_id=None,
            )
            db.add(branch)
            branches.append(branch)
    db.flush()

    curricula, versions, semesters = {}, {}, {}
    for branch in branches:
        course = branch.course
        regulator = program_meta[course.id]["regulator"]
        curriculum = Curriculum(
            course_id=course.id,
            branch_id=branch.id,
            code=f"{course.code}-{branch.code}-CUR",
            name=f"{course.name} – {branch.name} Curriculum",
            description=f"Outcome-based curriculum for {branch.name}, aligned with {regulator} and CBCS requirements.",
        )
        db.add(curriculum)
        db.flush()
        curricula[branch.id] = curriculum
        version_specs = (
            ("2023", f"{regulator} 2023 Regulation", 2023, 2023, 2023, "archived", False),
            ("2024", "CBCS 2024 Regulation", 2024, 2024, None, "active", True),
        )
        for version_code, title, effective, batch_start, batch_end, status, active in version_specs:
            version = CurriculumVersion(
                curriculum_id=curriculum.id,
                version_code=version_code,
                title=title,
                effective_year=effective,
                applicable_batch_start=batch_start,
                applicable_batch_end=batch_end,
                status=status,
                is_active=active,
                published_at=datetime(effective, 6, 1),
            )
            db.add(version)
            db.flush()
            versions[(branch.id, version_code)] = version
            for semester_number in _odd_semesters(program_meta[course.id]["duration"]):
                semester = AcademicSemester(
                    curriculum_version_id=version.id,
                    number=semester_number,
                    name=f"Semester {semester_number}",
                    minimum_credits=18,
                    maximum_credits=28,
                )
                db.add(semester)
                db.flush()
                semesters[(branch.id, version_code, semester_number)] = semester
    return departments, courses, branches, program_meta, curricula, versions, semesters


def _seed_teachers(db: Session, departments, branches, password_hash: str, year: int):
    teacher_role = db.query(Role).options(noload("*")).filter(Role.name == "teacher").one()
    teachers_by_branch = {}
    designations = ("Professor", "Professor", "Associate Professor", "Associate Professor", "Assistant Professor", "Assistant Professor")
    qualifications = ("Ph.D.", "Ph.D.", "Ph.D.", "Ph.D.", "M.Tech./Ph.D.", "M.Tech./Ph.D.")
    global_index = 0
    for branch_index, branch in enumerate(branches, start=1):
        branch_teachers = []
        for local_index, designation in enumerate(designations, start=1):
            first, last = _teacher_name(global_index)
            faculty_id = f"FC{str(year)[-2:]}{branch_index:02d}{local_index:02d}"
            user = User(
                email=f"{first.lower()}.{faculty_id.lower()}@cms.edu",
                username=faculty_id.lower(),
                hashed_password=password_hash,
                full_name=f"Dr. {first} {last}",
                phone=f"98{(71000000 + global_index):08d}",
                gender="female" if first in FEMALE_NAMES else "male",
                address=f"Faculty Housing, EduCore Campus, Block {chr(65 + branch_index % 8)}",
            )
            db.add(user)
            db.add(UserRole(user=user, role=teacher_role))
            teacher = Teacher(
                user=user,
                department_id=branch.course.department_id,
                branch_id=branch.id,
                faculty_id=faculty_id,
                employee_id=f"EC-{year}-{branch_index:02d}{local_index:02d}",
                designation=designation,
                specialization=branch.name,
                qualification=qualifications[local_index - 1],
                joining_date=date(year - (12 - local_index), 7, 1),
                experience_years=13 - local_index,
                bio=f"{designation} specializing in {branch.name}, teaching, mentoring, and applied research.",
            )
            db.add(teacher)
            branch_teachers.append(teacher)
            global_index += 1
        db.flush()
        teachers_by_branch[branch.id] = branch_teachers
    return teachers_by_branch


def _seed_subjects_and_sections(
    db: Session,
    year: int,
    academic_year: str,
    branches,
    program_meta,
    versions,
    semesters,
    teachers_by_branch,
):
    subject_types = {
        item.code: item
        for item in db.query(SubjectType).options(noload("*")).filter(SubjectType.code.in_(SUBJECT_TYPE_CODES)).all()
    }
    mappings = {}
    sections = []
    section_assignments = {}

    for branch in branches:
        course = branch.course
        teachers = teachers_by_branch[branch.id]
        for semester_number in _odd_semesters(program_meta[course.id]["duration"]):
            catalog = SUBJECT_CATALOG[course.code][semester_number]
            subjects = []
            for position, subject_name in enumerate(catalog, start=1):
                classification = (
                    "ELECTIVE" if position >= 5
                    else "LAB" if position == 3 and course.code in {"BT", "BP", "BCA", "MCA"}
                    else "SPECIALIZATION" if position in {2, 4}
                    else "COMMON"
                )
                delivery = "practical" if classification == "LAB" else "project" if "Project" in subject_name or "Dissertation" in subject_name else "theory"
                subject = Subject(
                    name=subject_name,
                    code=f"{course.code}{branch.code}{semester_number}{position:02d}",
                    description=f"{subject_name} for Semester {semester_number} of {branch.name}.",
                    credits=2 if delivery == "practical" else 4 if delivery == "project" else 3,
                    semester=semester_number,
                    type=delivery,
                    department_id=course.department_id,
                    teacher_id=teachers[(position - 1) % 6].id,
                    subject_type_id=subject_types[classification].id,
                )
                db.add(subject)
                subjects.append(subject)
            db.flush()

            for version_code in ("2023", "2024"):
                semester = semesters[(branch.id, version_code, semester_number)]
                group = ElectiveGroup(
                    semester_id=semester.id,
                    code=f"PE-{semester_number}",
                    name=f"Professional Elective – Semester {semester_number}",
                    minimum_choices=1,
                    maximum_choices=1,
                    description="Students select one professionally aligned elective from the offered basket.",
                )
                db.add(group)
                db.flush()
                for position, subject in enumerate(subjects, start=1):
                    mapping = CurriculumSubject(
                        semester_id=semester.id,
                        subject_id=subject.id,
                        branch_id=branch.id,
                        elective_group_id=group.id if position >= 5 else None,
                        is_mandatory=position < 5,
                        display_order=position,
                    )
                    db.add(mapping)
                    db.flush()
                    mappings[(branch.id, version_code, semester_number, position)] = mapping

            cohort_year = year - ((semester_number - 1) // 2)
            version_code = "2023" if cohort_year == 2023 else "2024"
            for section_code in ("A", "B"):
                section = Section(
                    course_id=course.id,
                    branch_id=branch.id,
                    curriculum_version_id=versions[(branch.id, version_code)].id,
                    semester_number=semester_number,
                    code=section_code,
                    academic_year=academic_year,
                    capacity=50,
                )
                db.add(section)
                db.flush()
                sections.append(section)
                assignments = []
                for position in range(1, 7):
                    assignment = FacultyAssignment(
                        teacher_id=teachers[(semester_number + position + (0 if section_code == "A" else 2)) % 6].id,
                        curriculum_subject_id=mappings[(branch.id, version_code, semester_number, position)].id,
                        section_id=section.id,
                        academic_year=academic_year,
                        role="primary" if position <= 5 else "co_faculty",
                    )
                    db.add(assignment)
                    assignments.append(assignment)
                db.flush()
                section_assignments[section.id] = assignments
                for assignment in assignments:
                    db.add(SubjectTeacher(
                        subject_id=assignment.curriculum_subject.subject_id,
                        teacher_id=assignment.teacher_id,
                        section=section.code,
                    ))
    db.flush()
    return sections, section_assignments, mappings


def _seed_students(
    db: Session,
    year: int,
    sections,
    password_hash: str,
    mappings,
):
    from app.services.crud_services import StudentService

    service = StudentService(db)
    student_role = db.query(Role).options(noload("*")).filter(Role.name == "student").one()
    students_by_section = {}
    all_students = []
    for section_index, section in enumerate(sections):
        students = []
        admission_year = year - ((section.semester_number - 1) // 2)
        for student_index in range(50):
            first, last, gender = _student_name(section_index, student_index)
            student_id = service.generate_student_id(admission_year, section.course, section.branch)
            institutional_email = f"{re.sub(r'[^a-z0-9]', '', first.lower())}.{student_id.lower()}@cms.edu"
            user = User(
                email=institutional_email,
                username=student_id.lower(),
                hashed_password=password_hash,
                full_name=f"{first} {last}",
                phone=f"9{(100000000 + section_index * 50 + student_index):09d}",
                gender=gender,
                address=f"{24 + student_index}, {last} Nagar, {['Delhi', 'Mumbai', 'Bengaluru', 'Jaipur', 'Lucknow'][section_index % 5]}",
            )
            db.add(user)
            db.add(UserRole(user=user, role=student_role))
            student = Student(
                user=user,
                department_id=section.course.department_id,
                course_id=section.course_id,
                branch_id=section.branch_id,
                curriculum_version_id=section.curriculum_version_id,
                section_id=section.id,
                student_id=student_id,
                enrollment_number=f"ENR-{student_id}",
                date_of_birth=date(admission_year - 18, (student_index % 12) + 1, (student_index % 27) + 1),
                admission_date=date(admission_year, 7, 15 + student_index % 10),
                admission_year=admission_year,
                semester=section.semester_number,
                current_semester=section.semester_number,
                section=section.code,
                guardian_name=f"{['Rajesh', 'Sunita', 'Michael', 'Farah'][student_index % 4]} {last}",
                guardian_phone=f"8{(200000000 + section_index * 50 + student_index):09d}",
                father_name=f"Mr. {['Rajesh', 'Suresh', 'Anil', 'Joseph'][student_index % 4]} {last}",
                mother_name=f"Mrs. {['Sunita', 'Kavita', 'Mary', 'Shabana'][student_index % 4]} {last}",
                blood_group=("A+", "B+", "O+", "AB+", "A-", "O-")[student_index % 6],
                personal_email=f"{first.lower()}.{last.lower()}{student_index + 1}@example.com",
            )
            db.add(student)
            students.append(student)
        db.flush()
        version_code = section.curriculum_version.version_code
        for student_index, student in enumerate(students):
            elective_position = 5 if student_index % 2 == 0 else 6
            db.add(StudentElective(
                student_id=student.id,
                curriculum_subject_id=mappings[(section.branch_id, version_code, section.semester_number, elective_position)].id,
                status="selected",
            ))
        students_by_section[section.id] = students
        all_students.extend(students)
    db.flush()
    return students_by_section, all_students


def _recent_working_days(count: int) -> list[date]:
    result = []
    cursor = date.today() - timedelta(days=1)
    while len(result) < count:
        if cursor.weekday() < 6:
            result.append(cursor)
        cursor -= timedelta(days=1)
    return result


def _seed_learning_records(db: Session, sections, students_by_section, section_assignments):
    attendance_dates = _recent_working_days(5)
    for section_index, section in enumerate(sections):
        students = students_by_section[section.id]
        assignments = section_assignments[section.id]
        graded_assignments = assignments[:4] + [assignments[4 if section_index % 2 == 0 else 5]]

        for day_index, attendance_date in enumerate(attendance_dates):
            faculty_assignment = graded_assignments[day_index % len(graded_assignments)]
            subject_id = faculty_assignment.curriculum_subject.subject_id
            for student_index, student in enumerate(students):
                selector = (student_index * 3 + day_index + section_index) % 20
                status = (
                    AttendanceStatus.ABSENT if selector == 0
                    else AttendanceStatus.LATE if selector == 1
                    else AttendanceStatus.EXCUSED if selector == 2
                    else AttendanceStatus.PRESENT
                )
                db.add(Attendance(
                    student_id=student.id,
                    subject_id=subject_id,
                    teacher_id=faculty_assignment.teacher_id,
                    section_id=section.id,
                    faculty_assignment_id=faculty_assignment.id,
                    date=attendance_date,
                    status=status,
                    remarks="Approved academic leave" if status == AttendanceStatus.EXCUSED else None,
                ))

        for subject_index, faculty_assignment in enumerate(graded_assignments):
            subject_id = faculty_assignment.curriculum_subject.subject_id
            for student_index, student in enumerate(students):
                score = 46 + ((student_index * 7 + subject_index * 11 + section_index * 3) % 50)
                db.add(Marks(
                    student_id=student.id,
                    subject_id=subject_id,
                    exam_type=ExamType.INTERNAL,
                    marks_obtained=float(score),
                    max_marks=100,
                    semester=section.semester_number,
                    remarks="Excellent performance" if score >= 85 else "Good progress" if score >= 65 else "Needs guided practice",
                ))

        assignment_specs = (
            ("Applied Case Study", "Analyze the supplied real-world scenario and submit a structured solution.", 10),
            ("Concept and Practice Portfolio", "Compile worked examples, reflections, and supporting references.", 18),
        )
        for assignment_index, (title, description, due_offset) in enumerate(assignment_specs):
            faculty_assignment = graded_assignments[assignment_index * 4]
            assignment = Assignment(
                title=f"{faculty_assignment.curriculum_subject.subject.name}: {title}",
                description=description,
                due_date=datetime.now() + timedelta(days=due_offset),
                faculty_assignment_id=faculty_assignment.id,
            )
            db.add(assignment)
            db.flush()
            for student_index, student in enumerate(students):
                state = ("pending", "submitted", "accepted", "accepted", "rejected")[(student_index + assignment_index) % 5]
                db.add(AssignmentSubmission(
                    assignment_id=assignment.id,
                    student_id=student.id,
                    status=state,
                    content=None if state == "pending" else f"Submission by {student.user.full_name}: completed analysis and supporting references.",
                    feedback=(
                        "Well reasoned and clearly presented." if state == "accepted"
                        else "Please revise the evidence and resubmit." if state == "rejected"
                        else None
                    ),
                    submitted_at=None if state == "pending" else datetime.now() - timedelta(days=(student_index % 6) + 1),
                ))
    db.flush()


def _seed_timetables(db: Session, admin: User, sections, section_assignments):
    for section in sections:
        version = TimetableVersion(
            course_id=section.course_id,
            department_id=section.course.department_id,
            branch_id=section.branch_id,
            section_id=section.id,
            semester=section.semester_number,
            version_number=1,
            status="approved",
            submitted_by_id=admin.id,
            approved_by_id=admin.id,
        )
        db.add(version)
        db.flush()
        assignments = section_assignments[section.id]
        for day_of_week in range(1, 7):
            for slot_index in range(1, 9):
                assignment = assignments[(day_of_week * 2 + slot_index - 3) % len(assignments)]
                db.add(TimetableSlot(
                    version_id=version.id,
                    day_of_week=day_of_week,
                    slot_index=slot_index,
                    subject_id=assignment.curriculum_subject.subject_id,
                    teacher_id=assignment.teacher_id,
                ))
    db.flush()


def _seed_finance(db: Session, admin: User, courses, sections, all_students, year: int, academic_year: str):
    base_fees = {
        "BT": 112500, "MT": 98500, "BBA": 68000, "MBA": 125000,
        "BP": 108000, "MP": 115000, "DP": 72000, "BCA": 62000, "MCA": 88000,
    }
    fee_structures = {}
    for course in courses.values():
        duration = int(course.duration_years)
        for semester_number in _odd_semesters(duration):
            structure = FeeStructure(
                name=f"{course.code} Semester {semester_number} Academic Fee",
                amount=base_fees[course.code] + (semester_number - 1) * 2500,
                course_id=course.id,
                academic_year=academic_year,
                semester=semester_number,
                description="Tuition, academic services, examinations, laboratories, and campus technology.",
            )
            db.add(structure)
            db.flush()
            fee_structures[(course.id, semester_number)] = structure

    methods = (PaymentMethod.UPI, PaymentMethod.ONLINE, PaymentMethod.BANK_TRANSFER, PaymentMethod.CHEQUE, PaymentMethod.CASH)
    for student_index, student in enumerate(all_students):
        structure = fee_structures[(student.course_id, student.current_semester)]
        ratio = (1.0, 1.0, 0.75, 0.5)[student_index % 4]
        invoice = StudentFee(
            student_id=student.id,
            fee_structure_id=structure.id,
            title=f"{academic_year} Semester {student.current_semester} Academic Fee",
            amount=structure.amount,
            due_date=date(year, 8, 31),
            status=FeeStatus.PAID if ratio == 1 else FeeStatus.PARTIAL,
            remarks="System-generated academic fee demand.",
        )
        db.add(invoice)
        db.flush()
        db.add(Payment(
            student_fee_id=invoice.id,
            amount=round(structure.amount * ratio, 2),
            payment_date=date(year, 7, 5 + student_index % 24),
            payment_method=methods[student_index % len(methods)],
            transaction_reference=f"EDU{year}{student.student_id}{student_index:04d}",
            status=PaymentStatus.SUCCESS,
            remarks="Verified student fee receipt.",
        ))

    categories = {}
    for name, description in (
        ("Campus Utilities", "Electricity, water, and energy services"),
        ("Laboratory Supplies", "Consumables, instruments, and maintenance"),
        ("IT Infrastructure", "Cloud services, networking, and software"),
        ("Library Acquisitions", "Books, journals, and databases"),
        ("Student Activities", "Clubs, cultural programs, and sports"),
        ("Repairs and Maintenance", "Buildings, furniture, and equipment"),
        ("Transport", "Campus vehicles, fuel, and servicing"),
        ("Examination Operations", "Assessment printing and logistics"),
    ):
        category = ExpenseCategory(name=name, description=description)
        db.add(category)
        categories[name] = category
    db.flush()

    expense_titles = (
        ("Electricity and solar grid settlement", "Campus Utilities", 286400),
        ("Chemistry laboratory glassware", "Laboratory Supplies", 118750),
        ("Campus ERP cloud hosting", "IT Infrastructure", 164000),
        ("IEEE and DELNET subscriptions", "Library Acquisitions", 225000),
        ("Inter-college sports meet", "Student Activities", 137500),
        ("Academic block HVAC servicing", "Repairs and Maintenance", 194800),
        ("College bus preventive maintenance", "Transport", 96500),
        ("End-semester answer book printing", "Examination Operations", 78400),
        ("Network core switch replacement", "IT Infrastructure", 312000),
        ("Pharmacy laboratory reagents", "Laboratory Supplies", 146250),
        ("Library textbook acquisition", "Library Acquisitions", 188600),
        ("Student induction programme", "Student Activities", 112000),
    )
    for index, (title, category_name, amount) in enumerate(expense_titles):
        db.add(Expense(
            title=title,
            amount=amount,
            expense_date=date(year, 6 + (index % 2), 2 + index * 2),
            category_id=categories[category_name].id,
            receipt_url=f"/uploads/receipts/{year}/EXP-{index + 1:04d}.pdf",
            recorded_by=admin.id,
            remarks="Approved against the institutional operating budget.",
        ))
    db.flush()


def _seed_salaries(db: Session, teachers_by_branch, year: int):
    salary_by_designation = {
        "Professor": 148000,
        "Associate Professor": 112000,
        "Assistant Professor": 78000,
    }
    teachers = [teacher for branch_teachers in teachers_by_branch.values() for teacher in branch_teachers]
    months = ((6, date(year, 6, 30)), (7, date(year, 7, 31)))
    for teacher_index, teacher in enumerate(teachers):
        for month, payment_date in months:
            db.add(StaffSalary(
                user_id=teacher.user_id,
                amount=salary_by_designation[teacher.designation],
                payment_date=payment_date,
                month=month,
                year=year,
                payment_method=PaymentMethod.BANK_TRANSFER,
                transaction_reference=f"SAL-{year}-{month:02d}-{teacher.faculty_id}",
                remarks="Monthly salary processed through institutional payroll.",
            ))
    db.flush()


def _seed_library(db: Session, all_students, teachers_by_branch, staff_users, year: int):
    category_data = (
        ("Computer Science", "CS-A"), ("Engineering", "ENG-B"), ("Management", "MGT-A"),
        ("Pharmacy", "PHA-A"), ("Mathematics", "SCI-C"), ("Research Methods", "REF-A"),
        ("Literature", "GEN-B"), ("Career Development", "GEN-C"),
    )
    categories = []
    for name, rack in category_data:
        record = BookCategory(name=name, default_rack=rack)
        db.add(record)
        categories.append(record)

    author_data = (
        ("Thomas H. Cormen", "Computer scientist and co-author of a definitive algorithms textbook."),
        ("Bjarne Stroustrup", "Designer of C++ and author on programming language design."),
        ("Abraham Silberschatz", "Author and researcher in operating systems and databases."),
        ("R. S. Khurmi", "Indian author of widely used mechanical engineering textbooks."),
        ("S. S. Bhavikatti", "Civil engineering educator and author."),
        ("Philip Kotler", "Scholar of modern marketing management."),
        ("Stephen P. Robbins", "Author in organizational behaviour and management."),
        ("I. M. Pandey", "Indian scholar and author in financial management."),
        ("K. D. Tripathi", "Indian pharmacology educator and author."),
        ("C. K. Kokate", "Author and academic in pharmacognosy."),
        ("Brahmankar D. M.", "Author in biopharmaceutics and pharmacokinetics."),
        ("V. Rajaraman", "Indian computer science educator and author."),
        ("Herbert Schildt", "Author of programming language reference books."),
        ("Ian Sommerville", "Researcher and author in software engineering."),
        ("Donald E. Knuth", "Computer scientist known for foundational work in algorithms."),
        ("C. R. Kothari", "Author of a standard text on research methodology."),
    )
    authors = []
    for name, biography in author_data:
        record = LibraryAuthor(name=name, biography=biography)
        db.add(record)
        authors.append(record)

    publisher_data = (
        ("Pearson Education India", "Higher education publishing; support@pearson.in"),
        ("McGraw Hill Education India", "Academic publishing; helpdesk@mheducation.co.in"),
        ("Oxford University Press", "University and research publishing; india.office@oup.com"),
        ("S. Chand Publishing", "Indian educational publishing; info@schandgroup.com"),
        ("Elsevier India", "Scientific and medical publishing; support@elsevier.com"),
        ("Wiley India", "Technical and professional publishing; csupport@wiley.com"),
        ("CBS Publishers & Distributors", "Medical and pharmacy publishing; delhi@cbspd.com"),
        ("PHI Learning", "Engineering and management publishing; phi@phindia.com"),
    )
    publishers = []
    for name, contact in publisher_data:
        record = LibraryPublisher(name=name, contact_info=contact)
        db.add(record)
        publishers.append(record)
    db.flush()

    book_titles = (
        "Introduction to Algorithms", "The C++ Programming Language", "Operating System Concepts",
        "Database System Concepts", "A Textbook of Machine Design", "Strength of Materials",
        "Structural Analysis", "Marketing Management", "Organizational Behaviour",
        "Financial Management", "Essentials of Medical Pharmacology", "Pharmacognosy",
        "Biopharmaceutics and Pharmacokinetics", "Fundamentals of Computers",
        "Java: The Complete Reference", "Software Engineering", "The Art of Computer Programming",
        "Research Methodology: Methods and Techniques", "Computer Networks", "Cloud Computing",
        "Engineering Mathematics", "Fluid Mechanics", "Surveying and Levelling",
        "Human Resource Management", "Consumer Behaviour", "Business Analytics",
        "Pharmaceutical Analysis", "Physical Pharmaceutics", "Hospital and Clinical Pharmacy",
        "Python Programming", "Data Structures Using C", "Web Technologies",
        "Artificial Intelligence", "Cyber Security Essentials", "Entrepreneurship Development",
        "Professional Communication",
    )
    books = []
    for index, title in enumerate(book_titles):
        category = categories[index % len(categories)]
        book = LibraryBook(
            title=title,
            isbn=f"97881{(1000000000 + index * 7919):010d}"[:13],
            edition=f"{2 + index % 5}{'nd' if index % 5 == 0 else 'th'} Edition",
            author_id=authors[index % len(authors)].id,
            publisher_id=publishers[index % len(publishers)].id,
            category_id=category.id,
            total_copies=12,
            available_copies=12,
            shelf_location=f"{category.default_rack}-{index + 1:03d}",
            description=f"Recommended academic reference for {category.name}.",
            status=BookStatus.AVAILABLE,
            purchase_date=date(year, 4 + index % 3, 1 + index % 25),
            price=Decimal(str(650 + (index % 12) * 95)),
            vendor="National Academic Book Suppliers",
            language="English",
            pages=280 + (index % 10) * 44,
            condition=BookCondition.NEW if index % 3 else BookCondition.GOOD,
        )
        db.add(book)
        books.append(book)
    db.flush()

    teachers = [teacher for branch_teachers in teachers_by_branch.values() for teacher in branch_teachers]
    members = []
    for student in all_students:
        member = LibraryMember(
            user_id=student.user_id,
            member_type=MemberType.STUDENT,
            membership_date=student.admission_date,
            expiry_date=date(year + 1, 6, 30),
            max_books_allowed=4,
            is_active=True,
        )
        db.add(member)
        members.append(member)
    for teacher in teachers:
        member = LibraryMember(
            user_id=teacher.user_id,
            member_type=MemberType.FACULTY,
            membership_date=teacher.joining_date,
            expiry_date=date(year + 2, 6, 30),
            max_books_allowed=8,
            is_active=True,
        )
        db.add(member)
        members.append(member)
    for user in staff_users:
        member = LibraryMember(
            user_id=user.id,
            member_type=MemberType.STAFF,
            membership_date=date(year, 1, 1),
            expiry_date=date(year + 1, 6, 30),
            max_books_allowed=5,
            is_active=True,
        )
        db.add(member)
        members.append(member)
    db.flush()

    for index in range(90):
        member = members[index]
        book = books[index % len(books)]
        mode = index % 3
        if mode == 0:
            status, return_date, due_date, fine_amount = IssueStatus.ISSUED, None, date.today() + timedelta(days=8), 0
            book.available_copies -= 1
        elif mode == 1:
            status, return_date, due_date, fine_amount = IssueStatus.OVERDUE, None, date.today() - timedelta(days=5), 50
            book.available_copies -= 1
        else:
            status, return_date, due_date, fine_amount = IssueStatus.RETURNED, date.today() - timedelta(days=2), date.today() - timedelta(days=4), 20
        issue = BookIssue(
            book_id=book.id,
            member_id=member.id,
            issue_date=date.today() - timedelta(days=18 + index % 10),
            due_date=due_date,
            return_date=return_date,
            fine_amount=fine_amount,
            status=status,
            remarks="Issued through the central circulation desk.",
            renewals_count=index % 2,
            fine_paid=status == IssueStatus.RETURNED,
            condition_on_issue=BookCondition.GOOD,
            condition_on_return=BookCondition.GOOD if return_date else None,
        )
        db.add(issue)
        db.flush()
        if fine_amount:
            db.add(LibraryFine(
                issue_id=issue.id,
                member_id=member.id,
                amount=Decimal(str(fine_amount)),
                reason="Overdue library material",
                is_paid=status == IssueStatus.RETURNED,
                payment_date=datetime.now() - timedelta(days=2) if status == IssueStatus.RETURNED else None,
            ))

    for index in range(30):
        db.add(BookReservation(
            book_id=books[(index + 7) % len(books)].id,
            member_id=members[index + 100].id,
            reservation_date=datetime.now() - timedelta(days=index % 8),
            status=(ReservationStatus.PENDING, ReservationStatus.FULFILLED, ReservationStatus.CANCELLED)[index % 3],
            notified_date=datetime.now() - timedelta(days=1) if index % 3 == 1 else None,
        ))
    db.flush()


def _seed_notifications(db: Session, admin: User):
    notifications = (
        ("Odd semester dataset is ready", "All active sections, students, faculty allocations, and timetables are available.", NotificationType.SUCCESS, "/dashboard"),
        ("Fee collection is active", "Academic fee invoices have been generated for every enrolled student.", NotificationType.INFO, "/student-fees"),
        ("Library circulation update", "Current issues, reservations, returns, and fines were synchronized.", NotificationType.INFO, "/book-issues"),
        ("Attendance review", "Recent attendance records are ready for department-level review.", NotificationType.WARNING, "/attendance"),
        ("Internal marks published", "Grade reports contain internal assessment marks for every active student.", NotificationType.SUCCESS, "/marks"),
    )
    for title, message, kind, link in notifications:
        db.add(Notification(
            user_id=admin.id,
            title=title,
            message=message,
            notification_type=kind,
            is_read=False,
            link=link,
        ))


def seed_demo_data(db: Session) -> None:
    """Replace business data with the complete, relational odd-semester graph."""
    seed_system_data(db)
    year = date.today().year
    academic_year = f"{year}-{year + 1}"
    if _seed_is_current(db, academic_year):
        logger.info("Comprehensive EduCore seed is already current; no changes required.")
        return

    clean_database_keep_admin(db)
    db.expire_all()
    admin = (
        db.query(User).options(noload("*")).join(UserRole).join(Role)
        .filter(Role.name == "admin", User.is_deleted.is_(False)).order_by(User.id).first()
    )
    password_hash = admin.hashed_password
    logger.info("Seeding the %s odd-semester campus dataset.", academic_year)

    departments, courses, branches, program_meta, curricula, versions, semesters = _seed_academic_hierarchy(db, year)
    teachers_by_branch = _seed_teachers(db, departments, branches, password_hash, year)
    sections, section_assignments, mappings = _seed_subjects_and_sections(
        db, year, academic_year, branches, program_meta, versions, semesters, teachers_by_branch,
    )
    students_by_section, all_students = _seed_students(db, year, sections, password_hash, mappings)
    _seed_learning_records(db, sections, students_by_section, section_assignments)
    _seed_timetables(db, admin, sections, section_assignments)
    _seed_finance(db, admin, courses, sections, all_students, year, academic_year)
    _seed_salaries(db, teachers_by_branch, year)

    accountant = _user(db, "neha.kapoor@cms.edu", "neha.accounts", "Neha Kapoor", password_hash, "accountant")
    librarian = _user(db, "rahul.menon@cms.edu", "rahul.library", "Rahul Menon", password_hash, "librarian")
    _seed_library(db, all_students, teachers_by_branch, (accountant, librarian), year)
    _seed_notifications(db, admin)

    db.commit()
    logger.info(
        "Comprehensive seed complete: %d departments, %d courses, %d branches, "
        "%d faculty, %d sections, and %d students.",
        len(departments), len(courses), len(branches),
        sum(len(items) for items in teachers_by_branch.values()),
        len(sections), len(all_students),
    )


def clean_database_keep_admin(db: Session) -> None:
    """Remove business data while retaining one administrator and RBAC metadata."""
    seed_system_data(db)
    admin = (
        db.query(User).join(UserRole).join(Role)
        .filter(Role.name == "admin", User.is_deleted.is_(False)).order_by(User.id).first()
    )
    admin_id = admin.id
    bind = db.get_bind()
    table_names = inspect(bind).get_table_names()
    preserved = {"alembic_version", "roles", "permissions", "role_permissions", "subject_types"}
    if bind.dialect.name == "mysql":
        db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    try:
        for table_name in table_names:
            if table_name in preserved or table_name in {"users", "user_roles"}:
                continue
            db.execute(text(f"DELETE FROM `{table_name}`"))
        db.execute(text("DELETE FROM user_roles WHERE user_id <> :admin_id"), {"admin_id": admin_id})
        db.execute(text("DELETE FROM users WHERE id <> :admin_id"), {"admin_id": admin_id})
        admin.is_deleted = False
        admin.deleted_at = None
        admin.is_active = True
        db.commit()
    finally:
        if bind.dialect.name == "mysql":
            db.execute(text("SET FOREIGN_KEY_CHECKS=1"))
            db.commit()
    logger.info("Database cleaned; administrator id=%s was preserved.", admin_id)


# Backwards-compatible import for application startup. Startup reconciles only
# permanent metadata; the comprehensive business seed remains an explicit CLI.
seed_database = seed_system_data


def main() -> None:
    parser = argparse.ArgumentParser(description="EduCore database seeding")
    parser.add_argument("--clean", action="store_true", help="delete business data and keep the current admin")
    parser.add_argument("--system", action="store_true", help="reconcile system metadata only")
    args = parser.parse_args()
    init_db()
    with SessionLocal() as db:
        if args.clean:
            clean_database_keep_admin(db)
        elif args.system:
            seed_system_data(db)
        else:
            seed_demo_data(db)


if __name__ == "__main__":
    main()
