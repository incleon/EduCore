from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.academic import Assignment, AssignmentSubmission, FacultyAssignment
from app.models.student import Student
from datetime import datetime

class AssignmentService:
    def __init__(self, db: Session):
        self.db = db

    def get_teacher_assignments(self, teacher_id: int):
        # Find all assignments for this teacher
        return self.db.query(Assignment).join(FacultyAssignment).filter(
            FacultyAssignment.teacher_id == teacher_id
        ).all()

    def get_student_assignments(self, student_id: int):
        # Find all submissions for this student
        return self.db.query(AssignmentSubmission).filter(
            AssignmentSubmission.student_id == student_id
        ).all()

    def create_assignment(self, teacher_id: int, data: dict):
        # Validate that the faculty assignment belongs to this teacher
        fa = self.db.query(FacultyAssignment).filter_by(id=data["faculty_assignment_id"], teacher_id=teacher_id).first()
        if not fa:
            raise HTTPException(status_code=403, detail="Not authorized for this faculty assignment")
            
        assignment = Assignment(**data)
        self.db.add(assignment)
        self.db.flush() # get assignment.id
        
        # Automatically create pending submissions for all students in the section
        if fa.section_id:
            students = self.db.query(Student).filter_by(section_id=fa.section_id).all()
            for student in students:
                sub = AssignmentSubmission(
                    assignment_id=assignment.id,
                    student_id=student.id,
                    status="pending"
                )
                self.db.add(sub)
        
        self.db.commit()
        return assignment

    def update_assignment(self, teacher_id: int, assignment_id: int, data: dict):
        assignment = self.db.query(Assignment).join(FacultyAssignment).filter(
            Assignment.id == assignment_id,
            FacultyAssignment.teacher_id == teacher_id,
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        for field, value in data.items():
            setattr(assignment, field, value)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def delete_assignment(self, teacher_id: int, assignment_id: int):
        assignment = self.db.query(Assignment).join(FacultyAssignment).filter(
            Assignment.id == assignment_id,
            FacultyAssignment.teacher_id == teacher_id,
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        self.db.delete(assignment)
        self.db.commit()

    def submit_assignment(self, student_id: int, submission_id: int, content: str):
        sub = self.db.query(AssignmentSubmission).filter_by(id=submission_id, student_id=student_id).first()
        if not sub:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        sub.content = content
        sub.status = "submitted"
        sub.submitted_at = datetime.utcnow()
        self.db.commit()
        return sub

    def get_assignment_submissions(self, teacher_id: int, assignment_id: int):
        assignment = self.db.query(Assignment).join(FacultyAssignment).filter(
            Assignment.id == assignment_id,
            FacultyAssignment.teacher_id == teacher_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
            
        return self.db.query(AssignmentSubmission).filter_by(assignment_id=assignment_id).all()

    def review_submission(self, teacher_id: int, submission_id: int, status: str, feedback: str = None):
        sub = self.db.query(AssignmentSubmission).join(Assignment).join(FacultyAssignment).filter(
            AssignmentSubmission.id == submission_id,
            FacultyAssignment.teacher_id == teacher_id
        ).first()
        if not sub:
            raise HTTPException(status_code=404, detail="Submission not found")
            
        sub.status = status
        if feedback is not None:
            sub.feedback = feedback
        self.db.commit()
        return sub
