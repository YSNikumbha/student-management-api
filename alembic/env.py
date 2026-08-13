from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import text

from alembic import context
from app.database.base import Base
from app.database.database import DATABASE_URL
from app.models.academic_year import AcademicYear  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401
from app.models.attendance_session import AttendanceSession  # noqa: F401
from app.models.batch import Batch  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.fee_category import FeeCategory  # noqa: F401
from app.models.fee_installment import FeeInstallment  # noqa: F401
from app.models.fee_structure import FeeStructure  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.role_permission import Permission, Role, RolePermission  # noqa: F401
from app.models.semester import Semester  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.student_fee import StudentFee  # noqa: F401
from app.models.subject import Subject  # noqa: F401
from app.models.user import User  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        if connection.dialect.name == "postgresql":
            # One historical revision id is longer than Alembic's default
            # VARCHAR(32) version column. PostgreSQL enforces that limit, so
            # create/expand the version table in its own committed transaction
            # before Alembic starts the migration transaction.
            with connection.begin():
                connection.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS alembic_version (
                            version_num VARCHAR(255) NOT NULL,
                            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                        )
                        """
                    )
                )
                connection.execute(
                    text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)")
                )
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
