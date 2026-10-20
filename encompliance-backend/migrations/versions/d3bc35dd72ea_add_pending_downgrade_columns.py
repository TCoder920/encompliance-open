"""add_pending_downgrade_columns

Revision ID: d3bc35dd72ea
Revises: c4103773c713
Create Date: 2025-06-03 12:38:52.311617

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3bc35dd72ea'
down_revision: Union[str, None] = 'c4103773c713'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to users table
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'users' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'pending_downgrade' not in columns:
            op.add_column('users', sa.Column('pending_downgrade', sa.Boolean(), nullable=True, default=False))
        if 'downgrade_after' not in columns:
            op.add_column('users', sa.Column('downgrade_after', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove the columns we added
    op.drop_column('users', 'downgrade_after')
    op.drop_column('users', 'pending_downgrade')
