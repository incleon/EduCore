"""
Page Routes — HTML Template Rendering (Jinja2)
=================================================

These routes render HTML pages for the browser-based frontend.
They use FastAPI's Jinja2Templates to serve Bootstrap 5 pages.
"""

from datetime import date
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db, get_current_user, get_optional_user
from app.core.security import CaptchaHandler
from app.services.dashboard_service import DashboardFactory
from app.services.crud_services import (
    StudentService, TeacherService, CourseService, DepartmentService,
    SubjectService, FeeService, LibraryService,
)
from app.repositories.concrete import AttendanceRepository, MarksRepository, SubjectRepository
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="app/templates")


# ── Helper to build template context ────────────────────────
def _context(request: Request, user=None, **kwargs):
    """Build standard template context."""
    ctx = {"request": request, "user": user}
    if user:
        ctx["roles"] = user.roles
        ctx["permissions"] = user.permissions
        
        role_hierarchy = ["admin", "hod", "accountant", "librarian", "teacher", "student"]
        primary_role = "user"
        if user.roles:
            for role in role_hierarchy:
                if role in user.roles:
                    primary_role = role
                    break
        ctx["primary_role"] = primary_role
        
    ctx.update(kwargs)
    return ctx


# ══════════════════════════════════════════════════════════════
# PUBLIC PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/", response_class=HTMLResponse)
def home(request: Request, user=Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user=Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)

    captcha_question, captcha_token = CaptchaHandler.create_challenge()
    # If reload requested, return full HTML so client can parse new token
    return templates.TemplateResponse(
        "auth/login.html",
        _context(
            request,
            captcha_question=captcha_question,
            captcha_token=captcha_token,
        ),
    )


# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db),
              user=Depends(get_current_user)):
    # Get primary role for dashboard selection based on a hierarchy
    role_hierarchy = ["admin", "hod", "accountant", "librarian", "teacher", "student"]
    primary_role = "student"
    if user.roles:
        for role in role_hierarchy:
            if role in user.roles:
                primary_role = role
                break

    # Use Factory Pattern to get role-specific dashboard data
    dashboard_obj = DashboardFactory.create(primary_role, db, user)
    stats = dashboard_obj.get_stats()

    template_name = f"dashboard/{primary_role}.html"
    try:
        return templates.TemplateResponse(
            template_name,
            _context(request, user, stats=stats, dashboard=stats),
        )
    except Exception:
        return templates.TemplateResponse(
            "dashboard/admin.html",
            _context(request, user, stats=stats, dashboard=stats),
        )


# ══════════════════════════════════════════════════════════════
# STUDENT PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/students", response_class=HTMLResponse)
def students_list(request: Request, course_id: Optional[str] = None, department_id: Optional[str] = None, 
                  db: Session = Depends(get_db), user=Depends(get_current_user), page: int = 1, search: str = ""):
    if "hod" in user.roles and "admin" not in user.roles and user.teacher:
        departments = [user.teacher.department] if user.teacher.department else []
        courses = [user.teacher.department.course] if user.teacher.department and user.teacher.department.course else []
        department_id = user.teacher.department_id
        course_id = user.teacher.department.course_id if user.teacher.department else None
    else:
        departments = DepartmentService(db).list(1, 100)["items"]
        courses = CourseService(db).list(1, 100)["items"]
        course_id = int(course_id) if course_id and str(course_id).isdigit() else None
        department_id = int(department_id) if department_id and str(department_id).isdigit() else None
    
    if course_id or department_id or search:
        students = StudentService(db).get_filtered_students(course_id, department_id, search)
        result = {"items": students, "total": len(students), "page": 1, "page_size": len(students)}
        result["is_filtered"] = True
    else:
        result = {"items": [], "total": 0, "page": 1, "page_size": 0, "is_filtered": False}
        
    return templates.TemplateResponse(
        "students/list.html",
        _context(request, user, **result, search=search, departments=departments, courses=courses,
                 current_course_id=course_id, current_department_id=department_id),
    )


@router.get("/students/create", response_class=HTMLResponse)
def student_create_page(request: Request, db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    departments = DepartmentService(db).list(1, 100)["items"]
    courses = CourseService(db).list(1, 100)["items"]
    return templates.TemplateResponse(
        "students/create.html",
        _context(request, user, departments=departments, courses=courses),
    )


@router.get("/students/{student_id}", response_class=HTMLResponse)
def student_detail(request: Request, student_id: int,
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    student = StudentService(db).get(student_id)
    return templates.TemplateResponse(
        "students/detail.html", _context(request, user, student=student),
    )


# ══════════════════════════════════════════════════════════════
# TEACHER PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/teachers", response_class=HTMLResponse)
def teachers_list(request: Request, course_id: Optional[str] = None, department_id: Optional[str] = None, 
                  db: Session = Depends(get_db), user=Depends(get_current_user), page: int = 1, search: str = ""):
    if "hod" in user.roles and "admin" not in user.roles and user.teacher:
        departments = [user.teacher.department] if user.teacher.department else []
        courses = [user.teacher.department.course] if user.teacher.department and user.teacher.department.course else []
        department_id = user.teacher.department_id
        course_id = user.teacher.department.course_id if user.teacher.department else None
    else:
        departments = DepartmentService(db).list(1, 100)["items"]
        courses = CourseService(db).list(1, 100)["items"]
        course_id = int(course_id) if course_id and str(course_id).isdigit() else None
        department_id = int(department_id) if department_id and str(department_id).isdigit() else None
    
    if course_id or department_id or search:
        if search:
            result = TeacherService(db).list(page, 500, search)
        else:
            teachers = TeacherService(db).get_filtered_teachers(course_id, department_id)
            result = {"items": teachers, "total": len(teachers), "page": 1, "page_size": len(teachers)}
        result["is_filtered"] = True
    else:
        result = {"items": [], "total": 0, "page": 1, "page_size": 0, "is_filtered": False}
        
    return templates.TemplateResponse(
        "teachers/list.html",
        _context(request, user, **result, search=search, departments=departments, courses=courses,
                 current_course_id=course_id, current_department_id=department_id),
    )


@router.get("/teachers/create", response_class=HTMLResponse)
def teacher_create_page(request: Request, db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    departments = DepartmentService(db).list(1, 100)["items"]
    return templates.TemplateResponse(
        "teachers/create.html",
        _context(request, user, departments=departments),
    )


@router.get("/teachers/{teacher_id}", response_class=HTMLResponse)
def teacher_detail(request: Request, teacher_id: int,
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    teacher = TeacherService(db).get(teacher_id)
    return templates.TemplateResponse(
        "teachers/detail.html", _context(request, user, teacher=teacher),
    )

# ══════════════════════════════════════════════════════════════
# HOD PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/hods", response_class=HTMLResponse)
def hods_list(request: Request, course_id: Optional[str] = None, db: Session = Depends(get_db),
              user=Depends(get_current_user)):
    course_id = int(course_id) if course_id and str(course_id).isdigit() else None
    
    courses = CourseService(db).list(1, 100)["items"]
    
    # Filter departments manually if a course is selected
    all_departments = DepartmentService(db).list(1, 100)["items"]
    if course_id:
        departments = [d for d in all_departments if d.course_id == course_id]
    else:
        departments = []
        
    return templates.TemplateResponse(
        "hods/list.html", _context(request, user, departments=departments, courses=courses, current_course_id=course_id),
    )


# ══════════════════════════════════════════════════════════════
# COURSE PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/courses", response_class=HTMLResponse)
def courses_list(request: Request, db: Session = Depends(get_db),
                 user=Depends(get_current_user), page: int = 1, search: str = ""):
    result = CourseService(db).list(page, 100, search or None)
    departments = DepartmentService(db).list(1, 100)["items"]
    return templates.TemplateResponse(
        "courses/list.html",
        _context(request, user, **result, search=search, departments=departments),
    )


@router.get("/courses/{course_id}", response_class=HTMLResponse)
def course_detail(request: Request, course_id: int, db: Session = Depends(get_db),
                  user=Depends(get_current_user)):
    course = CourseService(db).get(course_id)
    departments = course.departments.filter_by(is_deleted=False).all() if course else []
    return templates.TemplateResponse(
        "courses/detail.html", _context(request, user, course=course, departments=departments),
    )


# ══════════════════════════════════════════════════════════════
# DEPARTMENT PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/departments", response_class=HTMLResponse)
def departments_list(request: Request, db: Session = Depends(get_db),
                     user=Depends(get_current_user), page: int = 1):
    result = DepartmentService(db).list(page, 100)
    courses = CourseService(db).list(1, 100)["items"]
    return templates.TemplateResponse(
        "departments/list.html", _context(request, user, **result, courses=courses),
    )


@router.get("/departments/{dept_id}", response_class=HTMLResponse)
def department_detail(request: Request, dept_id: int, db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    department = DepartmentService(db).get(dept_id)
    courses = CourseService(db).list(1, 100)["items"]
    subjects = SubjectService(db).get_filtered_subjects(department_id=dept_id)
    return templates.TemplateResponse(
        "departments/detail.html", _context(request, user, department=department, courses=courses, subjects=subjects),
    )


@router.get("/departments/create", response_class=HTMLResponse)
def department_create_page(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    courses = CourseService(db).list(1, 100)["items"]
    return templates.TemplateResponse(
        "departments/create.html", _context(request, user, courses=courses),
    )

# ══════════════════════════════════════════════════════════════
# SUBJECT PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/subjects", response_class=HTMLResponse)
def subjects_list(request: Request, db: Session = Depends(get_db),
                 user=Depends(get_current_user), page: int = 1):
    if "hod" in user.roles and "admin" not in user.roles and user.teacher:
        departments = [user.teacher.department] if user.teacher.department else []
        courses = [user.teacher.department.course] if user.teacher.department and user.teacher.department.course else []
        dept_id = user.teacher.department_id
        subjects = SubjectService(db).get_filtered_subjects(department_id=dept_id)
        result = {"items": subjects, "total": len(subjects), "page": 1, "page_size": len(subjects)}
    else:
        result = SubjectService(db).list(page, 1000)
        departments = DepartmentService(db).list(1, 100)["items"]
        courses = CourseService(db).list(1, 100)["items"]
        
    teachers = TeacherService(db).list(1, 1000)["items"]
    return templates.TemplateResponse(
        "subjects/list.html", _context(request, user, **result, departments=departments, courses=courses, teachers=teachers),
    )


# ══════════════════════════════════════════════════════════════
# ATTENDANCE PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/attendance", response_class=HTMLResponse)
def attendance_list(request: Request, db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    """View attendance records."""
    att_repo = AttendanceRepository(db)
    
    if "admin" in user.roles:
        records = att_repo.get_all_with_relations(limit=200)
    elif "teacher" in user.roles and user.teacher:
        records = att_repo.get_teacher_records(user.teacher.id, limit=500)
    elif "student" in user.roles and user.student:
        records = att_repo.get_student_records(user.student.id)
    else:
        records = []
        
    return templates.TemplateResponse(
        "attendance/list.html",
        _context(request, user, records=records),
    )


@router.get("/attendance/mark", response_class=HTMLResponse)
def mark_attendance_page(request: Request, db: Session = Depends(get_db),
                         user=Depends(get_current_user)):
    """Mark attendance form page."""
    from app.repositories.concrete import SubjectRepository
    subject_repo = SubjectRepository(db)
    
    courses = []
    departments = []
    
    if "admin" in user.roles:
        subjects = subject_repo.get_all()
        courses = CourseService(db).list(1, 100)["items"]
        departments = DepartmentService(db).list(1, 100)["items"]
    elif "teacher" in user.roles and user.teacher:
        subjects = subject_repo.get_teacher_subjects(user.teacher.id)
    else:
        subjects = []
        
    return templates.TemplateResponse(
        "attendance/mark.html",
        _context(request, user, subjects=subjects, courses=courses, departments=departments, today=date.today().isoformat()),
    )


# ══════════════════════════════════════════════════════════════
# MARKS PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/marks", response_class=HTMLResponse)
def marks_list(request: Request, course_id: Optional[str] = None, department_id: Optional[str] = None, semester: Optional[str] = None, search: str = "",
               db: Session = Depends(get_db), user=Depends(get_current_user)):
    """View marks records."""
    marks_repo = MarksRepository(db)
    from app.services.crud_services import CourseService, DepartmentService
    
    course_id = int(course_id) if course_id and str(course_id).isdigit() else None
    department_id = int(department_id) if department_id and str(department_id).isdigit() else None
    semester = int(semester) if semester and str(semester).isdigit() else None
    
    courses = CourseService(db).list(page_size=100)["items"]
    departments = DepartmentService(db).list(page_size=100)["items"]
    is_filtered = False
    
    if "admin" in user.roles:
        if course_id or department_id or semester or search:
            records = marks_repo.get_filtered_marks(course_id, department_id, semester, search)
            is_filtered = True
        else:
            records = []
    elif "teacher" in user.roles and user.teacher:
        records = marks_repo.get_teacher_records_with_relations(user.teacher.id, limit=1000)
        is_filtered = True # Teachers always see their records
    elif "student" in user.roles and user.student:
        records = marks_repo.get_student_marks(user.student.id)
        is_filtered = True # Students always see their records
    else:
        records = []
        
    return templates.TemplateResponse(
        "marks/list.html",
        _context(request, user, records=records, courses=courses, departments=departments,
                 current_course_id=course_id, current_department_id=department_id, current_semester=semester, search=search, is_filtered=is_filtered),
    )


@router.get("/marks/upload", response_class=HTMLResponse)
def upload_marks_page(request: Request, db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    """Upload marks form page."""
    subject_repo = SubjectRepository(db)
    subjects = subject_repo.get_all()
    return templates.TemplateResponse(
        "marks/upload.html",
        _context(request, user, subjects=subjects),
    )


# ══════════════════════════════════════════════════════════════
# FEE PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/fees", response_class=HTMLResponse)
def fees_list(request: Request, course_id: Optional[str] = None, department_id: Optional[str] = None, semester: Optional[str] = None, search: str = "", db: Session = Depends(get_db),
              user=Depends(get_current_user), page: int = 1):
    from app.services.crud_services import CourseService, DepartmentService
    
    course_id = int(course_id) if course_id and str(course_id).isdigit() else None
    department_id = int(department_id) if department_id and str(department_id).isdigit() else None
    semester = int(semester) if semester and str(semester).isdigit() else None
    
    courses = CourseService(db).list(page_size=100)["items"]
    departments = DepartmentService(db).list(page_size=100)["items"]
    
    if "student" in user.roles and user.student:
        fees = FeeService(db).get_student_fees(user.student.id)
        result = {"items": fees}
    else:
        if course_id or department_id or semester or search:
            fees = FeeService(db).get_filtered_fees(course_id, department_id, semester, search)
            result = {"items": fees, "is_filtered": True}
        else:
            result = {"items": [], "is_filtered": False}
            
    return templates.TemplateResponse(
        "fees/list.html", _context(request, user, **result, courses=courses, departments=departments, 
                                  current_course_id=course_id, current_department_id=department_id, current_semester=semester, search=search),
    )


# ══════════════════════════════════════════════════════════════
# LIBRARY PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/library", response_class=HTMLResponse)
def library_page(request: Request, db: Session = Depends(get_db),
                 user=Depends(get_current_user), page: int = 1, search: str = ""):
    from app.services.crud_services import LibraryService
    
    lib_service = LibraryService(db)
    result = lib_service.list(page, 50, search or None)
    
    metrics = lib_service.get_dashboard_metrics()
    
    if "student" in user.roles and user.student:
        active_issues = lib_service.get_active_issues(user.student.id)
    else:
        active_issues = lib_service.get_active_issues()
        
    from datetime import date
    return templates.TemplateResponse(
        "library/books.html", _context(request, user, **result, search=search, metrics=metrics, active_issues=active_issues, today_date=date.today()),
    )


# ══════════════════════════════════════════════════════════════
# TIMETABLE PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/timetable", response_class=HTMLResponse)
def timetable_page(request: Request, course_id: Optional[str] = None, department_id: Optional[str] = None, semester: Optional[str] = None, db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    from app.services.crud_services import CourseService, DepartmentService, TimetableGridService, SubjectService, TeacherService
    
    course_id = int(course_id) if course_id and str(course_id).isdigit() else None
    department_id = int(department_id) if department_id and str(department_id).isdigit() else None
    semester = int(semester) if semester and str(semester).isdigit() else None
    
    if "admin" in user.roles:
        courses = CourseService(db).list(page_size=100)["items"]
        departments = DepartmentService(db).list(page_size=100)["items"]
    elif user.teacher and user.teacher.department:
        courses = [user.teacher.department.course] if user.teacher.department.course else []
        departments = [user.teacher.department]
    elif user.student and user.student.department:
        courses = [user.student.department.course] if user.student.department.course else []
        departments = [user.student.department]
    else:
        courses = []
        departments = []
    
    tg_service = TimetableGridService(db)
    
    version = None
    slots = []
    
    # Restrict scope based on role
    if "student" in user.roles and user.student:
        department_id = user.student.department_id
        semester = user.student.semester
    elif "teacher" in user.roles and user.teacher:
        # Teachers and HODs are locked to their department
        department_id = user.teacher.department_id
        if "hod" in user.roles:
            course_id = user.teacher.department.course_id if user.teacher.department else None

    # Only attempt to load a grid if department and semester are selected
    if department_id and semester:
        version = tg_service.get_version(department_id, semester)
        if version:
            slots = tg_service.get_slots(version.id)
            
    # For HOD editing, load subjects and teachers for their department
    subjects = []
    dept_teachers = []
    if "hod" in user.roles and department_id:
        subjects = SubjectService(db).get_filtered_subjects(department_id=department_id, semester=semester)
        dept_teachers = TeacherService(db).get_filtered_teachers(department_id=department_id)

    pending_versions = []
    if "manage_timetable" in user.permissions:
        pending_versions = tg_service.get_pending_versions()

    return templates.TemplateResponse(
        "timetable/list.html", _context(
            request, user, 
            version=version, 
            slots=slots, 
            courses=courses, 
            departments=departments,
            subjects=subjects,
            dept_teachers=dept_teachers,
            pending_versions=pending_versions,
            current_course_id=course_id, 
            current_department_id=department_id, 
            current_semester=semester,
            edit_mode=request.query_params.get("edit") == "1"
        ),
    )


# ══════════════════════════════════════════════════════════════
# NOTIFICATION PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/notifications", response_class=HTMLResponse)
def notifications_page(request: Request, db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    from app.repositories.concrete import NotificationRepository
    notif_repo = NotificationRepository(db)
    records = notif_repo.get_user_notifications(user.id)
    
    return templates.TemplateResponse(
        "notifications/list.html", _context(request, user, records=records),
    )

@router.post("/notifications/mark-all-read")
def mark_all_notifications_read(request: Request, db: Session = Depends(get_db),
                                user=Depends(get_current_user)):
    from app.repositories.concrete import NotificationRepository
    notif_repo = NotificationRepository(db)
    notif_repo.mark_all_read(user.id)
    return RedirectResponse(url="/notifications", status_code=302)


# ══════════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════════

@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(
        "users/profile.html", _context(request, user),
    )
