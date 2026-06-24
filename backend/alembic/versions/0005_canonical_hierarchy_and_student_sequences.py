"""Canonical hierarchy and durable student sequences.

Revision ID: 0005_hierarchy_sequences
Revises: 2c8000b87f5f
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_hierarchy_sequences"
down_revision = "2c8000b87f5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    department_columns = {column["name"] for column in inspector.get_columns("departments")}
    if "course_id" in department_columns:
        # Legacy data modeled Course -> Department. Choose the oldest owning
        # department when backfilling the now-canonical Department -> Course link.
        if bind.dialect.name == "mysql":
            op.execute(sa.text(
                "UPDATE courses c SET department_id=(SELECT MIN(d.id) FROM departments d "
                "WHERE d.course_id=c.id) WHERE c.department_id IS NULL"
            ))
        else:
            op.execute(sa.text(
                "UPDATE courses SET department_id=(SELECT MIN(departments.id) FROM departments "
                "WHERE departments.course_id=courses.id) WHERE department_id IS NULL"
            ))
        for fk in inspector.get_foreign_keys("departments"):
            if fk.get("constrained_columns") == ["course_id"] and fk.get("name"):
                op.drop_constraint(fk["name"], "departments", type_="foreignkey")
        op.drop_column("departments", "course_id")

    if "student_sequences" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "student_sequences",
            sa.Column("admission_year", sa.Integer(), nullable=False),
            sa.Column("course_id", sa.Integer(), nullable=False),
            sa.Column("branch_id", sa.Integer(), nullable=True),
            sa.Column("branch_scope_key", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_sequence", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("admission_year", "course_id", "branch_scope_key", name="uq_student_sequence_scope"),
            sa.CheckConstraint("last_sequence >= 0", name="ck_student_sequence_nonnegative"),
        )
        op.create_index("ix_student_sequences_year", "student_sequences", ["admission_year"])
        op.create_index("ix_student_sequences_course", "student_sequences", ["course_id"])
        op.create_index("ix_student_sequences_branch", "student_sequences", ["branch_id"])


def downgrade() -> None:
    op.drop_table("student_sequences")
    op.add_column("departments", sa.Column("course_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_departments_course_id", "departments", "courses", ["course_id"], ["id"], ondelete="CASCADE")
