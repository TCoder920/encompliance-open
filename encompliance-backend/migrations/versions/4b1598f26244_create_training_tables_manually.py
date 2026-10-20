"""Create training tables manually

Revision ID: 4b1598f26244
Revises: 64f598432fe9
Create Date: 2025-05-30 20:01:47.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b1598f26244'
down_revision: Union[str, None] = '64f598432fe9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    # Create training_programs table
    if 'training_programs' not in table_names:
        op.create_table('training_programs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('category', sa.String(length=100), nullable=True),
            sa.Column('is_mandatory', sa.Boolean(), nullable=True),
            sa.Column('requires_certification', sa.Boolean(), nullable=True),
            sa.Column('certification_valid_months', sa.Integer(), nullable=True),
            sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
            sa.Column('delivery_method', sa.String(length=50), nullable=True),
            sa.Column('prerequisites', sa.JSON(), nullable=True),
            sa.Column('reminder_schedule_days', sa.JSON(), nullable=True),
            sa.Column('auto_assign_new_staff', sa.Boolean(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_training_programs_id'), 'training_programs', ['id'], unique=False)
        op.create_index(op.f('ix_training_programs_title'), 'training_programs', ['title'], unique=False)

    # Create staff_members table
    if 'staff_members' not in table_names:
        op.create_table('staff_members',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('employee_id', sa.String(length=50), nullable=True),
            sa.Column('first_name', sa.String(length=100), nullable=False),
            sa.Column('last_name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('phone_number', sa.String(length=20), nullable=True),
            sa.Column('role', sa.String(length=20), nullable=True),
            sa.Column('department', sa.String(length=100), nullable=True),
            sa.Column('position_title', sa.String(length=100), nullable=True),
            sa.Column('hire_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('facility_administrator_id', sa.Integer(), nullable=False),
            sa.Column('facility_name', sa.String(length=255), nullable=True),
            sa.Column('facility_location', sa.String(length=255), nullable=True),
            sa.Column('training_completion_rate', sa.Integer(), nullable=True),
            sa.Column('certifications_current', sa.Integer(), nullable=True),
            sa.Column('certifications_expired', sa.Integer(), nullable=True),
            sa.Column('last_training_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('notification_preferences', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['facility_administrator_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_staff_members_id'), 'staff_members', ['id'], unique=False)
        op.create_index(op.f('ix_staff_members_employee_id'), 'staff_members', ['employee_id'], unique=False)
        op.create_index(op.f('ix_staff_members_email'), 'staff_members', ['email'], unique=False)

    # Create training_materials table
    if 'training_materials' not in table_names:
        op.create_table('training_materials',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('material_type', sa.String(length=20), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=True),
            sa.Column('file_name', sa.String(length=255), nullable=True),
            sa.Column('file_size', sa.Integer(), nullable=True),
            sa.Column('mime_type', sa.String(length=100), nullable=True),
            sa.Column('external_url', sa.String(length=500), nullable=True),
            sa.Column('embed_code', sa.Text(), nullable=True),
            sa.Column('duration_minutes', sa.Integer(), nullable=True),
            sa.Column('reading_time_minutes', sa.Integer(), nullable=True),
            sa.Column('difficulty_level', sa.String(length=20), nullable=True),
            sa.Column('version', sa.String(length=20), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('is_required', sa.Boolean(), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True),
            sa.Column('section', sa.String(length=100), nullable=True),
            sa.Column('quiz_questions', sa.JSON(), nullable=True),
            sa.Column('passing_score', sa.Integer(), nullable=True),
            sa.Column('max_attempts', sa.Integer(), nullable=True),
            sa.Column('access_restrictions', sa.JSON(), nullable=True),
            sa.Column('training_program_id', sa.Integer(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['training_program_id'], ['training_programs.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_training_materials_id'), 'training_materials', ['id'], unique=False)

    # Create training_assignments table
    if 'training_assignments' not in table_names:
        op.create_table('training_assignments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('training_program_id', sa.Integer(), nullable=False),
            sa.Column('staff_member_id', sa.Integer(), nullable=False),
            sa.Column('assigned_by', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('priority', sa.String(length=10), nullable=True),
            sa.Column('assigned_date', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('started_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('progress_percentage', sa.Integer(), nullable=True),
            sa.Column('time_spent_minutes', sa.Integer(), nullable=True),
            sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completion_verified', sa.Boolean(), nullable=True),
            sa.Column('verification_method', sa.String(length=50), nullable=True),
            sa.Column('verification_score', sa.Integer(), nullable=True),
            sa.Column('verification_notes', sa.Text(), nullable=True),
            sa.Column('reminder_sent_dates', sa.JSON(), nullable=True),
            sa.Column('escalation_sent', sa.Boolean(), nullable=True),
            sa.Column('assignment_notes', sa.Text(), nullable=True),
            sa.Column('completion_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['staff_member_id'], ['staff_members.id'], ),
            sa.ForeignKeyConstraint(['training_program_id'], ['training_programs.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_training_assignments_id'), 'training_assignments', ['id'], unique=False)

    # Create training_completions table
    if 'training_completions' not in table_names:
        op.create_table('training_completions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('training_assignment_id', sa.Integer(), nullable=False),
            sa.Column('staff_member_id', sa.Integer(), nullable=False),
            sa.Column('training_program_id', sa.Integer(), nullable=False),
            sa.Column('completion_status', sa.String(length=20), nullable=True),
            sa.Column('completed_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('completion_method', sa.String(length=50), nullable=True),
            sa.Column('verified_by', sa.Integer(), nullable=True),
            sa.Column('verification_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('verification_notes', sa.Text(), nullable=True),
            sa.Column('final_score', sa.Integer(), nullable=True),
            sa.Column('passing_score_required', sa.Integer(), nullable=True),
            sa.Column('attempts_taken', sa.Integer(), nullable=True),
            sa.Column('time_spent_minutes', sa.Integer(), nullable=True),
            sa.Column('certificate_status', sa.String(length=20), nullable=True),
            sa.Column('certificate_number', sa.String(length=100), nullable=True),
            sa.Column('certificate_file_path', sa.String(length=500), nullable=True),
            sa.Column('certificate_issued_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('expires_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('renewal_required', sa.Boolean(), nullable=True),
            sa.Column('renewal_reminder_sent', sa.Boolean(), nullable=True),
            sa.Column('compliance_notes', sa.Text(), nullable=True),
            sa.Column('audit_trail', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['staff_member_id'], ['staff_members.id'], ),
            sa.ForeignKeyConstraint(['training_assignment_id'], ['training_assignments.id'], ),
            sa.ForeignKeyConstraint(['training_program_id'], ['training_programs.id'], ),
            sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('training_assignment_id'),
            sa.UniqueConstraint('certificate_number')
        )
        op.create_index(op.f('ix_training_completions_id'), 'training_completions', ['id'], unique=False)

    # Create training_program_facility_types association table
    if 'training_program_facility_types' not in table_names:
        op.create_table('training_program_facility_types',
            sa.Column('training_program_id', sa.Integer(), nullable=False),
            sa.Column('facility_type_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['facility_type_id'], ['facility_types.id'], ),
            sa.ForeignKeyConstraint(['training_program_id'], ['training_programs.id'], ),
            sa.PrimaryKeyConstraint('training_program_id', 'facility_type_id')
        )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('training_program_facility_types')
    op.drop_index(op.f('ix_training_completions_id'), table_name='training_completions')
    op.drop_table('training_completions')
    op.drop_index(op.f('ix_training_assignments_id'), table_name='training_assignments')
    op.drop_table('training_assignments')
    op.drop_index(op.f('ix_training_materials_id'), table_name='training_materials')
    op.drop_table('training_materials')
    op.drop_index(op.f('ix_staff_members_email'), table_name='staff_members')
    op.drop_index(op.f('ix_staff_members_employee_id'), table_name='staff_members')
    op.drop_index(op.f('ix_staff_members_id'), table_name='staff_members')
    op.drop_table('staff_members')
    op.drop_index(op.f('ix_training_programs_title'), table_name='training_programs')
    op.drop_index(op.f('ix_training_programs_id'), table_name='training_programs')
    op.drop_table('training_programs')
