"""Make optional academic scopes unique even when their foreign key is null.

Revision ID: 0004_null_safe_academic_scopes
Revises: 0003_section_scoped_timetables
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_null_safe_academic_scopes"
down_revision = "0003_section_scoped_timetables"
branch_labels = None
depends_on = None


def _scope_column(name: str) -> sa.Column:
    return sa.Column(name, sa.Integer(), server_default="0", nullable=False)


def _inspector():
    return sa.inspect(op.get_bind())


def _has_column(table: str, name: str) -> bool:
    return name in {column["name"] for column in _inspector().get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    return name in {index["name"] for index in _inspector().get_indexes(table)}


def _has_check(table: str, name: str) -> bool:
    return name in {check["name"] for check in _inspector().get_check_constraints(table)}


def _ensure_scope(table: str, column: str, source: str, check_name: str) -> None:
    if not _has_column(table, column):
        op.add_column(table, _scope_column(column))
    op.execute(f"UPDATE {table} SET {column} = COALESCE({source}, 0)")
    if not _has_check(table, check_name):
        op.create_check_constraint(check_name, table, f"{column} = COALESCE({source}, 0)")


def _replace_unique(table: str, name: str, columns: list[str]) -> None:
    current = next((item for item in _inspector().get_indexes(table) if item["name"] == name), None)
    if current and current.get("column_names") == columns:
        return
    if current:
        op.drop_constraint(name, table, type_="unique")
    op.create_unique_constraint(name, table, columns)


def upgrade() -> None:
    _ensure_scope("sections", "branch_scope_key", "branch_id", "ck_section_branch_scope")
    _replace_unique(
        "sections", "uq_section_scope_code",
        ["course_id", "branch_scope_key", "semester_number", "academic_year", "code"],
    )

    _ensure_scope(
        "curriculum_subjects", "branch_scope_key", "branch_id",
        "ck_curriculum_subject_branch_scope",
    )
    _replace_unique(
        "curriculum_subjects", "uq_curriculum_subject_scope",
        ["semester_id", "subject_id", "branch_scope_key"],
    )

    _ensure_scope(
        "faculty_assignments", "section_scope_key", "section_id",
        "ck_faculty_assignment_section_scope",
    )
    if not _has_index("faculty_assignments", "ix_faculty_assignments_teacher_id"):
        op.create_index("ix_faculty_assignments_teacher_id", "faculty_assignments", ["teacher_id"])
    if not _has_index("faculty_assignments", "ix_faculty_assignments_curriculum_subject_id"):
        op.create_index(
            "ix_faculty_assignments_curriculum_subject_id",
            "faculty_assignments", ["curriculum_subject_id"],
        )
    _replace_unique(
        "faculty_assignments", "uq_faculty_assignment_scope",
        ["teacher_id", "curriculum_subject_id", "section_scope_key", "academic_year"],
    )

    # MySQL forbids checks that reference SET NULL foreign keys. The ORM keeps
    # these two stored scope keys synchronized before every insert/update.
    if not _has_column("timetable_versions", "branch_scope_key"):
        op.add_column("timetable_versions", _scope_column("branch_scope_key"))
    if not _has_column("timetable_versions", "section_scope_key"):
        op.add_column("timetable_versions", _scope_column("section_scope_key"))
    op.execute(
        "UPDATE timetable_versions SET "
        "branch_scope_key = COALESCE(branch_id, 0), "
        "section_scope_key = COALESCE(section_id, 0)"
    )
    _replace_unique(
        "timetable_versions", "uq_timetable_scope",
        ["course_id", "branch_scope_key", "semester", "section_scope_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_timetable_scope", "timetable_versions", type_="unique")
    op.create_unique_constraint(
        "uq_timetable_scope", "timetable_versions",
        ["course_id", "branch_id", "semester", "section_id"],
    )
    if _has_check("timetable_versions", "ck_timetable_section_scope"):
        op.drop_constraint("ck_timetable_section_scope", "timetable_versions", type_="check")
    if _has_check("timetable_versions", "ck_timetable_branch_scope"):
        op.drop_constraint("ck_timetable_branch_scope", "timetable_versions", type_="check")
    op.drop_column("timetable_versions", "section_scope_key")
    op.drop_column("timetable_versions", "branch_scope_key")

    op.drop_constraint("uq_faculty_assignment_scope", "faculty_assignments", type_="unique")
    op.create_unique_constraint(
        "uq_faculty_assignment_scope", "faculty_assignments",
        ["teacher_id", "curriculum_subject_id", "section_id", "academic_year"],
    )
    op.drop_constraint("ck_faculty_assignment_section_scope", "faculty_assignments", type_="check")
    op.drop_column("faculty_assignments", "section_scope_key")

    op.drop_constraint("uq_curriculum_subject_scope", "curriculum_subjects", type_="unique")
    op.create_unique_constraint(
        "uq_curriculum_subject_scope", "curriculum_subjects",
        ["semester_id", "subject_id", "branch_id"],
    )
    op.drop_constraint("ck_curriculum_subject_branch_scope", "curriculum_subjects", type_="check")
    op.drop_column("curriculum_subjects", "branch_scope_key")

    op.drop_constraint("uq_section_scope_code", "sections", type_="unique")
    op.create_unique_constraint(
        "uq_section_scope_code", "sections",
        ["course_id", "branch_id", "semester_number", "academic_year", "code"],
    )
    op.drop_constraint("ck_section_branch_scope", "sections", type_="check")
    op.drop_column("sections", "branch_scope_key")
