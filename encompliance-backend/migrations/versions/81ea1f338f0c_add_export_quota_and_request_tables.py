"""add_export_quota_and_request_tables

Revision ID: 81ea1f338f0c
Revises: c563c2ccc7a5
Create Date: 2025-05-29 21:06:31.825893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81ea1f338f0c'
down_revision: Union[str, None] = 'c563c2ccc7a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Create export_quotas table
    if 'export_quotas' not in inspector.get_table_names():
        op.create_table('export_quotas',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('quarter_year', sa.String(length=7), nullable=False),
            sa.Column('exports_used', sa.Integer(), nullable=False, default=0),
            sa.Column('last_export_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('total_data_size', sa.BigInteger(), nullable=False, default=0),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_export_quotas_id'), 'export_quotas', ['id'], unique=False)
        op.create_index(op.f('ix_export_quotas_user_id'), 'export_quotas', ['user_id'], unique=False)
        op.create_index(op.f('ix_export_quotas_quarter_year'), 'export_quotas', ['quarter_year'], unique=False)

    # Create export_requests table
    if 'export_requests' not in inspector.get_table_names():
        op.create_table('export_requests',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
            sa.Column('format', sa.String(length=10), nullable=False),
            sa.Column('data_types', sa.JSON(), nullable=False),
            sa.Column('estimated_size', sa.BigInteger(), nullable=False, default=0),
            sa.Column('actual_size', sa.BigInteger(), nullable=True),
            sa.Column('requires_fee', sa.Boolean(), nullable=False, default=False),
            sa.Column('fee_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('support_ticket_id', sa.String(length=100), nullable=True),
            sa.Column('file_path', sa.String(length=500), nullable=True),
            sa.Column('download_expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('progress_percentage', sa.Integer(), nullable=False, default=0),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_export_requests_id'), 'export_requests', ['id'], unique=False)
        op.create_index(op.f('ix_export_requests_user_id'), 'export_requests', ['user_id'], unique=False)
        op.create_index(op.f('ix_export_requests_status'), 'export_requests', ['status'], unique=False)


def downgrade() -> None:
    # Drop export_requests table
    op.drop_index(op.f('ix_export_requests_status'), table_name='export_requests')
    op.drop_index(op.f('ix_export_requests_user_id'), table_name='export_requests')
    op.drop_index(op.f('ix_export_requests_id'), table_name='export_requests')
    op.drop_table('export_requests')
    
    # Drop export_quotas table
    op.drop_index(op.f('ix_export_quotas_quarter_year'), table_name='export_quotas')
    op.drop_index(op.f('ix_export_quotas_user_id'), table_name='export_quotas')
    op.drop_index(op.f('ix_export_quotas_id'), table_name='export_quotas')
    op.drop_table('export_quotas')
