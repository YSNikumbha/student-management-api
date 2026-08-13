"""add roles and permissions

Revision ID: 0f3b2c1d4e5f
Revises: b4f7c2d9a103
Create Date: 2026-08-12 00:00:00.000000
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0f3b2c1d4e5f"
down_revision: Union[str, Sequence[str], None] = "b4f7c2d9a103"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = [
    ("dashboard.view", "View Dashboard", "View dashboard metrics and summaries", "Dashboard"),
    ("students.view", "View Students", "View student profiles and lists", "Students"),
    ("students.create", "Create Students", "Create student records", "Students"),
    ("students.edit", "Edit Students", "Update student records", "Students"),
    ("students.delete", "Delete Students", "Delete student records", "Students"),
    ("classes.view", "View Classes", "View classes and batches", "Classes"),
    ("classes.create", "Create Classes", "Create classes and batches", "Classes"),
    ("classes.edit", "Edit Classes", "Update classes and batches", "Classes"),
    ("classes.delete", "Delete Classes", "Delete classes and batches", "Classes"),
    ("attendance.view", "View Attendance", "View attendance records and sessions", "Attendance"),
    ("attendance.mark", "Mark Attendance", "Mark student attendance", "Attendance"),
    ("attendance.edit", "Edit Attendance", "Update attendance records", "Attendance"),
    ("attendance.delete", "Delete Attendance", "Delete attendance records", "Attendance"),
    ("fees.view", "View Fees", "View fee records and payments", "Fee Management"),
    ("fees.create", "Create Fees", "Create fee records and structures", "Fee Management"),
    ("fees.edit", "Edit Fees", "Update fee records and structures", "Fee Management"),
    ("fees.delete", "Delete Fees", "Delete fee records and structures", "Fee Management"),
    ("fees.record_payment", "Record Payments", "Record student fee payments", "Fee Management"),
    ("reports.view", "View Reports", "View academic, attendance, and finance reports", "Reports"),
    ("reports.export", "Export Reports", "Export reports as CSV or PDF", "Reports"),
    ("users.view", "View Users", "View user accounts", "User Management"),
    ("users.create", "Create Users", "Create user accounts", "User Management"),
    ("users.edit", "Edit Users", "Update user accounts", "User Management"),
    ("users.deactivate", "Deactivate Users", "Deactivate user accounts", "User Management"),
    ("roles.view", "View Roles", "View roles and permissions", "Roles & Permissions"),
    ("roles.manage", "Manage Roles", "Create roles and change permissions", "Roles & Permissions"),
    ("settings.view", "View Settings", "View system settings", "Settings"),
    ("settings.edit", "Edit Settings", "Update system settings", "Settings"),
    ("notifications.view", "View Notifications", "View notifications", "Notifications"),
    ("notifications.manage", "Manage Notifications", "Manage notification preferences and messages", "Notifications"),
    ("audit.view", "View Audit Logs", "View audit logs", "Audit"),
]

ROLE_MATRIX = {
    "super_admin": list(range(1, len(PERMISSIONS) + 1)),
    "admin": list(range(1, len(PERMISSIONS) + 1)),
    "teacher": [1, 2, 6, 10, 11, 12, 19],
    "accountant": [1, 2, 6, 14, 15, 16, 18, 19, 20],
    "staff": [1, 2, 6, 10, 11, 12, 14, 18, 19, 20, 27, 29],
    "viewer": [1, 2, 6, 10, 14, 19, 21, 25, 27, 29, 31],
}

ROLES = [
    (1, "super_admin", "Super Admin", "Full system access including protected system roles."),
    (2, "admin", "Admin", "Operational administrator with users, reports, and settings access."),
    (3, "teacher", "Teacher", "Academic staff access for students, classes, attendance, and academic reports."),
    (4, "accountant", "Accountant", "Finance staff access for fees, payments, and financial reporting."),
    (5, "staff", "Staff", "Legacy staff role preserved for existing installations."),
    (6, "viewer", "Viewer", "Read-only access to operational modules."),
]


def upgrade() -> None:
    now = datetime.now(UTC)

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("module", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_permissions_code"), "permissions", ["code"], unique=True)
    op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)
    op.create_index(op.f("ix_permissions_module"), "permissions", ["module"], unique=False)

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
    )
    op.create_index(op.f("ix_role_permissions_id"), "role_permissions", ["id"], unique=False)
    op.create_index(op.f("ix_role_permissions_permission_id"), "role_permissions", ["permission_id"], unique=False)
    op.create_index(op.f("ix_role_permissions_role_id"), "role_permissions", ["role_id"], unique=False)

    role_table = sa.table(
        "roles",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("display_name", sa.String),
        sa.column("description", sa.Text),
        sa.column("is_system", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    permission_table = sa.table(
        "permissions",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("module", sa.String),
        sa.column("created_at", sa.DateTime),
    )
    role_permission_table = sa.table(
        "role_permissions",
        sa.column("id", sa.Integer),
        sa.column("role_id", sa.Integer),
        sa.column("permission_id", sa.Integer),
    )

    op.bulk_insert(
        role_table,
        [
            {
                "id": role_id,
                "name": name,
                "display_name": display_name,
                "description": description,
                "is_system": True,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            for role_id, name, display_name, description in ROLES
        ],
    )
    op.bulk_insert(
        permission_table,
        [
            {
                "id": index,
                "code": code,
                "name": name,
                "description": description,
                "module": module,
                "created_at": now,
            }
            for index, (code, name, description, module) in enumerate(PERMISSIONS, start=1)
        ],
    )
    role_permission_rows = []
    row_id = 1
    for role_id, role_name, _display_name, _description in ROLES:
        for permission_id in ROLE_MATRIX[role_name]:
            role_permission_rows.append(
                {
                    "id": row_id,
                    "role_id": role_id,
                    "permission_id": permission_id,
                }
            )
            row_id += 1
    op.bulk_insert(role_permission_table, role_permission_rows)

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("role", existing_type=sa.String(length=20), type_=sa.String(length=50), existing_nullable=False)
        batch_op.add_column(sa.Column("role_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_users_role_id"), ["role_id"], unique=False)
        batch_op.create_foreign_key("fk_users_role_id_roles", "roles", ["role_id"], ["id"])

    op.execute("UPDATE users SET role = lower(replace(replace(role, '-', '_'), ' ', '_'))")
    op.execute("UPDATE users SET role = 'super_admin' WHERE role IN ('superadmin', 'super administrator')")
    op.execute("UPDATE users SET role = 'admin' WHERE role IN ('administrator')")
    op.execute("UPDATE users SET role_id = 1 WHERE role = 'super_admin'")
    op.execute("UPDATE users SET role_id = 2 WHERE role = 'admin'")
    op.execute("UPDATE users SET role_id = 3 WHERE role = 'teacher'")
    op.execute("UPDATE users SET role_id = 4 WHERE role = 'accountant'")
    op.execute("UPDATE users SET role_id = 5 WHERE role = 'staff'")
    op.execute("UPDATE users SET role_id = 6 WHERE role = 'viewer'")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("fk_users_role_id_roles", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_users_role_id"))
        batch_op.drop_column("role_id")
        batch_op.alter_column("role", existing_type=sa.String(length=50), type_=sa.String(length=20), existing_nullable=False)

    op.drop_index(op.f("ix_role_permissions_role_id"), table_name="role_permissions")
    op.drop_index(op.f("ix_role_permissions_permission_id"), table_name="role_permissions")
    op.drop_index(op.f("ix_role_permissions_id"), table_name="role_permissions")
    op.drop_table("role_permissions")

    op.drop_index(op.f("ix_permissions_module"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_id"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_code"), table_name="permissions")
    op.drop_table("permissions")

    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")
