"""pro_free_user_model_simple

Revision ID: c4103773c713
Revises: cc774cb6d15e
Create Date: 2025-06-03 11:23:15.478842

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c4103773c713'
down_revision: Union[str, None] = 'cc774cb6d15e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate to simplified Pro/Free user model."""
    connection = op.get_bind()
    
    # Update subscription_status to "pro" for users who are facility admins or have facilities
    connection.execute(text("""
        UPDATE users 
        SET subscription_status = 'pro' 
        WHERE is_facility_admin = TRUE OR facility_id IS NOT NULL;
    """))
    
    # Get Pro users without administered facilities
    pro_users_without_facilities = connection.execute(text("""
        SELECT id, full_name, email 
        FROM users 
        WHERE subscription_status = 'pro' 
        AND id NOT IN (SELECT admin_user_id FROM facilities WHERE admin_user_id IS NOT NULL)
    """)).fetchall()
    
    # Create personal facilities for Pro users without facilities
    for user in pro_users_without_facilities:
        facility_name = f"{user.full_name or user.email.split('@')[0]}'s Practice"
        
        # Check if facility already exists (idempotency)
        existing_facility = connection.execute(text("""
            SELECT id FROM facilities WHERE admin_user_id = :admin_user_id
        """), {'admin_user_id': user.id}).fetchone()
        
        facility_id = None
        if existing_facility:
            facility_id = existing_facility.id
        else:
            # Insert facility - Use CURRENT_TIMESTAMP for compatibility
            # Use RETURNING id to get the ID on Postgres
            try:
                result = connection.execute(text("""
                    INSERT INTO facilities (facility_name, admin_user_id, is_active, created_at, updated_at)
                    VALUES (:facility_name, :admin_user_id, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id
                """), {
                    'facility_name': facility_name,
                    'admin_user_id': user.id
                })
                # fetchone() to get RETURNING result
                row = result.fetchone()
                if row:
                    facility_id = row[0]
            except Exception:
                # If using SQLite or DB without RETURNING support efficiently or error occurs
                # fallback or just pass if already exists (covered by check above)
                pass
        
        if facility_id:
            # Update user with facility_id if they don't have one
            connection.execute(text("""
                UPDATE users 
                SET facility_id = :facility_id 
                WHERE id = :user_id AND facility_id IS NULL
            """), {
                'facility_id': facility_id,
                'user_id': user.id
            })


def downgrade() -> None:
    """Revert Pro/Free user model changes."""
    connection = op.get_bind()
    
    # Revert subscription_status changes
    connection.execute(text("""
        UPDATE users 
        SET subscription_status = 'free' 
        WHERE subscription_status = 'pro';
    """))
    
    # Note: We don't delete personal facilities created during migration
    # as they may contain user data by the time of downgrade
