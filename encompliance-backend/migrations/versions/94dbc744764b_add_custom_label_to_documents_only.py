"""Add custom_label to documents only

Revision ID: 94dbc744764b
Revises: 5799cd42bc64
Create Date: 2025-06-01 11:15:32.748293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94dbc744764b'
down_revision: Union[str, None] = '5799cd42bc64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add custom_label column to documents table
    op.add_column('documents', sa.Column('custom_label', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove custom_label column from documents table
    op.drop_column('documents', 'custom_label')
