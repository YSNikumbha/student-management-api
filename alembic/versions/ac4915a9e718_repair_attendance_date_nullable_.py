"""repair attendance schema compatibility

Revision ID: ac4915a9e718
Revises: repair_partial_academic_attendance_schema
Create Date: 2026-08-12 13:58:27.436190

This repair is intentionally data-preserving:
- add only missing academic/session columns, tables, indexes, and FKs
- keep legacy attendances.date support
- keep attendance_session_id nullable for historical attendance rows
- allow attendances.date to be nullable for session-based attendance rows
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac4915a9e718'
down_revision: Union[str, Sequence[str], None] = 'repair_partial_academic_attendance_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _table_names() -> set[str]:
    return set(_inspector().get_table_names())


def _columns(table_name: str) -> dict[str, dict]:
    return {column["name"]: column for column in _inspector().get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in _inspector().get_indexes(table_name)}


def _foreign_key_exists(
    table_name: str,
    column_name: str,
    referred_table: str,
    referred_column: str = "id",
) -> bool:
    for foreign_key in _inspector().get_foreign_keys(table_name):
        constrained_columns = foreign_key.get("constrained_columns") or []
        referred_columns = foreign_key.get("referred_columns") or []
        if (
            constrained_columns == [column_name]
            and foreign_key.get("referred_table") == referred_table
            and referred_columns == [referred_column]
        ):
            return True
    return False


def _unique_constraint_exists(table_name: str, name: str) -> bool:
    return any(
        constraint.get("name") == name
        for constraint in _inspector().get_unique_constraints(table_name)
    )


def _has_legacy_attendance_duplicates() -> bool:
    result = op.get_bind().exec_driver_sql(
        """
        SELECT 1
        FROM attendances
        WHERE date IS NOT NULL
        GROUP BY student_id, date
        HAVING COUNT(*) > 1
        LIMIT 1
        """
    )
    return result.first() is not None


def _table_is_empty(table_name: str) -> bool:
    result = op.get_bind().exec_driver_sql(f"SELECT COUNT(*) FROM {table_name}")
    return result.scalar_one() == 0


def _create_attendance_sessions_table() -> None:
    op.create_table(
        "attendance_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("semester_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("session_name", sa.String(length=100), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["batches.id"],
            name="fk_attendance_sessions_batch_id_batches",
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name="fk_attendance_sessions_course_id_courses",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_attendance_sessions_created_by_users",
        ),
        sa.ForeignKeyConstraint(
            ["semester_id"],
            ["semesters.id"],
            name="fk_attendance_sessions_semester_id_semesters",
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["subjects.id"],
            name="fk_attendance_sessions_subject_id_subjects",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def _ensure_attendance_session_indexes() -> None:
    if "attendance_sessions" not in _table_names():
        return

    indexes = _index_names("attendance_sessions")
    expected_indexes = {
        "ix_attendance_sessions_batch_id": ["batch_id"],
        "ix_attendance_sessions_course_id": ["course_id"],
        "ix_attendance_sessions_id": ["id"],
        "ix_attendance_sessions_semester_id": ["semester_id"],
        "ix_attendance_sessions_subject_id": ["subject_id"],
    }
    columns = _columns("attendance_sessions")

    with op.batch_alter_table("attendance_sessions", schema=None) as batch_op:
        for index_name, column_names in expected_indexes.items():
            if index_name not in indexes and all(name in columns for name in column_names):
                batch_op.create_index(index_name, column_names, unique=False)


def _ensure_students_schema() -> None:
    if "students" not in _table_names():
        return

    columns = _columns("students")
    indexes = _index_names("students")

    with op.batch_alter_table("students", schema=None) as batch_op:
        if "academic_year_id" not in columns:
            batch_op.add_column(sa.Column("academic_year_id", sa.Integer(), nullable=True))
        if "semester_id" not in columns:
            batch_op.add_column(sa.Column("semester_id", sa.Integer(), nullable=True))
        if "batch_id" not in columns:
            batch_op.add_column(sa.Column("batch_id", sa.Integer(), nullable=True))
        if "admission_date" not in columns:
            batch_op.add_column(sa.Column("admission_date", sa.Date(), nullable=True))

        if "ix_students_academic_year_id" not in indexes:
            batch_op.create_index(
                "ix_students_academic_year_id",
                ["academic_year_id"],
                unique=False,
            )
        if "ix_students_semester_id" not in indexes:
            batch_op.create_index(
                "ix_students_semester_id",
                ["semester_id"],
                unique=False,
            )
        if "ix_students_batch_id" not in indexes:
            batch_op.create_index("ix_students_batch_id", ["batch_id"], unique=False)

        if not _foreign_key_exists("students", "academic_year_id", "academic_years"):
            batch_op.create_foreign_key(
                "fk_students_academic_year_id",
                "academic_years",
                ["academic_year_id"],
                ["id"],
            )
        if not _foreign_key_exists("students", "semester_id", "semesters"):
            batch_op.create_foreign_key(
                "fk_students_semester_id",
                "semesters",
                ["semester_id"],
                ["id"],
            )
        if not _foreign_key_exists("students", "batch_id", "batches"):
            batch_op.create_foreign_key(
                "fk_students_batch_id",
                "batches",
                ["batch_id"],
                ["id"],
            )


def _ensure_attendance_sessions_schema() -> None:
    if "attendance_sessions" not in _table_names():
        _create_attendance_sessions_table()
        _ensure_attendance_session_indexes()
        return

    columns = _columns("attendance_sessions")
    nullable_when_existing_data = not _table_is_empty("attendance_sessions")

    required_columns = {
        "date": sa.Column("date", sa.DateTime(), nullable=nullable_when_existing_data),
        "course_id": sa.Column("course_id", sa.Integer(), nullable=nullable_when_existing_data),
        "batch_id": sa.Column("batch_id", sa.Integer(), nullable=nullable_when_existing_data),
        "semester_id": sa.Column("semester_id", sa.Integer(), nullable=nullable_when_existing_data),
        "subject_id": sa.Column("subject_id", sa.Integer(), nullable=nullable_when_existing_data),
        "created_by": sa.Column("created_by", sa.Integer(), nullable=nullable_when_existing_data),
        "created_at": sa.Column("created_at", sa.DateTime(), nullable=nullable_when_existing_data),
        "updated_at": sa.Column("updated_at", sa.DateTime(), nullable=nullable_when_existing_data),
        "session_name": sa.Column("session_name", sa.String(length=100), nullable=True),
        "start_time": sa.Column("start_time", sa.DateTime(), nullable=True),
        "end_time": sa.Column("end_time", sa.DateTime(), nullable=True),
    }

    with op.batch_alter_table("attendance_sessions", schema=None) as batch_op:
        for column_name, column in required_columns.items():
            if column_name not in columns:
                batch_op.add_column(column)

    _ensure_attendance_session_indexes()

    existing_tables = _table_names()
    fk_specs = [
        ("course_id", "courses", "fk_attendance_sessions_course_id_courses"),
        ("batch_id", "batches", "fk_attendance_sessions_batch_id_batches"),
        ("semester_id", "semesters", "fk_attendance_sessions_semester_id_semesters"),
        ("subject_id", "subjects", "fk_attendance_sessions_subject_id_subjects"),
        ("created_by", "users", "fk_attendance_sessions_created_by_users"),
    ]
    columns = _columns("attendance_sessions")
    with op.batch_alter_table("attendance_sessions", schema=None) as batch_op:
        for column_name, referred_table, constraint_name in fk_specs:
            if (
                column_name in columns
                and referred_table in existing_tables
                and not _foreign_key_exists(
                    "attendance_sessions",
                    column_name,
                    referred_table,
                )
            ):
                batch_op.create_foreign_key(
                    constraint_name,
                    referred_table,
                    [column_name],
                    ["id"],
                )


def _ensure_attendances_schema() -> None:
    if "attendances" not in _table_names():
        return

    columns = _columns("attendances")
    indexes = _index_names("attendances")
    has_attendance_sessions = "attendance_sessions" in _table_names()

    with op.batch_alter_table("attendances", schema=None) as batch_op:
        if "attendance_session_id" not in columns:
            batch_op.add_column(
                sa.Column("attendance_session_id", sa.Integer(), nullable=True)
            )
        if "date" not in columns:
            batch_op.add_column(sa.Column("date", sa.Date(), nullable=True))

        if "date" in columns and columns["date"].get("nullable") is False:
            batch_op.alter_column(
                "date",
                existing_type=sa.Date(),
                existing_nullable=False,
                nullable=True,
            )

        if "ix_attendances_attendance_session_id" not in indexes:
            batch_op.create_index(
                "ix_attendances_attendance_session_id",
                ["attendance_session_id"],
                unique=False,
            )
        if "ix_attendances_date" not in indexes:
            batch_op.create_index("ix_attendances_date", ["date"], unique=False)

        if (
            has_attendance_sessions
            and not _foreign_key_exists(
                "attendances",
                "attendance_session_id",
                "attendance_sessions",
            )
        ):
            batch_op.create_foreign_key(
                "fk_attendances_attendance_session_id",
                "attendance_sessions",
                ["attendance_session_id"],
                ["id"],
            )

        if (
            not _unique_constraint_exists(
                "attendances",
                "uq_attendances_student_id_date",
            )
            and ("date" not in columns or not _has_legacy_attendance_duplicates())
        ):
            batch_op.create_unique_constraint(
                "uq_attendances_student_id_date",
                ["student_id", "date"],
            )


def upgrade() -> None:
    """Upgrade schema."""
    _ensure_students_schema()
    _ensure_attendance_sessions_schema()
    _ensure_attendances_schema()


def downgrade() -> None:
    """Downgrade schema."""
    # Intentionally no-op. Re-tightening attendances.date to NOT NULL could fail
    # after legitimate session-based rows have been created without legacy dates.
