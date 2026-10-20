"""merge_training_and_task_heads

Revision ID: 47be40370c30
Revises: add_training_calendar_integration, task_management_001
Create Date: 2025-06-11 15:20:25.906104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47be40370c30'
down_revision: Union[str, None] = 'train_cal_int_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
