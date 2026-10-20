"""add role_description to users table

Revision ID: role_desc_001
Revises: 7c54c8ddeed5
Create Date: 2024-12-19 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'role_desc_001'
down_revision = '7c54c8ddeed5'
branch_labels = None
depends_on = None

def upgrade():
    # Add role_description column to users table
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'users' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'role_description' not in columns:
            op.add_column('users', sa.Column('role_description', sa.String(100), nullable=True))

def downgrade():
    # Remove role_description column from users table
    op.drop_column('users', 'role_description') 