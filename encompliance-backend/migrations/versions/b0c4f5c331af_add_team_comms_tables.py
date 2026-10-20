"""add team comms tables

Revision ID: b0c4f5c331af
Revises: a6a4d2f606e0
Create Date: 2025-11-17 03:18:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0c4f5c331af'
down_revision = 'a6a4d2f606e0'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'team_channels' not in table_names:
        op.create_table(
            'team_channels',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=120), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_private', sa.Boolean(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id']),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_team_channels_facility_id'), 'team_channels', ['facility_id'], unique=False)
        op.create_index(op.f('ix_team_channels_id'), 'team_channels', ['id'], unique=False)

    if 'team_messages' not in table_names:
        op.create_table(
            'team_messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('channel_id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('attachments', sa.JSON(), nullable=True),
            sa.Column('mentions', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['channel_id'], ['team_channels.id']),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id']),
            sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_team_messages_channel_id'), 'team_messages', ['channel_id'], unique=False)
        op.create_index(op.f('ix_team_messages_facility_id'), 'team_messages', ['facility_id'], unique=False)
        op.create_index(op.f('ix_team_messages_id'), 'team_messages', ['id'], unique=False)

    if 'email_campaigns' not in table_names:
        op.create_table(
            'email_campaigns',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('subject', sa.String(length=200), nullable=False),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('template_type', sa.String(length=50), nullable=True),
            sa.Column('target_roles', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
            sa.Column('delivery_metrics', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id']),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_email_campaigns_facility_id'), 'email_campaigns', ['facility_id'], unique=False)
        op.create_index(op.f('ix_email_campaigns_id'), 'email_campaigns', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_email_campaigns_id'), table_name='email_campaigns')
    op.drop_index(op.f('ix_email_campaigns_facility_id'), table_name='email_campaigns')
    op.drop_table('email_campaigns')
    op.drop_index(op.f('ix_team_messages_id'), table_name='team_messages')
    op.drop_index(op.f('ix_team_messages_facility_id'), table_name='team_messages')
    op.drop_index(op.f('ix_team_messages_channel_id'), table_name='team_messages')
    op.drop_table('team_messages')
    op.drop_index(op.f('ix_team_channels_id'), table_name='team_channels')
    op.drop_index(op.f('ix_team_channels_facility_id'), table_name='team_channels')
    op.drop_table('team_channels')

