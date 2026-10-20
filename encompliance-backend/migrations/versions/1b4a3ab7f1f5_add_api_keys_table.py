"""Add API keys table

Revision ID: 1b4a3ab7f1f5
Revises: fab2d1c4a4a0
Create Date: 2025-11-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1b4a3ab7f1f5"
down_revision: Union[str, None] = "fab2d1c4a4a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


api_key_status = sa.Enum("active", "revoked", "expired", name="apikeystatus")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    # Check if table exists
    if 'api_keys' not in table_names:
        # Check if type exists
        status_type = sa.Enum("active", "revoked", "expired", name="apikeystatus")
        if bind.dialect.name == 'postgresql':
            # Check for type existence in pg_type
            result = bind.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'apikeystatus'")).scalar()
            if result:
                status_type = sa.Enum("active", "revoked", "expired", name="apikeystatus", create_type=False)

        op.create_table(
            "api_keys",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("label", sa.String(length=255), nullable=False),
            sa.Column("prefix", sa.String(length=16), nullable=False),
            sa.Column("key_hash", sa.String(length=128), nullable=False),
            sa.Column("scopes", sa.JSON(), nullable=False),
            sa.Column("ip_allowlist", sa.JSON(), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("facility_id", sa.Integer(), sa.ForeignKey("facilities.id"), nullable=True),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", status_type, nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.UniqueConstraint("prefix"),
            sa.UniqueConstraint("key_hash"),
        )
        op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])
        op.create_index("ix_api_keys_facility_id", "api_keys", ["facility_id"])


def downgrade() -> None:
    op.drop_index("ix_api_keys_facility_id", table_name="api_keys")
    op.drop_index("ix_api_keys_user_id", table_name="api_keys")
    op.drop_table("api_keys")
    api_key_status.drop(op.get_bind(), checkfirst=True)

