from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

import app.models  # noqa: F401
from app.database.base import Base
from app.models.academic import (
    AcademicSemester, Branch, Curriculum, CurriculumSubject, CurriculumVersion,
    ElectiveGroup, Section, StudentElective, SubjectType,
)
from app.models.course import Course
from app.models.department import Department
from app.models.student import Student
from app.models.subject import Subject
from app.models.timetable_grid import TimetableVersion
from app.models.user import User
from app.repositories.concrete import TimetableVersionRepository
from app.services.academic_service import AcademicStructureService
from app.services.crud_services import StudentService


def academic_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_common_branch_and_elective_subject_resolution_without_duplicates():
    db = academic_session()
    department = Department(name="Engineering", code="ENG")
    course = Course(name="Bachelor of Technology", code="BTECH", department=department)
    cse = Branch(course=course, name="Computer Science", code="CSE")
    it = Branch(course=course, name="Information Technology", code="IT")
    types = {code: SubjectType(code=code, name=code.title()) for code in ("COMMON", "SPECIALIZATION", "ELECTIVE")}
    curriculum = Curriculum(course=course, code="BTECH-REG", name="B.Tech Regulations")
    version = CurriculumVersion(
        curriculum=curriculum, version_code="2025", title="2025 Regulation",
        effective_year=2025, applicable_batch_start=2025, is_active=True, status="active",
    )
    semester = AcademicSemester(curriculum_version=version, number=3, name="Semester 3")
    common = Subject(name="Discrete Mathematics", code="MATH-3", credits=4, semester=3, department=department, subject_type=types["COMMON"])
    dbms = Subject(name="Database Systems", code="CSE-DBMS", credits=4, semester=3, department=department, subject_type=types["SPECIALIZATION"])
    web = Subject(name="Web Technologies", code="IT-WEB", credits=4, semester=3, department=department, subject_type=types["SPECIALIZATION"])
    ai = Subject(name="Artificial Intelligence", code="CSE-AI", credits=3, semester=3, department=department, subject_type=types["ELECTIVE"])
    elective_group = ElectiveGroup(semester=semester, code="PE-1", name="Professional Elective", maximum_choices=1)
    common_map = CurriculumSubject(semester=semester, subject=common, branch=None, display_order=1)
    cse_map = CurriculumSubject(semester=semester, subject=dbms, branch=cse, display_order=2)
    CurriculumSubject(semester=semester, subject=web, branch=it, display_order=2)
    elective_map = CurriculumSubject(semester=semester, subject=ai, branch=cse, elective_group=elective_group, is_mandatory=False, display_order=3)
    user = User(email="student@example.edu", username="student", hashed_password="hash", full_name="Student")
    student = Student(
        user=user, department=department, course=course, branch=cse,
        curriculum_version=version, admission_year=2025, current_semester=3,
        semester=3, student_id="25-CSE-001", enrollment_number="ENR-25-CSE-001",
    )
    db.add_all([department, course, cse, it, *types.values(), curriculum, version, semester, common, dbms, web, ai, elective_group, common_map, cse_map, elective_map, student])
    db.commit()

    service = AcademicStructureService(db)
    before_selection = service.resolve_student_subjects(student.id)
    assert {item["code"] for item in before_selection} == {"MATH-3", "CSE-DBMS"}
    assert next(item for item in before_selection if item["code"] == "MATH-3")["source"] == "common"

    db.add(StudentElective(student_id=student.id, curriculum_subject_id=elective_map.id))
    db.commit()
    after_selection = service.resolve_student_subjects(student.id)
    assert {item["code"] for item in after_selection} == {"MATH-3", "CSE-DBMS", "CSE-AI"}
    assert "IT-WEB" not in {item["code"] for item in after_selection}


def test_curriculum_version_is_selected_by_admission_batch():
    db = academic_session()
    department = Department(name="Management", code="MGT")
    course = Course(name="MBA", code="MBA", department=department)
    curriculum = Curriculum(course=course, code="MBA-REG", name="MBA Regulations")
    version_2024 = CurriculumVersion(curriculum=curriculum, version_code="2024", title="2024 Regulation", effective_year=2024, applicable_batch_start=2024, applicable_batch_end=2024, is_active=True, status="active")
    version_2025 = CurriculumVersion(curriculum=curriculum, version_code="2025", title="2025 Regulation", effective_year=2025, applicable_batch_start=2025, is_active=True, status="active")
    db.add_all([department, course, curriculum, version_2024, version_2025])
    db.commit()

    service = AcademicStructureService(db)
    assert service.find_applicable_curriculum(course.id, None, 2024).id == version_2024.id
    assert service.find_applicable_curriculum(course.id, None, 2025).id == version_2025.id


def test_timetables_are_resolved_independently_for_each_section():
    db = academic_session()
    department = Department(name="Sciences", code="SCI")
    course = Course(name="Bachelor of Science", code="BSC", department=department)
    curriculum = Curriculum(course=course, code="BSC-REG", name="B.Sc Regulations")
    version = CurriculumVersion(
        curriculum=curriculum, version_code="2026", title="2026 Regulation",
        effective_year=2026, applicable_batch_start=2026, is_active=True, status="active",
    )
    section_a = Section(
        course=course, curriculum_version=version, code="BSC-1-A",
        semester_number=1, academic_year="2026-27",
    )
    section_b = Section(
        course=course, curriculum_version=version, code="BSC-1-B",
        semester_number=1, academic_year="2026-27",
    )
    db.add_all([department, course, curriculum, version, section_a, section_b])
    db.flush()
    timetable_a = TimetableVersion(
        department_id=department.id, course_id=course.id, semester=1,
        section_id=section_a.id, status="draft",
    )
    timetable_b = TimetableVersion(
        department_id=department.id, course_id=course.id, semester=1,
        section_id=section_b.id, status="approved",
    )
    db.add_all([timetable_a, timetable_b])
    db.commit()

    repository = TimetableVersionRepository(db)
    resolved_a = repository.get_by_academic_scope(
        department.id, course.id, 1, section_id=section_a.id
    )
    resolved_b = repository.get_by_academic_scope(
        department.id, course.id, 1, section_id=section_b.id
    )
    assert resolved_a.id == timetable_a.id
    assert resolved_b.id == timetable_b.id
    assert resolved_a.id != resolved_b.id


def test_database_rejects_duplicate_common_subject_allocations():
    db = academic_session()
    department = Department(name="Health Sciences", code="HLT")
    course = Course(name="Bachelor of Pharmacy", code="BPHARM", department=department)
    curriculum = Curriculum(course=course, code="BPHARM-REG", name="B.Pharm Regulations")
    version = CurriculumVersion(
        curriculum=curriculum, version_code="2026", title="2026 Regulation",
        effective_year=2026, applicable_batch_start=2026, is_active=True, status="active",
    )
    semester = AcademicSemester(curriculum_version=version, number=1, name="Semester 1")
    common_type = SubjectType(code="COMMON", name="Common")
    subject = Subject(
        name="Human Anatomy", code="PHA-101", credits=4, semester=1,
        department=department, subject_type=common_type,
    )
    db.add_all([department, course, curriculum, version, semester, common_type, subject])
    db.flush()
    db.add_all([
        CurriculumSubject(semester=semester, subject=subject),
        CurriculumSubject(semester=semester, subject=subject),
    ])
    with pytest.raises(IntegrityError):
        db.commit()


def test_student_sequence_uses_course_branch_format_and_survives_deletion():
    db = academic_session()
    department = Department(name="Engineering", code="ENG")
    course = Course(name="Bachelor of Technology", code="BT", department=department)
    branch = Branch(course=course, name="Computer Science", code="CS")
    db.add_all([department, course, branch])
    db.commit()

    service = StudentService(db)
    first_id = service.generate_student_id(2026, course, branch)
    assert first_id == "26BTCS001"
    user = User(email="first@cms.edu", username="26btcs001", hashed_password="hash", full_name="First Student")
    student = Student(user=user, department=department, course=course, branch=branch, admission_year=2026, current_semester=1, semester=1, student_id=first_id, enrollment_number=f"ENR-{first_id}")
    db.add(student)
    db.commit()
    service.delete(student.id)

    assert service.generate_student_id(2026, course, branch) == "26BTCS002"
