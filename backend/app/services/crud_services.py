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
    MarksRepository, LibraryBookRepository,
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
        from app.utils.serializer import serialize_sqlalchemy_obj
        return {"items": serialize_sqlalchemy_obj(items), "total": total, "page": page, "page_size": page_size}

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
        user = self._user_repo.get_by_id(id)
        if not user:
            return False
        self._db.delete(user)
        self._db.commit()
        return True


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

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc", department_id=None, course_id=None, branch_id=None, allowed_student_ids=None):
        skip = (page - 1) * page_size
        from sqlalchemy import or_
        from app.models.user import User
        query = self._db.query(Student).join(User).filter(Student.is_deleted == False)
        if allowed_student_ids is not None: query = query.filter(Student.id.in_(allowed_student_ids))
        if department_id: query = query.filter(Student.department_id == department_id)
        if course_id: query = query.filter(Student.course_id == course_id)
        if branch_id: query = query.filter(Student.branch_id == branch_id)
        if search:
            term = f"%{search}%"
            query = query.filter(or_(Student.student_id.ilike(term), Student.enrollment_number.ilike(term), User.full_name.ilike(term)))
        total = query.count()
        items = query.order_by(Student.id.desc()).offset(skip).limit(page_size).all()

        from app.utils.serializer import serialize_sqlalchemy_obj
        return {"items": serialize_sqlalchemy_obj(items), "total": total, "page": page, "page_size": page_size}

    def get_filtered_students(self, course_id: int = None, department_id: int = None, search: str = None):
        return self._student_repo.get_filtered_students(course_id, department_id, search)

    @staticmethod
    def _credential_code(value: str) -> str:
        import re
        code = re.sub(r"[^A-Za-z0-9]", "", value or "").upper()
        if not code:
            raise ValidationException("Course and branch codes must contain letters or numbers")
        return code

    def generate_student_id(self, admission_year: int, course, branch=None) -> str:
        """Allocate the next durable ID in a transaction-locked scope."""
        from app.models.student import StudentSequence

        branch_id = branch.id if branch else None
        branch_scope_key = branch_id or 0
        sequence = (
            self._db.query(StudentSequence)
            .filter(
                StudentSequence.admission_year == admission_year,
                StudentSequence.course_id == course.id,
                StudentSequence.branch_scope_key == branch_scope_key,
            )
            .with_for_update()
            .first()
        )
        if not sequence:
            sequence = StudentSequence(
                admission_year=admission_year,
                course_id=course.id,
                branch_id=branch_id,
                branch_scope_key=branch_scope_key,
                last_sequence=0,
            )
            self._db.add(sequence)
            self._db.flush()
        sequence.last_sequence += 1
        self._db.flush()

        course_code = self._credential_code(course.code)
        branch_code = self._credential_code(branch.code) if branch else ""
        return f"{str(admission_year)[-2:]}{course_code}{branch_code}{sequence.last_sequence:03d}"

    def create(self, data: Dict[str, Any]):
        # Generate student_id
        import datetime
        admission_year = data.get("admission_year")
        admission_date = data.get("admission_date")
        if admission_year:
            year = int(admission_year)
        elif admission_date:
            try:
                if isinstance(admission_date, str):
                    year = datetime.datetime.strptime(admission_date, "%Y-%m-%d").year
                else:
                    year = admission_date.year
            except:
                year = datetime.datetime.now().year
        else:
            year = datetime.datetime.now().year
            
        from app.models.course import Course
        from app.models.department import Department
        from app.models.academic import Branch
        dept = self._db.query(Department).filter(Department.id == data.get("department_id"), Department.is_deleted == False).first()
        course = self._db.query(Course).filter(Course.id == data.get("course_id"), Course.is_deleted == False).first()
        if not dept or not course:
            raise ValidationException("A valid department and course are required")
        if course.department_id != dept.id:
            raise ValidationException("Course does not belong to the selected department")
        branch = None
        if data.get("branch_id"):
            branch = self._db.query(Branch).filter(Branch.id == data["branch_id"], Branch.is_deleted == False).first()
            if not branch or branch.course_id != course.id:
                raise ValidationException("Branch does not belong to the selected course")
        student_id = self.generate_student_id(year, course, branch)

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
        data["initial_password"] = None

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
        
        user = self._user_repo.get_by_id(student.user_id)
        self._db.delete(student)
        self._db.flush()
        if user:
            self._db.delete(user)
        self._db.commit()
        return True

    def delete_all(self) -> int:
        items = self._student_repo.get_all(0, 10000)
        count = 0
        for item in items:
            if self.delete(item.id):
                count += 1
        return count

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

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc", department_id=None, course_id=None, branch_id=None):
        skip = (page - 1) * page_size
        from sqlalchemy import or_
        from app.models.user import User
        from app.models.academic import Branch
        query = self._db.query(Teacher).join(User).outerjoin(Branch, Teacher.branch_id == Branch.id).filter(Teacher.is_deleted == False)
        if department_id: query = query.filter(Teacher.department_id == department_id)
        if course_id: query = query.filter(Branch.course_id == course_id)
        if branch_id: query = query.filter(Teacher.branch_id == branch_id)
        if search:
            term = f"%{search}%"
            query = query.filter(or_(Teacher.employee_id.ilike(term), Teacher.faculty_id.ilike(term), User.full_name.ilike(term)))
        total = query.count()
        items = query.order_by(Teacher.id.desc()).offset(skip).limit(page_size).all()
        from app.utils.serializer import serialize_sqlalchemy_obj
        return {"items": serialize_sqlalchemy_obj(items), "total": total, "page": page, "page_size": page_size}

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
        designation = data.get("designation")
        if designation not in ["Professor", "Assistant Professor", "Associate Professor"]:
            raise ValidationException("Designation must be Professor, Assistant Professor, or Associate Professor")

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
            
        faculty_id = self.generate_faculty_id(year)

        if not data.get("employee_id"):
            last_teacher = self._db.query(Teacher).order_by(Teacher.id.desc()).first()
            next_seq = (last_teacher.id + 1) if last_teacher else 1
            from datetime import datetime as dt
            data["employee_id"] = f"EMP-{dt.now().year}-{next_seq:04d}"
        elif self._teacher_repo.get_by_employee_id(data.get("employee_id", "")):
            raise ConflictException(detail="Employee ID already exists")

        full_name = data.get("full_name", "Teacher").strip()
        first_name = full_name.split()[0].lower() if full_name else "teacher"
        import re
        first_name = re.sub(r'[^a-z0-9]', '', first_name)
        faculty_id_lower = faculty_id.lower()
        institutional_email = f"{first_name}.{faculty_id_lower}@cms.edu"
            
        if self._user_repo.get_by_email(institutional_email):
            raise ConflictException(detail="Generated email already registered")

        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(10))
        username = faculty_id_lower

        user_data = {
            "email": institutional_email,
            "username": username,
            "hashed_password": PasswordHasher.hash_password(password),
            "full_name": full_name,
            "phone": data.pop("phone", None),
            "gender": data.pop("gender", None),
        }
        
        # Remove dummy inputs from frontend if present
        data.pop("email", None)
        data.pop("username", None)
        data.pop("password", None)
        data.pop("full_name", None)

        user = self._user_repo.create(user_data)

        teacher_role = self._role_repo.get_by_name("teacher")
        if teacher_role:
            self._user_repo.assign_role(user.id, teacher_role.id)

        data["faculty_id"] = faculty_id
        data["user_id"] = user.id
        teacher = self._teacher_repo.create(data)
        self._db.refresh(teacher)

        email_data = {
            "teacher_name": full_name,
            "institutional_email": institutional_email,
            "faculty_id": faculty_id,
            "generated_password": password,
            "personal_email": data.get("email") # fallback if needed, but not used typically for teachers in this schema unless added. Assuming institutional is fine or we can pass None. Let's just pass what's needed.
        }
        return teacher, email_data

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
        user = self._user_repo.get_by_id(teacher.user_id)
        self._db.delete(teacher)
        self._db.flush()
        if user:
            self._db.delete(user)
        self._db.commit()
        return True

    def delete_all(self) -> int:
        items = self._teacher_repo.get_all(0, 10000)
        count = 0
        for item in items:
            if self.delete(item.id):
                count += 1
        return count


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

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc", department_id=None, branch_id=None):
        skip = (page - 1) * page_size
        from sqlalchemy import or_
        from app.models.course import Course
        query = self._db.query(Course).filter(Course.is_deleted == False)
        if department_id: query = query.filter(Course.department_id == department_id)
        if branch_id:
            from app.models.academic import Branch
            query = query.join(Branch).filter(Branch.id == branch_id)
        if search:
            term = f"%{search}%"; query = query.filter(or_(Course.name.ilike(term), Course.code.ilike(term)))
        total = query.count(); items = query.order_by(Course.id.desc()).offset(skip).limit(page_size).all()
        from app.utils.serializer import serialize_sqlalchemy_obj
        return {"items": serialize_sqlalchemy_obj(items), "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        from app.models.department import Department
        department = self._db.query(Department).filter(
            Department.id == data.get("department_id"), Department.is_deleted == False
        ).first()
        if not department:
            raise ValidationException("A valid department is required")
        if self._course_repo.get_by_code(data.get("code", "")):
            raise ConflictException(detail="Course code already exists")
        from sqlalchemy.exc import IntegrityError
        try:
            return self._course_repo.create(data)
        except IntegrityError as e:
            self._db.rollback()
            raise ConflictException(detail="A course with this name or code already exists")

    def update(self, id: int, data: Dict[str, Any]):
        update_data = {k: v for k, v in data.items() if v is not None}
        from sqlalchemy.exc import IntegrityError
        try:
            result = self._course_repo.update(id, update_data)
        except IntegrityError as e:
            self._db.rollback()
            raise ConflictException(detail="A course with this name or code already exists")
        if not result:
            raise NotFoundException("Course", id)
        return result

    def delete(self, id: int) -> bool:
        course = self._course_repo.get_by_id(id)
        if not course:
            return False
        from app.models.academic import Branch
        user_ids = [row[0] for row in self._db.query(Student.user_id).filter(Student.course_id == id).all()]
        user_ids += [row[0] for row in self._db.query(Teacher.user_id).join(Branch, Teacher.branch_id == Branch.id).filter(Branch.course_id == id).all()]
        self._db.delete(course)
        self._db.flush()
        if user_ids:
            self._db.query(User).filter(User.id.in_(set(user_ids))).delete(synchronize_session=False)
        self._db.commit()
        return True

    def delete_all(self) -> int:
        items = self._course_repo.get_all(0, 10000)
        count = 0
        for item in items:
            if self.delete(item.id):
                count += 1
        return count


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

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc", branch_id=None):
        skip = (page - 1) * page_size
        from app.models.department import Department
        query = self._db.query(Department).filter(Department.is_deleted == False)
        if branch_id:
            from app.models.academic import Branch
            from app.models.course import Course
            query = query.join(Course).join(Branch).filter(Branch.id == branch_id)
        if search:
            from sqlalchemy import or_
            term = f"%{search}%"
            query = query.filter(or_(Department.name.ilike(term), Department.code.ilike(term)))
        
        total = query.count()
        items = query.order_by(Department.id.desc()).offset(skip).limit(page_size).all()
        from app.utils.serializer import serialize_sqlalchemy_obj
        return {"items": serialize_sqlalchemy_obj(items), "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        if not data.get("code"):
            name = data.get("name", "DEPT")
            words = name.split()
            if len(words) > 1:
                code_base = "".join(w[0].upper() for w in words if w.lower() not in ["of", "and", "the", "for"])
            else:
                code_base = name[:3].upper()
            
            code_base = code_base[:15]
            code = code_base
            counter = 1
            while self._dept_repo.get_by_code(code):
                code = f"{code_base}{counter}"
                counter += 1
            data["code"] = code
            
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
        user_ids = [row[0] for row in self._db.query(Student.user_id).filter(Student.department_id == id).all()]
        user_ids += [row[0] for row in self._db.query(Teacher.user_id).filter(Teacher.department_id == id).all()]
        dept.hod_id = None
        self._db.flush()
        self._db.delete(dept)
        self._db.flush()
        if user_ids:
            self._db.query(User).filter(User.id.in_(set(user_ids))).delete(synchronize_session=False)
        self._db.commit()
        return True

    def delete_all(self) -> int:
        items = self._dept_repo.get_all(0, 10000)
        count = 0
        for item in items:
            if self.delete(item.id):
                count += 1
        return count

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

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc", department_id=None, allowed_subject_ids=None, branch_id=None):
        skip = (page - 1) * page_size
        from sqlalchemy import or_
        from app.models.subject import Subject
        query = self._db.query(Subject).filter(Subject.is_deleted == False)
        if allowed_subject_ids is not None: query = query.filter(Subject.id.in_(allowed_subject_ids))
        if department_id: query = query.filter(Subject.department_id == department_id)
        if branch_id:
            from app.models.academic import CurriculumSubject
            query = query.join(CurriculumSubject).filter(CurriculumSubject.branch_id == branch_id)
        if search:
            term=f"%{search}%"; query=query.filter(or_(Subject.name.ilike(term), Subject.code.ilike(term)))
        total=query.count(); items=query.order_by(Subject.id.desc()).offset(skip).limit(page_size).all()
        from app.utils.serializer import serialize_sqlalchemy_obj
        return {"items": serialize_sqlalchemy_obj(items), "total": total, "page": page, "page_size": page_size}

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
        subject = self._subject_repo.get_by_id(id)
        if not subject:
            return False
        self._db.delete(subject)
        self._db.commit()
        return True

    def delete_all(self) -> int:
        items = self._subject_repo.get_all(0, 10000)
        count = 0
        for item in items:
            if self.delete(item.id):
                count += 1
        return count

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

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc", department_id=None, course_id=None, branch_id=None, student_id=None, subject_id=None, allowed_student_ids=None, allowed_subject_ids=None):
        from app.models.attendance import Attendance
        query = self._db.query(Attendance).join(Student).filter(Attendance.is_deleted == False)
        if allowed_student_ids is not None: query=query.filter(Attendance.student_id.in_(allowed_student_ids))
        if allowed_subject_ids is not None: query=query.filter(Attendance.subject_id.in_(allowed_subject_ids))
        if department_id: query=query.filter(Student.department_id == department_id)
        if course_id: query=query.filter(Student.course_id == course_id)
        if branch_id: query=query.filter(Student.branch_id == branch_id)
        if student_id: query=query.filter(Attendance.student_id == student_id)
        if subject_id: query=query.filter(Attendance.subject_id == subject_id)
        total=query.count(); items=query.order_by(Attendance.id.desc()).offset((page-1)*page_size).limit(page_size).all()
        from app.utils.serializer import serialize_sqlalchemy_obj
        return {"items": serialize_sqlalchemy_obj(items), "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        return self._attendance_repo.create(data)

    def bulk_create(
        self, subject_id: int, att_date: date, records: list,
        teacher_id: int = None, section_id: int = None,
        faculty_assignment_id: int = None,
    ):
        """Bulk create or update attendance for a class."""
        created_or_updated = []
        for record in records:
            existing = self._attendance_repo.get_by_student_subject_date(record["student_id"], subject_id, att_date)
            if existing:
                update_data = {
                    "status": record.get("status", "present"),
                    "teacher_id": teacher_id,
                    "section_id": section_id,
                    "faculty_assignment_id": faculty_assignment_id,
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
                    "section_id": section_id,
                    "faculty_assignment_id": faculty_assignment_id,
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

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc", department_id=None, course_id=None, branch_id=None, student_id=None, subject_id=None, allowed_student_ids=None, allowed_subject_ids=None):
        from app.models.marks import Marks
        query=self._db.query(Marks).join(Student).filter(Marks.is_deleted == False)
        if allowed_student_ids is not None: query=query.filter(Marks.student_id.in_(allowed_student_ids))
        if allowed_subject_ids is not None: query=query.filter(Marks.subject_id.in_(allowed_subject_ids))
        if department_id: query=query.filter(Student.department_id == department_id)
        if course_id: query=query.filter(Student.course_id == course_id)
        if branch_id: query=query.filter(Student.branch_id == branch_id)
        if student_id: query=query.filter(Marks.student_id == student_id)
        if subject_id: query=query.filter(Marks.subject_id == subject_id)
        total=query.count(); items=query.order_by(Marks.id.desc()).offset((page-1)*page_size).limit(page_size).all()
        from app.utils.serializer import serialize_sqlalchemy_obj
        return {"items": serialize_sqlalchemy_obj(items), "total": total, "page": page, "page_size": page_size}

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
# LIBRARY SERVICE
# ══════════════════════════════════════════════════════════════

class LibraryService(IService):
    def __init__(self, db: Session):
        from app.repositories.concrete import (
            LibraryBookRepository, BookIssueRepository, LibraryMemberRepository,
            LibraryAuthorRepository, LibraryPublisherRepository, BookCategoryRepository,
            BookReservationRepository, LibraryFineRepository
        )
        self._book_repo = LibraryBookRepository(db)
        self._issue_repo = BookIssueRepository(db)
        self._member_repo = LibraryMemberRepository(db)
        self._author_repo = LibraryAuthorRepository(db)
        self._publisher_repo = LibraryPublisherRepository(db)
        self._category_repo = BookCategoryRepository(db)
        self._reservation_repo = BookReservationRepository(db)
        self._fine_repo = LibraryFineRepository(db)
        self._db = db

    def get(self, id: int):
        book = self._book_repo.get_by_id(id)
        if not book:
            raise NotFoundException("Book", id)
        return book

    def list(self, page=1, page_size=10, search=None, sort_by="id", sort_order="desc"):
        from sqlalchemy import or_
        from sqlalchemy.orm import selectinload
        from app.models.library import LibraryBook, LibraryAuthor, LibraryPublisher, BookCategory
        skip = (page - 1) * page_size
        query = (
            self._db.query(LibraryBook)
            .outerjoin(LibraryAuthor, LibraryBook.author_id == LibraryAuthor.id)
            .outerjoin(LibraryPublisher, LibraryBook.publisher_id == LibraryPublisher.id)
            .outerjoin(BookCategory, LibraryBook.category_id == BookCategory.id)
            .options(
                selectinload(LibraryBook.author),
                selectinload(LibraryBook.publisher),
                selectinload(LibraryBook.category),
            )
            .filter(LibraryBook.is_deleted.is_(False))
        )
        if search:
            term = f"%{search}%"
            query = query.filter(or_(
                LibraryBook.title.ilike(term), LibraryBook.isbn.ilike(term),
                LibraryAuthor.name.ilike(term), LibraryPublisher.name.ilike(term),
                BookCategory.name.ilike(term),
            ))
        total = query.count()
        order_column = getattr(LibraryBook, sort_by, LibraryBook.id)
        query = query.order_by(order_column.desc() if sort_order == "desc" else order_column.asc())
        items = query.offset(skip).limit(page_size).all()
        from app.utils.serializer import serialize_sqlalchemy_obj
        return {"items": serialize_sqlalchemy_obj(items), "total": total, "page": page, "page_size": page_size}

    def create(self, data: Dict[str, Any]):
        data["available_copies"] = data.get("total_copies", 1)
        return self._book_repo.create(data)

    def update(self, id: int, data: Dict[str, Any]):
        update_data = {k: v for k, v in data.items() if v is not None}
        return self._book_repo.update(id, update_data)

    def delete(self, id: int) -> bool:
        return self._book_repo.soft_delete(id)

    def issue_book(self, book_id: int, member_id: int, due_date: date):
        book = self.get(book_id)
        if book.available_copies <= 0:
            raise ValidationException("No copies available for issue")

        issue_data = {
            "book_id": book_id,
            "member_id": member_id,
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

    def get_active_issues(self, member_id: int = None):
        return self._issue_repo.get_active_issues(member_id)

    def get_issues(self, member_id: int = None):
        from sqlalchemy.orm import selectinload
        from app.models.library import BookIssue, LibraryMember
        query = (
            self._db.query(BookIssue)
            .options(
                selectinload(BookIssue.book),
                selectinload(BookIssue.member).selectinload(LibraryMember.user),
            )
            .filter(BookIssue.is_deleted.is_(False))
        )
        if member_id is not None:
            query = query.filter(BookIssue.member_id == member_id)
        return query.order_by(BookIssue.issue_date.desc()).all()

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

    def get_version(
        self, department_id: int, course_id: int, semester: int,
        branch_id: int = None, section_id: int = None,
    ):
        return self._version_repo.get_by_academic_scope(
            department_id, course_id, semester, branch_id, section_id
        )
        
    def get_pending_versions(self):
        return self._version_repo.get_pending()
        
    def get_slots(self, version_id: int):
        return self._slot_repo.get_by_version(version_id)
        
    def get_all_versions(
        self, department_id: int, course_id: int, semester: int,
        branch_id: int = None, section_id: int = None,
    ):
        return self._version_repo.get_all_versions_by_scope(
            department_id, course_id, semester, branch_id, section_id
        )

    def save_timetable(self, data: dict, user_id: int):
        department_id = data["department_id"]
        course_id = data["course_id"]
        branch_id = data.get("branch_id")
        section_id = data.get("section_id")
        semester = data["semester"]
        
        # Get latest version
        latest_version = self.get_version(
            department_id, course_id, semester, branch_id, section_id
        )
        
        new_status = "pending" if data.get("action") == "submit" else "draft"
        
        if not latest_version:
            version = self._version_repo.create({
                "department_id": department_id,
                "course_id": course_id,
                "branch_id": branch_id,
                "section_id": section_id,
                "semester": semester,
                "version_number": 1,
                "status": new_status,
                "submitted_by_id": user_id
            })
        elif latest_version.status == "approved":
            # Create a new version
            version = self._version_repo.create({
                "department_id": department_id,
                "course_id": course_id,
                "branch_id": branch_id,
                "section_id": section_id,
                "semester": semester,
                "version_number": latest_version.version_number + 1,
                "status": new_status,
                "submitted_by_id": user_id
            })
        else:
            # Update in place
            update_data = {
                "status": new_status,
                "submitted_by_id": user_id
            }
            self._version_repo.update(latest_version.id, update_data)
            version = latest_version
            
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

    def get_teacher_schedule(self, teacher_id: int):
        from sqlalchemy.orm import joinedload
        from app.models.timetable_grid import TimetableSlot, TimetableVersion
        
        # 1. Fetch all versions
        all_versions = self._db.query(TimetableVersion).filter(
            TimetableVersion.is_deleted == False,
            TimetableVersion.status == "approved"
        ).all()
        
        # 2. Get latest approved version for each scope
        scope_latest_version = {}
        for v in all_versions:
            key = f"{v.course_id}-{v.branch_id}-{v.semester}-{v.section_id}"
            if key not in scope_latest_version or v.version_number > scope_latest_version[key].version_number:
                scope_latest_version[key] = v
                
        active_version_ids = {v.id for v in scope_latest_version.values()}
        
        if not active_version_ids:
            return []
            
        # 3. Fetch slots for this teacher from the active versions
        slots = self._db.query(TimetableSlot).options(
            joinedload(TimetableSlot.subject),
            joinedload(TimetableSlot.version).joinedload(TimetableVersion.branch),
            joinedload(TimetableSlot.version).joinedload(TimetableVersion.section)
        ).filter(
            TimetableSlot.teacher_id == teacher_id,
            TimetableSlot.version_id.in_(active_version_ids),
            TimetableSlot.is_deleted == False
        ).all()
        
        return slots

    def get_user_activity(self, user_id: int, limit: int = 50):
        return self._audit_repo.get_by_user(user_id, limit)
