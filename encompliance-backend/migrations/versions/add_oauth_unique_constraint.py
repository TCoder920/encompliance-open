"""add_oauth_unique_constraint

Revision ID: 9e84a2f71c35
Revises: d64df3846c99
Create Date: 2025-04-23 17:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import UniqueConstraint

# revision identifiers, used by Alembic.
revision: str = '9e84a2f71c35'
down_revision: Union[str, None] = 'd64df3846c99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint on provider and provider_user_id for OAuth identities."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if 'oauth_identities' in inspector.get_table_names():
        constraints = [c['name'] for c in inspector.get_unique_constraints('oauth_identities')]
        if 'uix_provider_provider_user_id' not in constraints:
            # Use batch mode for SQLite ALTER TABLE operations
            with op.batch_alter_table('oauth_identities') as batch_op:
                # Create unique constraint
                batch_op.create_unique_constraint('uix_provider_provider_user_id', ['provider', 'provider_user_id'])


def downgrade() -> None:
    """Remove unique constraint on provider and provider_user_id for OAuth identities."""
    
    # Use batch mode for SQLite ALTER TABLE operations
    with op.batch_alter_table('oauth_identities') as batch_op:
        # Drop unique constraint
        batch_op.drop_constraint('uix_provider_provider_user_id', type_='unique')