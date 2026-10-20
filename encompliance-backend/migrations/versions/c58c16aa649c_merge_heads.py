"""merge heads

Revision ID: c58c16aa649c
Revises: 94a98367d8ef, role_desc_001
Create Date: 2025-06-04 20:36:32.009035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c58c16aa649c'
down_revision: Union[str, None] = ('94a98367d8ef', 'role_desc_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
