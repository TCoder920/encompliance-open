"""Add training_url to training_assignments

Revision ID: ed12ebba4aca
Revises: 8d8b8bdd3f26
Create Date: 2025-05-31 23:43:43.191336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed12ebba4aca'
down_revision: Union[str, None] = '8d8b8bdd3f26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add training_url column to training_assignments table
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'training_assignments' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('training_assignments')]
        if 'training_url' not in columns:
            op.add_column('training_assignments', sa.Column('training_url', sa.String(500), nullable=True))


def downgrade() -> None:
    # Remove training_url column from training_assignments table
    op.drop_column('training_assignments', 'training_url')
