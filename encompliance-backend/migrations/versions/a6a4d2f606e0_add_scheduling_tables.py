"""add scheduling tables

Revision ID: a6a4d2f606e0
Revises: 20c72e694aa6
Create Date: 2025-11-17 02:28:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6a4d2f606e0'
down_revision = '20c72e694aa6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'shifts' not in table_names:
        op.create_table(
            'shifts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('staff_member_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.String(length=1000), nullable=True),
            sa.Column('role', sa.String(length=100), nullable=True),
            sa.Column('department', sa.String(length=100), nullable=True),
            sa.Column('location', sa.String(length=255), nullable=True),
            sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('break_minutes', sa.Integer(), nullable=True),
            sa.Column('timezone', sa.String(length=64), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('color_code', sa.String(length=20), nullable=True),
            sa.Column('coverage_tags', sa.JSON(), nullable=True),
            sa.Column('compliance_notes', sa.String(length=1000), nullable=True),
            sa.Column('recurrence_pattern', sa.String(length=20), nullable=True),
            sa.Column('recurrence_interval', sa.Integer(), nullable=True),
            sa.Column('recurrence_days', sa.JSON(), nullable=True),
            sa.Column('recurrence_ends_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('conflict_code', sa.String(length=50), nullable=True),
            sa.Column('conflict_reason', sa.String(length=255), nullable=True),
            sa.Column('last_conflict_check', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_locked', sa.Boolean(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id']),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id']),
            sa.ForeignKeyConstraint(['staff_member_id'], ['staff_members.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_shifts_facility_id'), 'shifts', ['facility_id'], unique=False)
        op.create_index(op.f('ix_shifts_id'), 'shifts', ['id'], unique=False)
        op.create_index(op.f('ix_shifts_is_deleted'), 'shifts', ['is_deleted'], unique=False)
        op.create_index(op.f('ix_shifts_staff_member_id'), 'shifts', ['staff_member_id'], unique=False)
        op.create_index(op.f('ix_shifts_status'), 'shifts', ['status'], unique=False)

    if 'staff_availability' not in table_names:
        op.create_table(
            'staff_availability',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('staff_member_id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('day_of_week', sa.String(length=20), nullable=False),
            sa.Column('start_time', sa.String(length=5), nullable=False),
            sa.Column('end_time', sa.String(length=5), nullable=False),
            sa.Column('preference_level', sa.Integer(), nullable=True),
            sa.Column('effective_from', sa.DateTime(timezone=True), nullable=True),
            sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('exception_dates', sa.JSON(), nullable=True),
            sa.Column('notes', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id']),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id']),
            sa.ForeignKeyConstraint(['staff_member_id'], ['staff_members.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_staff_availability_facility_id'), 'staff_availability', ['facility_id'], unique=False)
        op.create_index(op.f('ix_staff_availability_id'), 'staff_availability', ['id'], unique=False)
        op.create_index(op.f('ix_staff_availability_staff_member_id'), 'staff_availability', ['staff_member_id'], unique=False)
        op.create_index(op.f('ix_staff_availability_status'), 'staff_availability', ['status'], unique=False)

    if 'time_off_requests' not in table_names:
        op.create_table(
            'time_off_requests',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('staff_member_id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('category', sa.String(length=20), nullable=True),
            sa.Column('requested_hours', sa.Integer(), nullable=True),
            sa.Column('is_paid', sa.Boolean(), nullable=True),
            sa.Column('reason', sa.String(length=1000), nullable=True),
            sa.Column('supporting_files', sa.JSON(), nullable=True),
            sa.Column('requested_by', sa.Integer(), nullable=False),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('decision_notes', sa.String(length=1000), nullable=True),
            sa.Column('audit_trail', sa.JSON(), nullable=True),
            sa.Column('overlaps_shift_ids', sa.JSON(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id']),
            sa.ForeignKeyConstraint(['requested_by'], ['users.id']),
            sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
            sa.ForeignKeyConstraint(['staff_member_id'], ['staff_members.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_time_off_requests_facility_id'), 'time_off_requests', ['facility_id'], unique=False)
        op.create_index(op.f('ix_time_off_requests_id'), 'time_off_requests', ['id'], unique=False)
        op.create_index(op.f('ix_time_off_requests_is_deleted'), 'time_off_requests', ['is_deleted'], unique=False)
        op.create_index(op.f('ix_time_off_requests_staff_member_id'), 'time_off_requests', ['staff_member_id'], unique=False)
        op.create_index(op.f('ix_time_off_requests_status'), 'time_off_requests', ['status'], unique=False)

    if 'shift_swap_requests' not in table_names:
        op.create_table(
            'shift_swap_requests',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('shift_id', sa.Integer(), nullable=False),
            sa.Column('requested_by_staff_id', sa.Integer(), nullable=False),
            sa.Column('requested_to_staff_id', sa.Integer(), nullable=True),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('resolved_by', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('reason', sa.String(length=1000), nullable=True),
            sa.Column('admin_notes', sa.String(length=1000), nullable=True),
            sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id']),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id']),
            sa.ForeignKeyConstraint(['requested_by_staff_id'], ['staff_members.id']),
            sa.ForeignKeyConstraint(['requested_to_staff_id'], ['staff_members.id']),
            sa.ForeignKeyConstraint(['resolved_by'], ['users.id']),
            sa.ForeignKeyConstraint(['shift_id'], ['shifts.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_shift_swap_requests_facility_id'), 'shift_swap_requests', ['facility_id'], unique=False)
        op.create_index(op.f('ix_shift_swap_requests_id'), 'shift_swap_requests', ['id'], unique=False)
        op.create_index(op.f('ix_shift_swap_requests_status'), 'shift_swap_requests', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_shift_swap_requests_status'), table_name='shift_swap_requests')
    op.drop_index(op.f('ix_shift_swap_requests_id'), table_name='shift_swap_requests')
    op.drop_index(op.f('ix_shift_swap_requests_facility_id'), table_name='shift_swap_requests')
    op.drop_table('shift_swap_requests')

    op.drop_index(op.f('ix_time_off_requests_status'), table_name='time_off_requests')
    op.drop_index(op.f('ix_time_off_requests_staff_member_id'), table_name='time_off_requests')
    op.drop_index(op.f('ix_time_off_requests_is_deleted'), table_name='time_off_requests')
    op.drop_index(op.f('ix_time_off_requests_id'), table_name='time_off_requests')
    op.drop_index(op.f('ix_time_off_requests_facility_id'), table_name='time_off_requests')
    op.drop_table('time_off_requests')

    op.drop_index(op.f('ix_staff_availability_status'), table_name='staff_availability')
    op.drop_index(op.f('ix_staff_availability_staff_member_id'), table_name='staff_availability')
    op.drop_index(op.f('ix_staff_availability_id'), table_name='staff_availability')
    op.drop_index(op.f('ix_staff_availability_facility_id'), table_name='staff_availability')
    op.drop_table('staff_availability')

    op.drop_index(op.f('ix_shifts_status'), table_name='shifts')
    op.drop_index(op.f('ix_shifts_staff_member_id'), table_name='shifts')
    op.drop_index(op.f('ix_shifts_is_deleted'), table_name='shifts')
    op.drop_index(op.f('ix_shifts_id'), table_name='shifts')
    op.drop_index(op.f('ix_shifts_facility_id'), table_name='shifts')
    op.drop_table('shifts')

