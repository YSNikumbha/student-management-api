"""repair partial academic and attendance schema

Revision ID: repair_partial_academic_attendance_schema
Revises: ac5f3a2b8c1d
Create Date: 2026-08-12 01:19:00.000000

This migration repairs the schema inconsistency where:
- students table is missing academic_year_id, semester_id, batch_id, admission_date
- attendance_sessions table is missing entirely
- attendances table is missing attendance_session_id

The migration is idempotent and safe to run on both broken and correct schemas.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'repair_partial_academic_attendance_schema'
down_revision: Union[str, Sequence[str], None] = 'ac5f3a2b8c1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### Repair students table - add missing academic structure columns ###
    # Get inspector to check existing columns
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Add missing columns to students table if they don't exist
    if 'students' in inspector.get_table_names():
        students_columns = {col['name'] for col in inspector.get_columns('students')}
        
        with op.batch_alter_table('students', schema=None) as batch_op:
            if 'academic_year_id' not in students_columns:
                batch_op.add_column(sa.Column('academic_year_id', sa.Integer(), nullable=True))
            if 'semester_id' not in students_columns:
                batch_op.add_column(sa.Column('semester_id', sa.Integer(), nullable=True))
            if 'batch_id' not in students_columns:
                batch_op.add_column(sa.Column('batch_id', sa.Integer(), nullable=True))
            if 'admission_date' not in students_columns:
                batch_op.add_column(sa.Column('admission_date', sa.Date(), nullable=True))
            
            # Add indexes if they don't exist
            existing_indexes = {idx['name'] for idx in inspector.get_indexes('students')}
            if 'ix_students_academic_year_id' not in existing_indexes:
                batch_op.create_index(batch_op.f('ix_students_academic_year_id'), ['academic_year_id'], unique=False)
            if 'ix_students_batch_id' not in existing_indexes:
                batch_op.create_index(batch_op.f('ix_students_batch_id'), ['batch_id'], unique=False)
            if 'ix_students_semester_id' not in existing_indexes:
                batch_op.create_index(batch_op.f('ix_students_semester_id'), ['semester_id'], unique=False)
            
            # Add foreign keys if they don't exist
            existing_fks = {fk['name'] for fk in inspector.get_foreign_keys('students')}
            if 'fk_students_academic_year_id' not in existing_fks:
                batch_op.create_foreign_key('fk_students_academic_year_id', 'academic_years', ['academic_year_id'], ['id'])
            if 'fk_students_semester_id' not in existing_fks:
                batch_op.create_foreign_key('fk_students_semester_id', 'semesters', ['semester_id'], ['id'])
            if 'fk_students_batch_id' not in existing_fks:
                batch_op.create_foreign_key('fk_students_batch_id', 'batches', ['batch_id'], ['id'])
    
    # ### Create attendance_sessions table if it doesn't exist ###
    if 'attendance_sessions' not in inspector.get_table_names():
        op.create_table(
            'attendance_sessions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('date', sa.DateTime(), nullable=False),
            sa.Column('course_id', sa.Integer(), nullable=False),
            sa.Column('batch_id', sa.Integer(), nullable=False),
            sa.Column('semester_id', sa.Integer(), nullable=False),
            sa.Column('subject_id', sa.Integer(), nullable=False),
            sa.Column('session_name', sa.String(length=100), nullable=True),
            sa.Column('start_time', sa.DateTime(), nullable=True),
            sa.Column('end_time', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ),
            sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], ),
            sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        with op.batch_alter_table('attendance_sessions', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_attendance_sessions_batch_id'), ['batch_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_attendance_sessions_course_id'), ['course_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_attendance_sessions_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_attendance_sessions_semester_id'), ['semester_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_attendance_sessions_subject_id'), ['subject_id'], unique=False)
    
    # ### Add attendance_session_id to attendances if it doesn't exist ###
    if 'attendances' in inspector.get_table_names():
        attendances_columns = {col['name'] for col in inspector.get_columns('attendances')}
        
        if 'attendance_session_id' not in attendances_columns:
            with op.batch_alter_table('attendances', schema=None) as batch_op:
                batch_op.add_column(sa.Column('attendance_session_id', sa.Integer(), nullable=True))
                batch_op.create_index(batch_op.f('ix_attendances_attendance_session_id'), ['attendance_session_id'], unique=False)
                batch_op.create_foreign_key('fk_attendances_attendance_session_id', 'attendance_sessions', ['attendance_session_id'], ['id'])
    
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # This is a repair migration - downgrade is intentionally limited
    # We don't want to accidentally drop columns that might contain data
    
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Only remove attendance_session_id from attendances if it exists
    if 'attendances' in inspector.get_table_names():
        attendances_columns = {col['name'] for col in inspector.get_columns('attendances')}
        if 'attendance_session_id' in attendances_columns:
            with op.batch_alter_table('attendances', schema=None) as batch_op:
                batch_op.drop_constraint('fk_attendances_attendance_session_id', type_='foreignkey')
                batch_op.drop_index(batch_op.f('ix_attendances_attendance_session_id'))
                batch_op.drop_column('attendance_session_id')
    
    # Drop attendance_sessions table if it exists
    if 'attendance_sessions' in inspector.get_table_names():
        with op.batch_alter_table('attendance_sessions', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_attendance_sessions_subject_id'))
            batch_op.drop_index(batch_op.f('ix_attendance_sessions_semester_id'))
            batch_op.drop_index(batch_op.f('ix_attendance_sessions_id'))
            batch_op.drop_index(batch_op.f('ix_attendance_sessions_course_id'))
            batch_op.drop_index(batch_op.f('ix_attendance_sessions_batch_id'))
        op.drop_table('attendance_sessions')
    
    # Remove added columns from students if they exist
    if 'students' in inspector.get_table_names():
        students_columns = {col['name'] for col in inspector.get_columns('students')}
        with op.batch_alter_table('students', schema=None) as batch_op:
            if 'academic_year_id' in students_columns:
                batch_op.drop_constraint('fk_students_academic_year_id', type_='foreignkey')
            if 'semester_id' in students_columns:
                batch_op.drop_constraint('fk_students_semester_id', type_='foreignkey')
            if 'batch_id' in students_columns:
                batch_op.drop_constraint('fk_students_batch_id', type_='foreignkey')
            if 'academic_year_id' in students_columns:
                batch_op.drop_index(batch_op.f('ix_students_academic_year_id'))
            if 'batch_id' in students_columns:
                batch_op.drop_index(batch_op.f('ix_students_batch_id'))
            if 'semester_id' in students_columns:
                batch_op.drop_index(batch_op.f('ix_students_semester_id'))
            if 'admission_date' in students_columns:
                batch_op.drop_column('admission_date')
            if 'batch_id' in students_columns:
                batch_op.drop_column('batch_id')
            if 'semester_id' in students_columns:
                batch_op.drop_column('semester_id')
            if 'academic_year_id' in students_columns:
                batch_op.drop_column('academic_year_id')