"""add_team_member_name_change_requests

Revision ID: 94a98367d8ef
Revises: 7c54c8ddeed5
Create Date: 2025-06-04 18:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94a98367d8ef'
down_revision: Union[str, None] = '7c54c8ddeed5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create team_member_name_change_requests table
    op.create_table('team_member_name_change_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('current_name', sa.String(length=255), nullable=False),
        sa.Column('requested_name', sa.String(length=255), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reviewed_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['reviewed_by_admin_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_member_name_change_requests_id'), 'team_member_name_change_requests', ['id'], unique=False)
    op.create_index(op.f('ix_team_member_name_change_requests_user_id'), 'team_member_name_change_requests', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop team_member_name_change_requests table
    op.drop_index(op.f('ix_team_member_name_change_requests_user_id'), table_name='team_member_name_change_requests')
    op.drop_index(op.f('ix_team_member_name_change_requests_id'), table_name='team_member_name_change_requests')
    op.drop_table('team_member_name_change_requests')
