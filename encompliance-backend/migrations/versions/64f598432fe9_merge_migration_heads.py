"""Merge migration heads

Revision ID: 64f598432fe9
Revises: bb91d494beda, ccbee48146f3
Create Date: 2025-05-30 19:53:14.686734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64f598432fe9'
down_revision: Union[str, None] = ('bb91d494beda', 'ccbee48146f3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
