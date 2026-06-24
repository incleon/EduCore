"""Business rules for academic hierarchy, curricula and subject allocation."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.academic import (
    AcademicSemester, Branch, Curriculum, CurriculumSubject, CurriculumVersion,
    ElectiveGroup, FacultyAssignment, Section, StudentElective, SubjectType,
)
from app.models.course import Course
from app.models.department import Department
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher


class AcademicStructureService:
    ELECTIVE_TYPES = {"ELECTIVE", "OPEN_ELECTIVE"}

    def __init__(self, db: Session):
        self.db = db

    def list_records(self, model, **filters):
        query = self.db.query(model).filter(model.is_deleted.is_(False))
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(model, key) == value)
        return query.order_by(model.id.desc()).all()

    def get_record(self, model, record_id: int, resource: str):
        record = self.db.query(model).filter(model.id == record_id, model.is_deleted.is_(False)).first()
        if not record:
            raise NotFoundException(resource, record_id)
        return record

    def update_record(self, model, record_id: int, data: dict, resource: str):
        record = self.get_record(model, record_id, resource)
        for key, value in data.items():
            setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete_record(self, model, record_id: int, resource: str):
        record = self.get_record(model, record_id, resource)
        user_ids = []
        if model is Branch:
            user_ids = [row[0] for row in self.db.query(Student.user_id).filter(Student.branch_id == record_id).all()]
            user_ids += [row[0] for row in self.db.query(Teacher.user_id).filter(Teacher.branch_id == record_id).all()]
        self.db.delete(record)
        self.db.flush()
        if user_ids:
            from app.models.user import User
            self.db.query(User).filter(User.id.in_(set(user_ids))).delete(synchronize_session=False)
        self.db.commit()

    def create_branch(self, data: dict):
        self.get_record(Course, data["course_id"], "Course")
        duplicate = self.db.query(Branch).filter(
            Branch.course_id == data["course_id"], Branch.code == data["code"], Branch.is_deleted.is_(False)
        ).first()
        if duplicate:
            raise ConflictException(detail="Branch code already exists in this program")
        return self._create(Branch, data)

    def update_branch(self, branch_id: int, data: dict):
        branch = self.get_record(Branch, branch_id, "Branch")
        if data.get("code"):
            duplicate = self.db.query(Branch).filter(
                Branch.course_id == branch.course_id, Branch.code == data["code"], Branch.id != branch_id,
                Branch.is_deleted.is_(False),
            ).first()
            if duplicate:
                raise ConflictException(detail="Branch code already exists in this program")
        return self.update_record(Branch, branch_id, data, "Branch")

    def create_curriculum(self, data: dict):
        course = self.get_record(Course, data["course_id"], "Course")
        branch = self._validate_branch_for_course(data.get("branch_id"), course.id)
        if self.db.query(Curriculum).filter(Curriculum.code == data["code"], Curriculum.is_deleted.is_(False)).first():
            raise ConflictException(detail="Curriculum code already exists")
        data["branch_id"] = branch.id if branch else None
        return self._create(Curriculum, data)

    def update_curriculum(self, curriculum_id: int, data: dict):
        curriculum = self.get_record(Curriculum, curriculum_id, "Curriculum")
        if "branch_id" in data:
            self._validate_branch_for_course(data.get("branch_id"), curriculum.course_id)
        return self.update_record(Curriculum, curriculum_id, data, "Curriculum")

    def create_curriculum_version(self, data: dict):
        curriculum = self.get_record(Curriculum, data["curriculum_id"], "Curriculum")
        duplicate = self.db.query(CurriculumVersion).filter(
            CurriculumVersion.curriculum_id == curriculum.id,
            CurriculumVersion.version_code == data["version_code"],
            CurriculumVersion.is_deleted.is_(False),
        ).first()
        if duplicate:
            raise ConflictException(detail="Version code already exists for this curriculum")
        self._validate_batch_range(data)
        if data.get("is_active"):
            data["status"] = "active"
            data["published_at"] = datetime.now(timezone.utc)
        return self._create(CurriculumVersion, data)

    def update_curriculum_version(self, version_id: int, data: dict):
        version = self.get_record(CurriculumVersion, version_id, "Curriculum version")
        merged = {
            "applicable_batch_start": data.get("applicable_batch_start", version.applicable_batch_start),
            "applicable_batch_end": data.get("applicable_batch_end", version.applicable_batch_end),
        }
        self._validate_batch_range(merged)
        if data.get("is_active") is True:
            data["status"] = "active"
            data["published_at"] = datetime.now(timezone.utc)
        return self.update_record(CurriculumVersion, version_id, data, "Curriculum version")

    def create_semester(self, data: dict):
        self.get_record(CurriculumVersion, data["curriculum_version_id"], "Curriculum version")
        duplicate = self.db.query(AcademicSemester).filter(
            AcademicSemester.curriculum_version_id == data["curriculum_version_id"],
            AcademicSemester.number == data["number"], AcademicSemester.is_deleted.is_(False),
        ).first()
        if duplicate:
            raise ConflictException(detail="Semester already exists in this curriculum version")
        return self._create(AcademicSemester, data)

    def create_section(self, data: dict):
        course = self.get_record(Course, data["course_id"], "Course")
        self._validate_branch_for_course(data.get("branch_id"), course.id)
        version = None
        if data.get("curriculum_version_id"):
            version = self.get_record(CurriculumVersion, data["curriculum_version_id"], "Curriculum version")
            if version.curriculum.course_id != course.id:
                raise ValidationException("Section curriculum must belong to the selected program")
        duplicate = self.db.query(Section).filter(
            Section.course_id == course.id, Section.branch_id == data.get("branch_id"),
            Section.semester_number == data["semester_number"], Section.academic_year == data["academic_year"],
            Section.code == data["code"], Section.is_deleted.is_(False),
        ).first()
        if duplicate:
            raise ConflictException(detail="Section already exists for this program, semester and year")
        return self._create(Section, data)

    def create_elective_group(self, data: dict):
        self.get_record(AcademicSemester, data["semester_id"], "Semester")
        duplicate = self.db.query(ElectiveGroup).filter(
            ElectiveGroup.semester_id == data["semester_id"], ElectiveGroup.code == data["code"],
            ElectiveGroup.is_deleted.is_(False),
        ).first()
        if duplicate:
            raise ConflictException(detail="Elective group code already exists in this semester")
        return self._create(ElectiveGroup, data)

    def add_curriculum_subject(self, data: dict):
        semester = self.get_record(AcademicSemester, data["semester_id"], "Semester")
        subject = self.get_record(Subject, data["subject_id"], "Subject")
        type_code = subject.subject_type.code if subject.subject_type else None
        if not type_code:
            raise ValidationException("Subject must have a subject classification before curriculum allocation")

        curriculum = semester.curriculum_version.curriculum
        branch = self._validate_branch_for_course(data.get("branch_id"), curriculum.course_id)
        if type_code == "COMMON" and branch:
            raise ValidationException("COMMON subjects cannot be restricted to a branch")
        if type_code == "SPECIALIZATION" and not branch:
            raise ValidationException("SPECIALIZATION subjects require a branch")

        group = None
        if data.get("elective_group_id"):
            group = self.get_record(ElectiveGroup, data["elective_group_id"], "Elective group")
            if group.semester_id != semester.id:
                raise ValidationException("Elective group must belong to the selected semester")
        if type_code in self.ELECTIVE_TYPES and not group:
            raise ValidationException("Elective subjects must belong to an elective group")
        if type_code not in self.ELECTIVE_TYPES and group:
            raise ValidationException("Only elective subjects may be placed in an elective group")

        duplicate = self.db.query(CurriculumSubject).filter(
            CurriculumSubject.semester_id == semester.id,
            CurriculumSubject.subject_id == subject.id,
            CurriculumSubject.branch_id == (branch.id if branch else None),
            CurriculumSubject.is_deleted.is_(False),
        ).first()
        if duplicate:
            raise ConflictException(detail="Subject already exists in this curriculum scope")
        data["branch_id"] = branch.id if branch else None
        return self._create(CurriculumSubject, data)

    def update_curriculum_subject(self, mapping_id: int, data: dict):
        mapping = self.get_record(CurriculumSubject, mapping_id, "Curriculum subject")
        merged = {
            "semester_id": mapping.semester_id,
            "subject_id": mapping.subject_id,
            "branch_id": data.get("branch_id", mapping.branch_id),
            "elective_group_id": data.get("elective_group_id", mapping.elective_group_id),
            "is_mandatory": data.get("is_mandatory", mapping.is_mandatory),
            "credits_override": data.get("credits_override", mapping.credits_override),
            "display_order": data.get("display_order", mapping.display_order),
        }
        # Reuse all classification and scope validation without creating a duplicate.
        subject = mapping.subject
        type_code = subject.subject_type.code if subject.subject_type else None
        curriculum = mapping.semester.curriculum_version.curriculum
        branch = self._validate_branch_for_course(merged.get("branch_id"), curriculum.course_id)
        if type_code == "COMMON" and branch:
            raise ValidationException("COMMON subjects cannot be restricted to a branch")
        if type_code == "SPECIALIZATION" and not branch:
            raise ValidationException("SPECIALIZATION subjects require a branch")
        if merged.get("elective_group_id"):
            group = self.get_record(ElectiveGroup, merged["elective_group_id"], "Elective group")
            if group.semester_id != mapping.semester_id:
                raise ValidationException("Elective group must belong to the selected semester")
        return self.update_record(CurriculumSubject, mapping_id, data, "Curriculum subject")

    def create_faculty_assignment(self, data: dict):
        teacher = self.get_record(Teacher, data["teacher_id"], "Faculty")
        mapping = self.get_record(CurriculumSubject, data["curriculum_subject_id"], "Curriculum subject")
        curriculum = mapping.semester.curriculum_version.curriculum
        if curriculum.course.department_id and teacher.department_id != curriculum.course.department_id:
            raise ValidationException("Faculty must belong to the program's department")
        if mapping.branch_id and teacher.branch_id not in (None, mapping.branch_id):
            raise ValidationException("Faculty specialization does not match the curriculum subject branch")
        if data.get("section_id"):
            section = self.get_record(Section, data["section_id"], "Section")
            if section.course_id != curriculum.course_id or (mapping.branch_id and section.branch_id != mapping.branch_id):
                raise ValidationException("Section does not match the curriculum subject scope")
        duplicate = self.db.query(FacultyAssignment).filter(
            FacultyAssignment.teacher_id == teacher.id,
            FacultyAssignment.curriculum_subject_id == mapping.id,
            FacultyAssignment.section_id == data.get("section_id"),
            FacultyAssignment.academic_year == data["academic_year"],
            FacultyAssignment.is_deleted.is_(False),
        ).first()
        if duplicate:
            raise ConflictException(detail="Faculty assignment already exists")
        return self._create(FacultyAssignment, data)

    def update_student_mapping(self, student_id: int, data: dict):
        student = self.get_record(Student, student_id, "Student")
        department = self.get_record(Department, data["department_id"], "Department")
        course = self.get_record(Course, data["course_id"], "Course")
        if course.department_id and course.department_id != department.id:
            raise ValidationException("Program does not belong to the selected department")
        branch = self._validate_branch_for_course(data.get("branch_id"), course.id)

        version = None
        if data.get("curriculum_version_id"):
            version = self._validate_student_curriculum(course.id, branch.id if branch else None, data["admission_year"], data["curriculum_version_id"])
        else:
            version = self.find_applicable_curriculum(course.id, branch.id if branch else None, data["admission_year"])

        section = None
        if data.get("section_id"):
            section = self.get_record(Section, data["section_id"], "Section")
            if section.course_id != course.id or section.branch_id != (branch.id if branch else None):
                raise ValidationException("Section does not match the student's program and branch")
            if section.semester_number != data["current_semester"]:
                raise ValidationException("Section semester does not match the student's current semester")

        student.department_id = department.id
        student.course_id = course.id
        student.branch_id = branch.id if branch else None
        student.admission_year = data["admission_year"]
        student.current_semester = data["current_semester"]
        student.semester = data["current_semester"]  # compatibility with existing modules
        student.section_id = section.id if section else None
        student.section = section.code if section else student.section
        student.curriculum_version_id = version.id if version else None
        if data.get("academic_status"):
            from app.models.student import EnrollmentStatus
            student.status = EnrollmentStatus(data["academic_status"])
        self.db.commit()
        self.db.refresh(student)
        return student

    def find_applicable_curriculum(self, course_id: int, branch_id: int | None, admission_year: int):
        branch_preference = case((Curriculum.branch_id == branch_id, 1), else_=0)
        return (
            self.db.query(CurriculumVersion)
            .join(Curriculum)
            .filter(
                Curriculum.course_id == course_id,
                or_(Curriculum.branch_id.is_(None), Curriculum.branch_id == branch_id),
                CurriculumVersion.is_active.is_(True),
                CurriculumVersion.is_deleted.is_(False),
                CurriculumVersion.applicable_batch_start <= admission_year,
                or_(CurriculumVersion.applicable_batch_end.is_(None), CurriculumVersion.applicable_batch_end >= admission_year),
            )
            .order_by(branch_preference.desc(), CurriculumVersion.effective_year.desc())
            .first()
        )

    def resolve_student_subjects(self, student_id: int, semester_number: int | None = None):
        student = self.get_record(Student, student_id, "Student")
        if not student.curriculum_version_id:
            return []
        semester_number = semester_number or student.current_semester or student.semester
        mappings = (
            self.db.query(CurriculumSubject)
            .join(AcademicSemester)
            .filter(
                AcademicSemester.curriculum_version_id == student.curriculum_version_id,
                AcademicSemester.number == semester_number,
                AcademicSemester.is_deleted.is_(False),
                CurriculumSubject.is_deleted.is_(False),
                or_(CurriculumSubject.branch_id.is_(None), CurriculumSubject.branch_id == student.branch_id),
            )
            .order_by(CurriculumSubject.display_order, CurriculumSubject.id)
            .all()
        )
        selected_ids = {
            item.curriculum_subject_id for item in self.db.query(StudentElective).filter(
                StudentElective.student_id == student.id,
                StudentElective.status == "selected",
                StudentElective.is_deleted.is_(False),
            ).all()
        }
        resolved = []
        for mapping in mappings:
            type_code = mapping.subject.subject_type.code if mapping.subject.subject_type else "SPECIALIZATION"
            if type_code in self.ELECTIVE_TYPES and mapping.id not in selected_ids:
                continue
            resolved.append({
                "curriculum_subject_id": mapping.id,
                "subject_id": mapping.subject.id,
                "code": mapping.subject.code,
                "name": mapping.subject.name,
                "subject_type": type_code,
                "credits": mapping.credits_override if mapping.credits_override is not None else mapping.subject.credits,
                "semester": semester_number,
                "branch_id": mapping.branch_id,
                "source": "elective" if type_code in self.ELECTIVE_TYPES else "common" if mapping.branch_id is None else "branch",
            })
        return resolved

    def select_elective(self, student_id: int, curriculum_subject_id: int):
        student = self.get_record(Student, student_id, "Student")
        mapping = self.get_record(CurriculumSubject, curriculum_subject_id, "Curriculum subject")
        type_code = mapping.subject.subject_type.code if mapping.subject.subject_type else None
        if type_code not in self.ELECTIVE_TYPES:
            raise ValidationException("Selected curriculum subject is not an elective")
        if mapping.semester.curriculum_version_id != student.curriculum_version_id:
            raise ValidationException("Elective is not part of the student's curriculum version")
        if mapping.branch_id not in (None, student.branch_id):
            raise ValidationException("Elective is not available to the student's branch")
        if mapping.elective_group:
            selected_count = (
                self.db.query(StudentElective)
                .join(CurriculumSubject)
                .filter(
                    StudentElective.student_id == student.id,
                    StudentElective.status == "selected",
                    StudentElective.is_deleted.is_(False),
                    CurriculumSubject.elective_group_id == mapping.elective_group_id,
                ).count()
            )
            if selected_count >= mapping.elective_group.maximum_choices:
                raise ValidationException("Maximum elective choices reached for this group")
        existing = self.db.query(StudentElective).filter(
            StudentElective.student_id == student.id,
            StudentElective.curriculum_subject_id == mapping.id,
        ).first()
        if existing:
            existing.status = "selected"
            existing.restore()
            self.db.commit()
            return existing
        return self._create(StudentElective, {"student_id": student.id, "curriculum_subject_id": mapping.id})

    def _validate_student_curriculum(self, course_id: int, branch_id: int | None, admission_year: int, version_id: int):
        version = self.get_record(CurriculumVersion, version_id, "Curriculum version")
        curriculum = version.curriculum
        if curriculum.course_id != course_id or curriculum.branch_id not in (None, branch_id):
            raise ValidationException("Curriculum version does not match the student's program and branch")
        if admission_year < version.applicable_batch_start or (version.applicable_batch_end and admission_year > version.applicable_batch_end):
            raise ValidationException("Curriculum version is not applicable to the student's admission batch")
        return version

    def _validate_branch_for_course(self, branch_id: int | None, course_id: int):
        if branch_id is None:
            return None
        branch = self.get_record(Branch, branch_id, "Branch")
        if branch.course_id != course_id:
            raise ValidationException("Branch does not belong to the selected program")
        return branch

    @staticmethod
    def _validate_batch_range(data: dict):
        if data.get("applicable_batch_end") is not None and data["applicable_batch_end"] < data["applicable_batch_start"]:
            raise ValidationException("Applicable batch end cannot be before batch start")

    def _create(self, model, data: dict):
        record = model(**data)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
