#!/usr/bin/env python3
"""Fix database schema for attendance sessions."""

from app.database.database import engine
from app.database.base import Base

# Import all models to ensure they are registered with Base.metadata
from app.models import attendance, attendance_session, student, course, batch, semester, subject, user

print("Creating/verifying database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created/verified successfully!")

# Verify tables exist
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\nExisting tables: {tables}")

if 'attendance_sessions' in tables:
    print("✓ attendance_sessions table exists")
else:
    print("✗ attendance_sessions table MISSING")

if 'attendances' in tables:
    columns = [col['name'] for col in inspector.get_columns('attendances')]
    print(f"attendances columns: {columns}")
    if 'attendance_session_id' in columns:
        print("✓ attendance_session_id column exists")
    else:
        print("✗ attendance_session_id column MISSING")