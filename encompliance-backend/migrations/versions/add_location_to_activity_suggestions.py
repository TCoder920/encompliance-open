"""add_location_to_activity_suggestions

Revision ID: add_location_simple
Revises: 59ed57e7ba6a
Create Date: 2025-06-14 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_location_simple'
down_revision: Union[str, None] = '59ed57e7ba6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add location column to activity_suggestions table
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('activity_suggestions')]
    if 'location' not in columns:
        op.add_column('activity_suggestions', sa.Column('location', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove location column from activity_suggestions table
    op.drop_column('activity_suggestions', 'location') 