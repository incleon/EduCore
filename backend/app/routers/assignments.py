from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.core.permissions import PermissionChecker
from app.services.assignment_service import AssignmentService
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    AssignmentSubmissionCreate, AssignmentSubmissionReview, AssignmentSubmissionResponse
)

assignments_router = APIRouter(prefix="/api/assignments", tags=["Assignments"])

@assignments_router.get("", response_model=List[AssignmentResponse | AssignmentSubmissionResponse])
def get_assignments(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    service = AssignmentService(db)
    if "student" in current_user.roles and current_user.student:
        return service.get_student_assignments(current_user.student.id)
    elif "teacher" in current_user.roles and current_user.teacher:
        return service.get_teacher_assignments(current_user.teacher.id)
    return []

@assignments_router.post("", response_model=AssignmentResponse, status_code=201)
def create_assignment(data: AssignmentCreate, db: Session = Depends(get_db), current_user = Depends(PermissionChecker(["manage_assignments"]))):
    service = AssignmentService(db)
    # Even if they have manage_curriculum, they must be a teacher
    if not current_user.teacher:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Must be a teacher")
    return service.create_assignment(current_user.teacher.id, data.model_dump())

@assignments_router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(assignment_id: int, data: AssignmentUpdate, db: Session = Depends(get_db), current_user = Depends(PermissionChecker(["manage_assignments"]))):
    if not current_user.teacher:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Must be a teacher")
    return AssignmentService(db).update_assignment(
        current_user.teacher.id, assignment_id, data.model_dump(exclude_unset=True)
    )

@assignments_router.delete("/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db), current_user = Depends(PermissionChecker(["manage_assignments"]))):
    if not current_user.teacher:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Must be a teacher")
    AssignmentService(db).delete_assignment(current_user.teacher.id, assignment_id)
    return {"message": "Assignment deleted successfully"}

@assignments_router.get("/{assignment_id}/submissions", response_model=List[AssignmentSubmissionResponse])
def get_submissions(assignment_id: int, db: Session = Depends(get_db), current_user = Depends(PermissionChecker(["manage_assignments"]))):
    service = AssignmentService(db)
    if not current_user.teacher:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Must be a teacher")
    return service.get_assignment_submissions(current_user.teacher.id, assignment_id)

@assignments_router.post("/submissions/{submission_id}/submit", response_model=AssignmentSubmissionResponse)
def submit_assignment(submission_id: int, data: AssignmentSubmissionCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    service = AssignmentService(db)
    if not current_user.student:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Must be a student")
    return service.submit_assignment(current_user.student.id, submission_id, data.content)

@assignments_router.post("/submissions/{submission_id}/review", response_model=AssignmentSubmissionResponse)
def review_submission(submission_id: int, data: AssignmentSubmissionReview, db: Session = Depends(get_db), current_user = Depends(PermissionChecker(["manage_assignments"]))):
    service = AssignmentService(db)
    if not current_user.teacher:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Must be a teacher")
    return service.review_submission(current_user.teacher.id, submission_id, data.status, data.feedback)
