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
from app.core.permissions import PermissionChecker
from app.services.crud_services import (
    UserService, StudentService, TeacherService, CourseService, DepartmentService,
    SubjectService, AttendanceService, MarksService,
    FeeService, LibraryService, AuditService,
)
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.student import StudentCreate, StudentUpdate
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.schemas.course import CourseCreate, CourseUpdate
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectTeacherAssign
from app.schemas.attendance import AttendanceCreate, AttendanceBulkCreate
from app.schemas.marks import MarksCreate, MarksUpdate
from app.schemas.fee import FeeCreate, FeePayment
from app.schemas.library import BookCreate, BookUpdate, BookIssueCreate, BookIssueReturn


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
    return UserService(db).get(user_id)


@users_router.post("", status_code=201)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_users"])),
):
    return UserService(db).create(data.model_dump())


@users_router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_users"])),
):
    return UserService(db).update(user_id, data.model_dump(exclude_unset=True))


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
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["view_students"])),
):
    return StudentService(db).list(page, page_size, search)


@students_router.get("/{student_id}")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["view_students"])),
):
    student = StudentService(db).get(student_id)
    return {
        "id": student.id,
        "user_id": student.user_id,
        "enrollment_number": student.enrollment_number,
        "full_name": student.user.full_name if student.user else None,
        "email": student.user.email if student.user else None,
        "phone": student.user.phone if student.user else None,
        "department_name": student.department.name if student.department else None,
        "department_id": student.department_id,
        "semester": student.semester,
        "section": student.section,
        "status": student.status.value if student.status else None,
        "profile_image": student.user.profile_image if student.user else None,
    }


from fastapi import BackgroundTasks
from app.services.email_service import send_student_credentials

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
    return student


@students_router.put("/{student_id}")
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_students"])),
):
    return StudentService(db).update(student_id, data.model_dump(exclude_unset=True))


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
    search: Optional[str] = None, db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["view_teachers"])),
):
    return TeacherService(db).list(page, page_size, search)


@teachers_router.get("/{teacher_id}")
def get_teacher(
    teacher_id: int, db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["view_teachers"])),
):
    teacher = TeacherService(db).get(teacher_id)
    return {
        "id": teacher.id, "user_id": teacher.user_id,
        "employee_id": teacher.employee_id,
        "full_name": teacher.user.full_name if teacher.user else None,
        "email": teacher.user.email if teacher.user else None,
        "department_name": teacher.department.name if teacher.department else None,
        "department_id": teacher.department_id,
        "designation": teacher.designation,
        "specialization": teacher.specialization,
    }


@teachers_router.post("", status_code=201)
def create_teacher(
    data: TeacherCreate, db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_teachers"])),
):
    return TeacherService(db).create(data.model_dump())


@teachers_router.put("/{teacher_id}")
def update_teacher(
    teacher_id: int, data: TeacherUpdate, db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_teachers"])),
):
    return TeacherService(db).update(teacher_id, data.model_dump(exclude_unset=True))


@teachers_router.delete("/{teacher_id}")
def delete_teacher(
    teacher_id: int, db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_teachers"])),
):
    TeacherService(db).delete(teacher_id)
    return {"message": "Teacher deleted successfully"}


@teachers_router.get("/by-department/{dept_id}")
def get_teachers_by_department(
    dept_id: int, db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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
    search: Optional[str] = None, db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["view_departments"])),
):
    return CourseService(db).list(page, page_size, search)


@courses_router.get("/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db),
               current_user=Depends(PermissionChecker(["view_departments"]))):
    return CourseService(db).get(course_id)


@courses_router.post("", status_code=201)
def create_course(data: CourseCreate, db: Session = Depends(get_db),
                  current_user=Depends(PermissionChecker(["manage_departments"]))):
    return CourseService(db).create(data.model_dump())


@courses_router.put("/{course_id}")
def update_course(course_id: int, data: CourseUpdate, db: Session = Depends(get_db),
                  current_user=Depends(PermissionChecker(["manage_departments"]))):
    return CourseService(db).update(course_id, data.model_dump(exclude_unset=True))


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
    search: Optional[str] = None, db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["view_departments"])),
):
    return DepartmentService(db).list(page, page_size, search)


@departments_router.get("/{dept_id}")
def get_department(dept_id: int, db: Session = Depends(get_db),
                   current_user=Depends(PermissionChecker(["view_departments"]))):
    return DepartmentService(db).get(dept_id)


@departments_router.post("", status_code=201)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db),
                      current_user=Depends(PermissionChecker(["manage_departments"]))):
    return DepartmentService(db).create(data.model_dump())


@departments_router.put("/{dept_id}")
def update_department(dept_id: int, data: DepartmentUpdate, db: Session = Depends(get_db),
                      current_user=Depends(PermissionChecker(["manage_departments"]))):
    return DepartmentService(db).update(dept_id, data.model_dump(exclude_unset=True))


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
                  search: Optional[str] = None, db: Session = Depends(get_db),
                  current_user=Depends(PermissionChecker(["view_subjects"]))):
    return SubjectService(db).list(page, page_size, search)


@subjects_router.post("", status_code=201)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db),
                   current_user=Depends(PermissionChecker(["manage_subjects"]))):
    return SubjectService(db).create(data.model_dump())


@subjects_router.post("/assign-teacher", status_code=201)
def assign_teacher(data: SubjectTeacherAssign, db: Session = Depends(get_db),
                   current_user=Depends(PermissionChecker(["manage_subjects"]))):
    return SubjectService(db).assign_teacher(data.subject_id, data.teacher_id, data.section)


@subjects_router.delete("/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db),
                   current_user=Depends(PermissionChecker(["manage_subjects"]))):
    SubjectService(db).delete(subject_id)
    return {"message": "Subject deleted successfully"}


@subjects_router.get("/{subject_id}/students")
def get_subject_students(subject_id: int, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    students = StudentService(db).get_students_for_subject(subject_id)
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
                    db: Session = Depends(get_db),
                    current_user=Depends(PermissionChecker(["view_attendance"]))):
    return AttendanceService(db).list(page, page_size)


@attendance_router.post("", status_code=201)
def create_attendance(data: AttendanceCreate, db: Session = Depends(get_db),
                      current_user=Depends(PermissionChecker(["mark_attendance"]))):
    att_data = data.model_dump()
    att_data["teacher_id"] = current_user.teacher.id if current_user.teacher else None
    return AttendanceService(db).create(att_data)


@attendance_router.post("/bulk", status_code=201)
def bulk_attendance(data: AttendanceBulkCreate, db: Session = Depends(get_db),
                    current_user=Depends(PermissionChecker(["mark_attendance"]))):
    teacher_id = current_user.teacher.id if current_user.teacher else None
    return AttendanceService(db).bulk_create(data.subject_id, data.date, data.records, teacher_id)


@attendance_router.get("/student/{student_id}/stats")
def student_attendance_stats(student_id: int, db: Session = Depends(get_db),
                             current_user=Depends(PermissionChecker(["view_attendance"]))):
    return AttendanceService(db).get_student_stats(student_id)


# ══════════════════════════════════════════════════════════════
# MARKS ROUTER
# ══════════════════════════════════════════════════════════════

marks_router = APIRouter(prefix="/api/marks", tags=["Marks"])


@marks_router.get("")
def list_marks(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
               db: Session = Depends(get_db),
               current_user=Depends(PermissionChecker(["view_marks"]))):
    return MarksService(db).list(page, page_size)


@marks_router.post("", status_code=201)
def create_marks(data: MarksCreate, db: Session = Depends(get_db),
                 current_user=Depends(PermissionChecker(["upload_marks"]))):
    return MarksService(db).create(data.model_dump())


@marks_router.put("/{marks_id}")
def update_marks(marks_id: int, data: MarksUpdate, db: Session = Depends(get_db),
                 current_user=Depends(PermissionChecker(["upload_marks"]))):
    return MarksService(db).update(marks_id, data.model_dump(exclude_unset=True))


@marks_router.get("/student/{student_id}")
def student_marks(student_id: int, semester: Optional[int] = None,
                  db: Session = Depends(get_db),
                  current_user=Depends(PermissionChecker(["view_marks"]))):
    return MarksService(db).get_student_marks(student_id, semester)


# ══════════════════════════════════════════════════════════════
# FEES ROUTER
# ══════════════════════════════════════════════════════════════

fees_router = APIRouter(prefix="/api/fees", tags=["Fees"])


@fees_router.get("")
def list_fees(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
              db: Session = Depends(get_db),
              current_user=Depends(PermissionChecker(["view_fees"]))):
    return FeeService(db).list(page, page_size)


@fees_router.post("", status_code=201)
def create_fee(data: FeeCreate, db: Session = Depends(get_db),
               current_user=Depends(PermissionChecker(["manage_fees"]))):
    return FeeService(db).create(data.model_dump())


@fees_router.post("/{fee_id}/pay")
def pay_fee(fee_id: int, data: FeePayment, db: Session = Depends(get_db),
            current_user=Depends(get_current_user)):
    fee = FeeService(db).get(fee_id)
    
    if not current_user.has_permission("manage_fees"):
        if not current_user.student or fee.student_id != current_user.student.id:
            from app.core.exceptions import UnauthorizedException
            raise UnauthorizedException(detail="You do not have permission to pay this fee")
            
    return FeeService(db).record_payment(fee_id, data.paid_amount, data.payment_method)


@fees_router.get("/pending")
def pending_fees(db: Session = Depends(get_db),
                 current_user=Depends(PermissionChecker(["view_fees"]))):
    return FeeService(db).get_pending_fees()


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
    return LibraryService(db).create(data.model_dump())


@library_router.put("/books/{book_id}")
def update_book(book_id: int, data: BookUpdate, db: Session = Depends(get_db),
                current_user=Depends(PermissionChecker(["manage_library"]))):
    return LibraryService(db).update(book_id, data.model_dump(exclude_unset=True))


@library_router.post("/issue", status_code=201)
def issue_book(data: BookIssueCreate, db: Session = Depends(get_db),
               current_user=Depends(PermissionChecker(["manage_library"]))):
    return LibraryService(db).issue_book(data.book_id, data.student_id, data.due_date)


@library_router.post("/return/{issue_id}")
def return_book(issue_id: int, data: BookIssueReturn, db: Session = Depends(get_db),
                current_user=Depends(PermissionChecker(["manage_library"]))):
    return LibraryService(db).return_book(issue_id, data.fine_amount)


@library_router.get("/issues")
def list_issues(student_id: Optional[int] = None, db: Session = Depends(get_db),
                current_user=Depends(PermissionChecker(["view_library"]))):
    return LibraryService(db).get_active_issues(student_id)

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
    semester: int
    action: str = Field(..., description="'draft' or 'submit'")
    slots: List[TimetableSlotSchema]

timetables_router = APIRouter(prefix="/api/timetables", tags=["Timetables"])

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
