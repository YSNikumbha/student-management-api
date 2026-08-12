"""add user last login timestamp

Revision ID: d8c1a7f4b921
Revises: ac4915a9e718
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d8c1a7f4b921"
down_revision: Union[str, Sequence[str], None] = "ac4915a9e718"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()
    if table_name not in table_names:
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    """Upgrade schema."""
    if not _has_column("users", "last_login_at"):
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.add_column(sa.Column("last_login_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    if _has_column("users", "last_login_at"):
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.drop_column("last_login_at")
