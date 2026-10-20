"""add ai usage log

Revision ID: d21b54d8e2bd
Revises: cce3e3e2b9fd
Create Date: 2025-11-17 04:25:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd21b54d8e2bd'
down_revision = 'cce3e3e2b9fd'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'ai_usage_logs' not in table_names:
        op.create_table(
            'ai_usage_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('tokens_used', sa.Integer(), nullable=True),
            sa.Column('cost_usd', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    op.drop_table('ai_usage_logs')

