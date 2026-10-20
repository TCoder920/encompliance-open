#!/usr/bin/env python3
"""
Utility script to seed a support portal account in the support portal database.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import support_portal_engine, SupportPortalBase
from app.models.support_portal_account import SupportPortalAccount
# Import all support portal models to ensure tables are created correctly
from app.models.support_ticket import SupportTicket, SupportTicketComment, SupportAgentProfile
from app.models.audit_log import AuditLog
from app.auth.support_portal_auth_utils import get_password_hash, SUPPORT_ADMIN_ROLE, normalize_role_names
from sqlalchemy.orm import sessionmaker

# Create session
SessionLocal = sessionmaker(bind=support_portal_engine)
db = SessionLocal()

try:
    SupportPortalBase.metadata.create_all(bind=support_portal_engine)
    existing = db.query(SupportPortalAccount).filter(
        (SupportPortalAccount.username == "support@example.com")
        | (SupportPortalAccount.email == "support@example.com")
    ).first()
    
    if existing:
        print(f"Support user already exists: {existing.username}")
        sys.exit(0)
    
    support_user = SupportPortalAccount(
        username="support@example.com",
        email="support@example.com",
        hashed_password=get_password_hash("TempPass123!"),
        roles=normalize_role_names([SUPPORT_ADMIN_ROLE])
    )
    db.add(support_user)
    db.commit()
    db.refresh(support_user)
    
    print(f"Support user created successfully!")
    print(f"  Username: {support_user.username}")
    print(f"  Email: {support_user.email}")
    print(f"  ID: {support_user.id}")
    print(f"  Roles: {support_user.roles}")
    
except Exception as exc:
    print(f"Error creating support user: {exc}")
    db.rollback()
    sys.exit(1)
finally:
    db.close()

