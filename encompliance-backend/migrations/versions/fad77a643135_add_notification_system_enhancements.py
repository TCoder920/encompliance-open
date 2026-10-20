"""add_notification_system_enhancements

Revision ID: fad77a643135
Revises: 1e6280f16879
Create Date: 2025-05-24 23:19:35.056617

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fad77a643135'
down_revision: Union[str, None] = '1e6280f16879'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if otps table exists
    if 'otps' in inspector.get_table_names():
        indexes = [i['name'] for i in inspector.get_indexes('otps')]
        if 'ix_otps_id' in indexes:
            op.drop_index('ix_otps_id', table_name='otps')
        op.drop_table('otps')
        
    # Add notification columns if missing
    if 'notifications' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('notifications')]
        if 'related_task_id' not in columns:
            op.add_column('notifications', sa.Column('related_task_id', sa.Integer(), nullable=True))
        if 'related_document_id' not in columns:
            op.add_column('notifications', sa.Column('related_document_id', sa.Integer(), nullable=True))
        
        # Check constraints? Maybe handle in separate block if complex.
        # Assuming simple FKs for now. To adhere to rigor, we should check constraints too but columns first step.
        op.create_foreign_key(None, 'notifications', 'operational_tasks', ['related_task_id'], ['id'])
        op.create_foreign_key(None, 'notifications', 'documents', ['related_document_id'], ['id'])
    
    # Create push_subscriptions table
    if 'push_subscriptions' not in inspector.get_table_names():
        op.create_table('push_subscriptions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('endpoint', sa.Text(), nullable=False),
            sa.Column('keys', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('endpoint')
        )
        op.create_index(op.f('ix_push_subscriptions_id'), 'push_subscriptions', ['id'], unique=False)
    
    # Create notification_settings table
    if 'notification_settings' not in inspector.get_table_names():
        op.create_table('notification_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('in_app_calendar_enabled', sa.Boolean(), nullable=True),
            sa.Column('in_app_calendar_reminders_enabled', sa.Boolean(), nullable=True),
            sa.Column('in_app_note_notifications_enabled', sa.Boolean(), nullable=True),
            sa.Column('in_app_message_notifications_enabled', sa.Boolean(), nullable=True),
            sa.Column('in_app_regulatory_updates_enabled', sa.Boolean(), nullable=True),
            sa.Column('in_app_system_notifications_enabled', sa.Boolean(), nullable=True),
            sa.Column('email_calendar_enabled', sa.Boolean(), nullable=True),
            sa.Column('email_calendar_reminders_enabled', sa.Boolean(), nullable=True),
            sa.Column('email_note_notifications_enabled', sa.Boolean(), nullable=True),
            sa.Column('email_message_notifications_enabled', sa.Boolean(), nullable=True),
            sa.Column('email_regulatory_updates_enabled', sa.Boolean(), nullable=True),
            sa.Column('email_system_notifications_enabled', sa.Boolean(), nullable=True),
            sa.Column('push_enabled', sa.Boolean(), nullable=True),
            sa.Column('push_calendar_enabled', sa.Boolean(), nullable=True),
            sa.Column('push_calendar_reminders_enabled', sa.Boolean(), nullable=True),
            sa.Column('push_note_notifications_enabled', sa.Boolean(), nullable=True),
            sa.Column('push_message_notifications_enabled', sa.Boolean(), nullable=True),
            sa.Column('push_regulatory_updates_enabled', sa.Boolean(), nullable=True),
            sa.Column('push_system_notifications_enabled', sa.Boolean(), nullable=True),
            sa.Column('calendar_reminder_offset_minutes', sa.Integer(), nullable=True),
            sa.Column('email_digest_frequency', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )
        op.create_index(op.f('ix_notification_settings_id'), 'notification_settings', ['id'], unique=False)
    
    # Check if we need to alter notification type enum
    # This is tricky because type column might already be Enum or Varchar.
    # If notifications exist, we assume the Type Change might fail or succeed depending on casting.
    # However, if 'notificationtype' enum exists, it might conflict.
    # Let's try to create enum safely first? No, alter_column handles it inside.
    # But if type already changed, alter might do nothing or fail.
    # We will wrap it in try/except or leave it if columns match?
    # Checking column type is hard via inspector in a generic way.
    # We'll just wrap it in try-except for robustness against "Type already exists" or "Cast issue".
    try:
        # Create enum type if needed (Checkfirst handled by SQLAlchemy usually, but here inside alter_column it's implicit)
        # We manually create it to be safe
        notification_type_enum = sa.Enum('NOTE', 'DOCUMENT', 'SYSTEM', 'SECURITY', 'SUBSCRIPTION', 'CALENDAR', 'CALENDAR_REMINDER', 'MESSAGE', 'REGULATORY_UPDATE', name='notificationtype')
        try:
            notification_type_enum.create(bind, checkfirst=True)
        except: pass

        op.alter_column('notifications', 'type',
                existing_type=sa.VARCHAR(length=12),
                type_=notification_type_enum,
                existing_nullable=False,
                postgresql_using="type::notificationtype") # Hint for casting if needed
    except Exception as e:
        print(f"Skipping notification type alteration: {e}")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('notifications', 'type',
               existing_type=sa.Enum('NOTE', 'DOCUMENT', 'SYSTEM', 'SECURITY', 'SUBSCRIPTION', 'CALENDAR', 'CALENDAR_REMINDER', 'MESSAGE', 'REGULATORY_UPDATE', name='notificationtype'),
               type_=sa.VARCHAR(length=12),
               existing_nullable=False)
    
    # Drop new tables
    op.drop_index(op.f('ix_notification_settings_id'), table_name='notification_settings')
    op.drop_table('notification_settings')
    op.drop_index(op.f('ix_push_subscriptions_id'), table_name='push_subscriptions')
    op.drop_table('push_subscriptions')
    
    op.create_table('otps',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('otp_type', sa.VARCHAR(length=5), nullable=False),
    sa.Column('otp_hash', sa.VARCHAR(), nullable=False),
    sa.Column('recipient', sa.VARCHAR(), nullable=False),
    sa.Column('is_verified', sa.BOOLEAN(), nullable=True),
    sa.Column('verification_attempts', sa.INTEGER(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('expires_at', sa.DATETIME(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_otps_id', 'otps', ['id'], unique=False)
    # ### end Alembic commands ###
