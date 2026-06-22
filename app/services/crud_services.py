"""
CRUD Services — Business Logic for All Modules
==================================================

Each service:
1. Implements IService (ABSTRACTION via ABC)
2. Composes a Repository (COMPOSITION)
3. Adds business validation and transformation logic
4. Is injected into routes via FastAPI's Depends

OOP Concepts: Inheritance, Composition, Polymorphism, Method Overriding
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
import uuid

from app.services.base import IService
from app.repositories.concrete import (
    UserRepository, RoleRepository, PermissionRepository,
    StudentRepository, TeacherRepository, CourseRepository, DepartmentRepository,
    SubjectRepository, AttendanceRepository,
    MarksRepository, FeeRepository, LibraryBookRepository,
    BookIssueRepository, AuditLogRepository,
)
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.core.security import PasswordHasher
from app.core.exceptions import (
    NotFoundException, ConflictException, ValidationException, BadRequestException,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# ══════════════════════════════════════════════════════════════
# USER SERVICE
# ══════════════════════════════════════════════════════════════

class UserService(IService):
    """
    User service — implements IService interface.

    Demonstrates:
    - INHERITANCE from IService (ABC)
    - COMPOSITION with UserRepository and RoleRepository
    - METHOD OVERRIDING (implements abstract methods)
    """

    def __init__(self, db: Session):
        self._user_repo = UserRepository(db)
        self._role_repo = RoleRepository(db)
        self._db = db

    def get(self, id: int) -> Optional[User]:
        user = self._user_repo.get_by_id(id)
        if not user:
            raise NotFoundException("User", id)
        return user

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        skip = (page - 1) * page_size
        if search:
            items = self._user_repo.search(
                ["email", "full_name", "username"], search, skip, page_size
            )
            total = self._user_repo.search_count(
                ["email", "full_name", "username"], search
            )
        else:
            items = self._user_repo.get_all(skip, page_size, sort_by, sort_order)
            total = self._user_repo.count()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]) -> User:
        # Check for duplicate email
        if self._user_repo.get_by_email(data.get("email", "")):
            raise ConflictException(detail="Email already registered")
        if self._user_repo.get_by_username(data.get("username", "")):
            raise ConflictException(detail="Username already taken")

        role_ids = data.pop("role_ids", [])
        password = data.pop("password")
        data["hashed_password"] = PasswordHasher.hash_password(password)

        user = self._user_repo.create(data)

        # Assign roles
        for role_id in role_ids:
            self._user_repo.assign_role(user.id, role_id)

        self._db.refresh(user)
        return user

    def update(self, id: int, data: Dict[str, Any]) -> Optional[User]:
        user = self._user_repo.get_by_id(id)
        if not user:
            raise NotFoundException("User", id)

        role_ids = data.pop("role_ids", None)

        # Filter None values
        update_data = {k: v for k, v in data.items() if v is not None}
        if update_data:
            self._user_repo.update(id, update_data)

        if role_ids is not None:
            # Remove existing roles and assign new ones
            existing = self._db.query(UserRole).filter(UserRole.user_id == id).all()
            for ur in existing:
                self._db.delete(ur)
            self._db.flush()
            for role_id in role_ids:
                self._user_repo.assign_role(id, role_id)

        self._db.refresh(user)
        return user

    def delete(self, id: int) -> bool:
        return self._user_repo.soft_delete(id)


# ══════════════════════════════════════════════════════════════
# STUDENT SERVICE
# ══════════════════════════════════════════════════════════════

class StudentService(IService):
    """Student service — creates both User and Student records."""

    def __init__(self, db: Session):
        self._student_repo = StudentRepository(db)
        self._user_repo = UserRepository(db)
        self._role_repo = RoleRepository(db)
        self._db = db

    def get(self, id: int):
        student = self._student_repo.get_by_id(id)
        if not student:
            raise NotFoundException("Student", id)
        return student

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        skip = (page - 1) * page_size
        if search:
            items = self._student_repo.search(
                ["enrollment_number", "student_id"], search, skip, page_size
            )
            total = self._student_repo.search_count(["enrollment_number", "student_id"], search)
        else:
            items = self._student_repo.get_all(skip, page_size, sort_by, sort_order)
            total = self._student_repo.count()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_filtered_students(self, course_id: int = None, department_id: int = None, search: str = None):
        return self._student_repo.get_filtered_students(course_id, department_id, search)

    def _get_branch_code(self, department_code: str) -> str:
        if department_code:
            return department_code.replace("-", "")[:4].upper()
        return "XXXX"

    def generate_student_id(self, admission_year: int, branch_code: str) -> str:
        from app.models.student import Student
        from sqlalchemy import desc
        
        yy = str(admission_year)[-2:]
        prefix = f"{yy}-{branch_code}-"
        
        last_student = (
            self._db.query(Student)
            .filter(Student.student_id.like(f"{prefix}%"))
            .order_by(desc(Student.student_id))
            .first()
        )
        
        if last_student and last_student.student_id:
            try:
                last_seq = int(last_student.student_id.split('-')[-1])
                next_seq = last_seq + 1
            except ValueError:
                next_seq = 1
        else:
            next_seq = 1
            
        return f"{prefix}{next_seq:03d}"

    def create(self, data: Dict[str, Any]):
        # Generate student_id
        import datetime
        admission_date = data.get("admission_date")
        if admission_date:
            try:
                if isinstance(admission_date, str):
                    year = datetime.datetime.strptime(admission_date, "%Y-%m-%d").year
                else:
                    year = admission_date.year
            except:
                year = datetime.datetime.now().year
        else:
            year = datetime.datetime.now().year
            
        dept_id = data.get("department_id")
        dept_code = "XX"
        if dept_id:
            from app.services.crud_services import DepartmentService
            dept = DepartmentService(self._db).get(dept_id)
            if dept:
                dept_code = dept.code
                
        branch_code = self._get_branch_code(dept_code)
        student_id = self.generate_student_id(year, branch_code)

        # Generate institutional email
        # Process names
        first_name_input = (data.pop("first_name", "") or "").strip()
        middle_name_input = (data.pop("middle_name", "") or "").strip()
        last_name_input = (data.pop("last_name", "") or "").strip()
        
        name_parts = [first_name_input]
        if middle_name_input:
            name_parts.append(middle_name_input)
        if last_name_input:
            name_parts.append(last_name_input)
            
        full_name = " ".join(name_parts)
        
        first_name = first_name_input.lower() if first_name_input else "student"
        import re
        first_name = re.sub(r'[^a-z0-9]', '', first_name)
        student_id_lower = student_id.lower()
        institutional_email = f"{first_name}.{student_id_lower}@cms.edu"

        if self._user_repo.get_by_email(institutional_email):
            raise ConflictException(detail="Generated email already registered")

        personal_email = data.pop("personal_email")
        
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(10))
        username = student_id_lower

        # Create user first
        user_data = {
            "email": institutional_email,
            "username": username,
            "hashed_password": PasswordHasher.hash_password(password),
            "full_name": full_name,
            "phone": data.pop("phone", None),
            "gender": data.pop("gender", None),
        }
        user = self._user_repo.create(user_data)

        # Assign student role
        student_role = self._role_repo.get_by_name("student")
        if student_role:
            self._user_repo.assign_role(user.id, student_role.id)

        data.pop("email", None) # Remove any dummy email if present
        data["student_id"] = student_id
        data["enrollment_number"] = f"ENR-{student_id}"
        data["personal_email"] = personal_email
        data["initial_password"] = password

        # Create student profile
        data["user_id"] = user.id
        student = self._student_repo.create(data)
        self._db.refresh(student)

        email_data = {
            "student_name": full_name,
            "personal_email": personal_email,
            "student_id": student_id,
            "institutional_email": institutional_email,
            "generated_password": password
        }

        return student, email_data

    def update(self, id: int, data: Dict[str, Any]):
        student = self._student_repo.get_by_id(id)
        if not student:
            raise NotFoundException("Student", id)

        # Update user fields
        user_fields = {}
        for field in ["full_name", "phone"]:
            if field in data and data[field] is not None:
                user_fields[field] = data.pop(field)
        if user_fields:
            self._user_repo.update(student.user_id, user_fields)

        # Update student fields
        update_data = {k: v for k, v in data.items() if v is not None}
        if update_data:
            self._student_repo.update(id, update_data)

        self._db.refresh(student)
        return student

    def delete(self, id: int) -> bool:
        student = self._student_repo.get_by_id(id)
        if not student:
            return False
        
        # Free up email and username so they can be reused, but keep the record (soft delete)
        # This ensures the student_id sequence continues to increment properly.
        import uuid
        user = self._user_repo.get_by_id(student.user_id)
        if user:
            random_suffix = uuid.uuid4().hex[:8]
            user.email = f"deleted_{random_suffix}_{user.email}"
            user.username = f"deleted_{random_suffix}_{user.username}"
            self._db.commit()
            
        self._user_repo.soft_delete(student.user_id)
        return self._student_repo.soft_delete(id)

    def get_students_for_subject(self, subject_id: int):
        from app.repositories.concrete import SubjectRepository
        from app.models.department import Department
        from app.models.student import Student
        
        subject = SubjectRepository(self._db).get_by_id(subject_id)
        if not subject:
            raise NotFoundException("Subject", subject_id)
            
        # If subject belongs to Applied Sciences, fetch all B.TECH students of that semester
        dept = self._db.query(Department).get(subject.department_id)
        if dept and "Applied Sciences" in dept.name and dept.course and dept.course.name == "B.TECH":
            return (
                self._db.query(Student)
                .join(Department, Student.department_id == Department.id)
                .filter(
                    Department.course_id == dept.course_id,
                    Student.semester == subject.semester,
                    Student.is_deleted == False
                )
                .all()
            )
            
        return self._student_repo.get_by_department_and_semester(
            department_id=subject.department_id,
            semester=subject.semester
        )


# ══════════════════════════════════════════════════════════════
# TEACHER SERVICE
# ══════════════════════════════════════════════════════════════

class TeacherService(IService):
    """Teacher service — creates both User and Teacher records."""

    def __init__(self, db: Session):
        self._teacher_repo = TeacherRepository(db)
        self._user_repo = UserRepository(db)
        self._role_repo = RoleRepository(db)
        self._db = db

    def get(self, id: int):
        teacher = self._teacher_repo.get_by_id(id)
        if not teacher:
            raise NotFoundException("Teacher", id)
        return teacher

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        skip = (page - 1) * page_size
        if search:
            items = self._teacher_repo.search(
                ["employee_id", "faculty_id"], search, skip, page_size
            )
            total = self._teacher_repo.search_count(["employee_id", "faculty_id"], search)
        else:
            items = self._teacher_repo.get_all(skip, page_size, sort_by, sort_order)
            total = self._teacher_repo.count()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_filtered_teachers(self, course_id: int = None, department_id: int = None):
        return self._teacher_repo.get_filtered_teachers(course_id, department_id)

    def generate_faculty_id(self, joining_year: int) -> str:
        from app.models.teacher import Teacher
        from sqlalchemy import desc
        
        yy = str(joining_year)[-2:]
        prefix = f"FC{yy}"
        
        last_teacher = (
            self._db.query(Teacher)
            .filter(Teacher.faculty_id.like(f"{prefix}%"))
            .order_by(desc(Teacher.faculty_id))
            .first()
        )
        
        if last_teacher and last_teacher.faculty_id:
            try:
                last_seq = int(last_teacher.faculty_id[-6:])
                next_seq = last_seq + 1
            except ValueError:
                next_seq = 1
        else:
            next_seq = 1
            
        return f"{prefix}{next_seq:06d}"

    def create(self, data: Dict[str, Any]):
        if not data.get("employee_id"):
            last_teacher = self._db.query(Teacher).order_by(Teacher.id.desc()).first()
            next_seq = (last_teacher.id + 1) if last_teacher else 1
            data["employee_id"] = f"EMP-{datetime.now().year}-{next_seq:04d}"
        elif self._teacher_repo.get_by_employee_id(data.get("employee_id", "")):
            raise ConflictException(detail="Employee ID already exists")
            
        if self._user_repo.get_by_email(data.get("email", "")):
            raise ConflictException(detail="Email already registered")

        user_data = {
            "email": data.pop("email"),
            "username": data.pop("username"),
            "hashed_password": PasswordHasher.hash_password(data.pop("password")),
            "full_name": data.pop("full_name"),
            "phone": data.pop("phone", None),
            "gender": data.pop("gender", None),
        }
        user = self._user_repo.create(user_data)

        teacher_role = self._role_repo.get_by_name("teacher")
        if teacher_role:
            self._user_repo.assign_role(user.id, teacher_role.id)

        import datetime
        joining_date = data.get("joining_date")
        if joining_date:
            try:
                if isinstance(joining_date, str):
                    year = datetime.datetime.strptime(joining_date, "%Y-%m-%d").year
                else:
                    year = joining_date.year
            except:
                year = datetime.datetime.now().year
        else:
            year = datetime.datetime.now().year
            
        data["faculty_id"] = self.generate_faculty_id(year)

        data["user_id"] = user.id
        teacher = self._teacher_repo.create(data)
        self._db.refresh(teacher)
        return teacher

    def update(self, id: int, data: Dict[str, Any]):
        teacher = self._teacher_repo.get_by_id(id)
        if not teacher:
            raise NotFoundException("Teacher", id)

        user_fields = {}
        for field in ["full_name", "phone"]:
            if field in data and data[field] is not None:
                user_fields[field] = data.pop(field)
        if user_fields:
            self._user_repo.update(teacher.user_id, user_fields)

        update_data = {k: v for k, v in data.items() if v is not None}
        if update_data:
            self._teacher_repo.update(id, update_data)

        self._db.refresh(teacher)
        return teacher

    def delete(self, id: int) -> bool:
        teacher = self._teacher_repo.get_by_id(id)
        if not teacher:
            return False
        self._user_repo.soft_delete(teacher.user_id)
        return self._teacher_repo.soft_delete(id)


# ══════════════════════════════════════════════════════════════
# COURSE SERVICE
# ══════════════════════════════════════════════════════════════

class CourseService(IService):
    def __init__(self, db: Session):
        self._course_repo = CourseRepository(db)
        self._db = db

    def get(self, id: int):
        course = self._course_repo.get_by_id(id)
        if not course:
            raise NotFoundException("Course", id)
        return course

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        skip = (page - 1) * page_size
        if search:
            items = self._course_repo.search(["name", "code"], search, skip, page_size)
            total = self._course_repo.search_count(["name", "code"], search)
        else:
            items = self._course_repo.get_all(skip, page_size, sort_by, sort_order)
            total = self._course_repo.count()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        if self._course_repo.get_by_code(data.get("code", "")):
            raise ConflictException(detail="Course code already exists")
        return self._course_repo.create(data)

    def update(self, id: int, data: Dict[str, Any]):
        update_data = {k: v for k, v in data.items() if v is not None}
        result = self._course_repo.update(id, update_data)
        if not result:
            raise NotFoundException("Course", id)
        return result

    def delete(self, id: int) -> bool:
        course = self._course_repo.get_by_id(id)
        if not course:
            return False
        # Cascade soft delete to all departments
        for dept in course.departments.filter_by(is_deleted=False).all():
            DepartmentService(self._db).delete(dept.id)
        return self._course_repo.soft_delete(id)


# ══════════════════════════════════════════════════════════════
# DEPARTMENT SERVICE
# ══════════════════════════════════════════════════════════════

class DepartmentService(IService):
    def __init__(self, db: Session):
        self._dept_repo = DepartmentRepository(db)
        self._db = db

    def get(self, id: int):
        dept = self._dept_repo.get_by_id(id)
        if not dept:
            raise NotFoundException("Department", id)
        return dept

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        skip = (page - 1) * page_size
        if search:
            items = self._dept_repo.search(["name", "code"], search, skip, page_size)
            total = self._dept_repo.search_count(["name", "code"], search)
        else:
            items = self._dept_repo.get_all(skip, page_size, sort_by, sort_order)
            total = self._dept_repo.count()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        if self._dept_repo.get_by_code(data.get("code", "")):
            raise ConflictException(detail="Department code already exists")
        return self._dept_repo.create(data)

    def update(self, id: int, data: Dict[str, Any]):
        update_data = {k: v for k, v in data.items() if v is not None}
        result = self._dept_repo.update(id, update_data)
        if not result:
            raise NotFoundException("Department", id)
        return result

    def delete(self, id: int) -> bool:
        dept = self._dept_repo.get_by_id(id)
        if not dept:
            return False
        # Cascade soft delete to all subjects
        for subject in dept.subjects.filter_by(is_deleted=False).all():
            SubjectService(self._db).delete(subject.id)
            
        # Cascade soft delete to all students
        for student in dept.students.filter_by(is_deleted=False).all():
            StudentService(self._db).delete(student.id)
            
        # Cascade soft delete to all teachers
        for teacher in dept.teachers.filter_by(is_deleted=False).all():
            TeacherService(self._db).delete(teacher.id)
            
        return self._dept_repo.soft_delete(id)

    def assign_hod(self, department_id: int, teacher_id: int):
        from app.models.teacher import Teacher
        from app.models.user import UserRole, Role
        
        dept = self._dept_repo.get_by_id(department_id)
        if not dept:
            raise NotFoundException("Department", department_id)
            
        teacher = self._db.query(Teacher).filter(Teacher.id == teacher_id).first()
        if not teacher:
            raise NotFoundException("Teacher", teacher_id)
            
        # Ensure teacher belongs to the department
        if teacher.department_id != department_id:
            raise ConflictException("Teacher does not belong to this department")
            
        hod_role = self._db.query(Role).filter(Role.name == "hod").first()
        if not hod_role:
            raise NotFoundException("Role", "hod")
            
        # 1. Remove hod role from current HOD if exists
        if dept.hod_id and dept.hod_id != teacher_id:
            old_hod = self._db.query(Teacher).filter(Teacher.id == dept.hod_id).first()
            if old_hod:
                old_ur = self._db.query(UserRole).filter(
                    UserRole.user_id == old_hod.user_id,
                    UserRole.role_id == hod_role.id
                ).first()
                if old_ur:
                    self._db.delete(old_ur)
                    
        # 2. Assign hod role to new HOD
        new_ur = self._db.query(UserRole).filter(
            UserRole.user_id == teacher.user_id,
            UserRole.role_id == hod_role.id
        ).first()
        if not new_ur:
            new_ur = UserRole(user_id=teacher.user_id, role_id=hod_role.id)
            self._db.add(new_ur)
            
        # 3. Update department
        dept.hod_id = teacher_id
        self._db.commit()
        return True


# ══════════════════════════════════════════════════════════════
# SUBJECT SERVICE
# ══════════════════════════════════════════════════════════════

class SubjectService(IService):
    def __init__(self, db: Session):
        self._subject_repo = SubjectRepository(db)
        self._db = db

    def get(self, id: int):
        subject = self._subject_repo.get_by_id(id)
        if not subject:
            raise NotFoundException("Subject", id)
        return subject

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        skip = (page - 1) * page_size
        if search:
            items = self._subject_repo.search(["name", "code"], search, skip, page_size)
            total = self._subject_repo.search_count(["name", "code"], search)
        else:
            items = self._subject_repo.get_all(skip, page_size, sort_by, sort_order)
            total = self._subject_repo.count()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        if self._subject_repo.get_by_code(data.get("code", "")):
            raise ConflictException(detail="Subject code already exists")
        return self._subject_repo.create(data)

    def update(self, id: int, data: Dict[str, Any]):
        update_data = {k: v for k, v in data.items() if v is not None}
        result = self._subject_repo.update(id, update_data)
        if not result:
            raise NotFoundException("Subject", id)
        return result

    def delete(self, id: int) -> bool:
        return self._subject_repo.soft_delete(id)

    def assign_teacher(self, subject_id: int, teacher_id: int, section: str = None):
        return self._subject_repo.assign_teacher(subject_id, teacher_id, section)

    def get_filtered_subjects(self, department_id: int = None, semester: int = None):
        if department_id:
            return self._subject_repo.get_by_department(department_id, semester)
        return self._subject_repo.get_all()


# ══════════════════════════════════════════════════════════════
# ATTENDANCE SERVICE
# ══════════════════════════════════════════════════════════════

class AttendanceService(IService):
    def __init__(self, db: Session):
        self._attendance_repo = AttendanceRepository(db)
        self._db = db

    def get(self, id: int):
        att = self._attendance_repo.get_by_id(id)
        if not att:
            raise NotFoundException("Attendance", id)
        return att

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        skip = (page - 1) * page_size
        items = self._attendance_repo.get_all(skip, page_size, sort_by, sort_order)
        total = self._attendance_repo.count()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        return self._attendance_repo.create(data)

    def bulk_create(self, subject_id: int, att_date: date, records: list, teacher_id: int = None):
        """Bulk create or update attendance for a class."""
        created_or_updated = []
        for record in records:
            existing = self._attendance_repo.get_by_student_subject_date(record["student_id"], subject_id, att_date)
            if existing:
                update_data = {
                    "status": record.get("status", "present"),
                    "teacher_id": teacher_id,
                    "remarks": record.get("remarks"),
                }
                created_or_updated.append(self._attendance_repo.update(existing.id, update_data))
            else:
                att_data = {
                    "student_id": record["student_id"],
                    "subject_id": subject_id,
                    "date": att_date,
                    "status": record.get("status", "present"),
                    "teacher_id": teacher_id,
                    "remarks": record.get("remarks"),
                }
                created_or_updated.append(self._attendance_repo.create(att_data))
        return created_or_updated

    def update(self, id: int, data: Dict[str, Any]):
        return self._attendance_repo.update(id, data)

    def delete(self, id: int) -> bool:
        return self._attendance_repo.soft_delete(id)

    def get_student_stats(self, student_id: int):
        return self._attendance_repo.get_student_attendance_stats(student_id)


# ══════════════════════════════════════════════════════════════
# MARKS SERVICE
# ══════════════════════════════════════════════════════════════

class MarksService(IService):
    def __init__(self, db: Session):
        self._marks_repo = MarksRepository(db)
        self._db = db

    def get(self, id: int):
        marks = self._marks_repo.get_by_id(id)
        if not marks:
            raise NotFoundException("Marks", id)
        return marks

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        skip = (page - 1) * page_size
        items = self._marks_repo.get_all(skip, page_size, sort_by, sort_order)
        total = self._marks_repo.count()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        if data.get("marks_obtained", 0) > data.get("max_marks", 100):
            raise ValidationException("Marks obtained cannot exceed maximum marks")
        return self._marks_repo.create(data)

    def update(self, id: int, data: Dict[str, Any]):
        update_data = {k: v for k, v in data.items() if v is not None}
        return self._marks_repo.update(id, update_data)

    def delete(self, id: int) -> bool:
        return self._marks_repo.soft_delete(id)

    def get_student_marks(self, student_id: int, semester: int = None):
        return self._marks_repo.get_student_marks(student_id, semester)


# ══════════════════════════════════════════════════════════════
# FEE SERVICE
# ══════════════════════════════════════════════════════════════

class FeeService(IService):
    def __init__(self, db: Session):
        self._fee_repo = FeeRepository(db)
        self._db = db

    def get(self, id: int):
        fee = self._fee_repo.get_by_id(id)
        if not fee:
            raise NotFoundException("Fee", id)
        return fee

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        skip = (page - 1) * page_size
        items = self._fee_repo.get_all(skip, page_size, sort_by, sort_order)
        total = self._fee_repo.count()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        return self._fee_repo.create(data)

    def update(self, id: int, data: Dict[str, Any]):
        update_data = {k: v for k, v in data.items() if v is not None}
        return self._fee_repo.update(id, update_data)

    def delete(self, id: int) -> bool:
        return self._fee_repo.soft_delete(id)

    def record_payment(self, fee_id: int, paid_amount: float, payment_method: str = "cash", strategy_type: str = "standard"):
        """Record a fee payment using Strategy & Observer patterns."""
        from app.core.events import EventDispatcher, FeePaidEvent
        from app.services.fee_strategies import StandardFeeStrategy, LatePenaltyStrategy, ScholarshipStrategy

        fee = self.get(fee_id)
        
        # Strategy Pattern: Select appropriate calculation strategy
        if strategy_type == "late_penalty":
            strategy = LatePenaltyStrategy()
        elif strategy_type == "scholarship":
            strategy = ScholarshipStrategy()
        else:
            strategy = StandardFeeStrategy()
            
        calc_result = strategy.calculate(fee, paid_amount)
        
        receipt = f"RCP-{uuid.uuid4().hex[:8].upper()}"

        update_data = {
            "paid_amount": calc_result["paid_amount"],
            "payment_method": payment_method,
            "receipt_number": receipt,
            "paid_date": date.today(),
            "status": calc_result["status"],
        }
        
        if "remarks" in calc_result:
            update_data["remarks"] = calc_result["remarks"]

        self._fee_repo.update(fee_id, update_data)
        self._db.refresh(fee)
        
        # Observer Pattern: Dispatch event to decoupled listeners
        EventDispatcher.dispatch(FeePaidEvent(
            fee_id=fee.id,
            student_id=fee.student_id,
            paid_amount=paid_amount,
            status=update_data["status"],
            receipt=receipt
        ))
        
        return fee

    def get_pending_fees(self):
        return self._fee_repo.get_pending_fees()

    def get_student_fees(self, student_id: int):
        return self._fee_repo.get_student_fees(student_id)

    def get_filtered_fees(self, course_id: int = None, department_id: int = None, semester: int = None, search: str = None):
        return self._fee_repo.get_filtered_fees(course_id, department_id, semester, search)


# ══════════════════════════════════════════════════════════════
# LIBRARY SERVICE
# ══════════════════════════════════════════════════════════════

class LibraryService(IService):
    def __init__(self, db: Session):
        self._book_repo = LibraryBookRepository(db)
        self._issue_repo = BookIssueRepository(db)
        self._db = db

    def get(self, id: int):
        book = self._book_repo.get_by_id(id)
        if not book:
            raise NotFoundException("Book", id)
        return book

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        skip = (page - 1) * page_size
        if search:
            items = self._book_repo.search(
                ["title", "author", "isbn", "category"], search, skip, page_size
            )
            total = self._book_repo.search_count(
                ["title", "author", "isbn", "category"], search
            )
        else:
            items = self._book_repo.get_all(skip, page_size, sort_by, sort_order)
            total = self._book_repo.count()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        data["available_copies"] = data.get("total_copies", 1)
        return self._book_repo.create(data)

    def update(self, id: int, data: Dict[str, Any]):
        update_data = {k: v for k, v in data.items() if v is not None}
        return self._book_repo.update(id, update_data)

    def delete(self, id: int) -> bool:
        return self._book_repo.soft_delete(id)

    def issue_book(self, book_id: int, student_id: int, due_date: date):
        book = self.get(book_id)
        if book.available_copies <= 0:
            raise ValidationException("No copies available for issue")

        issue_data = {
            "book_id": book_id,
            "student_id": student_id,
            "issue_date": date.today(),
            "due_date": due_date,
            "status": "issued",
        }
        issue = self._issue_repo.create(issue_data)

        # Decrement available copies
        self._book_repo.update(book_id, {"available_copies": book.available_copies - 1})
        return issue

    def return_book(self, issue_id: int, fine: int = 0):
        issue = self._issue_repo.get_by_id(issue_id)
        if not issue:
            raise NotFoundException("BookIssue", issue_id)

        self._issue_repo.update(issue_id, {
            "return_date": date.today(),
            "status": "returned",
            "fine_amount": fine,
        })

        # Increment available copies
        book = self._book_repo.get_by_id(issue.book_id)
        if book:
            self._book_repo.update(book.id, {"available_copies": book.available_copies + 1})

        self._db.refresh(issue)
        return issue

    def get_active_issues(self, student_id: int = None):
        return self._issue_repo.get_active_issues(student_id)

    def get_dashboard_metrics(self):
        from sqlalchemy import func
        from app.models.library import LibraryBook, BookIssue
        
        total_books = self._db.query(func.sum(LibraryBook.total_copies)).filter(LibraryBook.is_deleted == False).scalar() or 0
        available_books = self._db.query(func.sum(LibraryBook.available_copies)).filter(LibraryBook.is_deleted == False).scalar() or 0
        
        active_issues = self._db.query(func.count(BookIssue.id)).filter(BookIssue.status == "issued", BookIssue.is_deleted == False).scalar() or 0
        
        # Calculate overdue issues
        overdue_issues = self._db.query(func.count(BookIssue.id)).filter(
            BookIssue.status == "issued", 
            BookIssue.due_date < date.today(),
            BookIssue.is_deleted == False
        ).scalar() or 0
        
        return {
            "total_books": total_books,
            "available_books": available_books,
            "active_issues": active_issues,
            "overdue_issues": overdue_issues
        }


# ══════════════════════════════════════════════════════════════
# AUDIT SERVICE
# ══════════════════════════════════════════════════════════════

class AuditService:
    """Audit logging service."""

    def __init__(self, db: Session):
        self._audit_repo = AuditLogRepository(db)

    def log(self, user_id: int, action: str, resource: str,
            resource_id: int = None, details: str = None,
            old_values: dict = None, new_values: dict = None,
            ip_address: str = None, user_agent: str = None):
        return self._audit_repo.create({
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "details": details,
            "old_values": old_values,
            "new_values": new_values,
            "ip_address": ip_address,
            "user_agent": user_agent,
        })

# ══════════════════════════════════════════════════════════════
# TIMETABLE GRID SERVICE
# ══════════════════════════════════════════════════════════════

class TimetableGridService:
    def __init__(self, db: Session):
        from app.repositories.concrete import TimetableVersionRepository, TimetableSlotRepository
        self._version_repo = TimetableVersionRepository(db)
        self._slot_repo = TimetableSlotRepository(db)
        self._db = db

    def get_version(self, department_id: int, semester: int):
        return self._version_repo.get_by_department_semester(department_id, semester)
        
    def get_pending_versions(self):
        return self._version_repo.get_pending()
        
    def get_slots(self, version_id: int):
        return self._slot_repo.get_by_version(version_id)
        
    def save_timetable(self, data: dict, user_id: int):
        """
        data = {
            "department_id": 1,
            "course_id": 1,
            "semester": 1,
            "action": "draft" | "submit",
            "slots": [
                {"day_of_week": 1, "slot_index": 1, "subject_id": 1, "teacher_id": 2},
                ...
            ]
        }
        """
        department_id = data["department_id"]
        semester = data["semester"]
        
        # Upsert Version
        version = self.get_version(department_id, semester)
        if not version:
            version = self._version_repo.create({
                "department_id": department_id,
                "course_id": data["course_id"],
                "semester": semester,
                "status": "pending" if data.get("action") == "submit" else "draft",
                "submitted_by_id": user_id
            })
        else:
            update_data = {
                "status": "pending" if data.get("action") == "submit" else "draft",
                "submitted_by_id": user_id
            }
            self._version_repo.update(version.id, update_data)
            
        # Clear existing slots
        existing_slots = self.get_slots(version.id)
        for s in existing_slots:
            self._slot_repo.hard_delete(s.id)
            
        # Create new slots
        slots_data = data.get("slots", [])
        for slot in slots_data:
            if slot.get("is_free"):
                self._slot_repo.create({
                    "version_id": version.id,
                    "day_of_week": slot["day_of_week"],
                    "slot_index": slot["slot_index"],
                    "subject_id": None,
                    "teacher_id": None
                })
            elif slot.get("subject_id") and slot.get("teacher_id"):
                self._slot_repo.create({
                    "version_id": version.id,
                    "day_of_week": slot["day_of_week"],
                    "slot_index": slot["slot_index"],
                    "subject_id": slot["subject_id"],
                    "teacher_id": slot["teacher_id"]
                })
                
        return version

    def update_status(self, version_id: int, status: str, user_id: int):
        update_data = {"status": status}
        if status == "approved":
            update_data["approved_by_id"] = user_id
        return self._version_repo.update(version_id, update_data)

    def get_user_activity(self, user_id: int, limit: int = 50):
        return self._audit_repo.get_by_user(user_id, limit)
