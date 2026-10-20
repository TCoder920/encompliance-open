"""merge training migration heads

Revision ID: 8d8b8bdd3f26
Revises: 4b1598f26244, b00b579d0ffb
Create Date: 2025-05-30 20:43:11.760874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d8b8bdd3f26'
down_revision: Union[str, None] = ('4b1598f26244', 'b00b579d0ffb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
