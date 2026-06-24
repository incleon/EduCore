from app.core.config import settings
from app.main import create_app


def test_core_api_routes_are_registered():
    paths = {route.path for route in create_app().routes}

    assert "/auth/login" in paths
    assert "/api/dashboard" in paths
    assert "/api/students" in paths
    assert "/api/teachers" in paths
    assert "/api/timetables" in paths
    assert "/api/notifications" in paths


def test_cors_origins_are_normalized():
    assert settings.cors_origins
    assert all(origin == origin.strip() for origin in settings.cors_origins)


def test_admin_modules_expose_complete_mutation_routes():
    app = create_app()
    routes = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}
    expected = {
        ("/api/students", "POST"), ("/api/students/{student_id}", "PUT"), ("/api/students/{student_id}", "DELETE"),
        ("/api/teachers", "POST"), ("/api/teachers/{teacher_id}", "PUT"), ("/api/teachers/{teacher_id}", "DELETE"),
        ("/api/courses", "POST"), ("/api/courses/{course_id}", "PUT"), ("/api/courses/{course_id}", "DELETE"),
        ("/api/departments", "POST"), ("/api/departments/{dept_id}", "PUT"), ("/api/departments/{dept_id}", "DELETE"),
        ("/api/subjects", "POST"), ("/api/subjects/{subject_id}", "PUT"), ("/api/subjects/{subject_id}", "DELETE"),
        ("/api/attendance", "POST"), ("/api/attendance/{attendance_id}", "PUT"), ("/api/attendance/{attendance_id}", "DELETE"),
        ("/api/marks", "POST"), ("/api/marks/{marks_id}", "PUT"), ("/api/marks/{marks_id}", "DELETE"),
        ("/api/fees", "POST"), ("/api/fees/{fee_id}", "PUT"), ("/api/fees/{fee_id}", "DELETE"),
        ("/api/library/books", "POST"), ("/api/library/books/{book_id}", "PUT"), ("/api/library/books/{book_id}", "DELETE"),
    }
    assert expected <= routes


def test_academic_structure_exposes_complete_management_routes():
    app = create_app()
    routes = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}
    managed = {
        "branches": "branch_id",
        "curricula": "curriculum_id",
        "curriculum-versions": "version_id",
        "semesters": "semester_id",
        "sections": "section_id",
        "elective-groups": "group_id",
        "curriculum-subjects": "mapping_id",
        "faculty-assignments": "assignment_id",
    }
    expected = {("/api/academic/subject-types", "GET")}
    for resource, identifier in managed.items():
        expected |= {
            (f"/api/academic/{resource}", "GET"),
            (f"/api/academic/{resource}", "POST"),
            (f"/api/academic/{resource}/{{{identifier}}}", "PUT"),
            (f"/api/academic/{resource}/{{{identifier}}}", "DELETE"),
        }
    expected |= {
        ("/api/academic/students/{student_id}/mapping", "PUT"),
        ("/api/academic/students/{student_id}/subjects", "GET"),
        ("/api/academic/students/{student_id}/electives", "POST"),
    }
    assert expected <= routes
