"""add_user_role_field_only

Revision ID: 7c54c8ddeed5
Revises: 260f319f978a
Create Date: 2025-06-04 18:44:31.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c54c8ddeed5'
down_revision: Union[str, None] = '260f319f978a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type safely
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Handle Enum creation idempotently using postgresql dialect
    from sqlalchemy.dialects.postgresql import ENUM
    user_role_enum = ENUM('FREE_USER', 'FACILITY_ADMIN', 'TEAM_MEMBER', name='userrole', create_type=False)
    user_role_enum.create(bind, checkfirst=True)
    
    # Add user_role column with default value
    if 'users' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'user_role' not in columns:
            op.add_column('users', sa.Column('user_role', user_role_enum, nullable=False, server_default='FREE_USER'))
            
            # Update existing users based on their subscription status
            # Pro users become facility admins, others remain free users
            op.execute("UPDATE users SET user_role = 'FACILITY_ADMIN' WHERE subscription_status = 'pro'")
            op.execute("UPDATE users SET user_role = 'FREE_USER' WHERE subscription_status != 'pro' OR subscription_status IS NULL")


def downgrade() -> None:
    # Remove the user_role column
    op.drop_column('users', 'user_role')
    
    # Drop the enum type
    user_role_enum = sa.Enum('FREE_USER', 'FACILITY_ADMIN', 'TEAM_MEMBER', name='userrole')
    user_role_enum.drop(op.get_bind())
