"""Add assignment images table

Revision ID: 93d00b6b2345
Revises: 53585b47171e
Create Date: 2025-01-15 19:35:18.232212

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93d00b6b2345'
down_revision: Union[str, None] = '53585b47171e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    # Add new columns to task_assignments table
    if 'task_assignments' in table_names:
        columns = [c['name'] for c in inspector.get_columns('task_assignments')]
        
        if 'requires_before_photos' not in columns:
            op.add_column('task_assignments', sa.Column('requires_before_photos', sa.Boolean(), nullable=True))
        if 'requires_after_photos' not in columns:
            op.add_column('task_assignments', sa.Column('requires_after_photos', sa.Boolean(), nullable=True))
        if 'min_before_photos' not in columns:
            op.add_column('task_assignments', sa.Column('min_before_photos', sa.Integer(), nullable=True))
        if 'min_after_photos' not in columns:
            op.add_column('task_assignments', sa.Column('min_after_photos', sa.Integer(), nullable=True))
        if 'max_photos_per_type' not in columns:
            op.add_column('task_assignments', sa.Column('max_photos_per_type', sa.Integer(), nullable=True))
        if 'photo_requirements' not in columns:
            op.add_column('task_assignments', sa.Column('photo_requirements', sa.JSON(), nullable=True))
        if 'total_image_storage_bytes' not in columns:
            op.add_column('task_assignments', sa.Column('total_image_storage_bytes', sa.BigInteger(), nullable=True))
    
    # Create assignment_images table
    if 'assignment_images' not in table_names:
        op.create_table('assignment_images',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('assignment_id', sa.Integer(), nullable=False),
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
            sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('label', sa.String(length=255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('display_order', sa.Integer(), nullable=True),
            sa.Column('conversion_status', sa.String(length=20), nullable=True),
            sa.Column('image_metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['assignment_id'], ['task_assignments.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        # Create indexes for assignment_images table (only if table created or check individually)
        op.create_index(op.f('ix_assignment_images_assignment_id'), 'assignment_images', ['assignment_id'], unique=False)
        op.create_index(op.f('ix_assignment_images_image_type'), 'assignment_images', ['image_type'], unique=False)
        op.create_index('ix_assignment_images_display_order', 'assignment_images', ['assignment_id', 'display_order'], unique=False)
    else:
        # Check indexes if table exists
        existing_indexes = [i['name'] for i in inspector.get_indexes('assignment_images')]
        if 'ix_assignment_images_assignment_id' not in existing_indexes:
            op.create_index(op.f('ix_assignment_images_assignment_id'), 'assignment_images', ['assignment_id'], unique=False)
        if 'ix_assignment_images_image_type' not in existing_indexes:
            op.create_index(op.f('ix_assignment_images_image_type'), 'assignment_images', ['image_type'], unique=False)
        if 'ix_assignment_images_display_order' not in existing_indexes:
            op.create_index('ix_assignment_images_display_order', 'assignment_images', ['assignment_id', 'display_order'], unique=False)


def downgrade() -> None:
    # Drop assignment_images table and indexes
    op.drop_index('ix_assignment_images_display_order', table_name='assignment_images')
    op.drop_index(op.f('ix_assignment_images_image_type'), table_name='assignment_images')
    op.drop_index(op.f('ix_assignment_images_assignment_id'), table_name='assignment_images')
    op.drop_table('assignment_images')
    
    # Remove columns from task_assignments table
    op.drop_column('task_assignments', 'total_image_storage_bytes')
    op.drop_column('task_assignments', 'photo_requirements')
    op.drop_column('task_assignments', 'max_photos_per_type')
    op.drop_column('task_assignments', 'min_after_photos')
    op.drop_column('task_assignments', 'min_before_photos')
    op.drop_column('task_assignments', 'requires_after_photos')
    op.drop_column('task_assignments', 'requires_before_photos')
