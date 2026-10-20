"""
add_photo_requirements_to_operational_tasks

Revision ID: add_photo_requirements_to_operational_tasks
Revises: add_task_reference_images
Create Date: 2025-06-12 17:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'photo_reqs_ops'
down_revision: Union[str, None] = 'add_task_reference_images'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add photo requirement columns if they don't already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('operational_tasks')]

    if 'requires_before_photos' not in columns:
        op.add_column('operational_tasks', sa.Column('requires_before_photos', sa.Boolean(), server_default='true', nullable=False))
    if 'requires_after_photos' not in columns:
        op.add_column('operational_tasks', sa.Column('requires_after_photos', sa.Boolean(), server_default='true', nullable=False))
    if 'photo_instructions' not in columns:
        op.add_column('operational_tasks', sa.Column('photo_instructions', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove the columns added in upgrade()
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('operational_tasks')]

    if 'photo_instructions' in columns:
        op.drop_column('operational_tasks', 'photo_instructions')
    if 'requires_after_photos' in columns:
        op.drop_column('operational_tasks', 'requires_after_photos')
    if 'requires_before_photos' in columns:
        op.drop_column('operational_tasks', 'requires_before_photos') 