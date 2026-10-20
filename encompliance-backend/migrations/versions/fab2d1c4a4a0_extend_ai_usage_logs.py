"""extend ai usage logs

Revision ID: fab2d1c4a4a0
Revises: f7f47d9f1b9d
Create Date: 2025-11-17 07:25:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fab2d1c4a4a0'
down_revision = 'f7f47d9f1b9d'
branch_labels = None
depends_on = None


def upgrade():

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_name = 'ai_usage_logs'
    existing_columns = [c['name'] for c in inspector.get_columns(table_name)]

    if 'facility_id' not in existing_columns:
        op.add_column('ai_usage_logs', sa.Column('facility_id', sa.Integer(), nullable=True))
        try:
            op.create_foreign_key(None, 'ai_usage_logs', 'facilities', ['facility_id'], ['id'])
        except Exception:
            pass

    if 'prompt_tokens' not in existing_columns:
        op.add_column('ai_usage_logs', sa.Column('prompt_tokens', sa.Integer(), nullable=True, server_default='0'))

    if 'completion_tokens' not in existing_columns:
        op.add_column('ai_usage_logs', sa.Column('completion_tokens', sa.Integer(), nullable=True, server_default='0'))

    if 'model_name' not in existing_columns:
        op.add_column('ai_usage_logs', sa.Column('model_name', sa.String(length=100), nullable=True))

    existing_indexes = [i['name'] for i in inspector.get_indexes(table_name)]
    if 'ix_ai_usage_logs_facility_id' not in existing_indexes and 'facility_id' in [c['name'] for c in inspector.get_columns(table_name)]:
        op.create_index(op.f('ix_ai_usage_logs_facility_id'), 'ai_usage_logs', ['facility_id'], unique=False)


def downgrade():
    op.drop_constraint(None, 'ai_usage_logs', type_='foreignkey')
    op.drop_index(op.f('ix_ai_usage_logs_facility_id'), table_name='ai_usage_logs')
    op.drop_column('ai_usage_logs', 'model_name')
    op.drop_column('ai_usage_logs', 'completion_tokens')
    op.drop_column('ai_usage_logs', 'prompt_tokens')
    op.drop_column('ai_usage_logs', 'facility_id')

