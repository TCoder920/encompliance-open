"""create_sync_events_table_simple

Revision ID: 29da47530a7d
Revises: d676c02030d7
Create Date: 2025-06-05 16:25:24.896513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29da47530a7d'
down_revision: Union[str, None] = 'd676c02030d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sync_events table
    op.create_table('sync_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('facility_id', sa.Integer(), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('delivered', sa.Boolean(), nullable=True),
        sa.Column('delivery_attempts', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sync_events_facility_id'), 'sync_events', ['facility_id'], unique=False)
    op.create_index(op.f('ix_sync_events_target_user_id'), 'sync_events', ['target_user_id'], unique=False)
    op.create_index(op.f('ix_sync_events_user_id'), 'sync_events', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sync_events_user_id'), table_name='sync_events')
    op.drop_index(op.f('ix_sync_events_target_user_id'), table_name='sync_events')
    op.drop_index(op.f('ix_sync_events_facility_id'), table_name='sync_events')
    op.drop_table('sync_events')
