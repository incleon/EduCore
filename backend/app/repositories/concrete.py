"""
Concrete Repositories — Each extends BaseRepository with custom queries
=========================================================================

OOP Concept: INHERITANCE + METHOD OVERRIDING
Each repository inherits generic CRUD from BaseRepository and adds
model-specific query methods.
"""

from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.repositories.base import BaseRepository
from app.models.user import User, Role, Permission, UserRole, RolePermission
from app.models.course import Course
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.department import Department
from app.models.subject import Subject, SubjectTeacher
from app.models.attendance import Attendance
from app.models.marks import Marks

from app.models.library import (
    LibraryBook, BookIssue, LibraryMember, LibraryAuthor, LibraryPublisher,
    BookCategory, BookReservation, LibraryFine
)
from app.models.audit_log import AuditLog
from app.models.timetable_grid import TimetableVersion, TimetableSlot
from app.models.notification import Notification


# ══════════════════════════════════════════════════════════════
# USER REPOSITORY
# ══════════════════════════════════════════════════════════════

class UserRepository(BaseRepository[User]):
    """
    User repository — INHERITS BaseRepository and OVERRIDES/EXTENDS it.

    Demonstrates:
    - INHERITANCE: Gets create, get_by_id, get_all, update, delete for free
    - METHOD OVERRIDING: Adds user-specific query methods
    """

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Custom query — not in base repository."""
        return (
            self._db.query(User)
            .options(joinedload(User.user_roles).joinedload(UserRole.role))
            .filter(User.email == email, User.is_deleted == False)
            .first()
        )

    def get_by_username(self, username: str) -> Optional[User]:
        return (
            self._db.query(User)
            .filter(User.username == username, User.is_deleted == False)
            .first()
        )

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[User]:
        """OVERRIDE: Eager-load roles and permissions for users."""
        query = (
            self._db.query(User)
            .options(
                joinedload(User.user_roles)
                .joinedload(UserRole.role)
                .joinedload(Role.role_permissions)
                .joinedload(RolePermission.permission)
            )
            .filter(User.id == id)
        )
        if not include_deleted:
            query = query.filter(User.is_deleted == False)
        return query.first()

    def assign_role(self, user_id: int, role_id: int) -> UserRole:
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self._db.add(user_role)
        self._db.commit()
        return user_role

    def remove_role(self, user_id: int, role_id: int) -> bool:
        ur = (
            self._db.query(UserRole)
            .filter(UserRole.user_id == user_id, UserRole.role_id == role_id)
            .first()
        )
        if ur:
            self._db.delete(ur)
            self._db.commit()
            return True
        return False


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session):
        super().__init__(Role, db)

    def get_by_name(self, name: str) -> Optional[Role]:
        return self._db.query(Role).filter(Role.name == name).first()

    def assign_permission(self, role_id: int, permission_id: int) -> RolePermission:
        rp = RolePermission(role_id=role_id, permission_id=permission_id)
        self._db.add(rp)
        self._db.commit()
        return rp


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, db: Session):
        super().__init__(Permission, db)

    def get_by_name(self, name: str) -> Optional[Permission]:
        return self._db.query(Permission).filter(Permission.name == name).first()

    def get_by_resource(self, resource: str) -> List[Permission]:
        return self._db.query(Permission).filter(Permission.resource == resource).all()


# ══════════════════════════════════════════════════════════════
# STUDENT REPOSITORY
# ══════════════════════════════════════════════════════════════

class StudentRepository(BaseRepository[Student]):
    def __init__(self, db: Session):
        super().__init__(Student, db)

    def get_by_enrollment(self, enrollment: str) -> Optional[Student]:
        return (
            self._db.query(Student)
            .options(joinedload(Student.user), joinedload(Student.department))
            .filter(Student.enrollment_number == enrollment, Student.is_deleted == False)
            .first()
        )

    def get_by_user_id(self, user_id: int) -> Optional[Student]:
        return (
            self._db.query(Student)
            .options(joinedload(Student.user), joinedload(Student.department))
            .filter(Student.user_id == user_id, Student.is_deleted == False)
            .first()
        )

    def get_by_department(self, department_id: int) -> List[Student]:
        return (
            self._db.query(Student)
            .options(joinedload(Student.user))
            .filter(Student.department_id == department_id, Student.is_deleted == False)
            .all()
        )

    def get_by_department_and_semester(self, department_id: int, semester: int) -> List[Student]:
        return (
            self._db.query(Student)
            .options(joinedload(Student.user))
            .filter(Student.department_id == department_id, Student.semester == semester, Student.is_deleted == False)
            .all()
        )

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[Student]:
        """OVERRIDE: Eager load user and department."""
        query = (
            self._db.query(Student)
            .options(joinedload(Student.user), joinedload(Student.department))
            .filter(Student.id == id)
        )
        if not include_deleted:
            query = query.filter(Student.is_deleted == False)
        return query.first()

    def get_filtered_students(self, course_id: int = None, department_id: int = None, search: str = None) -> List[Student]:
        from app.models.department import Department
        from app.models.user import User
        from sqlalchemy import or_
        
        query = (
            self._db.query(Student)
            .join(Department, Student.department_id == Department.id)
            .join(User, Student.user_id == User.id)
            .options(joinedload(Student.user), joinedload(Student.department))
            .filter(Student.is_deleted == False)
        )
        
        if course_id:
            query = query.filter(Student.course_id == course_id)
        if department_id:
            query = query.filter(Student.department_id == department_id)
        if search:
            query = query.filter(
                or_(
                    User.full_name.ilike(f"%{search}%"),
                    Student.enrollment_number.ilike(f"%{search}%"),
                    Student.student_id.ilike(f"%{search}%")
                )
            )
            
        return query.order_by(Student.id.desc()).all()


# ══════════════════════════════════════════════════════════════
# TEACHER REPOSITORY
# ══════════════════════════════════════════════════════════════

class TeacherRepository(BaseRepository[Teacher]):
    def __init__(self, db: Session):
        super().__init__(Teacher, db)

    def get_by_employee_id(self, emp_id: str) -> Optional[Teacher]:
        return (
            self._db.query(Teacher)
            .options(joinedload(Teacher.user), joinedload(Teacher.department))
            .filter(Teacher.employee_id == emp_id, Teacher.is_deleted == False)
            .first()
        )

    def get_by_user_id(self, user_id: int) -> Optional[Teacher]:
        return (
            self._db.query(Teacher)
            .options(joinedload(Teacher.user), joinedload(Teacher.department))
            .filter(Teacher.user_id == user_id, Teacher.is_deleted == False)
            .first()
        )

    def get_by_department(self, department_id: int) -> List[Teacher]:
        return (
            self._db.query(Teacher)
            .options(joinedload(Teacher.user))
            .filter(Teacher.department_id == department_id, Teacher.is_deleted == False)
            .all()
        )

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[Teacher]:
        query = (
            self._db.query(Teacher)
            .options(joinedload(Teacher.user), joinedload(Teacher.department))
            .filter(Teacher.id == id)
        )
        if not include_deleted:
            query = query.filter(Teacher.is_deleted == False)
        return query.first()

    def get_filtered_teachers(self, course_id: int = None, department_id: int = None) -> List[Teacher]:
        from app.models.department import Department
        
        query = (
            self._db.query(Teacher)
            .outerjoin(Department, Teacher.department_id == Department.id)
            .options(joinedload(Teacher.user), joinedload(Teacher.department))
            .filter(Teacher.is_deleted == False)
        )
        
        if course_id:
            from app.models.course import Course
            course = self._db.query(Course).get(course_id)
            if course and course.department_id:
                query = query.filter(Teacher.department_id == course.department_id)
                
        if department_id:
            dept = self._db.query(Department).get(department_id)
            is_btech = False
            if dept and dept.programs:
                for prog in dept.programs:
                    if prog.name == "B.TECH":
                        is_btech = True
                        break
            
            if is_btech:
                as_dept = self._db.query(Department).filter(
                    Department.name.ilike("%Applied Sciences%")
                ).first()
                if as_dept:
                    query = query.filter(Teacher.department_id.in_([department_id, as_dept.id]))
                else:
                    query = query.filter(Teacher.department_id == department_id)
            else:
                query = query.filter(Teacher.department_id == department_id)
            
        return query.order_by(Teacher.id.desc()).all()


# ══════════════════════════════════════════════════════════════
# COURSE REPOSITORY
# ══════════════════════════════════════════════════════════════

class CourseRepository(BaseRepository[Course]):
    def __init__(self, db: Session):
        super().__init__(Course, db)

    def get_by_code(self, code: str) -> Optional[Course]:
        return (
            self._db.query(Course)
            .filter(Course.code == code, Course.is_deleted == False)
            .first()
        )


# ══════════════════════════════════════════════════════════════
# DEPARTMENT REPOSITORY
# ══════════════════════════════════════════════════════════════

class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db: Session):
        super().__init__(Department, db)

    def get_by_code(self, code: str) -> Optional[Department]:
        return (
            self._db.query(Department)
            .filter(Department.code == code, Department.is_deleted == False)
            .first()
        )


# ══════════════════════════════════════════════════════════════
# SUBJECT REPOSITORY
# ══════════════════════════════════════════════════════════════

class SubjectRepository(BaseRepository[Subject]):
    def __init__(self, db: Session):
        super().__init__(Subject, db)

    def get_by_code(self, code: str) -> Optional[Subject]:
        return (
            self._db.query(Subject)
            .options(joinedload(Subject.department), joinedload(Subject.teacher))
            .filter(Subject.code == code, Subject.is_deleted == False)
            .first()
        )

    def get_by_department(self, department_id: int, semester: int = None) -> List[Subject]:
        from app.models.department import Department
        
        dept = self._db.query(Department).get(department_id)
        dept_ids = [department_id]
        if dept and getattr(dept, "course", None) and dept.course.name == "B.TECH":
            if not semester or semester in [1, 2]:
                as_dept = self._db.query(Department).filter(
                    Department.course_id == dept.course_id,
                    Department.name.ilike("%Applied Sciences%")
                ).first()
                if as_dept:
                    dept_ids.append(as_dept.id)

        query = (
            self._db.query(Subject)
            .options(joinedload(Subject.department), joinedload(Subject.teacher))
            .filter(Subject.department_id.in_(dept_ids), Subject.is_deleted == False)
        )
        if semester:
            query = query.filter(Subject.semester == semester)
        return query.all()

    def assign_teacher(self, subject_id: int, teacher_id: int, section: str = None) -> SubjectTeacher:
        st = SubjectTeacher(subject_id=subject_id, teacher_id=teacher_id, section=section)
        self._db.add(st)
        self._db.commit()
        return st

    def get_teacher_subjects(self, teacher_id: int) -> List[Subject]:
        from sqlalchemy import or_
        from app.models.subject import SubjectTeacher
        
        return (
            self._db.query(Subject)
            .outerjoin(SubjectTeacher, Subject.id == SubjectTeacher.subject_id)
            .options(joinedload(Subject.department), joinedload(Subject.teacher))
            .filter(
                or_(
                    Subject.teacher_id == teacher_id,
                    SubjectTeacher.teacher_id == teacher_id
                ),
                Subject.is_deleted == False
            )
            .all()
        )


# ══════════════════════════════════════════════════════════════
# ATTENDANCE REPOSITORY
# ══════════════════════════════════════════════════════════════

class AttendanceRepository(BaseRepository[Attendance]):
    def __init__(self, db: Session):
        super().__init__(Attendance, db)

    def get_by_student_subject(
        self, student_id: int, subject_id: int
    ) -> List[Attendance]:
        return (
            self._db.query(Attendance)
            .filter(
                Attendance.student_id == student_id,
                Attendance.subject_id == subject_id,
                Attendance.is_deleted == False,
            )
            .order_by(Attendance.date.desc())
            .all()
        )

    def get_by_student_subject_date(self, student_id: int, subject_id: int, dt: date) -> Optional[Attendance]:
        return (
            self._db.query(Attendance)
            .filter(
                Attendance.student_id == student_id,
                Attendance.subject_id == subject_id,
                Attendance.date == dt,
                Attendance.is_deleted == False
            )
            .first()
        )

    def get_all_with_relations(self, limit: int = 200) -> List[Attendance]:
        """Admin view: get all attendance records with student and subject eager-loaded."""
        from app.models.student import Student
        from app.models.subject import Subject
        from app.models.department import Department
        return (
            self._db.query(Attendance)
            .options(
                joinedload(Attendance.subject).joinedload(Subject.department).joinedload(Department.course),
                joinedload(Attendance.student).joinedload(Student.user),
            )
            .filter(Attendance.is_deleted == False)
            .order_by(Attendance.date.desc())
            .limit(limit)
            .all()
        )

    def get_student_records(self, student_id: int) -> List[Attendance]:
        from app.models.teacher import Teacher
        return (
            self._db.query(Attendance)
            .options(joinedload(Attendance.subject), joinedload(Attendance.teacher).joinedload(Teacher.user))
            .filter(Attendance.student_id == student_id, Attendance.is_deleted == False)
            .order_by(Attendance.date.desc())
            .all()
        )

    def get_teacher_records(self, teacher_id: int, limit: int = 1000) -> List[Attendance]:
        from app.models.subject import Subject, SubjectTeacher
        from sqlalchemy import or_
        from app.models.student import Student
        from app.models.department import Department
        return (
            self._db.query(Attendance)
            .options(
                joinedload(Attendance.subject).joinedload(Subject.department).joinedload(Department.course), 
                joinedload(Attendance.student).joinedload(Student.user)
            )
            .join(Subject, Attendance.subject_id == Subject.id)
            .outerjoin(SubjectTeacher, Subject.id == SubjectTeacher.subject_id)
            .filter(
                or_(
                    Subject.teacher_id == teacher_id,
                    SubjectTeacher.teacher_id == teacher_id,
                    Attendance.teacher_id == teacher_id
                ),
                Attendance.is_deleted == False
            )
            .order_by(Attendance.date.desc())
            .limit(limit)
            .all()
        )

    def get_student_attendance_stats(self, student_id: int):
        """Get attendance percentage for a student."""
        total = (
            self._db.query(func.count(Attendance.id))
            .filter(Attendance.student_id == student_id, Attendance.is_deleted == False)
            .scalar()
        )
        present = (
            self._db.query(func.count(Attendance.id))
            .filter(
                Attendance.student_id == student_id,
                Attendance.status == "present",
                Attendance.is_deleted == False,
            )
            .scalar()
        )
        percentage = (present / total * 100) if total > 0 else 0
        return {"total": total, "present": present, "percentage": round(percentage, 2)}


# ══════════════════════════════════════════════════════════════
# MARKS REPOSITORY
# ══════════════════════════════════════════════════════════════

class MarksRepository(BaseRepository[Marks]):
    def __init__(self, db: Session):
        super().__init__(Marks, db)

    def get_student_marks(self, student_id: int, semester: int = None) -> List[Marks]:
        query = (
            self._db.query(Marks)
            .options(joinedload(Marks.subject))
            .filter(Marks.student_id == student_id, Marks.is_deleted == False)
        )
        if semester:
            query = query.filter(Marks.semester == semester)
        return query.all()

    def get_by_subject(self, subject_id: int, exam_type: str = None) -> List[Marks]:
        query = (
            self._db.query(Marks)
            .options(joinedload(Marks.student).joinedload(Student.user))
            .filter(Marks.subject_id == subject_id, Marks.is_deleted == False)
        )
        if exam_type:
            query = query.filter(Marks.exam_type == exam_type)
        return query.all()

    def get_all_with_relations(self, limit: int = 1000) -> List[Marks]:
        """Admin view: get marks with deep relationships eager-loaded."""
        from app.models.student import Student
        from app.models.subject import Subject
        from app.models.department import Department
        return (
            self._db.query(Marks)
            .options(
                joinedload(Marks.subject).joinedload(Subject.department).joinedload(Department.course),
                joinedload(Marks.student).joinedload(Student.user),
            )
            .filter(Marks.is_deleted == False)
            .order_by(Marks.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_filtered_marks(self, course_id: int = None, department_id: int = None, semester: int = None, search: str = None) -> List[Marks]:
        from app.models.student import Student
        from app.models.subject import Subject
        from app.models.department import Department
        from app.models.user import User
        from sqlalchemy import or_
        
        query = (
            self._db.query(Marks)
            .join(Student, Marks.student_id == Student.id)
            .join(User, Student.user_id == User.id)
            .join(Subject, Marks.subject_id == Subject.id)
            .join(Department, Subject.department_id == Department.id)
            .options(
                joinedload(Marks.subject).joinedload(Subject.department).joinedload(Department.course),
                joinedload(Marks.student).joinedload(Student.user),
            )
            .filter(Marks.is_deleted == False)
        )
        
        if course_id:
            query = query.filter(Department.course_id == course_id)
        if department_id:
            # We filter by subject's department to get marks for subjects belonging to that dept
            query = query.filter(Subject.department_id == department_id)
        if semester:
            query = query.filter(Marks.semester == semester)
        if search:
            query = query.filter(
                or_(
                    User.full_name.ilike(f"%{search}%"),
                    Student.enrollment_number.ilike(f"%{search}%")
                )
            )
            
        return query.order_by(Marks.created_at.desc()).all()

    def get_teacher_records_with_relations(self, teacher_id: int, limit: int = 1000) -> List[Marks]:
        """Teacher view: get marks for subjects assigned to them."""
        from app.models.student import Student
        from app.models.subject import Subject, SubjectTeacher
        from app.models.department import Department
        from sqlalchemy import or_
        return (
            self._db.query(Marks)
            .options(
                joinedload(Marks.subject).joinedload(Subject.department).joinedload(Department.course),
                joinedload(Marks.student).joinedload(Student.user),
            )
            .join(Subject, Marks.subject_id == Subject.id)
            .outerjoin(SubjectTeacher, Subject.id == SubjectTeacher.subject_id)
            .filter(
                or_(
                    Subject.teacher_id == teacher_id,
                    SubjectTeacher.teacher_id == teacher_id
                ),
                Marks.is_deleted == False
            )
            .order_by(Marks.created_at.desc())
            .limit(limit)
            .all()
        )





# ══════════════════════════════════════════════════════════════
# LIBRARY REPOSITORIES
# ══════════════════════════════════════════════════════════════

class LibraryBookRepository(BaseRepository[LibraryBook]):
    def __init__(self, db: Session):
        super().__init__(LibraryBook, db)

    def get_by_isbn(self, isbn: str) -> Optional[LibraryBook]:
        return (
            self._db.query(LibraryBook)
            .filter(LibraryBook.isbn == isbn, LibraryBook.is_deleted == False)
            .first()
        )

    def get_available_books(self) -> List[LibraryBook]:
        return (
            self._db.query(LibraryBook)
            .filter(LibraryBook.available_copies > 0, LibraryBook.is_deleted == False)
            .all()
        )


class BookIssueRepository(BaseRepository[BookIssue]):
    def __init__(self, db: Session):
        super().__init__(BookIssue, db)

    def get_active_issues(self, member_id: int = None) -> List[BookIssue]:
        query = (
            self._db.query(BookIssue)
            .options(
                joinedload(BookIssue.book),
                joinedload(BookIssue.member).joinedload(LibraryMember.user),
            )
            .filter(BookIssue.status == "issued", BookIssue.is_deleted == False)
        )
        if member_id:
            query = query.filter(BookIssue.member_id == member_id)
        return query.all()

    def get_overdue_count(self) -> int:
        from datetime import date
        return (
            self._db.query(BookIssue)
            .filter(
                BookIssue.status == "issued",
                BookIssue.due_date < date.today(),
                BookIssue.is_deleted == False,
            )
            .count()
        )


# ══════════════════════════════════════════════════════════════
# AUDIT LOG REPOSITORY
# ══════════════════════════════════════════════════════════════

class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def get_by_user(self, user_id: int, limit: int = 50) -> List[AuditLog]:
        return (
            self._db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_resource(self, resource: str, resource_id: int = None) -> List[AuditLog]:
        query = self._db.query(AuditLog).filter(AuditLog.resource == resource)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        return query.order_by(AuditLog.created_at.desc()).all()


# ══════════════════════════════════════════════════════════════
# TIMETABLE REPOSITORY
# ══════════════════════════════════════════════════════════════

class TimetableVersionRepository(BaseRepository[TimetableVersion]):
    def __init__(self, db: Session):
        super().__init__(TimetableVersion, db)

    def get_by_academic_scope(
        self,
        department_id: int,
        course_id: int,
        semester: int,
        branch_id: int | None = None,
        section_id: int | None = None,
    ) -> Optional[TimetableVersion]:
        return self._db.query(TimetableVersion).filter(
            TimetableVersion.department_id == department_id,
            TimetableVersion.course_id == course_id,
            TimetableVersion.branch_id == branch_id,
            TimetableVersion.section_id == section_id,
            TimetableVersion.semester == semester,
            TimetableVersion.is_deleted == False
        ).order_by(TimetableVersion.version_number.desc()).first()

    def get_all_versions_by_scope(
        self,
        department_id: int,
        course_id: int,
        semester: int,
        branch_id: int | None = None,
        section_id: int | None = None,
    ) -> List[TimetableVersion]:
        return self._db.query(TimetableVersion).filter(
            TimetableVersion.department_id == department_id,
            TimetableVersion.course_id == course_id,
            TimetableVersion.branch_id == branch_id,
            TimetableVersion.section_id == section_id,
            TimetableVersion.semester == semester,
            TimetableVersion.is_deleted == False
        ).order_by(TimetableVersion.version_number.desc()).all()

    def get_pending(self) -> List[TimetableVersion]:
        return self._db.query(TimetableVersion).filter(
            TimetableVersion.status == "pending",
            TimetableVersion.is_deleted == False
        ).order_by(TimetableVersion.updated_at.desc()).all()
        
    def get_approved(self) -> List[TimetableVersion]:
        return self._db.query(TimetableVersion).filter(
            TimetableVersion.status == "approved",
            TimetableVersion.is_deleted == False
        ).order_by(TimetableVersion.updated_at.desc()).all()


class TimetableSlotRepository(BaseRepository[TimetableSlot]):
    def __init__(self, db: Session):
        super().__init__(TimetableSlot, db)

    def get_by_version(self, version_id: int) -> List[TimetableSlot]:
        return self._db.query(TimetableSlot).options(
            joinedload(TimetableSlot.subject),
            joinedload(TimetableSlot.teacher)
        ).filter(
            TimetableSlot.version_id == version_id,
            TimetableSlot.is_deleted == False
        ).all()


# ══════════════════════════════════════════════════════════════
# NOTIFICATION REPOSITORY
# ══════════════════════════════════════════════════════════════

class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: Session):
        super().__init__(Notification, db)

    def get_user_notifications(self, user_id: int, unread_only: bool = False, limit: int = 50) -> List[Notification]:
        query = self._db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    def mark_all_read(self, user_id: int) -> int:
        notifications = self._db.query(Notification).filter(
            Notification.user_id == user_id, 
            Notification.is_read == False
        ).all()
        for n in notifications:
            n.is_read = True
        self._db.commit()
        return len(notifications)


class LibraryMemberRepository(BaseRepository[LibraryMember]):
    def __init__(self, db: Session):
        super().__init__(LibraryMember, db)

    def get_by_user_id(self, user_id: int) -> Optional[LibraryMember]:
        return self._db.query(LibraryMember).filter(LibraryMember.user_id == user_id, LibraryMember.is_deleted == False).first()


class LibraryAuthorRepository(BaseRepository[LibraryAuthor]):
    def __init__(self, db: Session):
        super().__init__(LibraryAuthor, db)


class LibraryPublisherRepository(BaseRepository[LibraryPublisher]):
    def __init__(self, db: Session):
        super().__init__(LibraryPublisher, db)


class BookCategoryRepository(BaseRepository[BookCategory]):
    def __init__(self, db: Session):
        super().__init__(BookCategory, db)


class BookReservationRepository(BaseRepository[BookReservation]):
    def __init__(self, db: Session):
        super().__init__(BookReservation, db)

    def get_active_by_member(self, member_id: int) -> List[BookReservation]:
        return self._db.query(BookReservation).filter(
            BookReservation.member_id == member_id,
            BookReservation.status == "PENDING",
            BookReservation.is_deleted == False
        ).all()


class LibraryFineRepository(BaseRepository[LibraryFine]):
    def __init__(self, db: Session):
        super().__init__(LibraryFine, db)

    def get_unpaid_by_member(self, member_id: int) -> List[LibraryFine]:
        return self._db.query(LibraryFine).filter(
            LibraryFine.member_id == member_id,
            LibraryFine.is_paid == False,
            LibraryFine.is_deleted == False
        ).all()
