"""add_signup_sessions_table

Revision ID: e4efa6a77c9c
Revises: 94dbc744764b
Create Date: 2025-06-01 22:58:44.893088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4efa6a77c9c'
down_revision: Union[str, None] = '94dbc744764b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create signup_sessions table
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'signup_sessions' not in table_names:
        op.create_table('signup_sessions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_token', sa.String(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('signup_data', sa.JSON(), nullable=False),
            sa.Column('step_completed', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('email_verification_sent', sa.Boolean(), nullable=True),
            sa.Column('verification_attempts', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_signup_sessions_id'), 'signup_sessions', ['id'], unique=False)
        op.create_index(op.f('ix_signup_sessions_session_token'), 'signup_sessions', ['session_token'], unique=True)
        op.create_index(op.f('ix_signup_sessions_email'), 'signup_sessions', ['email'], unique=False)


def downgrade() -> None:
    # Drop signup_sessions table
    op.drop_index(op.f('ix_signup_sessions_email'), table_name='signup_sessions')
    op.drop_index(op.f('ix_signup_sessions_session_token'), table_name='signup_sessions')
    op.drop_index(op.f('ix_signup_sessions_id'), table_name='signup_sessions')
    op.drop_table('signup_sessions')
