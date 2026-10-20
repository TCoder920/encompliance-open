"""add staff directory tables

Revision ID: e9acbaea9b4c
Revises: fca11f8d1f1c
Create Date: 2025-11-17 05:45:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9acbaea9b4c'
down_revision = 'fca11f8d1f1c'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'staff_facility_assignments' not in table_names:
        op.create_table(
            'staff_facility_assignments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('staff_member_id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
            sa.Column('assigned_by_user_id', sa.Integer(), nullable=False),
            sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('unassigned_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['assigned_by_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['staff_member_id'], ['staff_members.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_staff_facility_assignments_facility_id'), 'staff_facility_assignments', ['facility_id'], unique=False)
        op.create_index(op.f('ix_staff_facility_assignments_staff_member_id'), 'staff_facility_assignments', ['staff_member_id'], unique=False)
        op.create_index(op.f('ix_staff_facility_assignments_status'), 'staff_facility_assignments', ['status'], unique=False)

    if 'staff_transfer_requests' not in table_names:
        op.create_table(
            'staff_transfer_requests',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('staff_member_id', sa.Integer(), nullable=False),
            sa.Column('source_facility_id', sa.Integer(), nullable=False),
            sa.Column('target_facility_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('requested_by_user_id', sa.Integer(), nullable=False),
            sa.Column('approved_by_user_id', sa.Integer(), nullable=True),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('resolution_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['source_facility_id'], ['facilities.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['staff_member_id'], ['staff_members.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['target_facility_id'], ['facilities.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_staff_transfer_requests_staff_member_id'), 'staff_transfer_requests', ['staff_member_id'], unique=False)
        op.create_index(op.f('ix_staff_transfer_requests_status'), 'staff_transfer_requests', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_staff_transfer_requests_status'), table_name='staff_transfer_requests')
    op.drop_index(op.f('ix_staff_transfer_requests_staff_member_id'), table_name='staff_transfer_requests')
    op.drop_table('staff_transfer_requests')
    op.drop_index(op.f('ix_staff_facility_assignments_status'), table_name='staff_facility_assignments')
    op.drop_index(op.f('ix_staff_facility_assignments_staff_member_id'), table_name='staff_facility_assignments')
    op.drop_index(op.f('ix_staff_facility_assignments_facility_id'), table_name='staff_facility_assignments')
    op.drop_table('staff_facility_assignments')

