from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.exceptions import ForbiddenException
from app.core.permissions import RoleChecker
from app.core.portfolio import get_faculty_portfolio, require_portfolio_context
from app.database.base import Base
from app.models.academic import (
    AcademicSemester, Branch, Curriculum, CurriculumSubject,
    CurriculumVersion, FacultyAssignment, Section, SubjectType,
)
from app.models.course import Course
from app.models.department import Department
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import Role, User, UserRole
from app.services.crud_services import StudentService, SubjectService


def portfolio_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _portfolio_graph():
    db = portfolio_session()
    department = Department(name="Engineering", code="ENG")
    course = Course(name="Bachelor of Technology", code="BT", department=department)
    branch = Branch(course=course, name="Computer Science", code="CS")
    curriculum = Curriculum(course=course, branch=branch, code="BT-CS", name="B.Tech CS")
    version = CurriculumVersion(
        curriculum=curriculum, version_code="2026", title="2026 Regulation",
        effective_year=2026, applicable_batch_start=2026, status="active", is_active=True,
    )
    semester = AcademicSemester(curriculum_version=version, number=1, name="Semester 1")
    section_a = Section(
        course=course, branch=branch, curriculum_version=version,
        semester_number=1, code="A", academic_year="2026-27",
    )
    section_b = Section(
        course=course, branch=branch, curriculum_version=version,
        semester_number=1, code="B", academic_year="2026-27",
    )
    subject_type = SubjectType(code="SPECIALIZATION", name="Specialization")
    subject_a = Subject(
        name="Algorithms", code="CS101", credits=4, semester=1,
        department=department, subject_type=subject_type,
    )
    subject_b = Subject(
        name="Databases", code="CS102", credits=4, semester=1,
        department=department, subject_type=subject_type,
    )
    mapping_a = CurriculumSubject(semester=semester, subject=subject_a, branch=branch)
    mapping_b = CurriculumSubject(semester=semester, subject=subject_b, branch=branch)

    teacher_role = Role(name="teacher", display_name="Teacher")
    admin_role = Role(name="admin", display_name="Administrator")
    teacher_a_user = User(
        email="teacher.a@example.edu", username="teacher.a", hashed_password="hash",
        full_name="Teacher A",
    )
    teacher_b_user = User(
        email="teacher.b@example.edu", username="teacher.b", hashed_password="hash",
        full_name="Teacher B",
    )
    admin_user = User(
        email="admin@example.edu", username="admin", hashed_password="hash",
        full_name="Admin",
    )
    teacher_a = Teacher(
        user=teacher_a_user, department=department, branch=branch,
        faculty_id="FC-A", employee_id="EMP-A",
    )
    teacher_b = Teacher(
        user=teacher_b_user, department=department, branch=branch,
        faculty_id="FC-B", employee_id="EMP-B",
    )
    student_a_user = User(
        email="student.a@example.edu", username="student.a", hashed_password="hash",
        full_name="Student A",
    )
    student_b_user = User(
        email="student.b@example.edu", username="student.b", hashed_password="hash",
        full_name="Student B",
    )
    student_a = Student(
        user=student_a_user, department=department, course=course, branch=branch,
        curriculum_version=version, academic_section=section_a, student_id="26BTCSA01",
        enrollment_number="ENR-A", admission_year=2026, semester=1, current_semester=1,
    )
    student_b = Student(
        user=student_b_user, department=department, course=course, branch=branch,
        curriculum_version=version, academic_section=section_b, student_id="26BTCSB01",
        enrollment_number="ENR-B", admission_year=2026, semester=1, current_semester=1,
    )
    db.add_all([
        department, course, branch, curriculum, version, semester, section_a, section_b,
        subject_type, subject_a, subject_b, mapping_a, mapping_b, teacher_role, admin_role,
        teacher_a, teacher_b, student_a, student_b, admin_user,
    ])
    db.flush()
    db.add_all([
        UserRole(user_id=teacher_a_user.id, role_id=teacher_role.id),
        UserRole(user_id=teacher_b_user.id, role_id=teacher_role.id),
        UserRole(user_id=admin_user.id, role_id=admin_role.id),
    ])
    assignment_a = FacultyAssignment(
        teacher=teacher_a, curriculum_subject=mapping_a, section=section_a,
        academic_year="2026-27", role="primary",
    )
    assignment_b = FacultyAssignment(
        teacher=teacher_b, curriculum_subject=mapping_b, section=section_b,
        academic_year="2026-27", role="primary",
    )
    db.add_all([assignment_a, assignment_b])
    db.commit()
    return db, teacher_a_user, teacher_b_user, admin_user, student_a, student_b, subject_a, subject_b, assignment_a


def test_faculty_portfolio_contains_only_assigned_students_subjects_and_allocations():
    db, teacher_a, _, _, student_a, student_b, subject_a, subject_b, assignment_a = _portfolio_graph()
    portfolio = get_faculty_portfolio(db, teacher_a.teacher.id)

    assert portfolio.student_ids == {student_a.id}
    assert student_b.id not in portfolio.student_ids
    assert portfolio.subject_ids == {subject_a.id}
    assert subject_b.id not in portfolio.subject_ids
    assert portfolio.assignment_ids == {assignment_a.id}


def test_cross_teacher_portfolio_context_is_forbidden():
    db, teacher_a, _, _, student_a, student_b, subject_a, subject_b, _ = _portfolio_graph()

    require_portfolio_context(db, teacher_a, student_a.id, subject_a.id)
    with pytest.raises(ForbiddenException):
        require_portfolio_context(db, teacher_a, student_b.id, subject_b.id)


def test_admin_only_role_checker_rejects_teacher_and_accepts_admin():
    db, teacher_a, _, admin, *_ = _portfolio_graph()
    checker = RoleChecker(["admin"])

    with pytest.raises(ForbiddenException):
        checker(current_user=teacher_a)
    assert checker(current_user=admin) is admin


def test_list_services_apply_portfolio_allow_lists():
    db, teacher_a, _, _, student_a, student_b, subject_a, subject_b, _ = _portfolio_graph()
    portfolio = get_faculty_portfolio(db, teacher_a.teacher.id)

    students = StudentService(db).list(page_size=100, allowed_student_ids=portfolio.student_ids)
    subjects = SubjectService(db).list(page_size=100, allowed_subject_ids=portfolio.subject_ids)

    assert {item["id"] for item in students["items"]} == {student_a.id}
    assert student_b.id not in {item["id"] for item in students["items"]}
    assert {item["id"] for item in subjects["items"]} == {subject_a.id}
    assert subject_b.id not in {item["id"] for item in subjects["items"]}
