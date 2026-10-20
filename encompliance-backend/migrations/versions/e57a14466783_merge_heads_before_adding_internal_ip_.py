"""merge heads before adding internal_ip_address

Revision ID: e57a14466783
Revises: 74fe8d5df9c8, 2d5f6a8e9b3c
Create Date: 2025-04-17 00:01:56.464554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e57a14466783'
down_revision: Union[str, None] = ('74fe8d5df9c8', '2d5f6a8e9b3c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
