"""Normalized academic structure and versioned curricula.

Revision ID: 0002_academic_structure
Revises: 0001_initial_schema
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_academic_structure"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def audit_columns():
    return (
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def upgrade() -> None:
    op.alter_column("departments", "course_id", existing_type=sa.Integer(), nullable=True)
    op.create_table(
        "subject_types",
        *audit_columns(),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_subject_type_code"),
    )
    op.create_index("ix_subject_types_code", "subject_types", ["code"])

    subject_types = sa.table("subject_types", sa.column("code"), sa.column("name"), sa.column("description"))
    op.bulk_insert(subject_types, [
        {"code": "COMMON", "name": "Common", "description": "Required for all students in the program."},
        {"code": "SPECIALIZATION", "name": "Specialization", "description": "Required only for one branch or specialization."},
        {"code": "ELECTIVE", "name": "Elective", "description": "Selected from a program or branch elective group."},
        {"code": "OPEN_ELECTIVE", "name": "Open Elective", "description": "May be selected across departments."},
        {"code": "LAB", "name": "Laboratory", "description": "Practical or laboratory subject."},
        {"code": "PROJECT", "name": "Project", "description": "Minor or major project work."},
        {"code": "INTERNSHIP", "name": "Internship", "description": "Industry internship credits."},
    ])

    op.create_table(
        "branches",
        *audit_columns(),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("course_id", "code", name="uq_branch_course_code"),
    )
    op.create_index("ix_branch_course_active", "branches", ["course_id", "is_deleted"])

    op.create_table(
        "curricula",
        *audit_columns(),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("code", name="uq_curriculum_code"),
    )
    op.create_index("ix_curriculum_program_branch", "curricula", ["course_id", "branch_id"])

    op.create_table(
        "curriculum_versions",
        *audit_columns(),
        sa.Column("curriculum_id", sa.Integer(), nullable=False),
        sa.Column("version_code", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("effective_year", sa.Integer(), nullable=False),
        sa.Column("applicable_batch_start", sa.Integer(), nullable=False),
        sa.Column("applicable_batch_end", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("applicable_batch_end IS NULL OR applicable_batch_end >= applicable_batch_start", name="ck_curriculum_batch_range"),
        sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("curriculum_id", "version_code", name="uq_curriculum_version_code"),
    )
    op.create_index("ix_curriculum_version_effective", "curriculum_versions", ["curriculum_id", "effective_year", "is_active"])

    op.create_table(
        "academic_semesters",
        *audit_columns(),
        sa.Column("curriculum_version_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("minimum_credits", sa.Integer(), server_default="0", nullable=False),
        sa.Column("maximum_credits", sa.Integer(), nullable=True),
        sa.CheckConstraint("number > 0", name="ck_semester_positive"),
        sa.ForeignKeyConstraint(["curriculum_version_id"], ["curriculum_versions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("curriculum_version_id", "number", name="uq_curriculum_semester_number"),
    )

    op.create_table(
        "sections",
        *audit_columns(),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("curriculum_version_id", sa.Integer(), nullable=True),
        sa.Column("semester_number", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("academic_year", sa.String(20), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.CheckConstraint("semester_number > 0", name="ck_section_semester_positive"),
        sa.CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_section_capacity_positive"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["curriculum_version_id"], ["curriculum_versions.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("course_id", "branch_id", "semester_number", "academic_year", "code", name="uq_section_scope_code"),
    )
    op.create_index("ix_section_lookup", "sections", ["course_id", "branch_id", "semester_number", "academic_year"])

    op.create_table(
        "elective_groups",
        *audit_columns(),
        sa.Column("semester_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("minimum_choices", sa.Integer(), server_default="0", nullable=False),
        sa.Column("maximum_choices", sa.Integer(), server_default="1", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.CheckConstraint("minimum_choices >= 0", name="ck_elective_minimum"),
        sa.CheckConstraint("maximum_choices >= minimum_choices", name="ck_elective_maximum"),
        sa.ForeignKeyConstraint(["semester_id"], ["academic_semesters.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("semester_id", "code", name="uq_elective_group_semester_code"),
    )

    op.create_table(
        "curriculum_subjects",
        *audit_columns(),
        sa.Column("semester_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("elective_group_id", sa.Integer(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("credits_override", sa.Integer(), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint("credits_override IS NULL OR credits_override >= 0", name="ck_curriculum_subject_credits"),
        sa.ForeignKeyConstraint(["semester_id"], ["academic_semesters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["elective_group_id"], ["elective_groups.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("semester_id", "subject_id", "branch_id", name="uq_curriculum_subject_scope"),
    )
    op.create_index("ix_curriculum_subject_resolution", "curriculum_subjects", ["semester_id", "branch_id", "subject_id"])

    op.create_table(
        "student_electives",
        *audit_columns(),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("curriculum_subject_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="selected", nullable=False),
        sa.Column("selected_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["curriculum_subject_id"], ["curriculum_subjects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("student_id", "curriculum_subject_id", name="uq_student_elective_choice"),
    )
    op.create_index("ix_student_elective_lookup", "student_electives", ["student_id", "status"])

    op.create_table(
        "faculty_assignments",
        *audit_columns(),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("curriculum_subject_id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=True),
        sa.Column("academic_year", sa.String(20), nullable=False),
        sa.Column("role", sa.String(30), server_default="primary", nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["curriculum_subject_id"], ["curriculum_subjects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("teacher_id", "curriculum_subject_id", "section_id", "academic_year", name="uq_faculty_assignment_scope"),
    )
    op.create_index("ix_faculty_assignment_lookup", "faculty_assignments", ["curriculum_subject_id", "section_id", "academic_year"])

    _add_fk_column("courses", sa.Column("department_id", sa.Integer(), nullable=True), "departments", "fk_courses_department")
    _add_fk_column("subjects", sa.Column("subject_type_id", sa.Integer(), nullable=True), "subject_types", "fk_subjects_subject_type", ondelete="RESTRICT")
    _add_fk_column("students", sa.Column("course_id", sa.Integer(), nullable=True), "courses", "fk_students_course")
    _add_fk_column("students", sa.Column("branch_id", sa.Integer(), nullable=True), "branches", "fk_students_branch")
    _add_fk_column("students", sa.Column("curriculum_version_id", sa.Integer(), nullable=True), "curriculum_versions", "fk_students_curriculum_version")
    _add_fk_column("students", sa.Column("section_id", sa.Integer(), nullable=True), "sections", "fk_students_section")
    op.add_column("students", sa.Column("admission_year", sa.Integer(), nullable=True))
    op.add_column("students", sa.Column("current_semester", sa.Integer(), server_default="1", nullable=False))
    _add_fk_column("teachers", sa.Column("branch_id", sa.Integer(), nullable=True), "branches", "fk_teachers_branch")
    _add_fk_column("attendances", sa.Column("section_id", sa.Integer(), nullable=True), "sections", "fk_attendances_section")
    _add_fk_column("attendances", sa.Column("faculty_assignment_id", sa.Integer(), nullable=True), "faculty_assignments", "fk_attendances_faculty_assignment")
    _add_fk_column("timetable_versions", sa.Column("branch_id", sa.Integer(), nullable=True), "branches", "fk_timetable_versions_branch")
    _add_fk_column("timetable_versions", sa.Column("section_id", sa.Integer(), nullable=True), "sections", "fk_timetable_versions_section")

    op.execute("UPDATE students s JOIN departments d ON d.id = s.department_id SET s.course_id = d.course_id, s.current_semester = s.semester, s.admission_year = COALESCE(YEAR(s.admission_date), YEAR(s.created_at))")


def _add_fk_column(table, column, remote_table, constraint_name, ondelete="SET NULL"):
    op.add_column(table, column)
    op.create_foreign_key(constraint_name, table, remote_table, [column.name], ["id"], ondelete=ondelete)
    op.create_index(f"ix_{table}_{column.name}", table, [column.name])


def downgrade() -> None:
    for table, column, constraint in [
        ("timetable_versions", "section_id", "fk_timetable_versions_section"),
        ("timetable_versions", "branch_id", "fk_timetable_versions_branch"),
        ("attendances", "faculty_assignment_id", "fk_attendances_faculty_assignment"),
        ("attendances", "section_id", "fk_attendances_section"),
        ("teachers", "branch_id", "fk_teachers_branch"),
        ("students", "section_id", "fk_students_section"),
        ("students", "curriculum_version_id", "fk_students_curriculum_version"),
        ("students", "branch_id", "fk_students_branch"),
        ("students", "course_id", "fk_students_course"),
        ("subjects", "subject_type_id", "fk_subjects_subject_type"),
        ("courses", "department_id", "fk_courses_department"),
    ]:
        op.drop_index(f"ix_{table}_{column}", table_name=table)
        op.drop_constraint(constraint, table, type_="foreignkey")
        op.drop_column(table, column)
    op.drop_column("students", "current_semester")
    op.drop_column("students", "admission_year")

    for table in ["faculty_assignments", "student_electives", "curriculum_subjects", "elective_groups", "sections", "academic_semesters", "curriculum_versions", "curricula", "branches", "subject_types"]:
        op.drop_table(table)
    op.alter_column("departments", "course_id", existing_type=sa.Integer(), nullable=False)
