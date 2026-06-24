"""Scope timetables by program, branch, semester, and section.

Revision ID: 0003_section_scoped_timetables
Revises: 0002_academic_structure
"""

from alembic import op


revision = "0003_section_scoped_timetables"
down_revision = "0002_academic_structure"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MySQL may reuse the legacy unique key to support the department FK.
    # Give both core scope FKs dedicated indexes before replacing that key.
    op.create_index("ix_timetable_versions_department_id", "timetable_versions", ["department_id"])
    op.create_index("ix_timetable_versions_course_id", "timetable_versions", ["course_id"])
    op.drop_constraint("uq_department_semester", "timetable_versions", type_="unique")
    op.create_unique_constraint(
        "uq_timetable_scope",
        "timetable_versions",
        ["course_id", "branch_id", "semester", "section_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_timetable_scope", "timetable_versions", type_="unique")
    op.create_unique_constraint(
        "uq_department_semester",
        "timetable_versions",
        ["department_id", "semester"],
    )
    op.drop_index("ix_timetable_versions_course_id", table_name="timetable_versions")
    op.drop_index("ix_timetable_versions_department_id", table_name="timetable_versions")
