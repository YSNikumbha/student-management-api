"""add student documents notifications

Revision ID: a8c4e2d1f930
Revises: f7a2d5c8b4e1
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a8c4e2d1f930"
down_revision: Union[str, Sequence[str], None] = "f7a2d5c8b4e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def upgrade() -> None:
    """Upgrade schema."""
    if not _has_table("student_documents"):
        op.create_table(
            "student_documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("student_id", sa.Integer(), nullable=False),
            sa.Column("document_type", sa.String(length=50), nullable=False),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("stored_filename", sa.String(length=500), nullable=False),
            sa.Column("content_type", sa.String(length=100), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("uploaded_by", sa.Integer(), nullable=False),
            sa.Column("uploaded_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
            sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("stored_filename"),
        )
        with op.batch_alter_table("student_documents", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_student_documents_document_type"), ["document_type"], unique=False)
            batch_op.create_index(batch_op.f("ix_student_documents_id"), ["id"], unique=False)
            batch_op.create_index(batch_op.f("ix_student_documents_student_id"), ["student_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_student_documents_uploaded_by"), ["uploaded_by"], unique=False)

    if not _has_table("notifications"):
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=150), nullable=False),
            sa.Column("message", sa.String(length=1000), nullable=False),
            sa.Column("type", sa.String(length=50), nullable=False),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("read_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("notifications", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_notifications_created_at"), ["created_at"], unique=False)
            batch_op.create_index(batch_op.f("ix_notifications_id"), ["id"], unique=False)
            batch_op.create_index(batch_op.f("ix_notifications_is_read"), ["is_read"], unique=False)
            batch_op.create_index(batch_op.f("ix_notifications_type"), ["type"], unique=False)
            batch_op.create_index(batch_op.f("ix_notifications_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    if _has_table("notifications"):
        with op.batch_alter_table("notifications", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_notifications_user_id"))
            batch_op.drop_index(batch_op.f("ix_notifications_type"))
            batch_op.drop_index(batch_op.f("ix_notifications_is_read"))
            batch_op.drop_index(batch_op.f("ix_notifications_id"))
            batch_op.drop_index(batch_op.f("ix_notifications_created_at"))
        op.drop_table("notifications")

    if _has_table("student_documents"):
        with op.batch_alter_table("student_documents", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_student_documents_uploaded_by"))
            batch_op.drop_index(batch_op.f("ix_student_documents_student_id"))
            batch_op.drop_index(batch_op.f("ix_student_documents_id"))
            batch_op.drop_index(batch_op.f("ix_student_documents_document_type"))
        op.drop_table("student_documents")
