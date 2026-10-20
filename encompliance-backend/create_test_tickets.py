#!/usr/bin/env python3
"""
Create Test Support Tickets
----------------------------
Creates sample support tickets for testing the support portal.
"""

import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import get_support_portal_db, get_db
from app.models.support_ticket import (
    SupportTicket,
    TicketStatus,
    TicketPriority,
    TicketCategory,
    SupportTier,
)
from app.models.user import User
from datetime import datetime, timedelta

def create_test_tickets():
    """Create sample support tickets for testing."""
    support_db: Session = next(get_support_portal_db())
    user_db: Session = next(get_db())
    
    try:
        # Get a sample user if available
        sample_user = user_db.query(User).first()
        user_id = sample_user.id if sample_user else None
        facility_id = sample_user.facility_id if sample_user else None
        
        # Sample tickets to create
        test_tickets = [
            {
                "subject": "Unable to access compliance documents",
                "description": "I'm getting a 403 error when trying to access the compliance documents section. This started happening after the last update.",
                "category": TicketCategory.TECHNICAL,
                "priority": TicketPriority.HIGH,
                "support_tier_required": SupportTier.MID,
                "status": TicketStatus.OPEN,
            },
            {
                "subject": "Billing question about subscription renewal",
                "description": "I received an invoice but I'm not sure what it's for. Can someone clarify what services this covers?",
                "category": TicketCategory.BILLING,
                "priority": TicketPriority.MEDIUM,
                "support_tier_required": SupportTier.BEGINNER,
                "status": TicketStatus.OPEN,
            },
            {
                "subject": "Need help with training module setup",
                "description": "I'm trying to set up a new training module for my facility but I can't find the option to create custom content.",
                "category": TicketCategory.TRAINING,
                "priority": TicketPriority.LOW,
                "support_tier_required": SupportTier.BEGINNER,
                "status": TicketStatus.IN_PROGRESS,
            },
            {
                "subject": "Account access issue - urgent",
                "description": "I cannot log into my account and I have an important compliance deadline tomorrow. This is urgent!",
                "category": TicketCategory.ACCOUNT,
                "priority": TicketPriority.URGENT,
                "support_tier_required": SupportTier.SENIOR,
                "status": TicketStatus.OPEN,
            },
            {
                "subject": "Document upload not working",
                "description": "When I try to upload PDF documents, the upload progress bar gets stuck at 50% and never completes.",
                "category": TicketCategory.TECHNICAL,
                "priority": TicketPriority.MEDIUM,
                "support_tier_required": SupportTier.MID,
                "status": TicketStatus.OPEN,
            },
            {
                "subject": "Question about compliance regulations",
                "description": "I need clarification on the new Maryland COMAR regulations that were recently added. What's the compliance deadline?",
                "category": TicketCategory.DOCUMENTATION,
                "priority": TicketPriority.MEDIUM,
                "support_tier_required": SupportTier.MID,
                "status": TicketStatus.RESOLVED,
            },
            {
                "subject": "Feature request: Export to Excel",
                "description": "It would be great if we could export compliance reports directly to Excel format instead of just PDF.",
                "category": TicketCategory.OTHER,
                "priority": TicketPriority.LOW,
                "support_tier_required": SupportTier.BEGINNER,
                "status": TicketStatus.OPEN,
            },
        ]
        
        created_count = 0
        for ticket_data in test_tickets:
            # Check if ticket with same subject already exists
            existing = support_db.query(SupportTicket).filter(
                SupportTicket.subject == ticket_data["subject"]
            ).first()
            
            if existing:
                print(f"Ticket '{ticket_data['subject']}' already exists, skipping...")
                continue
            
            ticket = SupportTicket(
                subject=ticket_data["subject"],
                description=ticket_data["description"],
                category=ticket_data["category"],
                priority=ticket_data["priority"],
                support_tier_required=ticket_data["support_tier_required"],
                status=ticket_data["status"],
                user_id=user_id,
                facility_id=facility_id,
                created_at=datetime.utcnow() - timedelta(days=created_count),  # Stagger creation dates
            )
            
            support_db.add(ticket)
            created_count += 1
        
        support_db.commit()
        print(f"✅ Successfully created {created_count} test tickets!")
        print(f"📋 You can now view them in the support portal at http://localhost:5200")
        
    except Exception as e:
        print(f"❌ Error creating test tickets: {e}")
        import traceback
        traceback.print_exc()
        support_db.rollback()
    finally:
        support_db.close()
        user_db.close()

if __name__ == "__main__":
    print("Creating test support tickets...")
    create_test_tickets()

