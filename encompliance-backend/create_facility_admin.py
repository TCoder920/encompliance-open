#!/usr/bin/env python3
"""
Script to create a facility administrator account for testing.

This script creates:
1. A new user account with FACILITY_ADMIN role
2. A facility associated with that user
3. Sets up the user with pro subscription status

Usage:
    python create_facility_admin.py
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.user import User, UserRole
from app.models.facility import Facility
from app.auth.utils import get_password_hash
from datetime import datetime

def create_facility_admin(
    email: str = "facility_admin@test.com",
    username: str = "facility_admin",
    password: str = "TestPassword123!",
    full_name: str = "Facility Administrator",
    facility_name: str = "Test Healthcare Facility"
):
    """Create a facility administrator account with a facility."""
    db_gen = get_db()
    db = next(db_gen)

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            print(f"User with email '{email}' or username '{username}' already exists!")
            print(f"User ID: {existing_user.id}, Email: {existing_user.email}, Username: {existing_user.username}")
            print(f"Role: {existing_user.user_role}, Facility ID: {existing_user.facility_id}")
            
            # Check if they already have a facility
            if existing_user.administered_facility:
                print(f"User already administers facility: {existing_user.administered_facility.facility_name}")
            elif existing_user.facility_id:
                print(f"User is a member of facility ID: {existing_user.facility_id}")
            
            return existing_user
        
        # Create the user
        hashed_password = get_password_hash(password)
        db_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            user_role=UserRole.FACILITY_ADMIN,
            subscription_status="pro",
            is_active=True,
            email_verified=True
        )
        
        db.add(db_user)
        db.flush()  # Get user ID without committing
        
        # Create the facility
        db_facility = Facility(
            facility_name=facility_name,
            admin_user_id=db_user.id,
            is_active=True
        )
        
        db.add(db_facility)
        db.flush()  # Get facility ID without committing
        
        # Link user to facility
        db_user.facility_id = db_facility.id
        
        # Commit all changes
        db.commit()
        db.refresh(db_user)
        db.refresh(db_facility)
        
        print("=" * 60)
        print("Facility Administrator Account Created Successfully!")
        print("=" * 60)
        print(f"User ID: {db_user.id}")
        print(f"Email: {db_user.email}")
        print(f"Username: {db_user.username}")
        print(f"Full Name: {db_user.full_name}")
        print(f"Role: {db_user.user_role.value}")
        print(f"Subscription Status: {db_user.subscription_status}")
        print(f"Facility ID: {db_facility.id}")
        print(f"Facility Name: {db_facility.facility_name}")
        print(f"Password: {password}")
        print("=" * 60)
        print("\nYou can now log in with:")
        print(f"  Email/Username: {email}")
        print(f"  Password: {password}")
        print("=" * 60)
        
        return db_user
        
    except Exception as e:
        print(f"Error creating facility admin account: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # You can customize these values or pass them as command-line arguments
    create_facility_admin()

