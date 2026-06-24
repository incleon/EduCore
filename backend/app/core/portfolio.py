"""Server-side ownership rules for faculty portfolio data."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException
from app.models.academic import FacultyAssignment
from app.models.student import Student


@dataclass(frozen=True)
class FacultyPortfolio:
    assignment_ids: frozenset[int]
    subject_ids: frozenset[int]
    student_ids: frozenset[int]


def is_admin(user) -> bool:
    return "admin" in user.roles


def is_scoped_faculty(user) -> bool:
    return bool(user.teacher) and not is_admin(user)


def get_faculty_portfolio(db: Session, teacher_id: int) -> FacultyPortfolio:
    assignments = db.query(FacultyAssignment).filter(
        FacultyAssignment.teacher_id == teacher_id,
        FacultyAssignment.is_deleted.is_(False),
    ).all()
    assignment_ids = {item.id for item in assignments}
    subject_ids = {item.curriculum_subject.subject_id for item in assignments}
    student_ids: set[int] = set()

    for item in assignments:
        if item.section_id:
            student_ids.update(
                row[0] for row in db.query(Student.id).filter(
                    Student.section_id == item.section_id,
                    Student.is_deleted.is_(False),
                ).all()
            )
            continue

        mapping = item.curriculum_subject
        semester = mapping.semester
        curriculum = semester.curriculum_version.curriculum
        query = db.query(Student.id).filter(
            Student.course_id == curriculum.course_id,
            Student.current_semester == semester.number,
            Student.is_deleted.is_(False),
        )
        branch_id = mapping.branch_id or curriculum.branch_id
        if branch_id:
            query = query.filter(Student.branch_id == branch_id)
        student_ids.update(row[0] for row in query.all())

    return FacultyPortfolio(
        assignment_ids=frozenset(assignment_ids),
        subject_ids=frozenset(subject_ids),
        student_ids=frozenset(student_ids),
    )


def require_portfolio_student(db: Session, user, student_id: int) -> None:
    if is_scoped_faculty(user) and student_id not in get_faculty_portfolio(db, user.teacher.id).student_ids:
        raise ForbiddenException(detail="Student is outside your assigned teaching portfolio")


def require_portfolio_subject(db: Session, user, subject_id: int) -> None:
    if is_scoped_faculty(user) and subject_id not in get_faculty_portfolio(db, user.teacher.id).subject_ids:
        raise ForbiddenException(detail="Subject is outside your assigned teaching portfolio")


def require_portfolio_context(db: Session, user, student_id: int, subject_id: int) -> None:
    if not is_scoped_faculty(user):
        return
    portfolio = get_faculty_portfolio(db, user.teacher.id)
    if student_id not in portfolio.student_ids or subject_id not in portfolio.subject_ids:
        raise ForbiddenException(detail="Record is outside your assigned teaching portfolio")


def require_portfolio_assignment(db: Session, user, assignment_id: int) -> None:
    if is_scoped_faculty(user) and assignment_id not in get_faculty_portfolio(db, user.teacher.id).assignment_ids:
        raise ForbiddenException(detail="Teaching allocation is outside your assigned portfolio")
