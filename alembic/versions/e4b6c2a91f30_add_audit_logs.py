"""add audit logs

Revision ID: e4b6c2a91f30
Revises: d8c1a7f4b921
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e4b6c2a91f30"
down_revision: Union[str, Sequence[str], None] = "d8c1a7f4b921"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Upgrade schema."""
    if not _has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("entity_type", sa.String(length=100), nullable=False),
            sa.Column("entity_id", sa.String(length=100), nullable=True),
            sa.Column("description", sa.String(length=1000), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("audit_logs", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_audit_logs_action"), ["action"], unique=False)
            batch_op.create_index(batch_op.f("ix_audit_logs_created_at"), ["created_at"], unique=False)
            batch_op.create_index(batch_op.f("ix_audit_logs_entity_id"), ["entity_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_audit_logs_entity_type"), ["entity_type"], unique=False)
            batch_op.create_index(batch_op.f("ix_audit_logs_id"), ["id"], unique=False)
            batch_op.create_index(batch_op.f("ix_audit_logs_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    if _has_table("audit_logs"):
        with op.batch_alter_table("audit_logs", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_audit_logs_user_id"))
            batch_op.drop_index(batch_op.f("ix_audit_logs_id"))
            batch_op.drop_index(batch_op.f("ix_audit_logs_entity_type"))
            batch_op.drop_index(batch_op.f("ix_audit_logs_entity_id"))
            batch_op.drop_index(batch_op.f("ix_audit_logs_created_at"))
            batch_op.drop_index(batch_op.f("ix_audit_logs_action"))
        op.drop_table("audit_logs")
