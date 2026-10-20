"""facility_management_only

Revision ID: cc774cb6d15e
Revises: e4efa6a77c9c
Create Date: 2025-06-02 20:50:04.330311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc774cb6d15e'
down_revision: Union[str, None] = 'e4efa6a77c9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    # Create facilities table
    if 'facilities' not in table_names:
        op.create_table('facilities',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('facility_name', sa.String(length=255), nullable=False),
            sa.Column('facility_address', sa.Text(), nullable=True),
            sa.Column('facility_city', sa.String(length=100), nullable=True),
            sa.Column('facility_state', sa.String(length=50), nullable=True),
            sa.Column('facility_zip', sa.String(length=20), nullable=True),
            sa.Column('facility_phone', sa.String(length=20), nullable=True),
            sa.Column('facility_email', sa.String(length=255), nullable=True),
            sa.Column('admin_user_id', sa.Integer(), nullable=False),
            sa.Column('subscription_id', sa.String(length=255), nullable=True),
            sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
            sa.Column('max_users', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('invitation_code', sa.String(length=50), nullable=True),
            sa.Column('invitation_expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('admin_user_id'),
            sa.UniqueConstraint('invitation_code'),
            sa.UniqueConstraint('stripe_customer_id'),
            sa.UniqueConstraint('subscription_id')
        )
        op.create_index(op.f('ix_facilities_facility_name'), 'facilities', ['facility_name'], unique=False)
        op.create_index(op.f('ix_facilities_id'), 'facilities', ['id'], unique=False)

    # Create subscriptions table
    if 'subscriptions' not in table_names:
        op.create_table('subscriptions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('stripe_subscription_id', sa.String(length=255), nullable=False),
            sa.Column('stripe_customer_id', sa.String(length=255), nullable=False),
            sa.Column('stripe_price_id', sa.String(length=255), nullable=True),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
            sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
            sa.Column('seat_count', sa.Integer(), nullable=False),
            sa.Column('base_price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('per_seat_price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
            sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
            sa.Column('cancel_at_period_end', sa.Boolean(), nullable=True),
            sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('cancellation_reason', sa.Text(), nullable=True),
            sa.Column('latest_invoice_id', sa.String(length=255), nullable=True),
            sa.Column('next_payment_attempt', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('stripe_subscription_id')
        )
        op.create_index(op.f('ix_subscriptions_facility_id'), 'subscriptions', ['facility_id'], unique=False)
        op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
        op.create_index(op.f('ix_subscriptions_stripe_customer_id'), 'subscriptions', ['stripe_customer_id'], unique=False)
        op.create_index(op.f('ix_subscriptions_stripe_subscription_id'), 'subscriptions', ['stripe_subscription_id'], unique=False)

    # Create facility_invitations table
    if 'facility_invitations' not in table_names:
        op.create_table('facility_invitations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('invitation_code', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('created_by_user_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('used_by_user_id', sa.Integer(), nullable=True),
            sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('personal_message', sa.Text(), nullable=True),
            sa.Column('role_description', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ),
            sa.ForeignKeyConstraint(['used_by_user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('invitation_code')
        )
        op.create_index(op.f('ix_facility_invitations_email'), 'facility_invitations', ['email'], unique=False)
        op.create_index(op.f('ix_facility_invitations_facility_id'), 'facility_invitations', ['facility_id'], unique=False)
        op.create_index(op.f('ix_facility_invitations_id'), 'facility_invitations', ['id'], unique=False)
        op.create_index(op.f('ix_facility_invitations_invitation_code'), 'facility_invitations', ['invitation_code'], unique=False)

    # Add facility management columns to existing tables
    if 'users' in table_names:
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'facility_id' not in columns:
            op.add_column('users', sa.Column('facility_id', sa.Integer(), nullable=True))
            op.create_index(op.f('ix_users_facility_id'), 'users', ['facility_id'], unique=False)
            op.create_foreign_key(None, 'users', 'facilities', ['facility_id'], ['id'])
        if 'is_facility_admin' not in columns:
            op.add_column('users', sa.Column('is_facility_admin', sa.Boolean(), nullable=True))

    if 'calendar_events' in table_names:
        columns = [c['name'] for c in inspector.get_columns('calendar_events')]
        if 'facility_id' not in columns:
            op.add_column('calendar_events', sa.Column('facility_id', sa.Integer(), nullable=True))
            op.create_index(op.f('ix_calendar_events_facility_id'), 'calendar_events', ['facility_id'], unique=False)
            op.create_foreign_key(None, 'calendar_events', 'facilities', ['facility_id'], ['id'])
        if 'created_by_admin' not in columns:
            op.add_column('calendar_events', sa.Column('created_by_admin', sa.Boolean(), nullable=True))
        if 'is_editable_by_user' not in columns:
            op.add_column('calendar_events', sa.Column('is_editable_by_user', sa.Boolean(), nullable=True))

    if 'training_assignments' in table_names:
        columns = [c['name'] for c in inspector.get_columns('training_assignments')]
        if 'facility_id' not in columns:
            op.add_column('training_assignments', sa.Column('facility_id', sa.Integer(), nullable=True))
            op.create_index(op.f('ix_training_assignments_facility_id'), 'training_assignments', ['facility_id'], unique=False)
            op.create_foreign_key(None, 'training_assignments', 'facilities', ['facility_id'], ['id'])
        if 'assigned_by_admin_id' not in columns:
            op.add_column('training_assignments', sa.Column('assigned_by_admin_id', sa.Integer(), nullable=True))
            op.create_foreign_key(None, 'training_assignments', 'users', ['assigned_by_admin_id'], ['id'])

    if 'notifications' in table_names:
        columns = [c['name'] for c in inspector.get_columns('notifications')]
        if 'sender_id' not in columns:
            op.add_column('notifications', sa.Column('sender_id', sa.Integer(), nullable=True))
            op.create_index(op.f('ix_notifications_sender_id'), 'notifications', ['sender_id'], unique=False)
            op.create_foreign_key(None, 'notifications', 'users', ['sender_id'], ['id'])
        if 'related_entity_id' not in columns:
            op.add_column('notifications', sa.Column('related_entity_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove facility management columns from existing tables
    op.drop_constraint(None, 'notifications', type_='foreignkey')
    op.drop_index(op.f('ix_notifications_sender_id'), table_name='notifications')
    op.drop_column('notifications', 'related_entity_id')
    op.drop_column('notifications', 'sender_id')

    op.drop_constraint(None, 'training_assignments', type_='foreignkey')
    op.drop_constraint(None, 'training_assignments', type_='foreignkey')
    op.drop_index(op.f('ix_training_assignments_facility_id'), table_name='training_assignments')
    op.drop_column('training_assignments', 'assigned_by_admin_id')
    op.drop_column('training_assignments', 'facility_id')

    op.drop_constraint(None, 'calendar_events', type_='foreignkey')
    op.drop_index(op.f('ix_calendar_events_facility_id'), table_name='calendar_events')
    op.drop_column('calendar_events', 'is_editable_by_user')
    op.drop_column('calendar_events', 'created_by_admin')
    op.drop_column('calendar_events', 'facility_id')

    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_facility_id'), table_name='users')
    op.drop_column('users', 'is_facility_admin')
    op.drop_column('users', 'facility_id')

    # Drop facility management tables
    op.drop_index(op.f('ix_facility_invitations_invitation_code'), table_name='facility_invitations')
    op.drop_index(op.f('ix_facility_invitations_id'), table_name='facility_invitations')
    op.drop_index(op.f('ix_facility_invitations_facility_id'), table_name='facility_invitations')
    op.drop_index(op.f('ix_facility_invitations_email'), table_name='facility_invitations')
    op.drop_table('facility_invitations')
    
    op.drop_index(op.f('ix_subscriptions_stripe_subscription_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_stripe_customer_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_facility_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    
    op.drop_index(op.f('ix_facilities_id'), table_name='facilities')
    op.drop_index(op.f('ix_facilities_facility_name'), table_name='facilities')
    op.drop_table('facilities')
