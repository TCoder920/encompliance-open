"""add_task_reference_images

Revision ID: add_task_reference_images
Revises: 93d00b6b2345
Create Date: 2025-06-12 11:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_task_reference_images'
down_revision: Union[str, None] = '93d00b6b2345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    # Create task_reference_images table if not exists
    if 'task_reference_images' not in table_names:
        op.create_table(
            'task_reference_images',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('operational_task_id', sa.Integer(), nullable=False),
            sa.Column('image_type', sa.String(length=20), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=False),
            sa.Column('original_file_path', sa.String(length=500), nullable=True),
            sa.Column('file_name', sa.String(length=255), nullable=False),
            sa.Column('original_file_name', sa.String(length=255), nullable=False),
            sa.Column('file_size', sa.BigInteger(), nullable=False),
            sa.Column('original_file_size', sa.BigInteger(), nullable=True),
            sa.Column('mime_type', sa.String(length=100), nullable=False),
            sa.Column('original_mime_type', sa.String(length=100), nullable=False),
            sa.Column('uploaded_by', sa.Integer(), nullable=False),
            sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('label', sa.String(length=255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('display_order', sa.Integer(), server_default='0'),
            sa.Column('conversion_status', sa.String(length=20), server_default='none'),
            sa.Column('image_metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['operational_task_id'], ['operational_tasks.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index(op.f('ix_task_reference_images_id'), 'task_reference_images', ['id'], unique=False)
        op.create_index(op.f('ix_task_reference_images_operational_task_id'), 'task_reference_images', ['operational_task_id'], unique=False)
        op.create_index(op.f('ix_task_reference_images_image_type'), 'task_reference_images', ['image_type'], unique=False)
        op.create_index(op.f('ix_task_reference_images_display_order'), 'task_reference_images', ['display_order'], unique=False)
    else:
        # If table exists, ensure indexes exist
        existing_indexes = [i['name'] for i in inspector.get_indexes('task_reference_images')]
        if 'ix_task_reference_images_id' not in existing_indexes:
            op.create_index(op.f('ix_task_reference_images_id'), 'task_reference_images', ['id'], unique=False)
        if 'ix_task_reference_images_operational_task_id' not in existing_indexes:
            op.create_index(op.f('ix_task_reference_images_operational_task_id'), 'task_reference_images', ['operational_task_id'], unique=False)
        if 'ix_task_reference_images_image_type' not in existing_indexes:
            op.create_index(op.f('ix_task_reference_images_image_type'), 'task_reference_images', ['image_type'], unique=False)
        if 'ix_task_reference_images_display_order' not in existing_indexes:
            op.create_index(op.f('ix_task_reference_images_display_order'), 'task_reference_images', ['display_order'], unique=False)

    
    # Add photo requirements columns to operational_tasks
    if 'operational_tasks' in table_names:
        columns = [c['name'] for c in inspector.get_columns('operational_tasks')]
        
        if 'requires_before_photos' not in columns:
            op.add_column('operational_tasks', sa.Column('requires_before_photos', sa.Boolean(), server_default='1'))
        if 'requires_after_photos' not in columns:
            op.add_column('operational_tasks', sa.Column('requires_after_photos', sa.Boolean(), server_default='1'))
        if 'photo_instructions' not in columns:
            op.add_column('operational_tasks', sa.Column('photo_instructions', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove photo requirements columns from operational_tasks
    op.drop_column('operational_tasks', 'photo_instructions')
    op.drop_column('operational_tasks', 'requires_after_photos')
    op.drop_column('operational_tasks', 'requires_before_photos')
    
    # Drop indexes
    op.drop_index(op.f('ix_task_reference_images_display_order'), table_name='task_reference_images')
    op.drop_index(op.f('ix_task_reference_images_image_type'), table_name='task_reference_images')
    op.drop_index(op.f('ix_task_reference_images_operational_task_id'), table_name='task_reference_images')
    op.drop_index(op.f('ix_task_reference_images_id'), table_name='task_reference_images')
    
    # Drop task_reference_images table
    op.drop_table('task_reference_images') 