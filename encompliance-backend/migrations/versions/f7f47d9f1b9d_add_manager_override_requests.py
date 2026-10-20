"""add manager override requests

Revision ID: f7f47d9f1b9d
Revises: f1c9f7c8c8a3
Create Date: 2025-11-17 07:05:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7f47d9f1b9d'
down_revision = 'f1c9f7c8c8a3'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'manager_override_requests' not in table_names:
        op.create_table(
            'manager_override_requests',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('requested_by_user_id', sa.Integer(), nullable=False),
            sa.Column('approved_by_user_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('action_type', sa.String(length=100), nullable=False),
            sa.Column('payload', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('resolution_notes', sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_manager_override_requests_facility_id'), 'manager_override_requests', ['facility_id'], unique=False)
        op.create_index(op.f('ix_manager_override_requests_status'), 'manager_override_requests', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_manager_override_requests_status'), table_name='manager_override_requests')
    op.drop_index(op.f('ix_manager_override_requests_facility_id'), table_name='manager_override_requests')
    op.drop_table('manager_override_requests')

