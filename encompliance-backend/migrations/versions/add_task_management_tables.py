"""Add operational task and task assignment tables

Revision ID: task_management_001
Revises: 86ec248f1508
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = 'task_management_001'
down_revision = '86ec248f1508'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    # Create operational_tasks table
    if 'operational_tasks' not in table_names:
        op.create_table(
            'operational_tasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('category', sa.String(length=100), nullable=True),
            sa.Column('task_type', sa.String(length=20), nullable=False, default='one_time'),
            sa.Column('recurrence_pattern', sa.String(length=20), nullable=True),
            sa.Column('recurrence_interval', sa.Integer(), nullable=False, default=1),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('min_age_required', sa.Integer(), nullable=True),
            sa.Column('max_age_allowed', sa.Integer(), nullable=True),
            sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
            sa.Column('priority', sa.String(length=10), nullable=False, default='medium'),
            sa.Column('requires_supervision', sa.Boolean(), nullable=False, default=False),
            sa.Column('special_instructions', sa.Text(), nullable=True),
            sa.Column('location', sa.String(length=255), nullable=True),
            sa.Column('required_equipment', sa.JSON(), nullable=True),
            sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], )
        )
        op.create_index('ix_operational_tasks_id', 'operational_tasks', ['id'])
    
    # Create task_assignments table
    if 'task_assignments' not in table_names:
        op.create_table(
            'task_assignments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('operational_task_id', sa.Integer(), nullable=False),
            sa.Column('staff_member_id', sa.Integer(), nullable=False),
            sa.Column('assigned_by', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, default='assigned'),
            sa.Column('priority', sa.String(length=10), nullable=False, default='medium'),
            sa.Column('assigned_date', sa.DateTime(timezone=True), server_default=func.now()),
            sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('started_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('progress_percentage', sa.Integer(), nullable=False, default=0),
            sa.Column('time_spent_minutes', sa.Integer(), nullable=False, default=0),
            sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completion_verified', sa.Boolean(), nullable=False, default=False),
            sa.Column('verification_notes', sa.Text(), nullable=True),
            sa.Column('completion_photo_url', sa.String(length=500), nullable=True),
            sa.Column('verification_method', sa.String(length=50), nullable=True),
            sa.Column('reminder_sent_dates', sa.JSON(), nullable=True),
            sa.Column('escalation_sent', sa.Boolean(), nullable=False, default=False),
            sa.Column('escalation_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('assignment_notes', sa.Text(), nullable=True),
            sa.Column('completion_notes', sa.Text(), nullable=True),
            sa.Column('supervisor_notes', sa.Text(), nullable=True),
            sa.Column('quality_rating', sa.Integer(), nullable=True),
            sa.Column('efficiency_rating', sa.Integer(), nullable=True),
            sa.Column('requires_followup', sa.Boolean(), nullable=False, default=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['operational_task_id'], ['operational_tasks.id'], ),
            sa.ForeignKeyConstraint(['staff_member_id'], ['staff_members.id'], ),
            sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], )
        )
        op.create_index('ix_task_assignments_id', 'task_assignments', ['id'])
    
    # Add birth_date column to staff_members table
    # Check if table exists first (it should, but good practice)
    if 'staff_members' in table_names:
        columns = [c['name'] for c in inspector.get_columns('staff_members')]
        if 'birth_date' not in columns:
            op.add_column('staff_members', sa.Column('birth_date', sa.Date(), nullable=True))

def downgrade():
    # Remove birth_date column from staff_members table
    op.drop_column('staff_members', 'birth_date')
    
    # Drop task_assignments table
    op.drop_index('ix_task_assignments_id', table_name='task_assignments')
    op.drop_table('task_assignments')
    
    # Drop operational_tasks table
    op.drop_index('ix_operational_tasks_id', table_name='operational_tasks')
    op.drop_table('operational_tasks') 