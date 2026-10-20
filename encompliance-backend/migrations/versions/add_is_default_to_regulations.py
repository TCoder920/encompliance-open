"""add_is_default_to_regulations

Revision ID: 4f8d5b32a1c6
Revises: 93bc8d8aedbe
Create Date: 2023-04-13 17:23:16.425891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f8d5b32a1c6'
down_revision = '93bc8d8aedbe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_default column to regulations table with default value of False
    op.add_column('regulations', sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove is_default column from regulations table
    op.drop_column('regulations', 'is_default') 