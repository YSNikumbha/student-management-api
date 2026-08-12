from sqlalchemy import create_engine, inspect
from app.database.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print("=== DATABASE INSPECTION ===")
print(f"Database URL: {DATABASE_URL}")
print()

# Check tables
tables = inspector.get_table_names()
print(f"Tables found: {tables}")
print()

# Check students table
if 'students' in tables:
    print("=== STUDENTS TABLE ===")
    columns = inspector.get_columns('students')
    for col in columns:
        print(f"  {col['name']}: {col['type']}")
    print()
    
    # Check for missing columns
    column_names = {col['name'] for col in columns}
    expected = {'id', 'student_code', 'first_name', 'last_name', 'email', 'phone', 
                'date_of_birth', 'course_id', 'academic_year_id', 'semester_id', 
                'batch_id', 'admission_date', 'status', 'created_at'}
    missing = expected - column_names
    if missing:
        print(f"  MISSING COLUMNS: {missing}")
    else:
        print("  All expected columns present")
    print()

# Check attendance_sessions table
if 'attendance_sessions' in tables:
    print("=== ATTENDANCE_SESSIONS TABLE ===")
    columns = inspector.get_columns('attendance_sessions')
    for col in columns:
        print(f"  {col['name']}: {col['type']}")
    print()
else:
    print("=== ATTENDANCE_SESSIONS TABLE MISSING ===")
    print()

# Check attendances table
if 'attendances' in tables:
    print("=== ATTENDANCES TABLE ===")
    columns = inspector.get_columns('attendances')
    for col in columns:
        print(f"  {col['name']}: {col['type']}")
    print()
    
    # Check for missing columns
    column_names = {col['name'] for col in columns}
    expected = {'id', 'attendance_session_id', 'student_id', 'status', 'remarks', 
                'marked_by', 'created_at', 'updated_at'}
    missing = expected - column_names
    if missing:
        print(f"  MISSING COLUMNS: {missing}")
    else:
        print("  All expected columns present")
    print()

# Check alembic version
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    version = result.scalar()
    print(f"=== ALEMBIC VERSION: {version} ===")