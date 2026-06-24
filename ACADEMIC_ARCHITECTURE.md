# Academic structure and curriculum architecture

EduCore’s canonical academic hierarchy is:

```text
Department → Program/Course → optional Branch → Curriculum Version → Semester → Subject
                                                      ↓
                                                   Section
```

This model supports universities, engineering and management institutes, pharmacy and medical colleges, schools, and programs that do not use branches.

## Core entities

- `departments`: top-level academic ownership such as Engineering or Management.
- `courses`: programs such as B.Tech, MBA, B.Pharm, or MBBS. `courses.department_id` is the canonical hierarchy link.
- `branches`: optional program specializations such as CSE, IT, Finance, or Psychology.
- `curricula`: stable curriculum identities for a program and optional branch.
- `curriculum_versions`: immutable regulations selected by effective year and admission-batch range.
- `academic_semesters`: semester definitions inside a curriculum version.
- `subjects`: one global subject catalogue. A subject is never copied for every branch.
- `curriculum_subjects`: maps catalogue subjects into semesters. A null `branch_id` means common to all branches; a branch value restricts it to that specialization.
- `elective_groups` and `student_electives`: elective availability, choice limits, and student selections.
- `sections`: program, optional branch, semester, curriculum version, and academic-year-specific sections.
- `faculty_assignments`: many-to-many teaching assignments scoped to curriculum subjects, academic years, and optional sections.

## Subject classification

The seeded `subject_types` table contains:

```text
COMMON
SPECIALIZATION
ELECTIVE
OPEN_ELECTIVE
LAB
PROJECT
INTERNSHIP
```

The service layer enforces that `COMMON` mappings have no branch, `SPECIALIZATION` mappings have a branch, and elective types belong to an elective group.

## Automatic subject resolution

`GET /api/academic/students/{student_id}/subjects` resolves the student’s subjects from their locked curriculum version and current semester:

1. Include curriculum mappings with no branch (common subjects).
2. Include mappings matching the student’s branch.
3. Include `ELECTIVE` and `OPEN_ELECTIVE` mappings only when selected by the student.
4. Include applicable lab, project, and internship mappings.

The subject catalogue row is reused in every case, so common first-year subjects are not duplicated.

## Curriculum locking

Each student stores department, program, optional branch, admission year, current semester, section, academic status, and `curriculum_version_id`. When a mapping is created without an explicit version, EduCore selects the newest active version whose batch range contains the admission year. Later curriculum publications do not change the student’s stored version.

## Migration

Migration `0002_academic_structure` is additive. It creates the normalized tables, makes the old inverse `departments.course_id` link nullable, adds canonical academic fields, and backfills student program, semester, and admission-year values. Migration `0003_section_scoped_timetables` permits independent program, branch, semester, and section timetables. Migration `0004_null_safe_academic_scopes` makes optional branch and section uniqueness null-safe, preventing duplicate common allocations at the database layer. Legacy fields remain temporarily for compatibility with existing operational modules.

For an existing installation, apply upgrades with:

```powershell
cd backend
python -m alembic upgrade head
python -m app.cli init-db
```

For a new empty database, follow the fresh-install sequence in `DB_SETUP.md` so the legacy baseline is stamped only after the current schema has been created.
