"""add escalation tables

Revision ID: ed0c2f1a6f6a
Revises: e9acbaea9b4c
Create Date: 2025-11-17 06:20:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed0c2f1a6f6a'
down_revision = 'e9acbaea9b4c'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'escalation_policies' not in table_names:
        op.create_table(
            'escalation_policies',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=150), nullable=False),
            sa.Column('incident_type', sa.String(length=50), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('created_by_user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_escalation_policies_facility_id'), 'escalation_policies', ['facility_id'], unique=False)

    if 'escalation_steps' not in table_names:
        op.create_table(
            'escalation_steps',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('policy_id', sa.Integer(), nullable=False),
            sa.Column('step_number', sa.Integer(), nullable=False),
            sa.Column('delay_minutes', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('channel', sa.Enum('EMAIL', 'SMS', 'PUSH', 'PAGER', name='escalationchannel'), nullable=False),
            sa.Column('target_role', sa.String(length=50), nullable=True),
            sa.Column('target_user_id', sa.Integer(), nullable=True),
            sa.Column('custom_recipient', sa.String(length=255), nullable=True),
            sa.Column('message_template', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['policy_id'], ['escalation_policies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['target_user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_escalation_steps_policy_id'), 'escalation_steps', ['policy_id'], unique=False)

    if 'escalation_incidents' not in table_names:
        op.create_table(
            'escalation_incidents',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('policy_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.Enum('PENDING', 'ACKNOWLEDGED', 'RESOLVED', name='escalationincidentstatus'), nullable=False, server_default='PENDING'),
            sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_step_sent', sa.Integer(), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['policy_id'], ['escalation_policies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_escalation_incidents_policy_id'), 'escalation_incidents', ['policy_id'], unique=False)
        op.create_index(op.f('ix_escalation_incidents_status'), 'escalation_incidents', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_escalation_incidents_status'), table_name='escalation_incidents')
    op.drop_index(op.f('ix_escalation_incidents_policy_id'), table_name='escalation_incidents')
    op.drop_table('escalation_incidents')
    op.drop_index(op.f('ix_escalation_steps_policy_id'), table_name='escalation_steps')
    op.drop_table('escalation_steps')
    op.drop_index(op.f('ix_escalation_policies_facility_id'), table_name='escalation_policies')
    op.drop_table('escalation_policies')

