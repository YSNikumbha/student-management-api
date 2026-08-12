"""figma backend alignment

Revision ID: b4f7c2d9a103
Revises: a8c4e2d1f930
Create Date: 2026-08-12 00:00:00.000000

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b4f7c2d9a103"
down_revision: Union[str, Sequence[str], None] = "a8c4e2d1f930"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(column["name"] == column_name for column in _inspector().get_columns(table_name))


def _index_names(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()
    return {index["name"] for index in _inspector().get_indexes(table_name)}


def upgrade() -> None:
    """Upgrade schema."""
    student_columns = [
        ("profile_photo", sa.String(length=500)),
        ("gender", sa.String(length=20)),
        ("address", sa.String(length=500)),
        ("parent_name", sa.String(length=150)),
        ("parent_phone", sa.String(length=20)),
        ("blood_group", sa.String(length=10)),
    ]
    with op.batch_alter_table("students", schema=None) as batch_op:
        for column_name, column_type in student_columns:
            if not _has_column("students", column_name):
                batch_op.add_column(sa.Column(column_name, column_type, nullable=True))

    with op.batch_alter_table("batches", schema=None) as batch_op:
        if not _has_column("batches", "class_teacher_id"):
            batch_op.add_column(sa.Column("class_teacher_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_batches_class_teacher_id_users",
                "users",
                ["class_teacher_id"],
                ["id"],
            )
            batch_op.create_index(batch_op.f("ix_batches_class_teacher_id"), ["class_teacher_id"], unique=False)
        if not _has_column("batches", "room"):
            batch_op.add_column(sa.Column("room", sa.String(length=50), nullable=True))
        if not _has_column("batches", "schedule"):
            batch_op.add_column(sa.Column("schedule", sa.String(length=150), nullable=True))

    if not _has_column("student_fees", "invoice_number"):
        with op.batch_alter_table("student_fees", schema=None) as batch_op:
            batch_op.add_column(sa.Column("invoice_number", sa.String(length=50), nullable=True))
        connection = op.get_bind()
        fee_rows = connection.execute(sa.text("SELECT id, due_date FROM student_fees ORDER BY id")).mappings().all()
        for row in fee_rows:
            due_year = str(row["due_date"])[:4] if row["due_date"] else str(datetime.utcnow().year)
            connection.execute(
                sa.text("UPDATE student_fees SET invoice_number = :invoice_number WHERE id = :fee_id"),
                {"invoice_number": f"INV-{due_year}-{int(row['id']):04d}", "fee_id": row["id"]},
            )
        with op.batch_alter_table("student_fees", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_student_fees_invoice_number"), ["invoice_number"], unique=True)

    if not _has_table("assessments"):
        op.create_table(
            "assessments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=150), nullable=False),
            sa.Column("subject_id", sa.Integer(), nullable=False),
            sa.Column("semester_id", sa.Integer(), nullable=False),
            sa.Column("academic_year_id", sa.Integer(), nullable=False),
            sa.Column("assessment_type", sa.String(length=50), nullable=False),
            sa.Column("max_marks", sa.Numeric(7, 2), nullable=False),
            sa.Column("weight_percentage", sa.Numeric(5, 2), nullable=True),
            sa.Column("date", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
            sa.ForeignKeyConstraint(["semester_id"], ["semesters.id"]),
            sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("assessments", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_assessments_academic_year_id"), ["academic_year_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_assessments_date"), ["date"], unique=False)
            batch_op.create_index(batch_op.f("ix_assessments_id"), ["id"], unique=False)
            batch_op.create_index(batch_op.f("ix_assessments_name"), ["name"], unique=False)
            batch_op.create_index(batch_op.f("ix_assessments_semester_id"), ["semester_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_assessments_subject_id"), ["subject_id"], unique=False)

    if not _has_table("student_results"):
        op.create_table(
            "student_results",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("assessment_id", sa.Integer(), nullable=False),
            sa.Column("student_id", sa.Integer(), nullable=False),
            sa.Column("marks_obtained", sa.Numeric(7, 2), nullable=False),
            sa.Column("grade", sa.String(length=5), nullable=True),
            sa.Column("remarks", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
            sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("assessment_id", "student_id", name="uq_student_result_assessment_student"),
        )
        with op.batch_alter_table("student_results", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_student_results_assessment_id"), ["assessment_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_student_results_id"), ["id"], unique=False)
            batch_op.create_index(batch_op.f("ix_student_results_student_id"), ["student_id"], unique=False)

    if not _has_table("system_settings"):
        op.create_table(
            "system_settings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("school_name", sa.String(length=200), nullable=False),
            sa.Column("official_email", sa.String(length=255), nullable=True),
            sa.Column("phone", sa.String(length=30), nullable=True),
            sa.Column("address", sa.String(length=500), nullable=True),
            sa.Column("logo_path", sa.String(length=500), nullable=True),
            sa.Column("default_academic_year_id", sa.Integer(), nullable=True),
            sa.Column("currency", sa.String(length=10), nullable=False),
            sa.Column("timezone", sa.String(length=80), nullable=False),
            sa.Column("language", sa.String(length=50), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["default_academic_year_id"], ["academic_years.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("system_settings", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_system_settings_default_academic_year_id"), ["default_academic_year_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_system_settings_id"), ["id"], unique=False)
        now = datetime.utcnow()
        op.bulk_insert(
            sa.table(
                "system_settings",
                sa.column("school_name", sa.String),
                sa.column("currency", sa.String),
                sa.column("timezone", sa.String),
                sa.column("language", sa.String),
                sa.column("created_at", sa.DateTime),
                sa.column("updated_at", sa.DateTime),
            ),
            [
                {
                    "school_name": "Student Management System",
                    "currency": "INR",
                    "timezone": "Asia/Kolkata",
                    "language": "English",
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )

    if not _has_table("notification_preferences"):
        op.create_table(
            "notification_preferences",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("fee_alerts", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("attendance_alerts", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("system_notifications", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("notification_preferences", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_notification_preferences_id"), ["id"], unique=False)
            batch_op.create_index(batch_op.f("ix_notification_preferences_user_id"), ["user_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    if _has_table("notification_preferences"):
        with op.batch_alter_table("notification_preferences", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_notification_preferences_user_id"))
            batch_op.drop_index(batch_op.f("ix_notification_preferences_id"))
        op.drop_table("notification_preferences")

    if _has_table("system_settings"):
        with op.batch_alter_table("system_settings", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_system_settings_id"))
            batch_op.drop_index(batch_op.f("ix_system_settings_default_academic_year_id"))
        op.drop_table("system_settings")

    if _has_table("student_results"):
        with op.batch_alter_table("student_results", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_student_results_student_id"))
            batch_op.drop_index(batch_op.f("ix_student_results_id"))
            batch_op.drop_index(batch_op.f("ix_student_results_assessment_id"))
        op.drop_table("student_results")

    if _has_table("assessments"):
        with op.batch_alter_table("assessments", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_assessments_subject_id"))
            batch_op.drop_index(batch_op.f("ix_assessments_semester_id"))
            batch_op.drop_index(batch_op.f("ix_assessments_name"))
            batch_op.drop_index(batch_op.f("ix_assessments_id"))
            batch_op.drop_index(batch_op.f("ix_assessments_date"))
            batch_op.drop_index(batch_op.f("ix_assessments_academic_year_id"))
        op.drop_table("assessments")

    if _has_column("student_fees", "invoice_number"):
        with op.batch_alter_table("student_fees", schema=None) as batch_op:
            if batch_op.f("ix_student_fees_invoice_number") in _index_names("student_fees"):
                batch_op.drop_index(batch_op.f("ix_student_fees_invoice_number"))
            batch_op.drop_column("invoice_number")

    with op.batch_alter_table("batches", schema=None) as batch_op:
        if _has_column("batches", "schedule"):
            batch_op.drop_column("schedule")
        if _has_column("batches", "room"):
            batch_op.drop_column("room")
        if _has_column("batches", "class_teacher_id"):
            if batch_op.f("ix_batches_class_teacher_id") in _index_names("batches"):
                batch_op.drop_index(batch_op.f("ix_batches_class_teacher_id"))
            batch_op.drop_constraint("fk_batches_class_teacher_id_users", type_="foreignkey")
            batch_op.drop_column("class_teacher_id")

    with op.batch_alter_table("students", schema=None) as batch_op:
        for column_name in ("blood_group", "parent_phone", "parent_name", "address", "gender", "profile_photo"):
            if _has_column("students", column_name):
                batch_op.drop_column(column_name)
