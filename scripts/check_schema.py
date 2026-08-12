"""Diagnostic script to inspect database schema without modifying it."""
import os
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./student_management.db")

def mask_password(url: str) -> str:
    """Mask password in database URL for safe display."""
    if "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "@" in rest:
        credentials, host = rest.split("@", 1)
        if ":" in credentials:
            user, _ = credentials.split(":", 1)
            return f"{scheme}://{user}:****@{host}"
    return url

def main():
    print("=" * 60)
    print("DATABASE SCHEMA DIAGNOSTIC")
    print("=" * 60)
    
    # Show database URL (masked)
    print(f"\nDatabase URL: {mask_password(DATABASE_URL)}")
    
    # Create engine and inspector
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Get all tables
    tables = inspector.get_table_names()
    print(f"\nExisting tables: {tables}")
    
    # Check expected tables
    expected_tables = [
        "users", "courses", "academic_years", "semesters", 
        "subjects", "batches", "students", "attendance_sessions",
        "attendances", "student_fees", "payments"
    ]
    
    print("\n" + "=" * 60)
    print("TABLE EXISTENCE CHECK")
    print("=" * 60)
    for table in expected_tables:
        exists = table in tables
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"{status}: {table}")
    
    # Check students table columns
    print("\n" + "=" * 60)
    print("STUDENTS TABLE COLUMNS")
    print("=" * 60)
    if "students" in tables:
        columns = [col["name"] for col in inspector.get_columns("students")]
        expected_columns = [
            "id", "student_code", "first_name", "last_name", "email",
            "phone", "date_of_birth", "course_id", "academic_year_id",
            "semester_id", "batch_id", "admission_date", "status",
            "created_at"
        ]
        for col in expected_columns:
            exists = col in columns
            status = "✓" if exists else "✗"
            print(f"{status} {col}")
    
    # Check attendances table columns
    print("\n" + "=" * 60)
    print("ATTENDANCES TABLE COLUMNS")
    print("=" * 60)
    if "attendances" in tables:
        columns = [col["name"] for col in inspector.get_columns("attendances")]
        expected_columns = [
            "id", "attendance_session_id", "student_id", "status",
            "remarks", "marked_by", "created_at", "updated_at"
        ]
        for col in expected_columns:
            exists = col in columns
            status = "✓" if exists else "✗"
            print(f"{status} {col}")
    
    # Check attendance_sessions table
    print("\n" + "=" * 60)
    print("ATTENDANCE_SESSIONS TABLE")
    print("=" * 60)
    if "attendance_sessions" in tables:
        columns = [col["name"] for col in inspector.get_columns("attendance_sessions")]
        print("Columns:", columns)
    else:
        print("✗ TABLE MISSING")
    
    # Check Alembic version
    print("\n" + "=" * 60)
    print("ALEMBIC VERSION")
    print("=" * 60)
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
        
        # Get current version
        from sqlalchemy import text
        with engine.connect() as conn:
            if "alembic_version" in tables:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar_one_or_none()
                print(f"Current Alembic revision: {version}")
            else:
                print("✗ alembic_version table not found")
    except Exception as e:
        print(f"Error checking Alembic version: {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()