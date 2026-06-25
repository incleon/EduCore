"""
API Routers — All CRUD endpoints for every module.

Each router:
- Uses APIRouter with prefix and tags
- Applies PermissionChecker dependencies for authorization
- Delegates to service layer (thin controller pattern)
- Returns consistent response format
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.core.permissions import PermissionChecker, RoleChecker
from app.core.portfolio import (
    get_faculty_portfolio, is_scoped_faculty, require_portfolio_assignment,
    require_portfolio_context, require_portfolio_student, require_portfolio_subject,
)
from app.services.crud_services import (
    UserService, StudentService, TeacherService, CourseService, DepartmentService,
    SubjectService, AttendanceService, MarksService,
    LibraryService, AuditService,
)
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.student import StudentCreate, StudentUpdate
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.schemas.course import CourseCreate, CourseUpdate
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectTeacherAssign
from app.schemas.attendance import AttendanceCreate, AttendanceBulkCreate, AttendanceUpdate
from app.schemas.marks import MarksCreate, MarksUpdate

from app.schemas.library import (
    BookCreate, BookUpdate, BookIssueCreate, BookIssueReturn,
    CategoryCreate, CategoryResponse, AuthorCreate, AuthorResponse,
    PublisherCreate, PublisherResponse, MemberCreate, MemberResponse,
    ReservationCreate, ReservationResponse, FineCreate, FineResponse
)
from app.utils.serializer import serialize_sqlalchemy_obj


def _serialize(value):
    """Return ORM results as bounded, secret-free JSON data."""
    return serialize_sqlalchemy_obj(value)


# ══════════════════════════════════════════════════════════════
# USERS ROUTER
# ══════════════════════════════════════════════════════════════

users_router = APIRouter(prefix="/api/users", tags=["Users"])


@users_router.get("")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_users"])),
):
    service = UserService(db)
    return service.list(page, page_size, search)


@users_router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_users"])),
):
    return _serialize(UserService(db).get(user_id))


@users_router.post("", status_code=201)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_users"])),
):
    return _serialize(UserService(db).create(data.model_dump()))


@users_router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_users"])),
):
    return _serialize(UserService(db).update(user_id, data.model_dump(exclude_unset=True)))


@users_router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_users"])),
):
    UserService(db).delete(user_id)
    return {"message": "User deleted successfully"}


# ══════════════════════════════════════════════════════════════
# STUDENTS ROUTER
# ══════════════════════════════════════════════════════════════

students_router = APIRouter(prefix="/api/students", tags=["Students"])


@students_router.get("")
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    department_id: Optional[int] = None, course_id: Optional[int] = None, branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["view_students"])),
):
    allowed_ids = None
    if is_scoped_faculty(current_user):
        allowed_ids = get_faculty_portfolio(db, current_user.teacher.id).student_ids
    return StudentService(db).list(
        page, page_size, search, department_id=department_id, course_id=course_id,
        branch_id=branch_id, allowed_student_ids=allowed_ids,
    )


@students_router.get("/{student_id}")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["view_students"])),
):
    require_portfolio_student(db, current_user, student_id)
    student = StudentService(db).get(student_id)
    return {
        "id": student.id,
        "user_id": student.user_id,
        "student_id": student.student_id,
        "enrollment_number": student.enrollment_number,
        "full_name": student.user.full_name if student.user else None,
        "email": student.user.email if student.user else None,
        "phone": student.user.phone if student.user else None,
        "gender": student.user.gender.value if student.user and student.user.gender else None,
        "personal_email": student.personal_email,
        "department_name": student.department.name if student.department else None,
        "department_id": student.department_id,
        "course_id": student.course_id,
        "course_name": student.course.name if student.course else None,
        "branch_id": student.branch_id,
        "branch_name": student.branch.name if student.branch else None,
        "admission_year": student.admission_year,
        "current_semester": student.current_semester,
        "curriculum_version_id": student.curriculum_version_id,
        "curriculum_version": student.curriculum_version.title if student.curriculum_version else None,
        "section_id": student.section_id,
        "semester": student.semester,
        "section": student.section,
        "date_of_birth": student.date_of_birth,
        "admission_date": student.admission_date,
        "guardian_name": student.guardian_name,
        "guardian_phone": student.guardian_phone,
        "father_name": student.father_name,
        "mother_name": student.mother_name,
        "blood_group": student.blood_group,
        "status": student.status.value if student.status else None,
        "profile_image": student.user.profile_image if student.user else None,
        "created_at": student.created_at,
        "profile_image": student.user.profile_image if student.user else None,
        "created_at": student.created_at,
    }


from fastapi import BackgroundTasks
from app.services.email_service import send_student_credentials, send_teacher_credentials

def _format_student(student):
    return {
        "id": student.id,
        "user_id": student.user_id,
        "student_id": student.student_id,
        "enrollment_number": student.enrollment_number,
        "full_name": student.user.full_name if student.user else None,
        "email": student.user.email if student.user else None,
        "phone": student.user.phone if student.user else None,
        "gender": student.user.gender.value if student.user and student.user.gender else None,
        "personal_email": student.personal_email,
        "department_name": student.department.name if student.department else None,
        "department_id": student.department_id,
        "course_id": student.course_id,
        "course_name": student.course.name if student.course else None,
        "branch_id": student.branch_id,
        "branch_name": student.branch.name if student.branch else None,
        "admission_year": student.admission_year,
        "current_semester": student.current_semester,
        "curriculum_version_id": student.curriculum_version_id,
        "curriculum_version": student.curriculum_version.title if student.curriculum_version else None,
        "section_id": student.section_id,
        "semester": student.semester,
        "section": student.section,
        "date_of_birth": student.date_of_birth,
        "admission_date": student.admission_date,
        "guardian_name": student.guardian_name,
        "guardian_phone": student.guardian_phone,
        "father_name": student.father_name,
        "mother_name": student.mother_name,
        "blood_group": student.blood_group,
        "status": student.status.value if student.status else None,
        "profile_image": student.user.profile_image if student.user else None,
        "created_at": student.created_at,
    }

@students_router.post("", status_code=201)
def create_student(
    data: StudentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_students"])),
):
    student, email_data = StudentService(db).create(data.model_dump())
    if email_data:
        background_tasks.add_task(
            send_student_credentials,
            email_data["student_name"],
            email_data["personal_email"],
            email_data["student_id"],
            email_data["institutional_email"],
            email_data["generated_password"]
        )
    return _format_student(student)


@students_router.put("/{student_id}")
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_students"])),
):
    student = StudentService(db).update(student_id, data.model_dump(exclude_unset=True))
    return _format_student(student)


@students_router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_students"])),
):
    StudentService(db).delete(student_id)
    return {"message": "Student deleted successfully"}

# ══════════════════════════════════════════════════════════════
# TEACHERS ROUTER
# ══════════════════════════════════════════════════════════════

teachers_router = APIRouter(prefix="/api/teachers", tags=["Teachers"])


@teachers_router.get("")
def list_teachers(
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None, department_id: Optional[int] = None,
    course_id: Optional[int] = None, branch_id: Optional[int] = None, db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["admin"])),
):
    return TeacherService(db).list(page, page_size, search, department_id=department_id, course_id=course_id, branch_id=branch_id)


def _format_teacher(teacher):
    return {
        "id": teacher.id, "user_id": teacher.user_id,
        "employee_id": teacher.employee_id, "faculty_id": teacher.faculty_id,
        "full_name": teacher.user.full_name if teacher.user else None,
        "email": teacher.user.email if teacher.user else None,
        "phone": teacher.user.phone if teacher.user else None,
        "gender": teacher.user.gender.value if teacher.user and teacher.user.gender else None,
        "department_name": teacher.department.name if teacher.department else None,
        "department_id": teacher.department_id,
        "branch_id": teacher.branch_id,
        "branch_name": teacher.branch.name if teacher.branch else None,
        "course_id": teacher.branch.course_id if teacher.branch else None,
        "course_name": teacher.branch.course.name if teacher.branch and teacher.branch.course else None,
        "designation": teacher.designation,
        "specialization": teacher.specialization,
        "qualification": teacher.qualification,
        "joining_date": teacher.joining_date,
        "experience_years": teacher.experience_years,
        "bio": teacher.bio,
        "profile_image": teacher.user.profile_image if teacher.user else None,
        "created_at": teacher.created_at,
    }


@teachers_router.get("/{teacher_id}")
def get_teacher(
    teacher_id: int, db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["admin"])),
):
    teacher = TeacherService(db).get(teacher_id)
    return _format_teacher(teacher)


@teachers_router.post("", status_code=201)
def create_teacher(
    data: TeacherCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["admin"])),
):
    teacher, email_data = TeacherService(db).create(data.model_dump())
    if email_data and email_data.get("personal_email"):
        background_tasks.add_task(
            send_teacher_credentials,
            email_data["teacher_name"],
            email_data["personal_email"],
            email_data["faculty_id"],
            email_data["institutional_email"],
            email_data["generated_password"]
        )
    return _format_teacher(teacher)


@teachers_router.put("/{teacher_id}")
def update_teacher(
    teacher_id: int, data: TeacherUpdate, db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["admin"])),
):
    teacher = TeacherService(db).update(teacher_id, data.model_dump(exclude_unset=True))
    return _format_teacher(teacher)


@teachers_router.delete("/all")
def delete_all_teachers(db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["admin"])),
):
    count = TeacherService(db).delete_all()
    return {"message": f"{count} teachers deleted successfully"}


@teachers_router.delete("/{teacher_id}")
def delete_teacher(
    teacher_id: int, db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["admin"])),
):
    TeacherService(db).delete(teacher_id)
    return {"message": "Teacher deleted successfully"}


@teachers_router.get("/by-department/{dept_id}")
def get_teachers_by_department(
    dept_id: int, db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["admin"])),
):
    """Get all teachers belonging to a specific department."""
    from app.repositories.concrete import TeacherRepository
    teachers = TeacherRepository(db).get_by_department(dept_id)
    return [
        {
            "id": t.id,
            "employee_id": t.employee_id,
            "faculty_id": t.faculty_id,
            "full_name": t.user.full_name if t.user else "Unknown",
            "designation": t.designation,
        }
        for t in teachers
    ]


# ══════════════════════════════════════════════════════════════
# COURSES ROUTER
# ══════════════════════════════════════════════════════════════

courses_router = APIRouter(prefix="/api/courses", tags=["Courses"])


@courses_router.get("")
def list_courses(
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None, department_id: Optional[int] = None, branch_id: Optional[int] = None, db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["view_departments"]))
):
    return CourseService(db).list(page, page_size, search, department_id=department_id, branch_id=branch_id)


@courses_router.get("/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db),
               current_user=Depends(PermissionChecker(["view_departments"]))):
    return _serialize(CourseService(db).get(course_id))


@courses_router.post("", status_code=201)
def create_course(data: CourseCreate, db: Session = Depends(get_db),
                  current_user=Depends(PermissionChecker(["manage_departments"]))):
    return _serialize(CourseService(db).create(data.model_dump()))


@courses_router.put("/{course_id}")
def update_course(course_id: int, data: CourseUpdate, db: Session = Depends(get_db),
                  current_user=Depends(PermissionChecker(["manage_departments"]))):
    return _serialize(CourseService(db).update(course_id, data.model_dump(exclude_unset=True)))


@courses_router.delete("/all")
def delete_all_courses(db: Session = Depends(get_db),
                  current_user=Depends(PermissionChecker(["manage_departments"]))):
    count = CourseService(db).delete_all()
    return {"message": f"{count} courses deleted successfully"}


@courses_router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db),
                  current_user=Depends(PermissionChecker(["manage_departments"]))):
    CourseService(db).delete(course_id)
    return {"message": "Course deleted successfully"}


# ══════════════════════════════════════════════════════════════
# DEPARTMENTS ROUTER
# ══════════════════════════════════════════════════════════════

departments_router = APIRouter(prefix="/api/departments", tags=["Departments"])


@departments_router.get("")
def list_departments(
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None, branch_id: Optional[int] = None, db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["view_departments"])),
):
    return DepartmentService(db).list(page, page_size, search, branch_id=branch_id)


@departments_router.get("/{dept_id}")
def get_department(dept_id: int, db: Session = Depends(get_db),
                   current_user=Depends(PermissionChecker(["view_departments"]))):
    return _serialize(DepartmentService(db).get(dept_id))


@departments_router.post("", status_code=201)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db),
                      current_user=Depends(PermissionChecker(["manage_departments"]))):
    return _serialize(DepartmentService(db).create(data.model_dump()))


@departments_router.put("/{dept_id}")
def update_department(dept_id: int, data: DepartmentUpdate, db: Session = Depends(get_db),
                      current_user=Depends(PermissionChecker(["manage_departments"]))):
    return _serialize(DepartmentService(db).update(dept_id, data.model_dump(exclude_unset=True)))


@departments_router.delete("/all")
def delete_all_departments(db: Session = Depends(get_db),
                      current_user=Depends(PermissionChecker(["manage_departments"]))):
    count = DepartmentService(db).delete_all()
    return {"message": f"{count} departments deleted successfully"}


@departments_router.delete("/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db),
                      current_user=Depends(PermissionChecker(["manage_departments"]))):
    DepartmentService(db).delete(dept_id)
    return {"message": "Department deleted successfully"}

from pydantic import BaseModel
class AssignHODRequest(BaseModel):
    teacher_id: int

@departments_router.put("/{dept_id}/hod")
def assign_hod(dept_id: int, data: AssignHODRequest, db: Session = Depends(get_db),
               current_user=Depends(PermissionChecker(["manage_departments"]))):
    DepartmentService(db).assign_hod(dept_id, data.teacher_id)
    return {"message": "HOD assigned successfully"}

# ══════════════════════════════════════════════════════════════
# SUBJECTS ROUTER
# ══════════════════════════════════════════════════════════════

subjects_router = APIRouter(prefix="/api/subjects", tags=["Subjects"])


@subjects_router.get("")
def list_subjects(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
                  search: Optional[str] = None, department_id: Optional[int] = None, branch_id: Optional[int] = None, db: Session = Depends(get_db),
                  current_user=Depends(PermissionChecker(["view_subjects"]))):
    allowed_ids = None
    if is_scoped_faculty(current_user):
        allowed_ids = get_faculty_portfolio(db, current_user.teacher.id).subject_ids
    return SubjectService(db).list(
        page, page_size, search, department_id=department_id,
        allowed_subject_ids=allowed_ids, branch_id=branch_id,
    )


@subjects_router.post("", status_code=201)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db),
                   current_user=Depends(PermissionChecker(["manage_subjects"]))):
    return _serialize(SubjectService(db).create(data.model_dump()))


@subjects_router.put("/{subject_id}")
def update_subject(subject_id: int, data: SubjectUpdate, db: Session = Depends(get_db),
                   current_user=Depends(PermissionChecker(["manage_subjects"]))):
    return _serialize(SubjectService(db).update(subject_id, data.model_dump(exclude_unset=True)))


@subjects_router.post("/assign-teacher", status_code=201)
def assign_teacher(data: SubjectTeacherAssign, db: Session = Depends(get_db),
                   current_user=Depends(PermissionChecker(["manage_subjects"]))):
    return _serialize(SubjectService(db).assign_teacher(data.subject_id, data.teacher_id, data.section))


@subjects_router.delete("/all")
def delete_all_subjects(db: Session = Depends(get_db),
                   current_user=Depends(PermissionChecker(["manage_subjects"]))):
    count = SubjectService(db).delete_all()
    return {"message": f"{count} subjects deleted successfully"}


@subjects_router.delete("/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db),
                   current_user=Depends(PermissionChecker(["manage_subjects"]))):
    SubjectService(db).delete(subject_id)
    return {"message": "Subject deleted successfully"}


@subjects_router.get("/{subject_id}/students")
def get_subject_students(subject_id: int, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    require_portfolio_subject(db, current_user, subject_id)
    students = StudentService(db).get_students_for_subject(subject_id)
    if is_scoped_faculty(current_user):
        allowed = get_faculty_portfolio(db, current_user.teacher.id).student_ids
        students = [student for student in students if student.id in allowed]
    return [
        {
            "id": s.id,
            "enrollment_number": s.enrollment_number,
            "full_name": s.user.full_name if s.user else None,
            "name": s.user.full_name if s.user else None,
        }
        for s in students
    ]


# ══════════════════════════════════════════════════════════════
# ATTENDANCE ROUTER
# ══════════════════════════════════════════════════════════════

attendance_router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


@attendance_router.get("")
def list_attendance(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
                    department_id: Optional[int] = None, course_id: Optional[int] = None, branch_id: Optional[int] = None,
                    student_id: Optional[int] = None, subject_id: Optional[int] = None,
                    db: Session = Depends(get_db),
                    current_user=Depends(PermissionChecker(["view_attendance"]))):
    if "student" in current_user.roles and current_user.student:
        student_id = current_user.student.id
    allowed_students = allowed_subjects = None
    if is_scoped_faculty(current_user):
        portfolio = get_faculty_portfolio(db, current_user.teacher.id)
        allowed_students, allowed_subjects = portfolio.student_ids, portfolio.subject_ids
    return AttendanceService(db).list(
        page, page_size, department_id=department_id, course_id=course_id,
        branch_id=branch_id, student_id=student_id, subject_id=subject_id,
        allowed_student_ids=allowed_students, allowed_subject_ids=allowed_subjects,
    )


@attendance_router.post("", status_code=201)
def create_attendance(data: AttendanceCreate, db: Session = Depends(get_db),
                      current_user=Depends(PermissionChecker(["mark_attendance"]))):
    require_portfolio_context(db, current_user, data.student_id, data.subject_id)
    if data.faculty_assignment_id:
        require_portfolio_assignment(db, current_user, data.faculty_assignment_id)
    att_data = data.model_dump()
    att_data["teacher_id"] = current_user.teacher.id if current_user.teacher else None
    return _serialize(AttendanceService(db).create(att_data))


@attendance_router.put("/{attendance_id}")
def update_attendance(attendance_id: int, data: AttendanceUpdate, db: Session = Depends(get_db),
                      current_user=Depends(PermissionChecker(["mark_attendance"]))):
    record = AttendanceService(db).get(attendance_id)
    require_portfolio_context(db, current_user, record.student_id, record.subject_id)
    if data.faculty_assignment_id:
        require_portfolio_assignment(db, current_user, data.faculty_assignment_id)
    return _serialize(AttendanceService(db).update(attendance_id, data.model_dump(exclude_unset=True)))


@attendance_router.delete("/{attendance_id}")
def delete_attendance(attendance_id: int, db: Session = Depends(get_db),
                      current_user=Depends(PermissionChecker(["mark_attendance"]))):
    record = AttendanceService(db).get(attendance_id)
    require_portfolio_context(db, current_user, record.student_id, record.subject_id)
    AttendanceService(db).delete(attendance_id)
    return {"message": "Attendance record deleted successfully"}


@attendance_router.post("/bulk", status_code=201)
def bulk_attendance(data: AttendanceBulkCreate, db: Session = Depends(get_db),
                    current_user=Depends(PermissionChecker(["mark_attendance"]))):
    require_portfolio_subject(db, current_user, data.subject_id)
    if data.faculty_assignment_id:
        require_portfolio_assignment(db, current_user, data.faculty_assignment_id)
    for record in data.records:
        require_portfolio_context(db, current_user, record["student_id"], data.subject_id)
    teacher_id = current_user.teacher.id if current_user.teacher else None
    return AttendanceService(db).bulk_create(
        data.subject_id, data.date, data.records, teacher_id,
        data.section_id, data.faculty_assignment_id,
    )


@attendance_router.get("/student/{student_id}/stats")
def student_attendance_stats(student_id: int, db: Session = Depends(get_db),
                             current_user=Depends(PermissionChecker(["view_attendance"]))):
    require_portfolio_student(db, current_user, student_id)
    return AttendanceService(db).get_student_stats(student_id)


# ══════════════════════════════════════════════════════════════
# MARKS ROUTER
# ══════════════════════════════════════════════════════════════

marks_router = APIRouter(prefix="/api/marks", tags=["Marks"])


@marks_router.get("")
def list_marks(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
               department_id: Optional[int] = None, course_id: Optional[int] = None, branch_id: Optional[int] = None,
               student_id: Optional[int] = None, subject_id: Optional[int] = None,
               db: Session = Depends(get_db),
               current_user=Depends(PermissionChecker(["view_marks"]))):
    if "student" in current_user.roles and current_user.student:
        student_id = current_user.student.id
    allowed_students = allowed_subjects = None
    if is_scoped_faculty(current_user):
        portfolio = get_faculty_portfolio(db, current_user.teacher.id)
        allowed_students, allowed_subjects = portfolio.student_ids, portfolio.subject_ids
    return MarksService(db).list(
        page, page_size, department_id=department_id, course_id=course_id,
        branch_id=branch_id, student_id=student_id, subject_id=subject_id,
        allowed_student_ids=allowed_students, allowed_subject_ids=allowed_subjects,
    )


@marks_router.post("", status_code=201)
def create_marks(data: MarksCreate, db: Session = Depends(get_db),
                 current_user=Depends(PermissionChecker(["upload_marks"]))):
    require_portfolio_context(db, current_user, data.student_id, data.subject_id)
    return _serialize(MarksService(db).create(data.model_dump()))


@marks_router.put("/{marks_id}")
def update_marks(marks_id: int, data: MarksUpdate, db: Session = Depends(get_db),
                 current_user=Depends(PermissionChecker(["upload_marks"]))):
    record = MarksService(db).get(marks_id)
    require_portfolio_context(db, current_user, record.student_id, record.subject_id)
    return _serialize(MarksService(db).update(marks_id, data.model_dump(exclude_unset=True)))


@marks_router.delete("/{marks_id}")
def delete_marks(marks_id: int, db: Session = Depends(get_db),
                 current_user=Depends(PermissionChecker(["upload_marks"]))):
    record = MarksService(db).get(marks_id)
    require_portfolio_context(db, current_user, record.student_id, record.subject_id)
    MarksService(db).delete(marks_id)
    return {"message": "Marks record deleted successfully"}


@marks_router.get("/student/{student_id}")
def student_marks(student_id: int, semester: Optional[int] = None,
                  db: Session = Depends(get_db),
                  current_user=Depends(PermissionChecker(["view_marks"]))):
    require_portfolio_student(db, current_user, student_id)
    records = MarksService(db).get_student_marks(student_id, semester)
    if is_scoped_faculty(current_user):
        allowed_subjects = get_faculty_portfolio(db, current_user.teacher.id).subject_ids
        records = [record for record in records if record.subject_id in allowed_subjects]
    return _serialize(records)




# ══════════════════════════════════════════════════════════════
# LIBRARY ROUTER
# ══════════════════════════════════════════════════════════════

library_router = APIRouter(prefix="/api/library", tags=["Library"])


@library_router.get("/books")
def list_books(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
               search: Optional[str] = None, db: Session = Depends(get_db),
               current_user=Depends(PermissionChecker(["view_library"]))):
    return LibraryService(db).list(page, page_size, search)


@library_router.post("/books", status_code=201)
def add_book(data: BookCreate, db: Session = Depends(get_db),
             current_user=Depends(PermissionChecker(["manage_library"]))):
    return _serialize(LibraryService(db).create(data.model_dump()))


@library_router.put("/books/{book_id}")
def update_book(book_id: int, data: BookUpdate, db: Session = Depends(get_db),
                current_user=Depends(PermissionChecker(["manage_library"]))):
    return _serialize(LibraryService(db).update(book_id, data.model_dump(exclude_unset=True)))


@library_router.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db),
                current_user=Depends(PermissionChecker(["manage_library"]))):
    LibraryService(db).delete(book_id)
    return {"message": "Book deleted successfully"}


@library_router.post("/issue", status_code=201)
def issue_book(data: BookIssueCreate, db: Session = Depends(get_db),
               current_user=Depends(PermissionChecker(["manage_library"]))):
    return _serialize(LibraryService(db).issue_book(data.book_id, data.member_id, data.due_date))


@library_router.post("/return/{issue_id}")
def return_book(issue_id: int, data: BookIssueReturn, db: Session = Depends(get_db),
                current_user=Depends(PermissionChecker(["manage_library"]))):
    return _serialize(LibraryService(db).return_book(issue_id, data.fine_amount))


@library_router.get("/issues")
def list_issues(member_id: Optional[int] = None, db: Session = Depends(get_db),
                current_user=Depends(PermissionChecker(["view_library"]))):
    if "librarian" not in current_user.roles:
        # Get member_id for the current user
        from app.repositories.concrete import LibraryMemberRepository
        member = LibraryMemberRepository(db).get_by_user_id(current_user.id)
        if member:
            member_id = member.id
        else:
            member_id = -1 # force empty
    return _serialize(LibraryService(db).get_active_issues(member_id))


# --- Additional Library Routes ---
@library_router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    return _serialize(LibraryService(db)._category_repo.get_all(0, 100))

@library_router.get("/authors")
def list_authors(db: Session = Depends(get_db)):
    return _serialize(LibraryService(db)._author_repo.get_all(0, 100))

@library_router.get("/publishers")
def list_publishers(db: Session = Depends(get_db)):
    return _serialize(LibraryService(db)._publisher_repo.get_all(0, 100))

@library_router.get("/members")
def list_members(db: Session = Depends(get_db)):
    return _serialize(LibraryService(db)._member_repo.get_all(0, 100))

@library_router.get("/reservations")
def list_reservations(db: Session = Depends(get_db)):
    return _serialize(LibraryService(db)._reservation_repo.get_all(0, 100))

@library_router.get("/fines")
def list_fines(db: Session = Depends(get_db)):
    return _serialize(LibraryService(db)._fine_repo.get_all(0, 100))

# ══════════════════════════════════════════════════════════════
# TIMETABLES ROUTER
# ══════════════════════════════════════════════════════════════

from pydantic import BaseModel, Field

class TimetableSlotSchema(BaseModel):
    day_of_week: int
    slot_index: int
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    is_free: Optional[bool] = False

class TimetableSaveRequest(BaseModel):
    department_id: int
    course_id: int
    branch_id: Optional[int] = None
    section_id: Optional[int] = None
    semester: int
    action: str = Field(..., description="'draft' or 'submit'")
    slots: List[TimetableSlotSchema]

timetables_router = APIRouter(prefix="/api/timetables", tags=["Timetables"])

@timetables_router.get("/teacher")
def get_teacher_timetable(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get the consolidated timetable for the currently logged in teacher."""
    from fastapi import HTTPException
    if not current_user.teacher:
        raise HTTPException(status_code=403, detail="Not a teacher")
        
    from app.services.crud_services import TimetableGridService
    service = TimetableGridService(db)
    slots = service.get_teacher_schedule(current_user.teacher.id)
    
    return {
        "slots": [{
            "id": item.id,
            "day_of_week": item.day_of_week,
            "slot_index": item.slot_index,
            "subject": ({"id": item.subject.id, "name": item.subject.name, "code": item.subject.code} if item.subject else None),
            "branch": ({"id": item.version.branch.id, "name": item.version.branch.name, "code": item.version.branch.code} if item.version.branch else None),
            "section": ({"id": item.version.section.id, "code": item.version.section.code} if item.version.section else None),
            "semester": item.version.semester
        } for item in slots]
    }

@timetables_router.get("")
def get_timetable(
    department_id: Optional[int] = None,
    course_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    section_id: Optional[int] = None,
    semester: Optional[int] = None,
    version_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Load the role-scoped timetable workspace previously assembled by the page router."""
    from app.services.crud_services import CourseService, DepartmentService, SubjectService, TeacherService, TimetableGridService
    from app.repositories.concrete import TimetableVersionRepository

    if "student" in current_user.roles and current_user.student:
        department_id = current_user.student.department_id
        course_id = current_user.student.course_id
        branch_id = current_user.student.branch_id
        section_id = current_user.student.section_id
        semester = current_user.student.current_semester
    elif "teacher" in current_user.roles and current_user.teacher:
        department_id = current_user.teacher.department_id
        branch_id = current_user.teacher.branch_id

    if "admin" in current_user.roles:
        courses = CourseService(db).list(page_size=100)["items"]
        departments = DepartmentService(db).list(page_size=100)["items"]
        course_options = [{"id": item["id"], "name": item["name"], "code": item["code"]} for item in courses]
        department_options = [{
            "id": item["id"], "name": item["name"], "code": item["code"],
            "course_id": item.get("course_id"),
        } for item in departments]
    else:
        department = (current_user.teacher.department if current_user.teacher else current_user.student.department if current_user.student else None)
        scoped_course = (
            current_user.teacher.branch.course
            if current_user.teacher and current_user.teacher.branch
            else current_user.student.course if current_user.student else None
        )
        courses = [scoped_course] if scoped_course else []
        departments = [department] if department else []
        course_options = [{"id": item.id, "name": item.name, "code": item.code} for item in courses]
        department_options = [{
            "id": item.id, "name": item.name, "code": item.code,
            "course_id": scoped_course.id if scoped_course else None,
        } for item in departments]

    service = TimetableGridService(db)
    
    if version_id:
        version = TimetableVersionRepository(db).get_by_id(version_id)
    else:
        version = service.get_version(
            department_id, course_id, semester, branch_id, section_id
        ) if department_id and course_id and semester else None
        
    slots = service.get_slots(version.id) if version else []
    
    versions_history = []
    if department_id and course_id and semester:
        all_versions = service.get_all_versions(department_id, course_id, semester, branch_id, section_id)
        versions_history = [{"id": v.id, "version_number": v.version_number, "status": v.status} for v in all_versions]
    
    can_manage = "hod" in current_user.roles or "admin" in current_user.roles
    subjects = SubjectService(db).get_filtered_subjects(department_id=department_id, semester=semester) if can_manage and department_id else []
    teachers = TeacherService(db).get_filtered_teachers(department_id=department_id) if can_manage and department_id else []
    
    from app.models.academic import Section
    sections_query = db.query(Section)
    if course_id:
        sections_query = sections_query.filter(Section.course_id == course_id)
    if semester:
        sections_query = sections_query.filter(Section.semester_number == semester)
    if branch_id:
        sections_query = sections_query.filter(Section.branch_id == branch_id)
    section_options = [{"id": s.id, "code": s.code, "course_id": s.course_id, "semester": s.semester_number, "branch_id": s.branch_id} for s in sections_query.all()]

    pending = service.get_pending_versions() if "manage_timetable" in current_user.permissions else []

    return {
        "is_student": "student" in current_user.roles,
        "is_teacher": "teacher" in current_user.roles,
        "current_department_id": department_id,
        "current_course_id": course_id,
        "current_branch_id": branch_id,
        "current_section_id": section_id,
        "current_semester": semester,
        "courses": course_options,
        "departments": department_options,
        "sections": section_options,
        "version": ({
            "id": version.id, "status": version.status, "semester": version.semester,
            "version_number": version.version_number,
            "course_id": version.course_id, "branch_id": version.branch_id,
            "section_id": version.section_id,
        } if version else None),
        "versions_history": versions_history,
        "slots": [{
            "id": item.id, "day_of_week": item.day_of_week, "slot_index": item.slot_index,
            "subject": ({"id": item.subject.id, "name": item.subject.name, "code": item.subject.code} if item.subject else None),
            "teacher": ({"id": item.teacher.id, "name": item.teacher.user.full_name if item.teacher.user else item.teacher.employee_id} if item.teacher else None),
        } for item in slots],
        "subjects": [{"id": item.id, "name": item.name, "code": item.code} for item in subjects],
        "teachers": [{"id": item.id, "name": item.user.full_name if item.user else item.employee_id} for item in teachers],
        "pending_versions": [{"id": item.id, "department_id": item.department_id, "semester": item.semester, "status": item.status} for item in pending],
    }

@timetables_router.post("/version", status_code=200)
def save_timetable(data: TimetableSaveRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user.has_permission("manage_timetable"):
        if not ("hod" in current_user.roles and current_user.teacher and current_user.teacher.department_id == data.department_id):
            from app.core.exceptions import UnauthorizedException
            raise UnauthorizedException(detail="Not authorized to edit timetables for this department")
            
    from app.services.crud_services import TimetableGridService
    service = TimetableGridService(db)
    version = service.save_timetable(data.model_dump(), current_user.id)
    return {"message": f"Timetable saved as {version.status}", "version_id": version.id}

class TimetableStatusRequest(BaseModel):
    status: str = Field(..., description="'approved' or 'rejected'")

@timetables_router.put("/version/{version_id}/status")
def update_timetable_status(version_id: int, data: TimetableStatusRequest, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_timetable"]))):
    from app.services.crud_services import TimetableGridService
    service = TimetableGridService(db)
    service.update_status(version_id, data.status, current_user.id)
    return {"message": f"Timetable marked as {data.status}"}
