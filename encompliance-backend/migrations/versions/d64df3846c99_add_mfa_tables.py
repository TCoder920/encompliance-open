"""add_mfa_tables

Revision ID: d64df3846c99
Revises: fix_missing_columns
Create Date: 2025-04-23 16:19:37.787596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'd64df3846c99'
down_revision: Union[str, None] = 'fix_missing_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects.postgresql import ENUM

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # --- Create enum types ---
    # We use a helper to safely create types if they don't exist.
    def create_enum_safely(enum_obj):
        try:
            enum_obj.create(bind, checkfirst=True)
        except Exception:
            pass # Assume exists or race condition

    # Use postgresql ENUM explicitly to ensure create_type=False works reliably
    mfa_method_enum = ENUM('NONE', 'EMAIL', 'SMS', 'TOTP', 'WEBAUTHN', name='mfamethod', create_type=False)
    create_enum_safely(mfa_method_enum)

    otp_channel_enum = ENUM('EMAIL', 'SMS', name='otpchannel', create_type=False)
    create_enum_safely(otp_channel_enum)

    otp_purpose_enum = ENUM('LOGIN', 'REGISTRATION', 'PASSWORD_RESET', 'MFA', name='otppurpose', create_type=False)
    create_enum_safely(otp_purpose_enum)

    magic_link_purpose_enum = ENUM('LOGIN', 'REGISTRATION', 'PASSWORD_RESET', name='magiclinkpurpose', create_type=False)
    create_enum_safely(magic_link_purpose_enum)

    oauth_provider_enum = ENUM('GOOGLE', 'APPLE', 'MICROSOFT', 'GITHUB', name='oauthprovider', create_type=False)
    create_enum_safely(oauth_provider_enum)
    
    # --- Update users table with MFA fields ---
    if 'users' in existing_tables:
        columns = [c['name'] for c in inspector.get_columns('users')]
        
        if 'mfa_enabled' not in columns:
            op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=True, default=False))
        
        if 'preferred_mfa_method' not in columns:
            op.add_column('users', sa.Column('preferred_mfa_method', mfa_method_enum, nullable=True, default='NONE'))
        
        if 'recovery_codes' not in columns:
            op.add_column('users', sa.Column('recovery_codes', sa.String(), nullable=True))
        
        if 'totp_secret' not in columns:
            op.add_column('users', sa.Column('totp_secret', sa.String(), nullable=True))
            
        if 'phone_verified' not in columns:
            op.add_column('users', sa.Column('phone_verified', sa.Boolean(), nullable=True, default=False))
            
        if 'email_verified' not in columns:
            op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True, default=False))
            
        if 'mfa_required' not in columns:
            op.add_column('users', sa.Column('mfa_required', sa.Boolean(), nullable=True, default=False))
    
    # --- Create WebAuthn credentials table ---
    if 'webauthn_credentials' not in existing_tables:
        op.create_table(
            'webauthn_credentials',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('credential_id', sa.String(), nullable=False),
            sa.Column('public_key', sa.LargeBinary(), nullable=False),
            sa.Column('sign_count', sa.Integer(), nullable=False, default=0),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('device_type', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('credential_id')
        )
        op.create_index(op.f('ix_webauthn_credentials_id'), 'webauthn_credentials', ['id'], unique=False)
    
    # --- Create User OTP table ---
    if 'user_otps' not in existing_tables:
        op.create_table(
            'user_otps',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('hashed_code', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_used', sa.Boolean(), default=False),
            sa.Column('attempt_count', sa.Integer(), default=0),
            sa.Column('channel', otp_channel_enum, nullable=False),
            sa.Column('purpose', otp_purpose_enum, nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_otps_id'), 'user_otps', ['id'], unique=False)
    
    # --- Create Magic Link table ---
    if 'magic_links' not in existing_tables:
        op.create_table(
            'magic_links',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('token', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_used', sa.Boolean(), default=False),
            sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('ip_address', sa.String(), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('purpose', magic_link_purpose_enum, nullable=False, default='LOGIN'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_magic_links_id'), 'magic_links', ['id'], unique=False)
        op.create_index(op.f('ix_magic_links_token'), 'magic_links', ['token'], unique=True)
    
    # --- Create OAuth Identity table ---
    if 'oauth_identities' not in existing_tables:
        op.create_table(
            'oauth_identities',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('provider', sa.String(), nullable=False),
            sa.Column('provider_user_id', sa.String(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('access_token', sa.String(), nullable=True),
            sa.Column('refresh_token', sa.String(), nullable=True),
            sa.Column('id_token', sa.String(), nullable=True),
            sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('profile_data', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_oauth_identities_id'), 'oauth_identities', ['id'], unique=False)
        op.create_index(op.f('ix_oauth_identities_provider_user_id'), 'oauth_identities', ['provider', 'provider_user_id'], unique=True)
        
    if 'user_mfa_methods' not in existing_tables:
        op.create_table(
            'user_mfa_methods',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('method', mfa_method_enum, nullable=False),
            sa.Column('secret', sa.String(), nullable=True),
            sa.Column('is_default', sa.Boolean(), nullable=False),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_mfa_methods_id'), 'user_mfa_methods', ['id'], unique=False)
        op.create_index(op.f('ix_user_mfa_methods_user_id'), 'user_mfa_methods', ['user_id'], unique=False)
    
    if 'mfa_backup_codes' not in existing_tables:
        op.create_table(
            'mfa_backup_codes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('code', sa.String(), nullable=False),
            sa.Column('used', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_mfa_backup_codes_code'), 'mfa_backup_codes', ['code'], unique=True)
        op.create_index(op.f('ix_mfa_backup_codes_id'), 'mfa_backup_codes', ['id'], unique=False)
        op.create_index(op.f('ix_mfa_backup_codes_user_id'), 'mfa_backup_codes', ['user_id'], unique=False)


def downgrade() -> None:
    # --- Drop tables ---
    op.drop_table('user_mfa_methods')
    op.drop_table('mfa_backup_codes')
    op.drop_table('oauth_identities')
    op.drop_table('magic_links')
    op.drop_table('user_otps')
    op.drop_table('webauthn_credentials')
    
    # --- Drop columns from users table ---
    op.drop_column('users', 'mfa_required')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'totp_secret')
    op.drop_column('users', 'recovery_codes')
    op.drop_column('users', 'preferred_mfa_method')
    op.drop_column('users', 'mfa_enabled')
    
    # --- Drop enum types ---
    try:
        sa.Enum(name='mfamethod').drop(op.get_bind())
    except: pass
    try:
        sa.Enum(name='otpchannel').drop(op.get_bind())
    except: pass
    try:
        sa.Enum(name='otppurpose').drop(op.get_bind())
    except: pass
    try:
        sa.Enum(name='magiclinkpurpose').drop(op.get_bind())
    except: pass
    try:
        sa.Enum(name='oauthprovider').drop(op.get_bind())
    except: pass
