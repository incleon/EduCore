"""
System Maintenance Service
==========================

Provides utility methods to maintain database integrity and clean up orphaned or invalid records.
This demonstrates modularity by encapsulating maintenance tasks in a dedicated service.
"""

from sqlalchemy.orm import Session
from app.services.base import IService
from app.models.department import Department
from app.models.subject import Subject
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.course import Course
from app.models.user import User
from app.services.crud_services import DepartmentService, SubjectService, StudentService, TeacherService, UserService
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class SystemMaintenanceService(IService):
    def __init__(self, db: Session):
        self._db = db

    def get(self, id: int):
        pass

    def list(self):
        pass

    def create(self, data):
        pass

    def update(self, id, data):
        pass

    def delete(self, id):
        pass

    def cleanup_ghost_records(self) -> dict:
        """
        Cleans up orphaned records in the database.
        This includes:
        - Departments whose Course was soft-deleted.
        - Subjects whose Department was soft-deleted.
        - Students and Teachers whose Department was soft-deleted.
        - Users with student/teacher roles but no active student/teacher record.
        """
        results = {
            "departments": 0,
            "subjects": 0,
            "students": 0,
            "teachers": 0,
            "orphaned_users": 0
        }

        # 1. Cleanup Ghost Departments
        ghost_departments = self._db.query(Department).join(Course).filter(
            Course.is_deleted == True,
            Department.is_deleted == False
        ).all()
        for dept in ghost_departments:
            DepartmentService(self._db).delete(dept.id)
            results["departments"] += 1

        # 2. Cleanup Ghost Subjects
        ghost_subjects = self._db.query(Subject).join(Department).filter(
            Department.is_deleted == True,
            Subject.is_deleted == False
        ).all()
        for subj in ghost_subjects:
            SubjectService(self._db).delete(subj.id)
            results["subjects"] += 1

        # 3. Cleanup Ghost Students
        ghost_students = self._db.query(Student).join(Department).filter(
            Department.is_deleted == True,
            Student.is_deleted == False
        ).all()
        for student in ghost_students:
            StudentService(self._db).delete(student.id)
            results["students"] += 1

        # 4. Cleanup Ghost Teachers
        ghost_teachers = self._db.query(Teacher).join(Department, Teacher.department_id == Department.id).filter(
            Department.is_deleted == True,
            Teacher.is_deleted == False
        ).all()
        for teacher in ghost_teachers:
            TeacherService(self._db).delete(teacher.id)
            results["teachers"] += 1

        # 5. Cleanup Orphaned Student/Teacher User accounts
        # Any user account whose email matches standard generated patterns but has no associated profile
        student_users = self._db.query(User).filter(
            User.email.like('student%@cms.edu'),
            User.is_deleted == False
        ).all()
        
        user_service = UserService(self._db)
        for u in student_users:
            # Check if this user actually has an active student profile
            has_profile = self._db.query(Student).filter(Student.user_id == u.id, Student.is_deleted == False).first()
            if not has_profile:
                user_service.delete(u.id)
                results["orphaned_users"] += 1

        logger.info(f"Ghost records cleaned: {results}")
        return results
