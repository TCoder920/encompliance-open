"""add_grace_period_end_column_only

Revision ID: 260f319f978a
Revises: d3bc35dd72ea
Create Date: 2025-06-03 12:44:13.495302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '260f319f978a'
down_revision: Union[str, None] = 'd3bc35dd72ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add grace_period_end column to subscriptions table
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'subscriptions' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('subscriptions')]
        if 'grace_period_end' not in columns:
            op.add_column('subscriptions', sa.Column('grace_period_end', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove grace_period_end column from subscriptions table
    op.drop_column('subscriptions', 'grace_period_end')
