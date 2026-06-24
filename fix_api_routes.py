import sys

path = r'c:\CMS\backend\app\routers\api_routes.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    if '@students_router.put("/{student_id}")' in lines[i]:
        # Replace up to line 252 (which is index 251, so up to line where @teachers_router.post is)
        new_lines.append('''@students_router.put("/{student_id}")
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_students"])),
):
    student = StudentService(db).update(student_id, data.model_dump(exclude_unset=True))
    return _format_student(student)


@students_router.delete("/all")
def delete_all_students(
    db: Session = Depends(get_db),
    current_user=Depends(PermissionChecker(["manage_students"])),
):
    count = StudentService(db).delete_all()
    return {"message": f"{count} students deleted successfully"}


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
    current_user=Depends(PermissionChecker(["view_teachers"])),
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
    current_user=Depends(PermissionChecker(["view_teachers"])),
):
    teacher = TeacherService(db).get(teacher_id)
    return _format_teacher(teacher)
''')
        # skip lines until @teachers_router.post
        while i < len(lines) and '@teachers_router.post("", status_code=201)' not in lines[i]:
            i += 1
        continue
    
    new_lines.append(lines[i])
    i += 1

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("File fixed.")
