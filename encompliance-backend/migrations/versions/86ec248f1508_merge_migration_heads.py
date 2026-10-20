"""Merge migration heads

Revision ID: 86ec248f1508
Revises: 29da47530a7d, e3bd418e27e2
Create Date: 2025-06-09 20:44:16.533686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86ec248f1508'
down_revision: Union[str, None] = ('29da47530a7d', 'e3bd418e27e2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
