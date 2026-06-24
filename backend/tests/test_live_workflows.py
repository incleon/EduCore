"""Opt-in, destructive-safe smoke test for every major live CMS workflow.

Run while the backend is listening on port 8000:
    $env:RUN_LIVE_CMS_TESTS='1'; python -m pytest tests/test_live_workflows.py -q

Every record receives a unique ``SMOKE`` suffix and is removed in ``finally``.
"""

import os
from datetime import date, datetime, timedelta
from uuid import uuid4

import httpx
import pytest

from app.core.config import settings
from app.database.session import SessionLocal
from app.core.security import PasswordHasher
from app.models.academic import Assignment
from app.models.student import Student
from app.services.crud_services import DepartmentService


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_CMS_TESTS") != "1",
    reason="set RUN_LIVE_CMS_TESTS=1 to exercise the running local CMS",
)


def _login(email: str, password: str) -> httpx.Client:
    client = httpx.Client(base_url=os.getenv("CMS_BASE_URL", "http://127.0.0.1:8000"), timeout=60)
    challenge = client.get("/captcha/new").raise_for_status().json()
    response = client.post("/auth/login", json={
        "email": email,
        "password": password,
        "captcha_answer": challenge["captcha_text"],
        "captcha_token": challenge["captcha_token"],
    })
    response.raise_for_status()
    return client


def _request(client, method, path, payload=None):
    response = client.request(method, path, json=payload)
    assert response.status_code < 400, f"{method} {path}: {response.status_code} {response.text}"
    return response.json() if response.content else None


def test_all_major_live_workflows():
    suffix = uuid4().hex[:8].upper()
    admin = _login(settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD)
    created = {}
    teacher = student = None

    try:
        assert _request(admin, "GET", "/auth/me")["email"] == settings.ADMIN_EMAIL
        _request(admin, "GET", "/api/dashboard")
        _request(admin, "GET", "/api/notifications")

        department = _request(admin, "POST", "/api/departments", {
            "name": f"Smoke Department {suffix}", "code": f"SD{suffix[:5]}", "description": "Live workflow test"
        })
        created["department"] = department["id"]
        _request(admin, "PUT", f"/api/departments/{department['id']}", {"description": "Updated live workflow test"})

        course = _request(admin, "POST", "/api/courses", {
            "department_id": department["id"], "name": f"Smoke Program {suffix}",
            "code": f"SP{suffix[:5]}", "duration_years": "4",
        })
        created["course"] = course["id"]
        _request(admin, "PUT", f"/api/courses/{course['id']}", {"description": "Updated program"})

        branch = _request(admin, "POST", "/api/academic/branches", {
            "course_id": course["id"], "name": f"Smoke Branch {suffix}", "code": f"SB{suffix[:5]}"
        })
        created["branch"] = branch["id"]
        _request(admin, "PUT", f"/api/academic/branches/{branch['id']}", {"description": "Updated branch"})

        curriculum = _request(admin, "POST", "/api/academic/curricula", {
            "course_id": course["id"], "branch_id": branch["id"],
            "code": f"CUR-{suffix}", "name": f"Smoke Curriculum {suffix}",
        })
        created["curriculum"] = curriculum["id"]
        _request(admin, "PUT", f"/api/academic/curricula/{curriculum['id']}", {"description": "Updated curriculum"})

        version = _request(admin, "POST", "/api/academic/curriculum-versions", {
            "curriculum_id": curriculum["id"], "version_code": suffix, "title": f"Regulation {suffix}",
            "effective_year": date.today().year, "applicable_batch_start": date.today().year,
            "status": "active", "is_active": True,
        })
        created["version"] = version["id"]
        _request(admin, "PUT", f"/api/academic/curriculum-versions/{version['id']}", {"title": f"Updated Regulation {suffix}"})

        semester = _request(admin, "POST", "/api/academic/semesters", {
            "curriculum_version_id": version["id"], "number": 1, "name": "Smoke Semester", "maximum_credits": 30,
        })
        created["semester"] = semester["id"]
        _request(admin, "PUT", f"/api/academic/semesters/{semester['id']}", {"minimum_credits": 18})

        section = _request(admin, "POST", "/api/academic/sections", {
            "course_id": course["id"], "branch_id": branch["id"], "curriculum_version_id": version["id"],
            "semester_number": 1, "code": f"A{suffix[:3]}", "academic_year": f"{date.today().year}-{date.today().year + 1}", "capacity": 60,
        })
        created["section"] = section["id"]
        _request(admin, "PUT", f"/api/academic/sections/{section['id']}", {"capacity": 55})

        subject_type = _request(admin, "GET", "/api/academic/subject-types")[0]
        subject = _request(admin, "POST", "/api/subjects", {
            "name": f"Smoke Subject {suffix}", "code": f"SS{suffix[:6]}", "credits": 4,
            "semester": 1, "type": "theory", "department_id": department["id"], "subject_type_id": subject_type["id"],
        })
        created["subject"] = subject["id"]
        _request(admin, "PUT", f"/api/subjects/{subject['id']}", {"credits": 3})

        elective_group = _request(admin, "POST", "/api/academic/elective-groups", {
            "semester_id": semester["id"], "code": f"EG{suffix[:5]}", "name": f"Smoke Electives {suffix}",
            "minimum_choices": 0, "maximum_choices": 1,
        })
        created["elective_group"] = elective_group["id"]
        _request(admin, "PUT", f"/api/academic/elective-groups/{elective_group['id']}", {"description": "Updated group"})

        mapping = _request(admin, "POST", "/api/academic/curriculum-subjects", {
            "semester_id": semester["id"], "subject_id": subject["id"], "branch_id": branch["id"],
            "is_mandatory": True, "display_order": 1,
        })
        created["mapping"] = mapping["id"]
        _request(admin, "PUT", f"/api/academic/curriculum-subjects/{mapping['id']}", {"display_order": 2})

        teacher_password = f"Teach!{suffix}9"
        faculty = _request(admin, "POST", "/api/teachers", {
            "email": f"teacher.{suffix.lower()}@example.test", "username": f"teacher_{suffix.lower()}",
            "password": teacher_password, "full_name": "Smoke Teacher", "employee_id": f"EMP-{suffix}",
            "department_id": department["id"], "branch_id": branch["id"], "designation": "Professor",
        })
        created["teacher"] = faculty["id"]
        _request(admin, "PUT", f"/api/teachers/{faculty['id']}", {"designation": "Senior Professor"})

        faculty_assignment = _request(admin, "POST", "/api/academic/faculty-assignments", {
            "teacher_id": faculty["id"], "curriculum_subject_id": mapping["id"], "section_id": section["id"],
            "academic_year": section["academic_year"], "role": "primary",
        })
        created["faculty_assignment"] = faculty_assignment["id"]
        _request(admin, "PUT", f"/api/academic/faculty-assignments/{faculty_assignment['id']}", {"role": "co_faculty"})

        student_record = _request(admin, "POST", "/api/students", {
            "first_name": "Smoke", "last_name": "Student", "personal_email": f"student.{suffix.lower()}@example.test",
            "department_id": department["id"], "course_id": course["id"], "branch_id": branch["id"],
            "curriculum_version_id": version["id"], "section_id": section["id"],
            "admission_year": date.today().year, "current_semester": 1, "semester": 1,
        })
        created["student"] = student_record["id"]
        _request(admin, "PUT", f"/api/students/{student_record['id']}", {"guardian_name": "Updated Guardian"})
        _request(admin, "GET", f"/api/academic/students/{student_record['id']}/subjects")

        attendance = _request(admin, "POST", "/api/attendance", {
            "student_id": student_record["id"], "subject_id": subject["id"], "section_id": section["id"],
            "faculty_assignment_id": faculty_assignment["id"], "date": date.today().isoformat(), "status": "present",
        })
        _request(admin, "PUT", f"/api/attendance/{attendance['id']}", {"status": "late"})
        _request(admin, "GET", f"/api/attendance/student/{student_record['id']}/stats")

        marks = _request(admin, "POST", "/api/marks", {
            "student_id": student_record["id"], "subject_id": subject["id"], "exam_type": "quiz",
            "marks_obtained": 18, "max_marks": 20, "semester": 1,
        })
        _request(admin, "PUT", f"/api/marks/{marks['id']}", {"marks_obtained": 19})
        _request(admin, "GET", f"/api/marks/student/{student_record['id']}")

        fee = _request(admin, "POST", "/api/fees", {
            "student_id": student_record["id"], "fee_type": "tuition", "amount": 1000,
            "due_date": (date.today() + timedelta(days=30)).isoformat(), "semester": 1,
        })
        _request(admin, "PUT", f"/api/fees/{fee['id']}", {"remarks": "Updated fee"})
        _request(admin, "POST", f"/api/fees/{fee['id']}/pay", {"paid_amount": 250, "payment_method": "cash"})

        book = _request(admin, "POST", "/api/library/books", {
            "title": f"Smoke Book {suffix}", "author": "Test Author", "isbn": f"ISBN-{suffix}", "total_copies": 2,
        })
        _request(admin, "PUT", f"/api/library/books/{book['id']}", {"category": "Testing"})
        issue = _request(admin, "POST", "/api/library/issue", {
            "book_id": book["id"], "student_id": student_record["id"],
            "due_date": (date.today() + timedelta(days=14)).isoformat(),
        })
        _request(admin, "GET", "/api/library/issues")
        _request(admin, "POST", f"/api/library/return/{issue['id']}", {"fine_amount": 0})

        timetable = _request(admin, "POST", "/api/timetables/version", {
            "department_id": department["id"], "course_id": course["id"], "branch_id": branch["id"],
            "section_id": section["id"], "semester": 1, "action": "submit",
            "slots": [{"day_of_week": 1, "slot_index": 1, "subject_id": subject["id"], "teacher_id": faculty["id"]}],
        })
        _request(admin, "GET", f"/api/timetables?department_id={department['id']}&course_id={course['id']}&branch_id={branch['id']}&section_id={section['id']}&semester=1")
        _request(admin, "PUT", f"/api/timetables/version/{timetable['version_id']}/status", {"status": "approved"})

        teacher = _login(f"teacher.{suffix.lower()}@example.test", teacher_password)
        assignment = _request(teacher, "POST", "/api/assignments", {
            "title": f"Smoke Assignment {suffix}", "description": "Workflow test",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(), "faculty_assignment_id": faculty_assignment["id"],
        })
        created["assignment"] = assignment["id"]
        _request(teacher, "PUT", f"/api/assignments/{assignment['id']}", {"description": "Updated workflow test"})
        submissions = _request(teacher, "GET", f"/api/assignments/{assignment['id']}/submissions")
        assert len(submissions) == 1

        student_password = f"Student!{suffix}9"
        with SessionLocal() as db:
            record = db.query(Student).filter(Student.id == student_record["id"]).one()
            record.user.hashed_password = PasswordHasher.hash_password(student_password)
            db.commit()
        student = _login(student_record["email"], student_password)
        student_assignments = _request(student, "GET", "/api/assignments")
        assert student_assignments[0]["assignment"]["title"] == assignment["title"]
        submitted = _request(student, "POST", f"/api/assignments/submissions/{submissions[0]['id']}/submit", {"content": "Completed work"})
        _request(teacher, "POST", f"/api/assignments/submissions/{submitted['id']}/review", {"status": "accepted", "feedback": "Good work"})
        _request(teacher, "DELETE", f"/api/assignments/{assignment['id']}")
        created.pop("assignment")

        _request(admin, "DELETE", f"/api/attendance/{attendance['id']}")
        _request(admin, "DELETE", f"/api/marks/{marks['id']}")
        _request(admin, "DELETE", f"/api/fees/{fee['id']}")
        _request(admin, "DELETE", f"/api/library/books/{book['id']}")
        _request(admin, "DELETE", f"/api/students/{student_record['id']}")
        created.pop("student")
        _request(admin, "DELETE", f"/api/academic/faculty-assignments/{faculty_assignment['id']}")
        created.pop("faculty_assignment")
        _request(admin, "DELETE", f"/api/teachers/{faculty['id']}")
        created.pop("teacher")
        _request(admin, "DELETE", f"/api/academic/curriculum-subjects/{mapping['id']}")
        created.pop("mapping")
        _request(admin, "DELETE", f"/api/academic/elective-groups/{elective_group['id']}")
        created.pop("elective_group")
        _request(admin, "DELETE", f"/api/subjects/{subject['id']}")
        created.pop("subject")
        _request(admin, "DELETE", f"/api/academic/sections/{section['id']}")
        created.pop("section")
        _request(admin, "DELETE", f"/api/academic/semesters/{semester['id']}")
        created.pop("semester")
        _request(admin, "DELETE", f"/api/academic/curriculum-versions/{version['id']}")
        created.pop("version")
        _request(admin, "DELETE", f"/api/academic/curricula/{curriculum['id']}")
        created.pop("curriculum")
        _request(admin, "DELETE", f"/api/academic/branches/{branch['id']}")
        created.pop("branch")
        _request(admin, "DELETE", f"/api/courses/{course['id']}")
        created.pop("course")
        _request(admin, "DELETE", f"/api/departments/{department['id']}")
        created.pop("department")
    finally:
        if created.get("department"):
            with SessionLocal() as db:
                if created.get("assignment"):
                    record = db.get(Assignment, created["assignment"])
                    if record:
                        db.delete(record)
                        db.commit()
                DepartmentService(db).delete(created["department"])
        if student:
            student.close()
        if teacher:
            teacher.close()
        admin.close()
