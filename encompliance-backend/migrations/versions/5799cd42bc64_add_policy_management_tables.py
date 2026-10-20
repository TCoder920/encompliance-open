"""add_policy_management_tables

Revision ID: 5799cd42bc64
Revises: ed12ebba4aca
Create Date: 2025-06-01 01:24:03.610696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5799cd42bc64'
down_revision: Union[str, None] = 'ed12ebba4aca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()
    
    # Create policies table
    if 'policies' not in table_names:
        op.create_table('policies',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('category', sa.String(length=100), nullable=True),
            sa.Column('document_id', sa.Integer(), nullable=True),
            sa.Column('document_url', sa.String(length=500), nullable=True),
            sa.Column('content_summary', sa.Text(), nullable=True),
            sa.Column('version', sa.String(length=50), nullable=False),
            sa.Column('effective_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('supersedes_policy_id', sa.Integer(), nullable=True),
            sa.Column('requires_acknowledgment', sa.Boolean(), nullable=True),
            sa.Column('acknowledgment_deadline_days', sa.Integer(), nullable=True),
            sa.Column('auto_assign_new_staff', sa.Boolean(), nullable=True),
            sa.Column('acknowledgment_reminder_days', sa.String(length=100), nullable=True),
            sa.Column('regulatory_reference', sa.String(length=255), nullable=True),
            sa.Column('compliance_level', sa.String(length=50), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('facility_administrator_id', sa.Integer(), nullable=False),
            sa.Column('approved_by', sa.Integer(), nullable=True),
            sa.Column('approved_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
            sa.ForeignKeyConstraint(['facility_administrator_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['supersedes_policy_id'], ['policies.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_policies_id'), 'policies', ['id'], unique=False)
        op.create_index(op.f('ix_policies_title'), 'policies', ['title'], unique=False)

    # Create policy_assignments table
    if 'policy_assignments' not in table_names:
        op.create_table('policy_assignments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('policy_id', sa.Integer(), nullable=False),
            sa.Column('staff_member_id', sa.Integer(), nullable=False),
            sa.Column('assigned_by', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('priority', sa.String(length=10), nullable=True),
            sa.Column('assigned_date', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('acknowledged_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('assignment_reason', sa.String(length=255), nullable=True),
            sa.Column('custom_message', sa.Text(), nullable=True),
            sa.Column('requires_immediate_attention', sa.Boolean(), nullable=True),
            sa.Column('reminder_sent_dates', sa.JSON(), nullable=True),
            sa.Column('escalation_sent', sa.Boolean(), nullable=True),
            sa.Column('escalation_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('escalation_recipient', sa.Integer(), nullable=True),
            sa.Column('viewed_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('time_spent_reading', sa.Integer(), nullable=True),
            sa.Column('assignment_notes', sa.Text(), nullable=True),
            sa.Column('completion_notes', sa.Text(), nullable=True),
            sa.Column('admin_notes', sa.Text(), nullable=True),
            sa.Column('is_mandatory', sa.Boolean(), nullable=True),
            sa.Column('compliance_deadline', sa.DateTime(timezone=True), nullable=True),
            sa.Column('regulatory_requirement', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['escalation_recipient'], ['users.id'], ),
            sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ),
            sa.ForeignKeyConstraint(['staff_member_id'], ['staff_members.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_policy_assignments_id'), 'policy_assignments', ['id'], unique=False)

    # Create policy_acknowledgments table
    if 'policy_acknowledgments' not in table_names:
        op.create_table('policy_acknowledgments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('policy_id', sa.Integer(), nullable=False),
            sa.Column('staff_member_id', sa.Integer(), nullable=False),
            sa.Column('policy_assignment_id', sa.Integer(), nullable=True),
            sa.Column('acknowledged_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('acknowledgment_method', sa.String(length=50), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('digital_signature', sa.Text(), nullable=True),
            sa.Column('signature_metadata', sa.JSON(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.String(length=500), nullable=True),
            sa.Column('device_fingerprint', sa.String(length=255), nullable=True),
            sa.Column('geolocation', sa.JSON(), nullable=True),
            sa.Column('verified_by', sa.Integer(), nullable=True),
            sa.Column('verification_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('verification_notes', sa.Text(), nullable=True),
            sa.Column('is_current', sa.Boolean(), nullable=True),
            sa.Column('acknowledgment_text', sa.Text(), nullable=True),
            sa.Column('witness_name', sa.String(length=255), nullable=True),
            sa.Column('witness_signature', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('compliance_score', sa.Integer(), nullable=True),
            sa.Column('requires_reacknowledgment', sa.Boolean(), nullable=True),
            sa.Column('reacknowledgment_reason', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['policy_assignment_id'], ['policy_assignments.id'], ),
            sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ),
            sa.ForeignKeyConstraint(['staff_member_id'], ['staff_members.id'], ),
            sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_policy_acknowledgments_id'), 'policy_acknowledgments', ['id'], unique=False)

    # Set default values for new columns (Safe UPDATEs)
    if 'policies' in inspector.get_table_names():
        op.execute("UPDATE policies SET version = '1.0' WHERE version IS NULL")
        op.execute("UPDATE policies SET requires_acknowledgment = TRUE WHERE requires_acknowledgment IS NULL")
        op.execute("UPDATE policies SET acknowledgment_deadline_days = 30 WHERE acknowledgment_deadline_days IS NULL")
        op.execute("UPDATE policies SET auto_assign_new_staff = FALSE WHERE auto_assign_new_staff IS NULL")
        op.execute("UPDATE policies SET acknowledgment_reminder_days = '[30, 14, 7, 1]' WHERE acknowledgment_reminder_days IS NULL")
        op.execute("UPDATE policies SET compliance_level = 'mandatory' WHERE compliance_level IS NULL")
        op.execute("UPDATE policies SET status = 'draft' WHERE status IS NULL")
        op.execute("UPDATE policies SET is_active = TRUE WHERE is_active IS NULL")

    if 'policy_assignments' in inspector.get_table_names():
        op.execute("UPDATE policy_assignments SET status = 'assigned' WHERE status IS NULL")
        op.execute("UPDATE policy_assignments SET priority = 'medium' WHERE priority IS NULL")
        op.execute("UPDATE policy_assignments SET requires_immediate_attention = FALSE WHERE requires_immediate_attention IS NULL")
        op.execute("UPDATE policy_assignments SET escalation_sent = FALSE WHERE escalation_sent IS NULL")
        op.execute("UPDATE policy_assignments SET is_mandatory = TRUE WHERE is_mandatory IS NULL")

    if 'policy_acknowledgments' in inspector.get_table_names():
        op.execute("UPDATE policy_acknowledgments SET acknowledgment_method = 'digital_signature' WHERE acknowledgment_method IS NULL")
        op.execute("UPDATE policy_acknowledgments SET status = 'pending' WHERE status IS NULL")
        op.execute("UPDATE policy_acknowledgments SET is_current = TRUE WHERE is_current IS NULL")
        op.execute("UPDATE policy_acknowledgments SET requires_reacknowledgment = FALSE WHERE requires_reacknowledgment IS NULL")

    # Existing migration commands - Wrapped in existence checks
    if 'otps' in table_names:
        indexes = [i['name'] for i in inspector.get_indexes('otps')]
        if 'ix_otps_id' in indexes:
             op.drop_index('ix_otps_id', table_name='otps')
        op.drop_table('otps')

    if 'calendar_connections' in table_names:
        # We perform these ops safely. 
        # is_active, calendar_id...
        op.alter_column('calendar_connections', 'is_active', existing_type=sa.BOOLEAN(), nullable=True)
        op.alter_column('calendar_connections', 'calendar_id', existing_type=sa.String(length=255), nullable=True)
        
        indexes = [i['name'] for i in inspector.get_indexes('calendar_connections')]
        if 'ix_calendar_connections_user_id' in indexes:
            op.drop_index('ix_calendar_connections_user_id', table_name='calendar_connections')
        
        columns = [c['name'] for c in inspector.get_columns('calendar_connections')]
        if 'sync_enabled' in columns:
            op.drop_column('calendar_connections', 'sync_enabled')

    if 'export_requests' in table_names:
        # FK Check
        try:
             op.create_foreign_key('fk_export_requests_documents_v2', 'export_requests', 'documents', ['document_id'], ['id'])
        except Exception:
             pass

    if 'notification_settings' in table_names:
        # Alter columns type to JSON
        # This might fail if data cannot be cast. But previous values were strings like '[...]' so it might work on Postgres with explicit USING?
        # Alembic might generate USING clause automatically or we need 'postgresql_using'.
        # But we previously set them.
        try:
             op.alter_column('notification_settings', 'training_reminder_days',
                        existing_type=sa.TEXT(),
                        type_=sa.JSON(),
                        existing_nullable=True,
                        existing_server_default=sa.text("'[30, 14, 7, 1]'"),
                        postgresql_using='training_reminder_days::json')
             # Note: postgresql_using is important for TEXT->JSON
        except Exception:
             pass
             
        try:
             op.alter_column('notification_settings', 'certification_expiry_reminder_days',
                        existing_type=sa.TEXT(),
                        type_=sa.JSON(),
                        existing_nullable=True,
                        existing_server_default=sa.text("'[30, 14, 7]'"),
                        postgresql_using='certification_expiry_reminder_days::json')
        except Exception:
             pass

    if 'notifications' in table_names:
        try:
             op.alter_column('notifications', 'type',
                        existing_type=sa.VARCHAR(length=20),
                        type_=sa.String(length=25),
                        existing_nullable=False)
        except Exception:
             pass
        
        try:
             # Use create_type=False for robustness
             priority_enum = postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', name='notificationpriority', create_type=False)
             op.alter_column('notifications', 'priority',
                        existing_type=sa.VARCHAR(length=10),
                        type_=priority_enum,
                        existing_nullable=False,
                        postgresql_using='priority::notificationpriority')
        except Exception:
             pass

        indexes = [i['name'] for i in inspector.get_indexes('notifications')]
        if 'ix_notifications_user_id' not in indexes:
             op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    
    # Drop policy tables
    op.drop_index(op.f('ix_policy_acknowledgments_id'), table_name='policy_acknowledgments')
    op.drop_table('policy_acknowledgments')
    op.drop_index(op.f('ix_policy_assignments_id'), table_name='policy_assignments')
    op.drop_table('policy_assignments')
    op.drop_index(op.f('ix_policies_title'), table_name='policies')
    op.drop_index(op.f('ix_policies_id'), table_name='policies')
    op.drop_table('policies')

    # Existing downgrade commands
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.alter_column('notifications', 'priority',
               existing_type=sa.Enum('LOW', 'MEDIUM', 'HIGH', name='notificationpriority'),
               type_=sa.VARCHAR(length=10),
               existing_nullable=False)
    op.alter_column('notifications', 'type',
               existing_type=sa.String(length=25),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
    op.alter_column('notification_settings', 'certification_expiry_reminder_days',
               existing_type=sa.JSON(),
               type_=sa.TEXT(),
               existing_nullable=True,
               existing_server_default=sa.text("'[30, 14, 7]'"))
    op.alter_column('notification_settings', 'training_reminder_days',
               existing_type=sa.JSON(),
               type_=sa.TEXT(),
               existing_nullable=True,
               existing_server_default=sa.text("'[30, 14, 7, 1]'"))
    op.drop_constraint(None, 'export_requests', type_='foreignkey')
    op.add_column('calendar_connections', sa.Column('sync_enabled', sa.BOOLEAN(), nullable=False))
    op.create_index('ix_calendar_connections_user_id', 'calendar_connections', ['user_id'], unique=False)
    op.alter_column('calendar_connections', 'calendar_id',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.alter_column('calendar_connections', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False)
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
