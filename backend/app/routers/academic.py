"""Enterprise academic structure and curriculum management API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import ForbiddenException
from app.core.permissions import PermissionChecker, RoleChecker
from app.core.portfolio import is_scoped_faculty
from app.models.academic import (
    AcademicSemester, Branch, Curriculum, CurriculumSubject, CurriculumVersion,
    ElectiveGroup, FacultyAssignment, Section, SubjectType,
)
from app.models.course import Course
from app.schemas.academic import (
    BranchCreate, BranchUpdate, CurriculumCreate, CurriculumSubjectCreate,
    CurriculumSubjectUpdate, CurriculumUpdate, CurriculumVersionCreate,
    CurriculumVersionUpdate, ElectiveGroupCreate, ElectiveGroupUpdate,
    FacultyAssignmentCreate, FacultyAssignmentUpdate, SectionCreate, SectionUpdate,
    SemesterCreate, SemesterUpdate, StudentAcademicMappingUpdate, StudentElectiveCreate,
)
from app.services.academic_service import AcademicStructureService


router = APIRouter(prefix="/api/academic", tags=["Academic Structure"])


def service(db):
    return AcademicStructureService(db)


@router.get("/subject-types")
def list_subject_types(db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_academic_structure"]))):
    return [_subject_type(item) for item in service(db).list_records(SubjectType)]


@router.get("/branches")
def list_branches(course_id: int | None = None, department_id: int | None = None, branch_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_academic_structure"]))):
    query = db.query(Branch).join(Course).filter(Branch.is_deleted.is_(False))
    if course_id: query = query.filter(Branch.course_id == course_id)
    if department_id: query = query.filter(Course.department_id == department_id)
    if branch_id: query = query.filter(Branch.id == branch_id)
    return {"items": [_branch(item) for item in query.order_by(Branch.id.desc()).all()]}


@router.post("/branches", status_code=201)
def create_branch(data: BranchCreate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_academic_structure"]))):
    return _branch(service(db).create_branch(data.model_dump()))


@router.put("/branches/{branch_id}")
def update_branch(branch_id: int, data: BranchUpdate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_academic_structure"]))):
    return _branch(service(db).update_branch(branch_id, data.model_dump(exclude_unset=True)))


@router.delete("/branches/{branch_id}")
def delete_branch(branch_id: int, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_academic_structure"]))):
    service(db).delete_record(Branch, branch_id, "Branch")
    return {"message": "Branch deleted successfully"}


@router.get("/curricula")
def list_curricula(course_id: int | None = None, branch_id: int | None = None, department_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_academic_structure"]))):
    query=db.query(Curriculum).join(Course).filter(Curriculum.is_deleted.is_(False))
    if course_id: query=query.filter(Curriculum.course_id == course_id)
    if branch_id: query=query.filter(Curriculum.branch_id == branch_id)
    if department_id: query=query.filter(Course.department_id == department_id)
    return {"items": [_curriculum(item) for item in query.order_by(Curriculum.id.desc()).all()]}


@router.post("/curricula", status_code=201)
def create_curriculum(data: CurriculumCreate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    return _curriculum(service(db).create_curriculum(data.model_dump()))


@router.put("/curricula/{curriculum_id}")
def update_curriculum(curriculum_id: int, data: CurriculumUpdate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    return _curriculum(service(db).update_curriculum(curriculum_id, data.model_dump(exclude_unset=True)))


@router.delete("/curricula/{curriculum_id}")
def delete_curriculum(curriculum_id: int, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    service(db).delete_record(Curriculum, curriculum_id, "Curriculum")
    return {"message": "Curriculum deleted successfully"}


@router.get("/curriculum-versions")
def list_curriculum_versions(curriculum_id: int | None = None, branch_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_academic_structure"]))):
    query = db.query(CurriculumVersion).join(Curriculum).filter(CurriculumVersion.is_deleted.is_(False))
    if curriculum_id: query = query.filter(CurriculumVersion.curriculum_id == curriculum_id)
    if branch_id: query = query.filter(Curriculum.branch_id == branch_id)
    return {"items": [_version(item) for item in query.order_by(CurriculumVersion.id.desc()).all()]}


@router.post("/curriculum-versions", status_code=201)
def create_curriculum_version(data: CurriculumVersionCreate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    return _version(service(db).create_curriculum_version(data.model_dump()))


@router.put("/curriculum-versions/{version_id}")
def update_curriculum_version(version_id: int, data: CurriculumVersionUpdate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    return _version(service(db).update_curriculum_version(version_id, data.model_dump(exclude_unset=True)))


@router.delete("/curriculum-versions/{version_id}")
def delete_curriculum_version(version_id: int, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    service(db).delete_record(CurriculumVersion, version_id, "Curriculum version")
    return {"message": "Curriculum version deleted successfully"}


@router.get("/semesters")
def list_semesters(curriculum_version_id: int | None = None, branch_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_academic_structure"]))):
    query = db.query(AcademicSemester).join(CurriculumVersion).join(Curriculum).filter(AcademicSemester.is_deleted.is_(False))
    if curriculum_version_id: query = query.filter(AcademicSemester.curriculum_version_id == curriculum_version_id)
    if branch_id: query = query.filter(Curriculum.branch_id == branch_id)
    return {"items": [_semester(item) for item in query.order_by(AcademicSemester.id.desc()).all()]}


@router.post("/semesters", status_code=201)
def create_semester(data: SemesterCreate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    return _semester(service(db).create_semester(data.model_dump()))


@router.put("/semesters/{semester_id}")
def update_semester(semester_id: int, data: SemesterUpdate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    return _semester(service(db).update_record(AcademicSemester, semester_id, data.model_dump(exclude_unset=True), "Semester"))


@router.delete("/semesters/{semester_id}")
def delete_semester(semester_id: int, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    service(db).delete_record(AcademicSemester, semester_id, "Semester")
    return {"message": "Semester deleted successfully"}


@router.get("/sections")
def list_sections(course_id: int | None = None, branch_id: int | None = None, department_id: int | None = None, academic_year: str | None = None, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_academic_structure"]))):
    query=db.query(Section).join(Course).filter(Section.is_deleted.is_(False))
    if course_id: query=query.filter(Section.course_id == course_id)
    if branch_id: query=query.filter(Section.branch_id == branch_id)
    if department_id: query=query.filter(Course.department_id == department_id)
    if academic_year: query=query.filter(Section.academic_year == academic_year)
    return {"items": [_section(item) for item in query.order_by(Section.id.desc()).all()]}


@router.post("/sections", status_code=201)
def create_section(data: SectionCreate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_academic_structure"]))):
    return _section(service(db).create_section(data.model_dump()))


@router.put("/sections/{section_id}")
def update_section(section_id: int, data: SectionUpdate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_academic_structure"]))):
    return _section(service(db).update_record(Section, section_id, data.model_dump(exclude_unset=True), "Section"))


@router.delete("/sections/{section_id}")
def delete_section(section_id: int, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_academic_structure"]))):
    service(db).delete_record(Section, section_id, "Section")
    return {"message": "Section deleted successfully"}


@router.get("/elective-groups")
def list_elective_groups(semester_id: int | None = None, branch_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_academic_structure"]))):
    query = db.query(ElectiveGroup).join(AcademicSemester).join(CurriculumVersion).join(Curriculum).filter(ElectiveGroup.is_deleted.is_(False))
    if semester_id: query = query.filter(ElectiveGroup.semester_id == semester_id)
    if branch_id: query = query.filter(Curriculum.branch_id == branch_id)
    return {"items": [_elective_group(item) for item in query.order_by(ElectiveGroup.id.desc()).all()]}


@router.post("/elective-groups", status_code=201)
def create_elective_group(data: ElectiveGroupCreate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    return _elective_group(service(db).create_elective_group(data.model_dump()))


@router.put("/elective-groups/{group_id}")
def update_elective_group(group_id: int, data: ElectiveGroupUpdate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    return _elective_group(service(db).update_record(ElectiveGroup, group_id, data.model_dump(exclude_unset=True), "Elective group"))


@router.delete("/elective-groups/{group_id}")
def delete_elective_group(group_id: int, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    service(db).delete_record(ElectiveGroup, group_id, "Elective group")
    return {"message": "Elective group deleted successfully"}


@router.get("/curriculum-subjects")
def list_curriculum_subjects(semester_id: int | None = None, branch_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_academic_structure"]))):
    return {"items": [_curriculum_subject(item) for item in service(db).list_records(CurriculumSubject, semester_id=semester_id, branch_id=branch_id)]}


@router.post("/curriculum-subjects", status_code=201)
def create_curriculum_subject(data: CurriculumSubjectCreate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    return _curriculum_subject(service(db).add_curriculum_subject(data.model_dump()))


@router.put("/curriculum-subjects/{mapping_id}")
def update_curriculum_subject(mapping_id: int, data: CurriculumSubjectUpdate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    return _curriculum_subject(service(db).update_curriculum_subject(mapping_id, data.model_dump(exclude_unset=True)))


@router.delete("/curriculum-subjects/{mapping_id}")
def delete_curriculum_subject(mapping_id: int, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_curriculum"]))):
    service(db).delete_record(CurriculumSubject, mapping_id, "Curriculum subject")
    return {"message": "Curriculum subject removed successfully"}


@router.get("/faculty-assignments")
def list_faculty_assignments(section_id: int | None = None, branch_id: int | None = None, academic_year: str | None = None, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["view_academic_structure"]))):
    filters = {"section_id": section_id, "academic_year": academic_year}
    if is_scoped_faculty(current_user):
        filters["teacher_id"] = current_user.teacher.id
    
    query = db.query(FacultyAssignment).filter(FacultyAssignment.is_deleted.is_(False))
    for key, value in filters.items():
        if value is not None:
            query = query.filter(getattr(FacultyAssignment, key) == value)
            
    if branch_id:
        query = query.join(Section).filter(Section.branch_id == branch_id)
        
    return {"items": [_faculty_assignment(item) for item in query.order_by(FacultyAssignment.id.desc()).all()]}


@router.post("/faculty-assignments", status_code=201)
def create_faculty_assignment(data: FacultyAssignmentCreate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin"]))):
    return _faculty_assignment(service(db).create_faculty_assignment(data.model_dump()))


@router.put("/faculty-assignments/{assignment_id}")
def update_faculty_assignment(assignment_id: int, data: FacultyAssignmentUpdate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin"]))):
    return _faculty_assignment(service(db).update_record(FacultyAssignment, assignment_id, data.model_dump(exclude_unset=True), "Faculty assignment"))


@router.delete("/faculty-assignments/{assignment_id}")
def delete_faculty_assignment(assignment_id: int, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["admin"]))):
    service(db).delete_record(FacultyAssignment, assignment_id, "Faculty assignment")
    return {"message": "Faculty assignment deleted successfully"}


@router.put("/students/{student_id}/mapping")
def update_student_mapping(student_id: int, data: StudentAcademicMappingUpdate, db: Session = Depends(get_db), current_user=Depends(PermissionChecker(["manage_students"]))):
    student = service(db).update_student_mapping(student_id, data.model_dump())
    return {"id": student.id, "course_id": student.course_id, "branch_id": student.branch_id, "curriculum_version_id": student.curriculum_version_id, "current_semester": student.current_semester, "section_id": student.section_id}


@router.get("/students/{student_id}/subjects")
def get_student_subjects(student_id: int, semester: int | None = Query(None, ge=1, le=20), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user.has_permission("view_students") and (not current_user.student or current_user.student.id != student_id):
        raise ForbiddenException()
    return {"items": service(db).resolve_student_subjects(student_id, semester)}


@router.post("/students/{student_id}/electives", status_code=201)
def select_student_elective(student_id: int, data: StudentElectiveCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user.has_permission("manage_students") and (not current_user.student or current_user.student.id != student_id):
        raise ForbiddenException()
    selection = service(db).select_elective(student_id, data.curriculum_subject_id)
    return {"id": selection.id, "student_id": selection.student_id, "curriculum_subject_id": selection.curriculum_subject_id, "status": selection.status}


def _subject_type(item):
    return {"id": item.id, "code": item.code, "name": item.name, "description": item.description}


def _branch(item):
    return {"id": item.id, "course_id": item.course_id, "department_id": item.course.department_id, "department": {"id": item.course.department.id, "name": item.course.department.name} if item.course.department else None, "course": {"id": item.course.id, "name": item.course.name, "code": item.course.code}, "name": item.name, "code": item.code, "description": item.description, "hod_id": item.hod_id, "hod": {"id": item.hod.id, "name": item.hod.user.full_name} if item.hod and item.hod.user else ({"id": item.hod.id, "name": item.hod.employee_id} if item.hod else None)}


def _curriculum(item):
    return {"id": item.id, "department_id": item.course.department_id, "department": {"id": item.course.department.id, "name": item.course.department.name} if item.course.department else None, "course_id": item.course_id, "branch_id": item.branch_id, "course": {"id": item.course.id, "name": item.course.name}, "branch": ({"id": item.branch.id, "name": item.branch.name} if item.branch else None), "code": item.code, "name": item.name, "description": item.description}


def _version(item):
    return {"id": item.id, "curriculum_id": item.curriculum_id, "curriculum": {"id": item.curriculum.id, "name": item.curriculum.name}, "version_code": item.version_code, "title": item.title, "effective_year": item.effective_year, "applicable_batch_start": item.applicable_batch_start, "applicable_batch_end": item.applicable_batch_end, "status": item.status, "is_active": item.is_active}


def _semester(item):
    return {"id": item.id, "curriculum_version_id": item.curriculum_version_id, "curriculum_version": {"id": item.curriculum_version.id, "title": item.curriculum_version.title}, "number": item.number, "name": item.name or f"Semester {item.number}", "minimum_credits": item.minimum_credits, "maximum_credits": item.maximum_credits}


def _section(item):
    return {"id": item.id, "department_id": item.course.department_id, "department": {"id": item.course.department.id, "name": item.course.department.name} if item.course.department else None, "course_id": item.course_id, "branch_id": item.branch_id, "curriculum_version_id": item.curriculum_version_id, "course": {"id": item.course.id, "name": item.course.name}, "branch": ({"id": item.branch.id, "name": item.branch.name} if item.branch else None), "semester_number": item.semester_number, "code": item.code, "academic_year": item.academic_year, "capacity": item.capacity}


def _elective_group(item):
    return {"id": item.id, "semester_id": item.semester_id, "semester": {"id": item.semester.id, "name": item.semester.name or f"Semester {item.semester.number}"}, "code": item.code, "name": item.name, "minimum_choices": item.minimum_choices, "maximum_choices": item.maximum_choices, "description": item.description}


def _curriculum_subject(item):
    return {"id": item.id, "semester_id": item.semester_id, "subject_id": item.subject_id, "branch_id": item.branch_id, "elective_group_id": item.elective_group_id, "semester": {"id": item.semester.id, "number": item.semester.number}, "subject": {"id": item.subject.id, "code": item.subject.code, "name": item.subject.name, "type": item.subject.subject_type.code if item.subject.subject_type else item.subject.type}, "branch": ({"id": item.branch.id, "name": item.branch.name} if item.branch else None), "is_mandatory": item.is_mandatory, "credits_override": item.credits_override, "display_order": item.display_order}


def _faculty_assignment(item):
    return {"id": item.id, "teacher_id": item.teacher_id, "curriculum_subject_id": item.curriculum_subject_id, "section_id": item.section_id, "teacher": {"id": item.teacher.id, "name": item.teacher.user.full_name if item.teacher.user else item.teacher.employee_id}, "subject": {"id": item.curriculum_subject.subject.id, "name": item.curriculum_subject.subject.name, "code": item.curriculum_subject.subject.code}, "section": ({"id": item.section.id, "code": item.section.code} if item.section else None), "academic_year": item.academic_year, "role": item.role}
