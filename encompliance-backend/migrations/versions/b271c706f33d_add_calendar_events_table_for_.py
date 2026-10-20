"""Add calendar_events table for persistent storage

Revision ID: b271c706f33d
Revises: c212b3bb6e03
Create Date: 2025-05-28 21:46:43.688238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b271c706f33d'
down_revision: Union[str, None] = 'c212b3bb6e03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Create calendar_events table
    if 'calendar_events' not in inspector.get_table_names():
        op.create_table('calendar_events',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('start', sa.String(length=50), nullable=False),
            sa.Column('end', sa.String(length=50), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('location', sa.String(length=255), nullable=True),
            sa.Column('all_day', sa.Boolean(), nullable=False),
            sa.Column('reminder_sent', sa.Boolean(), nullable=False),
            sa.Column('start_notification_sent', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_calendar_events_id'), 'calendar_events', ['id'], unique=False)
        op.create_index(op.f('ix_calendar_events_user_id'), 'calendar_events', ['user_id'], unique=False)
    
    # Clean up old tables
    try:
        # Check if table exists before dropping to be safer, though try/except handles it.
        # But we already dropped it in previous migrations potentially. 
        if 'otps' in inspector.get_table_names():
            op.drop_index('ix_otps_id', table_name='otps')
            op.drop_table('otps')
    except:
        pass  # Table may not exist


def downgrade() -> None:
    # Drop calendar_events table
    op.drop_index(op.f('ix_calendar_events_user_id'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_id'), table_name='calendar_events')
    op.drop_table('calendar_events')
