"""Inspect actual database schema vs expected models."""
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import configure_mappers
from app.database.database import DATABASE_URL
from app.models.base import Base
from app.models import (
    AcademicYear, Attendance, AttendanceSession, Batch, Course,
    Payment, Semester, Student, StudentFee, Subject, User
)

# Configure mappers first
configure_mappers()

# Create engine and inspector
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print("=" * 80)
print("ACTUAL DATABASE SCHEMA")
print("=" * 80)

# Get all tables
actual_tables = inspector.get_table_names()
print(f"\nTables in database: {sorted(actual_tables)}")

# Expected tables from models
expected_tables = sorted(Base.metadata.tables.keys())
print(f"\nExpected tables from models: {expected_tables}")

# Check for missing tables
missing_tables = set(expected_tables) - set(actual_tables)
if missing_tables:
    print(f"\n❌ MISSING TABLES: {sorted(missing_tables)}")
else:
    print("\n✅ All expected tables exist")

# Detailed column inspection
print("\n" + "=" * 80)
print("COLUMN DETAILS")
print("=" * 80)

for table_name in sorted(actual_tables):
    if table_name in expected_tables:
        print(f"\n{table_name}:")
        columns = inspector.get_columns(table_name)
        for col in columns:
            print(f"  - {col['name']}: {col['type']} (nullable={col.get('nullable', True)})")
        
        # Check foreign keys
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            print(f"  Foreign Keys:")
            for fk in fks:
                print(f"    {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

# Specific checks for known issues
print("\n" + "=" * 80)
print("SPECIFIC CHECKS")
print("=" * 80)

# Check students table
if 'students' in actual_tables:
    columns = [c['name'] for c in inspector.get_columns('students')]
    required = ['academic_year_id', 'semester_id', 'batch_id', 'admission_date']
    for col in required:
        if col in columns:
            print(f"✅ students.{col} exists")
        else:
            print(f"❌ students.{col} MISSING")

# Check attendance_sessions table
if 'attendance_sessions' in actual_tables:
    print("✅ attendance_sessions table exists")
    columns = [c['name'] for c in inspector.get_columns('attendance_sessions')]
    print(f"  Columns: {columns}")
else:
    print("❌ attendance_sessions table MISSING")

# Check attendances table
if 'attendances' in actual_tables:
    print("✅ attendances table exists")
    columns = [c['name'] for c in inspector.get_columns('attendances')]
    if 'attendance_session_id' in columns:
        print("✅ attendances.attendance_session_id exists")
    else:
        print("❌ attendances.attendance_session_id MISSING")
else:
    print("❌ attendances table MISSING")

print("\n" + "=" * 80)
print("ALEMBIC STATUS")
print("=" * 80)

from alembic import command
from alembic.config import Config
from app.database.database import DATABASE_URL

alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

try:
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    context = MigrationContext.configure(session.connection())
    current_rev = context.get_current_revision()
    print(f"Current revision: {current_rev}")
    
    # Get heads
    from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(alembic_cfg)
    heads = script.get_heads()
    print(f"Heads: {heads}")
    
    if current_rev in heads:
        print("✅ Database is up to date")
    else:
        print(f"⚠️  Database is NOT up to date (current: {current_rev}, heads: {heads})")
        
except Exception as e:
    print(f"Error checking Alembic status: {e}")

session.close()