"""make_otp_user_id_nullable

Revision ID: 20c72e694aa6
Revises: 
Create Date: 2025-01-14 20:26:05.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20c72e694aa6'
down_revision = 'add_location_simple'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    
    if bind.dialect.name == 'postgresql':
        # PostgreSQL-specific logic
        
        # safely create ENUM type
        op.execute("DO $$ BEGIN CREATE TYPE otptype AS ENUM ('EMAIL', 'SMS'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
        
        # Make user_id nullable
        op.alter_column('otps', 'user_id',
               existing_type=sa.Integer(),
               nullable=True)

        # Update otp_type column to use the ENUM
        # We assume existing data is compatible (EMAIL, SMS strings)
        op.alter_column('otps', 'otp_type',
               existing_type=sa.String(),
               type_=sa.Enum('EMAIL', 'SMS', name='otptype'),
               postgresql_using="otp_type::text::otptype")
               
    else:
        # SQLite logic (copy and reconstruct)
        # First, create a new table with nullable user_id
        # Note: for SQLite we can't easily use Postgres ENUMs, so we might fallback to VARCHAR or check Enum support
        
        # For SQLite, Enum is usually VARCHAR with CheckConstraint.
        op.create_table('otps_new',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('otp_type', sa.Enum('EMAIL', 'SMS', name='otptype'), nullable=False),
            sa.Column('otp_hash', sa.String(), nullable=False),
            sa.Column('recipient', sa.String(), nullable=False),
            sa.Column('is_verified', sa.Boolean(), nullable=True),
            sa.Column('verification_attempts', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_otps_new_id'), 'otps_new', ['id'], unique=False)
        
        # Copy data from old table to new table
        # We need to list columns explicitly if schema differs slightly, but * usually works if columns match
        op.execute('INSERT INTO otps_new SELECT * FROM otps')
        
        # Drop old table
        op.drop_table('otps')
        
        # Rename new table to original name
        op.rename_table('otps_new', 'otps')


def downgrade():
    # Reverse the process - recreate table with non-nullable user_id
    op.create_table('otps_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('otp_type', sa.Enum('EMAIL', 'SMS', name='otptype'), nullable=False),
        sa.Column('otp_hash', sa.String(), nullable=False),
        sa.Column('recipient', sa.String(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('verification_attempts', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_otps_new_id'), 'otps_new', ['id'], unique=False)
    
    # Copy data from old table to new table (excluding rows with NULL user_id)
    op.execute('INSERT INTO otps_new SELECT * FROM otps WHERE user_id IS NOT NULL')
    
    # Drop old table
    op.drop_table('otps')
    
    # Rename new table to original name
    op.rename_table('otps_new', 'otps')
