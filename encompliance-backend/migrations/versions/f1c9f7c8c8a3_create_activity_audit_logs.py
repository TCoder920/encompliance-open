"""create activity audit logs

Revision ID: f1c9f7c8c8a3
Revises: ed0c2f1a6f6a
Create Date: 2025-11-17 06:45:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1c9f7c8c8a3'
down_revision = 'ed0c2f1a6f6a'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'activity_audit_logs' not in table_names:
        op.create_table(
            'activity_audit_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('actor_user_id', sa.Integer(), nullable=True),
            sa.Column('facility_id', sa.Integer(), nullable=True),
            sa.Column('event_type', sa.String(length=100), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=False),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.Column('prev_hash', sa.String(length=128), nullable=True),
            sa.Column('entry_hash', sa.String(length=128), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['actor_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_activity_audit_logs_actor_user_id'), 'activity_audit_logs', ['actor_user_id'], unique=False)
        op.create_index(op.f('ix_activity_audit_logs_facility_id'), 'activity_audit_logs', ['facility_id'], unique=False)
        op.create_index(op.f('ix_activity_audit_logs_event_type'), 'activity_audit_logs', ['event_type'], unique=False)
        op.create_index(op.f('ix_activity_audit_logs_entry_hash'), 'activity_audit_logs', ['entry_hash'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_activity_audit_logs_entry_hash'), table_name='activity_audit_logs')
    op.drop_index(op.f('ix_activity_audit_logs_event_type'), table_name='activity_audit_logs')
    op.drop_index(op.f('ix_activity_audit_logs_facility_id'), table_name='activity_audit_logs')
    op.drop_index(op.f('ix_activity_audit_logs_actor_user_id'), table_name='activity_audit_logs')
    op.drop_table('activity_audit_logs')

