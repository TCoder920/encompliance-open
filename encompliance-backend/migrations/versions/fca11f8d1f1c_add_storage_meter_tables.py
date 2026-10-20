"""add storage meter tables

Revision ID: fca11f8d1f1c
Revises: d21b54d8e2bd
Create Date: 2025-11-17 05:10:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fca11f8d1f1c'
down_revision = 'd21b54d8e2bd'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'storage_meters' not in table_names:
        op.create_table(
            'storage_meters',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('billing_period_start', sa.DateTime(timezone=True), nullable=False),
            sa.Column('billing_period_end', sa.DateTime(timezone=True), nullable=False),
            sa.Column('tier_name', sa.String(length=32), nullable=False, server_default='pro'),
            sa.Column('included_bytes', sa.BigInteger(), nullable=False, server_default='26843545600'),
            sa.Column('used_bytes', sa.BigInteger(), nullable=False, server_default='0'),
            sa.Column('overage_bytes', sa.BigInteger(), nullable=False, server_default='0'),
            sa.Column('alert_level', sa.String(length=32), nullable=True),
            sa.Column('last_alert_sent_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_storage_meters_billing_period_end'), 'storage_meters', ['billing_period_end'], unique=False)
        op.create_index(op.f('ix_storage_meters_billing_period_start'), 'storage_meters', ['billing_period_start'], unique=False)
        op.create_index(op.f('ix_storage_meters_facility_id'), 'storage_meters', ['facility_id'], unique=False)

    if 'storage_usage_events' not in table_names:
        op.create_table(
            'storage_usage_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('meter_id', sa.Integer(), nullable=True),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('resource_type', sa.String(length=64), nullable=False),
            sa.Column('resource_id', sa.Integer(), nullable=False),
            sa.Column('delta_bytes', sa.BigInteger(), nullable=False),
            sa.Column('source', sa.String(length=32), nullable=False, server_default='document'),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['meter_id'], ['storage_meters.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_storage_usage_events_created_at'), 'storage_usage_events', ['created_at'], unique=False)
        op.create_index(op.f('ix_storage_usage_events_facility_id'), 'storage_usage_events', ['facility_id'], unique=False)
        op.create_index(op.f('ix_storage_usage_events_meter_id'), 'storage_usage_events', ['meter_id'], unique=False)
        op.create_index(op.f('ix_storage_usage_events_resource_type'), 'storage_usage_events', ['resource_type'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_storage_usage_events_resource_type'), table_name='storage_usage_events')
    op.drop_index(op.f('ix_storage_usage_events_meter_id'), table_name='storage_usage_events')
    op.drop_index(op.f('ix_storage_usage_events_facility_id'), table_name='storage_usage_events')
    op.drop_index(op.f('ix_storage_usage_events_created_at'), table_name='storage_usage_events')
    op.drop_table('storage_usage_events')
    op.drop_index(op.f('ix_storage_meters_facility_id'), table_name='storage_meters')
    op.drop_index(op.f('ix_storage_meters_billing_period_start'), table_name='storage_meters')
    op.drop_index(op.f('ix_storage_meters_billing_period_end'), table_name='storage_meters')
    op.drop_table('storage_meters')

