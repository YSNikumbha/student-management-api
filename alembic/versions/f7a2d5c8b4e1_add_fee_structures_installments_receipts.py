"""add fee structures installments receipts

Revision ID: f7a2d5c8b4e1
Revises: e4b6c2a91f30
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7a2d5c8b4e1"
down_revision: Union[str, Sequence[str], None] = "e4b6c2a91f30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_CATEGORIES = (
    ("Tuition", "Tuition and academic instruction fees"),
    ("Exam", "Examination and assessment fees"),
    ("Library", "Library access and resource fees"),
    ("Hostel", "Hostel and accommodation fees"),
    ("Transport", "Transport service fees"),
    ("Other", "Other fee category"),
)


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(column["name"] == column_name for column in _inspector().get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    if not _has_table("fee_categories"):
        op.create_table(
            "fee_categories",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
        with op.batch_alter_table("fee_categories", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_fee_categories_id"), ["id"], unique=False)
            batch_op.create_index(batch_op.f("ix_fee_categories_name"), ["name"], unique=True)

        fee_categories_table = sa.table(
            "fee_categories",
            sa.column("name", sa.String),
            sa.column("description", sa.String),
            sa.column("is_active", sa.Boolean),
        )
        op.bulk_insert(
            fee_categories_table,
            [
                {"name": name, "description": description, "is_active": True}
                for name, description in DEFAULT_CATEGORIES
            ],
        )

    if not _has_table("fee_structures"):
        op.create_table(
            "fee_structures",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=150), nullable=False),
            sa.Column("course_id", sa.Integer(), nullable=False),
            sa.Column("academic_year_id", sa.Integer(), nullable=False),
            sa.Column("semester_id", sa.Integer(), nullable=True),
            sa.Column("category_id", sa.Integer(), nullable=False),
            sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
            sa.ForeignKeyConstraint(["category_id"], ["fee_categories.id"]),
            sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
            sa.ForeignKeyConstraint(["semester_id"], ["semesters.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("fee_structures", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_fee_structures_academic_year_id"), ["academic_year_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_fee_structures_category_id"), ["category_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_fee_structures_course_id"), ["course_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_fee_structures_id"), ["id"], unique=False)
            batch_op.create_index(batch_op.f("ix_fee_structures_name"), ["name"], unique=False)
            batch_op.create_index(batch_op.f("ix_fee_structures_semester_id"), ["semester_id"], unique=False)

    if not _has_column("student_fees", "fee_structure_id"):
        with op.batch_alter_table("student_fees", schema=None) as batch_op:
            batch_op.add_column(sa.Column("fee_structure_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_student_fees_fee_structure_id_fee_structures",
                "fee_structures",
                ["fee_structure_id"],
                ["id"],
            )
            batch_op.create_index(batch_op.f("ix_student_fees_fee_structure_id"), ["fee_structure_id"], unique=False)

    if not _has_table("fee_installments"):
        op.create_table(
            "fee_installments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("student_fee_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=150), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=False),
            sa.Column("sequence_number", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["student_fee_id"], ["student_fees.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("student_fee_id", "sequence_number", name="uq_fee_installment_fee_sequence"),
        )
        with op.batch_alter_table("fee_installments", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_fee_installments_id"), ["id"], unique=False)
            batch_op.create_index(batch_op.f("ix_fee_installments_student_fee_id"), ["student_fee_id"], unique=False)

    if not _has_column("payments", "fee_installment_id"):
        with op.batch_alter_table("payments", schema=None) as batch_op:
            batch_op.add_column(sa.Column("fee_installment_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_payments_fee_installment_id_fee_installments",
                "fee_installments",
                ["fee_installment_id"],
                ["id"],
            )
            batch_op.create_index(batch_op.f("ix_payments_fee_installment_id"), ["fee_installment_id"], unique=False)

    if not _has_column("payments", "receipt_number"):
        with op.batch_alter_table("payments", schema=None) as batch_op:
            batch_op.add_column(sa.Column("receipt_number", sa.String(length=50), nullable=True))
            batch_op.create_index(batch_op.f("ix_payments_receipt_number"), ["receipt_number"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    if _has_column("payments", "receipt_number"):
        with op.batch_alter_table("payments", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_payments_receipt_number"))
            batch_op.drop_column("receipt_number")

    if _has_column("payments", "fee_installment_id"):
        with op.batch_alter_table("payments", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_payments_fee_installment_id"))
            batch_op.drop_constraint("fk_payments_fee_installment_id_fee_installments", type_="foreignkey")
            batch_op.drop_column("fee_installment_id")

    if _has_table("fee_installments"):
        with op.batch_alter_table("fee_installments", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_fee_installments_student_fee_id"))
            batch_op.drop_index(batch_op.f("ix_fee_installments_id"))
        op.drop_table("fee_installments")

    if _has_column("student_fees", "fee_structure_id"):
        with op.batch_alter_table("student_fees", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_student_fees_fee_structure_id"))
            batch_op.drop_constraint("fk_student_fees_fee_structure_id_fee_structures", type_="foreignkey")
            batch_op.drop_column("fee_structure_id")

    if _has_table("fee_structures"):
        with op.batch_alter_table("fee_structures", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_fee_structures_semester_id"))
            batch_op.drop_index(batch_op.f("ix_fee_structures_name"))
            batch_op.drop_index(batch_op.f("ix_fee_structures_id"))
            batch_op.drop_index(batch_op.f("ix_fee_structures_course_id"))
            batch_op.drop_index(batch_op.f("ix_fee_structures_category_id"))
            batch_op.drop_index(batch_op.f("ix_fee_structures_academic_year_id"))
        op.drop_table("fee_structures")

    if _has_table("fee_categories"):
        with op.batch_alter_table("fee_categories", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_fee_categories_name"))
            batch_op.drop_index(batch_op.f("ix_fee_categories_id"))
        op.drop_table("fee_categories")
