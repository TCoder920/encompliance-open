"""add rbac and org tables

Revision ID: cce3e3e2b9fd
Revises: b0c4f5c331af
Create Date: 2025-11-17 04:05:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cce3e3e2b9fd'
down_revision = 'b0c4f5c331af'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'organizations' not in table_names:
        op.create_table(
            'organizations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
    
    if 'facilities' in table_names:
        fac_columns = [c['name'] for c in inspector.get_columns('facilities')]
        if 'organization_id' not in fac_columns:
            op.add_column('facilities', sa.Column('organization_id', sa.Integer(), nullable=True))
            try:
                op.create_foreign_key(None, 'facilities', 'organizations', ['organization_id'], ['id'])
            except Exception:
                pass

    if 'roles' not in table_names:
        op.create_table(
            'roles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('scope', sa.String(length=50), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )

    if 'permissions' not in table_names:
        op.create_table(
            'permissions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('code', sa.String(length=120), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('code')
        )

    if 'role_permissions' not in table_names:
        op.create_table(
            'role_permissions',
            sa.Column('role_id', sa.Integer(), nullable=False),
            sa.Column('permission_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['permission_id'], ['permissions.id']),
            sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
            sa.PrimaryKeyConstraint('role_id', 'permission_id')
        )

    if 'user_role_assignments' not in table_names:
        op.create_table(
            'user_role_assignments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('role_id', sa.Integer(), nullable=False),
            sa.Column('facility_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['facility_id'], ['facilities.id']),
            sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    op.drop_table('user_role_assignments')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_constraint(None, 'facilities', type_='foreignkey')
    op.drop_column('facilities', 'organization_id')
    op.drop_table('organizations')

