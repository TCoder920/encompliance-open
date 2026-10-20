"""Fix notification type enum for calendar events

Revision ID: c212b3bb6e03
Revises: 71cb4e88c360
Create Date: 2025-05-27 18:31:22.578346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c212b3bb6e03'
down_revision: Union[str, None] = '71cb4e88c360'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For SQLite, we need to recreate the table to change the VARCHAR length
    # First, create a backup table
    op.execute("""
        CREATE TABLE notifications_backup AS 
        SELECT * FROM notifications
    """)
    
    # Drop the original table
    op.drop_table('notifications')
    
    # Recreate the table with proper VARCHAR length for type column
    # Recreate the table with proper VARCHAR length for type column
    # Use existing notificationpriority and notificationtype enums if available, or create generically.
    # We use PG ENUM for priority to avoid duplicate type error.
    from sqlalchemy.dialects.postgresql import ENUM
    notification_priority_enum = ENUM('LOW', 'MEDIUM', 'HIGH', name='notificationpriority', create_type=False)

    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),  # Increased from 17 to 20 to accommodate CALENDAR_REMINDER
        sa.Column('priority', notification_priority_enum, nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('related_id', sa.String(length=100), nullable=True),
        sa.Column('related_type', sa.String(length=50), nullable=True),
        sa.Column('action_url', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create the index
    op.create_index('ix_notifications_id', 'notifications', ['id'], unique=False)
    
    # Copy data back from backup
    op.execute("""
        INSERT INTO notifications (id, user_id, title, message, type, priority, is_read, created_at, related_id, related_type, action_url)
        SELECT id, user_id, title, message, type, priority, is_read, created_at, related_id, related_type, action_url
        FROM notifications_backup
    """)
    
    # Drop the backup table
    op.execute("DROP TABLE notifications_backup")


def downgrade() -> None:
    # For downgrade, recreate with the old schema
    op.execute("""
        CREATE TABLE notifications_backup AS 
        SELECT * FROM notifications
    """)
    
    op.drop_table('notifications')
    
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=17), nullable=False),  # Back to original length
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='notificationpriority'), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('related_id', sa.String(length=100), nullable=True),
        sa.Column('related_type', sa.String(length=50), nullable=True),
        sa.Column('action_url', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_notifications_id', 'notifications', ['id'], unique=False)
    
    op.execute("""
        INSERT INTO notifications (id, user_id, title, message, type, priority, is_read, created_at, related_id, related_type, action_url)
        SELECT id, user_id, title, message, type, priority, is_read, created_at, related_id, related_type, action_url
        FROM notifications_backup
    """)
    
    op.execute("DROP TABLE notifications_backup")
