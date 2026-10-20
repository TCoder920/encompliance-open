"""make_photo_requirements_optional

Revision ID: make_photo_requirements_optional
Revises: add_photo_requirements_to_operational_tasks
Create Date: 2025-06-12 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'photo_reqs_opt'
down_revision: Union[str, None] = 'photo_reqs_ops'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change default values from True to False for existing columns
    # First, update existing records to have optional photo requirements
    op.execute("UPDATE operational_tasks SET requires_before_photos = FALSE, requires_after_photos = FALSE")
    
    # Note: SQLite doesn't support ALTER COLUMN to change default values
    # The model default changes will apply to new records


def downgrade() -> None:
    # Restore all tasks to require photos
    op.execute("UPDATE operational_tasks SET requires_before_photos = TRUE, requires_after_photos = TRUE") 