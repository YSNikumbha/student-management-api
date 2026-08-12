"""Check foreign keys and indexes in the database."""
from sqlalchemy import create_engine, inspect
from app.database.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print("=== FOREIGN KEYS AND INDEXES ===\n")

tables = inspector.get_table_names()

for table in sorted(tables):
    if table == 'alembic_version':
        continue
    
    print(f"{table}:")
    
    # Foreign keys
    fks = inspector.get_foreign_keys(table)
    if fks:
        for fk in fks:
            print(f"  FK: {fk['name']}")
            print(f"      Columns: {fk['constrained_columns']}")
            print(f"      References: {fk['referred_table']}.{fk['referred_columns']}")
    else:
        print(f"  No foreign keys")
    
    # Indexes
    indexes = inspector.get_indexes(table)
    if indexes:
        for idx in indexes:
            print(f"  Index: {idx['name']} on {idx['column_names']} (unique={idx['unique']})")
    
    print()

# Check specific foreign keys that should exist
print("\n=== CRITICAL FOREIGN KEY CHECKS ===\n")

critical_fks = {
    'students': [
        ('course_id', 'courses.id'),
        ('academic_year_id', 'academic_years.id'),
        ('semester_id', 'semesters.id'),
        ('batch_id', 'batches.id'),
    ],
    'attendances': [
        ('student_id', 'students.id'),
        ('attendance_session_id', 'attendance_sessions.id'),
        ('marked_by', 'users.id'),
    ],
    'attendance_sessions': [
        ('course_id', 'courses.id'),
        ('batch_id', 'batches.id'),
        ('semester_id', 'semesters.id'),
        ('subject_id', 'subjects.id'),
        ('created_by', 'users.id'),
    ]
}

for table, expected_fks in critical_fks.items():
    if table not in tables:
        print(f"❌ Table {table} does not exist")
        continue
    
    actual_fks = inspector.get_foreign_keys(table)
    actual_refs = set()
    for fk in actual_fks:
        for col, ref_col in zip(fk['constrained_columns'], fk['referred_columns']):
            actual_refs.add((col, f"{fk['referred_table']}.{ref_col}"))
    
    for col, ref in expected_fks:
        if (col, ref) in actual_refs:
            print(f"✅ {table}.{col} -> {ref}")
        else:
            print(f"❌ {table}.{col} -> {ref} MISSING")

# Check critical indexes
print("\n=== CRITICAL INDEX CHECKS ===\n")

critical_indexes = {
    'students': ['student_code', 'email', 'academic_year_id', 'semester_id', 'batch_id'],
    'attendances': ['student_id', 'attendance_session_id', 'date'],
    'attendance_sessions': ['course_id', 'batch_id', 'semester_id', 'subject_id'],
}

for table, expected_indexes in critical_indexes.items():
    if table not in tables:
        continue
    
    actual_indexes = inspector.get_indexes(table)
    indexed_columns = set()
    for idx in actual_indexes:
        indexed_columns.update(idx['column_names'])
    
    for col in expected_indexes:
        if col in indexed_columns:
            print(f"✅ {table}.{col} is indexed")
        else:
            print(f"❌ {table}.{col} is NOT indexed")