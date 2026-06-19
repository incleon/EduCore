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

from app.core.dependencies import get_db, get_current_user, get_optional_user
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
    return templates.TemplateResponse("auth/login.html", _context(request))


# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db),
              user=Depends(get_current_user)):
    # Get primary role for dashboard selection
    primary_role = user.roles[0] if user.roles else "student"

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
def students_list(request: Request, db: Session = Depends(get_db),
                  user=Depends(get_current_user), page: int = 1, search: str = ""):
    result = StudentService(db).list(page, 500, search or None)
    departments = DepartmentService(db).list(1, 100)["items"]
    return templates.TemplateResponse(
        "students/list.html",
        _context(request, user, **result, search=search, departments=departments),
    )


@router.get("/students/create", response_class=HTMLResponse)
def student_create_page(request: Request, db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    departments = DepartmentService(db).list(1, 100)["items"]
    return templates.TemplateResponse(
        "students/create.html",
        _context(request, user, departments=departments),
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
def teachers_list(request: Request, db: Session = Depends(get_db),
                  user=Depends(get_current_user), page: int = 1, search: str = ""):
    result = TeacherService(db).list(page, 10, search or None)
    return templates.TemplateResponse(
        "teachers/list.html",
        _context(request, user, **result, search=search),
    )


@router.get("/teachers/create", response_class=HTMLResponse)
def teacher_create_page(request: Request, db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    departments = DepartmentService(db).list(1, 100)["items"]
    return templates.TemplateResponse(
        "teachers/create.html",
        _context(request, user, departments=departments),
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
    result = SubjectService(db).list(page, 100)
    departments = DepartmentService(db).list(1, 100)["items"]
    return templates.TemplateResponse(
        "subjects/list.html", _context(request, user, **result, departments=departments),
    )


# ══════════════════════════════════════════════════════════════
# ATTENDANCE PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/attendance", response_class=HTMLResponse)
def attendance_list(request: Request, db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    """View attendance records."""
    att_repo = AttendanceRepository(db)
    records = att_repo.get_all(limit=50)
    return templates.TemplateResponse(
        "attendance/list.html",
        _context(request, user, records=records),
    )


@router.get("/attendance/mark", response_class=HTMLResponse)
def mark_attendance_page(request: Request, db: Session = Depends(get_db),
                         user=Depends(get_current_user)):
    """Mark attendance form page."""
    subject_repo = SubjectRepository(db)
    subjects = subject_repo.get_all()
    return templates.TemplateResponse(
        "attendance/mark.html",
        _context(request, user, subjects=subjects, today=date.today().isoformat()),
    )


# ══════════════════════════════════════════════════════════════
# MARKS PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/marks", response_class=HTMLResponse)
def marks_list(request: Request, db: Session = Depends(get_db),
               user=Depends(get_current_user)):
    """View marks records."""
    marks_repo = MarksRepository(db)
    records = marks_repo.get_all(limit=50)
    return templates.TemplateResponse(
        "marks/list.html",
        _context(request, user, records=records),
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
def fees_list(request: Request, db: Session = Depends(get_db),
              user=Depends(get_current_user), page: int = 1):
    result = FeeService(db).list(page, 10)
    return templates.TemplateResponse(
        "fees/list.html", _context(request, user, **result),
    )


# ══════════════════════════════════════════════════════════════
# LIBRARY PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/library", response_class=HTMLResponse)
def library_page(request: Request, db: Session = Depends(get_db),
                 user=Depends(get_current_user), page: int = 1, search: str = ""):
    result = LibraryService(db).list(page, 10, search or None)
    return templates.TemplateResponse(
        "library/books.html", _context(request, user, **result, search=search),
    )


# ══════════════════════════════════════════════════════════════
# TIMETABLE PAGES
# ══════════════════════════════════════════════════════════════

@router.get("/timetable", response_class=HTMLResponse)
def timetable_page(request: Request, db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    from app.repositories.concrete import TimetableRepository
    
    tt_repo = TimetableRepository(db)
    records = []
    
    if "student" in user.roles and user.student:
        records = tt_repo.get_by_student(user.student.semester, user.student.section)
    elif "teacher" in user.roles and user.teacher:
        records = tt_repo.get_by_teacher(user.teacher.id)
    else:
        records = tt_repo.get_all()

    # Format records into a weekly grid
    time_slots = {}
    for r in records:
        time_str = f"{r.start_time.strftime('%H:%M')} - {r.end_time.strftime('%H:%M')}"
        if time_str not in time_slots:
            time_slots[time_str] = {"time": time_str}
        time_slots[time_str][r.day.value] = r

    formatted_records = sorted(time_slots.values(), key=lambda x: x["time"])

    return templates.TemplateResponse(
        "timetable/list.html", _context(request, user, records=formatted_records),
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
