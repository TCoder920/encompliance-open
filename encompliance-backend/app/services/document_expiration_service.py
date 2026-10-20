"""
Document Expiration Service Module

This module provides automated notification functionality for document expiration tracking
in Pro Mode facility administrator environments.

Key functionalities:
- Document expiration monitoring and alerts
- Automated reminder scheduling (30, 14, 7, 1 days before expiry)
- Facility administrator notification delivery
- Document renewal tracking
- Integration with existing notification system

Dependencies:
- app.models.document: Document model with expiration tracking
- app.models.notification_settings: User notification preferences
- app.services.notification_service: Core notification functionality
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.models.facility import Facility
from app.models.notification_settings import NotificationSettings
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationCreate
from app.models.notification import NotificationType, NotificationPriority

logger = logging.getLogger(__name__)

class DocumentExpirationService:
    """Service for automated document expiration monitoring and notification management."""
    
    @staticmethod
    async def check_and_send_document_expiration_reminders():
        """Check for expiring documents and send automated reminders to facility administrators."""
        try:
            db = next(get_db())
            current_time = datetime.now()
            
            # Get all documents with expiration dates that haven't expired yet
            expiring_documents = db.query(Document).filter(
                Document.expiration_date.isnot(None),
                Document.expiration_date > current_time,
                Document.is_deleted == False,
                Document.facility_id.isnot(None)
            ).all()
            
            reminders_sent = 0
            
            for document in expiring_documents:
                try:
                    # Calculate days until expiry
                    days_until_expiry = (document.expiration_date - current_time).days
                    
                    # Get facility administrator
                    facility = db.query(Facility).filter(Facility.id == document.facility_id).first()
                    if not facility:
                        continue
                    
                    admin_user = db.query(User).filter(User.id == facility.admin_user_id).first()
                    if not admin_user:
                        continue
                    
                    # Get user's notification preferences
                    settings = db.query(NotificationSettings).filter(
                        NotificationSettings.user_id == admin_user.id
                    ).first()
                    
                    if not settings or not settings.document_expiration_reminders_enabled:
                        continue
                    
                    # Determine which reminder to send based on days until expiry
                    reminder_to_send = None
                    reminder_days = settings.document_expiration_reminder_days or [30, 14, 7, 1]
                    
                    if days_until_expiry <= 1 and not document.expiration_reminder_1_day_sent:
                        reminder_to_send = 1
                    elif days_until_expiry <= 7 and not document.expiration_reminder_7_days_sent:
                        reminder_to_send = 7
                    elif days_until_expiry <= 14 and not document.expiration_reminder_14_days_sent:
                        reminder_to_send = 14
                    elif days_until_expiry <= 30 and not document.expiration_reminder_30_days_sent:
                        reminder_to_send = 30
                    
                    # Only send if this day count is in the user's preferences
                    if reminder_to_send and reminder_to_send in reminder_days:
                        success = await DocumentExpirationService._send_document_expiration_notification(
                            db, document, admin_user, days_until_expiry
                        )
                        
                        if success:
                            # Mark reminder as sent
                            if reminder_to_send == 1:
                                document.expiration_reminder_1_day_sent = True
                            elif reminder_to_send == 7:
                                document.expiration_reminder_7_days_sent = True
                            elif reminder_to_send == 14:
                                document.expiration_reminder_14_days_sent = True
                            elif reminder_to_send == 30:
                                document.expiration_reminder_30_days_sent = True
                            
                            db.commit()
                            reminders_sent += 1
                
                except Exception as e:
                    logger.error(f"Error processing document expiration {document.id}: {str(e)}")
                    continue
            
            logger.info(f"Sent {reminders_sent} document expiration reminders")
            db.close()
            
        except Exception as e:
            logger.error(f"Error in document expiration reminder check: {str(e)}")
    
    @staticmethod
    async def _send_document_expiration_notification(
        db: Session,
        document: Document,
        admin_user: User,
        days_until_expiry: int
    ) -> bool:
        """Send document expiration notification to facility administrator."""
        try:
            # Determine priority based on urgency
            if days_until_expiry <= 1:
                priority = NotificationPriority.HIGH
                urgency_text = "expires tomorrow" if days_until_expiry == 1 else "expires today"
            elif days_until_expiry <= 7:
                priority = NotificationPriority.MEDIUM
                urgency_text = f"expires in {days_until_expiry} days"
            else:
                priority = NotificationPriority.LOW
                urgency_text = f"expires in {days_until_expiry} days"
            
            # Create document title for notification
            document_title = document.custom_label or document.filename
            if document.document_type:
                document_title = f"{document.document_type}: {document_title}"
            
            notification_data = NotificationCreate(
                title="Document Expiring",
                message=f"'{document_title}' {urgency_text} on {document.expiration_date.strftime('%B %d, %Y')}",
                type=NotificationType.DOCUMENT_EXPIRING,
                priority=priority,
                related_id=str(document.id),
                related_type="document",
                action_url=f"/documents?id={document.id}"
            )
            
            await NotificationService.create_notification(
                db, notification_data, admin_user.id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending document expiration notification: {str(e)}")
            return False
    
    @staticmethod
    async def set_document_expiration(
        db: Session,
        document_id: int,
        expiration_date: datetime,
        document_type: str,
        issuing_authority: Optional[str] = None,
        renewal_required: bool = True
    ) -> bool:
        """Set expiration information for a document."""
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return False
            
            document.expiration_date = expiration_date
            document.document_type = document_type
            document.issuing_authority = issuing_authority
            document.renewal_required = renewal_required
            
            # Reset reminder flags when expiration date is updated
            document.expiration_reminder_30_days_sent = False
            document.expiration_reminder_14_days_sent = False
            document.expiration_reminder_7_days_sent = False
            document.expiration_reminder_1_day_sent = False
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error setting document expiration: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    async def get_expiring_documents(
        db: Session,
        facility_id: int,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """Get documents expiring within specified timeframe for a facility."""
        try:
            current_time = datetime.now()
            end_date = current_time + timedelta(days=days_ahead)
            
            expiring_docs = db.query(Document).filter(
                Document.facility_id == facility_id,
                Document.expiration_date.isnot(None),
                Document.expiration_date.between(current_time, end_date),
                Document.is_deleted == False
            ).order_by(Document.expiration_date).all()
            
            results = []
            for doc in expiring_docs:
                results.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "custom_label": doc.custom_label,
                    "document_type": doc.document_type,
                    "expiration_date": doc.expiration_date.isoformat(),
                    "days_until_expiry": doc.days_until_expiry,
                    "is_expired": doc.is_expired,
                    "issuing_authority": doc.issuing_authority,
                    "renewal_required": doc.renewal_required
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting expiring documents: {str(e)}")
            return []
    
    @staticmethod
    async def check_expired_documents():
        """Check for expired documents and send notifications."""
        try:
            db = next(get_db())
            current_time = datetime.now()
            
            # Get all expired documents that haven't been marked as expired yet
            expired_documents = db.query(Document).filter(
                Document.expiration_date.isnot(None),
                Document.expiration_date <= current_time,
                Document.is_deleted == False,
                Document.facility_id.isnot(None)
            ).all()
            
            expired_notifications_sent = 0
            
            for document in expired_documents:
                try:
                    # Get facility administrator
                    facility = db.query(Facility).filter(Facility.id == document.facility_id).first()
                    if not facility:
                        continue
                    
                    admin_user = db.query(User).filter(User.id == facility.admin_user_id).first()
                    if not admin_user:
                        continue
                    
                    # Send expired notification
                    document_title = document.custom_label or document.filename
                    if document.document_type:
                        document_title = f"{document.document_type}: {document_title}"
                    
                    notification_data = NotificationCreate(
                        title="Document Expired",
                        message=f"'{document_title}' expired on {document.expiration_date.strftime('%B %d, %Y')}. Renewal may be required.",
                        type=NotificationType.DOCUMENT_EXPIRED,
                        priority=NotificationPriority.HIGH,
                        related_id=str(document.id),
                        related_type="document",
                        action_url=f"/documents?id={document.id}"
                    )
                    
                    await NotificationService.create_notification(
                        db, notification_data, admin_user.id
                    )
                    
                    expired_notifications_sent += 1
                
                except Exception as e:
                    logger.error(f"Error processing expired document {document.id}: {str(e)}")
                    continue
            
            logger.info(f"Sent {expired_notifications_sent} expired document notifications")
            db.close()
            
        except Exception as e:
            logger.error(f"Error in expired document check: {str(e)}") 