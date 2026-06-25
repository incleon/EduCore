"""System bootstrap, deterministic demo seeding, and admin-preserving cleanup.

Run ``python -m app.database.seed`` to add demo data.
Run ``python -m app.database.seed --clean`` to remove business data while
preserving the current administrator and authorization metadata.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, noload

from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.security import PasswordHasher
from app.database.session import SessionLocal
from app.models.academic import (
    AcademicSemester, Branch, Curriculum, CurriculumSubject, CurriculumVersion,
    ElectiveGroup, FacultyAssignment, Section, StudentElective, SubjectType,
    SUBJECT_TYPE_CODES,
)
from app.models.attendance import Attendance, AttendanceStatus
from app.models.course import Course
from app.models.department import Department
from app.models.finance import StudentFee, FeeStatus
from app.models.library import BookIssue, IssueStatus, LibraryBook
from app.models.marks import ExamType, Marks
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.timetable_grid import TimetableSlot, TimetableVersion
from app.models.user import Permission, Role, RolePermission, User, UserRole

logger = get_logger(__name__)


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
    "student": ["view_attendance", "view_marks", "view_fees", "view_library", "view_dashboard", "manage_profile", "view_academic_structure", "select_electives"],
    "accountant": ["view_fees", "manage_fees", "view_students", "view_reports", "view_dashboard", "manage_profile", "view_academic_structure"],
    "librarian": ["view_library", "manage_library", "view_students", "view_dashboard", "manage_profile", "view_academic_structure"],
}

ROLE_NAMES = {
    "admin": "Administrator", "hod": "Head of Department", "teacher": "Teacher",
    "student": "Student", "accountant": "Accountant", "librarian": "Librarian",
}


def seed_system_data(db: Session) -> None:
    """Reconcile non-demo metadata and create an admin only when absent."""
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
        for permission_name in names:
            exists = db.query(RolePermission).options(noload("*")).filter_by(
                role_id=roles[role_name].id, permission_id=permissions[permission_name].id
            ).first()
            if not exists:
                db.add(RolePermission(role_id=roles[role_name].id, permission_id=permissions[permission_name].id))

    # Faculty-directory access is administrator-only. Remove legacy grants from
    # built-in non-admin roles so existing databases converge to this boundary.
    view_teachers = permissions["view_teachers"]
    for role_name in set(ROLE_NAMES) - {"admin"}:
        db.query(RolePermission).filter_by(
            role_id=roles[role_name].id,
            permission_id=view_teachers.id,
        ).delete(synchronize_session=False)

    descriptions = {
        "COMMON": "Required for all students in the program",
        "SPECIALIZATION": "Restricted to a branch or specialization",
        "ELECTIVE": "Selected from a program elective group",
        "OPEN_ELECTIVE": "Selectable across departments",
        "LAB": "Practical or laboratory subject",
        "PROJECT": "Project work", "INTERNSHIP": "Industry internship credits",
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
            email=settings.ADMIN_EMAIL, username=settings.ADMIN_USERNAME,
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
        record = User(email=email, username=username, full_name=name, hashed_password=password_hash)
        db.add(record)
        db.flush()
    _assign_role(db, record, role)
    return record


def seed_demo_data(db: Session) -> None:
    """Create a coherent ten-record demo graph without duplicating prior runs."""
    seed_system_data(db)
    logger.info("Demo seed: system metadata ready")
    year = date.today().year
    target_tables = (
        "departments", "courses", "branches", "curricula", "curriculum_versions",
        "academic_semesters", "sections", "subjects", "curriculum_subjects",
        "elective_groups", "student_electives", "faculty_assignments", "students",
        "teachers", "attendances", "marks", "student_fees",
        "timetable_versions", "timetable_slots",
    )
    counts = [db.execute(text(f"SELECT COUNT(*) FROM `{table}`")).scalar_one() for table in target_tables]
    seeded_students = db.execute(
        text("SELECT COUNT(*) FROM students WHERE student_id LIKE :prefix"),
        {"prefix": f"{str(year)[-2:]}BTCS%"},
    ).scalar_one()
    if seeded_students >= 10 and all(count >= 10 for count in counts):
        logger.info("Demo data is already complete; no changes required.")
        return
    admin = db.query(User).options(noload("*")).join(UserRole).join(Role).filter(Role.name == "admin").order_by(User.id).first()
    password_hash = admin.hashed_password

    department_data = [
        ("Engineering and Technology", "ENG"), ("Management Studies", "MGT"),
        ("Pharmaceutical Sciences", "PHA"), ("Commerce", "COM"),
        ("Arts and Humanities", "ART"), ("Science", "SCI"),
        ("Law", "LAW"), ("Education", "EDU"), ("Design", "DES"),
        ("Health Sciences", "HSC"),
    ]
    course_data = [
        ("Bachelor of Technology", "BT", "4"), ("Master of Business Administration", "MBA", "2"),
        ("Bachelor of Pharmacy", "BP", "4"), ("Bachelor of Commerce", "BC", "3"),
        ("Bachelor of Arts", "BA", "3"), ("Bachelor of Science", "BS", "3"),
        ("Bachelor of Laws", "LLB", "3"), ("Bachelor of Education", "BED", "2"),
        ("Bachelor of Design", "BD", "4"), ("Bachelor of Physiotherapy", "BPT", "4"),
    ]
    branch_data = [
        ("Computer Science", "CS"), ("Finance", "FIN"), ("Pharmaceutics", "PHT"),
        ("Accounting", "ACC"), ("Psychology", "PSY"), ("Data Science", "DS"),
        ("Corporate Law", "CL"), ("Special Education", "SE"),
        ("Interaction Design", "ID"), ("Sports Physiotherapy", "SP"),
    ]

    departments, courses, branches = [], [], []
    for index, ((dept_name, dept_code), (course_name, course_code, duration), (branch_name, branch_code)) in enumerate(zip(department_data, course_data, branch_data)):
        department = db.query(Department).options(noload("*")).filter(Department.code == dept_code).first()
        if not department:
            department = Department(name=dept_name, code=dept_code, description=f"Department of {dept_name}")
            db.add(department); db.flush()
        course = db.query(Course).options(noload("*")).filter(Course.code == course_code).first()
        if not course:
            course = Course(name=course_name, code=course_code, duration_years=duration, department_id=department.id, description=f"{course_name} program")
            db.add(course); db.flush()
        branch = db.query(Branch).options(noload("*")).filter_by(course_id=course.id, code=branch_code).first()
        if not branch:
            branch = Branch(course_id=course.id, name=branch_name, code=branch_code, description=f"{branch_name} specialization")
            db.add(branch); db.flush()
        departments.append(department); courses.append(course); branches.append(branch)
    logger.info("Demo seed: hierarchy roots ready")

    curricula, versions, semesters, sections, groups = [], [], [], [], []
    for index in range(10):
        curriculum = db.query(Curriculum).options(noload("*")).filter(Curriculum.code == f"{courses[index].code}-{year}").first()
        if not curriculum:
            curriculum = Curriculum(course_id=courses[index].id, branch_id=branches[index].id, code=f"{courses[index].code}-{year}", name=f"{course_data[index][0]} {year} Curriculum")
            db.add(curriculum); db.flush()
        version = db.query(CurriculumVersion).options(noload("*")).filter_by(curriculum_id=curriculum.id, version_code=str(year)).first()
        if not version:
            version = CurriculumVersion(curriculum_id=curriculum.id, version_code=str(year), title=f"{year} Regulation", effective_year=year, applicable_batch_start=year, status="active", is_active=True, published_at=datetime.utcnow())
            db.add(version); db.flush()
        semester = db.query(AcademicSemester).options(noload("*")).filter_by(curriculum_version_id=version.id, number=1).first()
        if not semester:
            semester = AcademicSemester(curriculum_version_id=version.id, number=1, name="Semester 1", minimum_credits=18, maximum_credits=28)
            db.add(semester); db.flush()
        section = db.query(Section).options(noload("*")).filter_by(course_id=courses[index].id, branch_scope_key=branches[index].id, semester_number=1, academic_year=f"{year}-{year+1}", code="A").first()
        if not section:
            section = Section(course_id=courses[index].id, branch_id=branches[index].id, branch_scope_key=branches[index].id, curriculum_version_id=version.id, semester_number=1, code="A", academic_year=f"{year}-{year+1}", capacity=60)
            db.add(section); db.flush()
        group = db.query(ElectiveGroup).options(noload("*")).filter_by(semester_id=semester.id, code="PE1").first()
        if not group:
            group = ElectiveGroup(semester_id=semester.id, code="PE1", name="Professional Elective I", minimum_choices=0, maximum_choices=1)
            db.add(group); db.flush()
        curricula.append(curriculum); versions.append(version); semesters.append(semester); sections.append(section); groups.append(group)
    logger.info("Demo seed: curricula ready")

    common_type = db.query(SubjectType).filter_by(code="COMMON").one()
    elective_type = db.query(SubjectType).filter_by(code="ELECTIVE").one()
    subject_names = ["Foundations of Computing", "Managerial Economics", "Pharmaceutical Analysis", "Financial Accounting", "Introduction to Psychology", "Applied Statistics", "Constitutional Studies", "Learning and Pedagogy", "Design Fundamentals", "Human Anatomy"]
    subjects, mappings = [], []
    for index, name in enumerate(subject_names):
        code = f"{courses[index].code}101"
        subject = db.query(Subject).options(noload("*")).filter(Subject.code == code).first()
        if not subject:
            subject = Subject(name=name, code=code, credits=4, semester=1, department_id=departments[index].id, subject_type_id=(elective_type.id if index == 0 else common_type.id), type="theory")
            db.add(subject); db.flush()
        mapping = db.query(CurriculumSubject).options(noload("*")).filter_by(semester_id=semesters[index].id, subject_id=subject.id, branch_scope_key=(branches[index].id if index == 0 else 0)).first()
        if not mapping:
            mapping = CurriculumSubject(semester_id=semesters[index].id, subject_id=subject.id, branch_id=(branches[index].id if index == 0 else None), branch_scope_key=(branches[index].id if index == 0 else 0), elective_group_id=(groups[index].id if index == 0 else None), is_mandatory=index != 0, display_order=1)
            db.add(mapping); db.flush()
        subjects.append(subject); mappings.append(mapping)
    logger.info("Demo seed: subjects ready")

    faculty_names = ["Aarav Mehta", "Ishita Rao", "Kabir Sharma", "Meera Nair", "Rohan Gupta", "Ananya Iyer", "Vikram Singh", "Nisha Verma", "Arjun Kapoor", "Kavya Menon"]
    teachers, assignments = [], []
    for index, name in enumerate(faculty_names):
        email = f"faculty{index+1}@cms.edu"
        user = _user(db, email, f"faculty{index+1}", name, password_hash, "teacher")
        teacher = db.query(Teacher).options(noload("*")).filter(Teacher.user_id == user.id).first()
        if not teacher:
            teacher = Teacher(user_id=user.id, department_id=departments[index].id, branch_id=branches[index].id, faculty_id=f"FC{str(year)[-2:]}{index+1:06d}", employee_id=f"EMP-{year}-{index+1:04d}", designation="Assistant Professor" if index else "Professor and HOD", specialization=branch_data[index][0], qualification="Ph.D.", joining_date=date(year-5, 7, 1), experience_years=5, bio=f"Faculty specialist in {branch_data[index][0]}.")
            db.add(teacher); db.flush()
        assignment = db.query(FacultyAssignment).options(noload("*")).filter_by(teacher_id=teacher.id, curriculum_subject_id=mappings[index].id, section_scope_key=sections[index].id, academic_year=f"{year}-{year+1}").first()
        if not assignment:
            assignment = FacultyAssignment(teacher_id=teacher.id, curriculum_subject_id=mappings[index].id, section_id=sections[index].id, section_scope_key=sections[index].id, academic_year=f"{year}-{year+1}", role="primary")
            db.add(assignment); db.flush()
        teachers.append(teacher); assignments.append(assignment)
    logger.info("Demo seed: faculty ready")
    departments[0].hod_id = teachers[0].id
    _assign_role(db, teachers[0].user, "hod")

    from app.services.crud_services import StudentService
    student_names = [("Aarav", "Shah"), ("Diya", "Patel"), ("Vivaan", "Kumar"), ("Anaya", "Singh"), ("Aditya", "Joshi"), ("Sara", "Khan"), ("Reyansh", "Gupta"), ("Ira", "Nair"), ("Yash", "Verma"), ("Myra", "Mehta")]
    students = []
    for index, (first, last) in enumerate(student_names):
        expected_prefix = f"{str(year)[-2:]}BTCS"
        existing = db.query(Student).options(noload("*")).join(User).filter(User.email.like(f"{first.lower()}.{expected_prefix.lower()}%@cms.edu")).first()
        if existing:
            students.append(existing); continue
        student_id = StudentService(db).generate_student_id(year, courses[0], branches[0])
        user = _user(db, f"{first.lower()}.{student_id.lower()}@cms.edu", student_id.lower(), f"{first} {last}", password_hash, "student")
        student = Student(user_id=user.id, department_id=departments[0].id, course_id=courses[0].id, branch_id=branches[0].id, curriculum_version_id=versions[0].id, section_id=sections[0].id, student_id=student_id, enrollment_number=f"ENR-{student_id}", admission_year=year, current_semester=1, semester=1, section="A", date_of_birth=date(year-18, (index % 12)+1, min(index+1, 28)), admission_date=date(year, 7, 15), guardian_name=f"Guardian of {first}", guardian_phone=f"987650{index:04d}", father_name=f"Mr. {last}", mother_name=f"Mrs. {last}", blood_group=["A+", "B+", "O+", "AB+"][index % 4], personal_email=f"{first.lower()}.{last.lower()}@example.com")
        db.add(student); db.flush(); students.append(student)
    logger.info("Demo seed: students ready")

    for index, student in enumerate(students[:10]):
        if not db.query(StudentElective).filter_by(student_id=student.id, curriculum_subject_id=mappings[0].id).first():
            db.add(StudentElective(student_id=student.id, curriculum_subject_id=mappings[0].id))
        if not db.query(Attendance).filter_by(student_id=student.id, subject_id=subjects[0].id, date=date.today()-timedelta(days=index)).first():
            db.add(Attendance(student_id=student.id, subject_id=subjects[0].id, teacher_id=teachers[0].id, section_id=sections[0].id, faculty_assignment_id=assignments[0].id, date=date.today()-timedelta(days=index), status=AttendanceStatus.PRESENT if index != 3 else AttendanceStatus.ABSENT))
        if not db.query(Marks).filter_by(student_id=student.id, subject_id=subjects[0].id, exam_type=ExamType.INTERNAL).first():
            db.add(Marks(student_id=student.id, subject_id=subjects[0].id, exam_type=ExamType.INTERNAL, marks_obtained=72+index, max_marks=100, semester=1, remarks="Satisfactory progress"))
        if not db.query(StudentFee).filter_by(student_id=student.id).first():
            db.add(StudentFee(student_id=student.id, title="Tuition Fee", amount=75000, due_date=date(year, 8, 31), status=FeeStatus.PAID if index < 6 else FeeStatus.PARTIAL))
    logger.info("Demo seed: student operations ready")

    # books = []
    # for index in range(10):
    #     isbn = f"978000000{index:04d}"
    #     book = db.query(LibraryBook).options(noload("*")).filter_by(isbn=isbn).first()
    #     if not book:
    #         book = LibraryBook(title=f"University Reference Volume {index+1}", author=f"Author {faculty_names[index]}", isbn=isbn, publisher="EduCore Press", edition="2nd", category=branch_data[index][0], total_copies=5, available_copies=4, shelf_location=f"A-{index+1:02d}")
    #         db.add(book); db.flush()
    #     books.append(book)
    #     if index < len(students) and not db.query(BookIssue).filter_by(book_id=book.id, student_id=students[index].id).first():
    #         db.add(BookIssue(book_id=book.id, student_id=students[index].id, issue_date=date.today()-timedelta(days=5), due_date=date.today()+timedelta(days=9), status=IssueStatus.ISSUED))

    for index in range(10):
        version = db.query(TimetableVersion).options(noload("*")).filter_by(course_id=courses[index].id, branch_scope_key=branches[index].id, semester=1, section_scope_key=sections[index].id).first()
        if not version:
            version = TimetableVersion(course_id=courses[index].id, department_id=departments[index].id, branch_id=branches[index].id, section_id=sections[index].id, branch_scope_key=branches[index].id, section_scope_key=sections[index].id, semester=1, status="approved", submitted_by_id=admin.id, approved_by_id=admin.id)
            db.add(version); db.flush()
        if not db.query(TimetableSlot).filter_by(version_id=version.id, day_of_week=1, slot_index=1).first():
            db.add(TimetableSlot(version_id=version.id, day_of_week=1, slot_index=1, subject_id=subjects[index].id, teacher_id=teachers[index].id))

    _user(db, "accountant.demo@cms.edu", "accountant.demo", "Neha Accounts", password_hash, "accountant")
    _user(db, "librarian.demo@cms.edu", "librarian.demo", "Rahul Librarian", password_hash, "librarian")
    db.commit()
    logger.info("Demo data seeded. Student IDs use %sBTCS001 through %sBTCS010.", str(year)[-2:], str(year)[-2:])


def clean_database_keep_admin(db: Session) -> None:
    """Permanently remove demo/business data while retaining one administrator."""
    seed_system_data(db)
    admin = db.query(User).join(UserRole).join(Role).filter(Role.name == "admin", User.is_deleted.is_(False)).order_by(User.id).first()
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


# Backwards-compatible import for older callers. It now means system data only.
seed_database = seed_system_data


def main() -> None:
    parser = argparse.ArgumentParser(description="EduCore database seeding")
    parser.add_argument("--clean", action="store_true", help="delete business data and keep the current admin")
    parser.add_argument("--system", action="store_true", help="reconcile system metadata only")
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.clean:
            clean_database_keep_admin(db)
        elif args.system:
            seed_system_data(db)
        else:
            seed_demo_data(db)


if __name__ == "__main__":
    main()
