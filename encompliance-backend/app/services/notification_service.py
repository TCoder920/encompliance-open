"""
Description: Notification service for handling notification operations.
Purpose: Provides business logic for creating, retrieving, and managing notifications.
Educational Note: Implements comprehensive notification system with email, push, and in-app delivery.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import json
import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.notification_settings import NotificationSettings
from app.models.push_subscription import PushSubscription
from app.schemas.notification import NotificationCreate, NotificationUpdate
from app.core.config import get_settings
from app.database import SessionLocal
from app.models.user import User  # add import

# Educational Note: Using pywebpush for Web Push Protocol implementation
try:
    from pywebpush import webpush, WebPushException
except ImportError:
    webpush = None
    WebPushException = Exception

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationService:
    @staticmethod
    async def create_notification(
        db: Session, 
        notification_data: NotificationCreate, 
        user_id: int,
        send_email: bool = True,
        send_push: bool = True
    ) -> Notification:
        """Create a new notification for a user."""
        db_notification = Notification(
            title=notification_data.title,
            message=notification_data.message,
            type=notification_data.type.value if isinstance(notification_data.type, NotificationType) else notification_data.type,
            priority=notification_data.priority.value if isinstance(notification_data.priority, NotificationPriority) else notification_data.priority,
            related_id=notification_data.related_id,
            related_type=notification_data.related_type,
            action_url=notification_data.action_url,
            user_id=user_id
        )
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        
        # Send email and push notifications if enabled (handle errors gracefully)
        try:
            if send_email:
                asyncio.create_task(NotificationService._send_email_notification(db, db_notification))
            if send_push:
                asyncio.create_task(NotificationService._send_push_notification(db, db_notification))
        except Exception as e:
            logger.error(f"Failed to create notification delivery tasks: {e}")
            # Don't fail the notification creation if delivery tasks fail
        
        return db_notification

    @staticmethod
    async def create_note_notification(
        db: Session, 
        user_id: int, 
        note_id: int, 
        action: str,
        title: str,
        note_title: str
    ) -> Notification:
        """Create a notification for a note-related action."""
        message = f"Your note '{note_title}' has been {action}."
        
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=NotificationType.NOTE.value,
            priority=NotificationPriority.LOW.value,
            related_id=str(note_id),
            related_type="note",
            action_url=f"/notes/{note_id}"
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    async def get_notifications(
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """Get all notifications for a user with pagination."""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        # Apply unread filter if requested
        if unread_only:
            query = query.filter(Notification.is_read == False)
            
        # Get total count for pagination
        total = query.count()
        
        # Get unread count
        unread_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
        
        # Apply sorting and pagination
        notifications = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()
        
        return {
            "notifications": notifications,
            "total": total,
            "unread_count": unread_count
        }

    @staticmethod
    async def get_notification(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        """Get a specific notification by ID for a user."""
        return db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

    @staticmethod
    async def mark_as_read(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        """Mark a notification as read."""
        db_notification = await NotificationService.get_notification(db, notification_id, user_id)
        if not db_notification:
            return None
            
        db_notification.is_read = True
        db.commit()
        db.refresh(db_notification)
        return db_notification

    @staticmethod
    async def mark_all_as_read(db: Session, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        result = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True})
        
        db.commit()
        return result

    @staticmethod
    async def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
        """Delete a notification for a user."""
        db_notification = await NotificationService.get_notification(db, notification_id, user_id)
        if not db_notification:
            return False
            
        db.delete(db_notification)
        db.commit()
        return True

    @staticmethod
    async def delete_all_notifications(db: Session, user_id: int) -> int:
        """Delete all notifications for a user."""
        result = db.query(Notification).filter(Notification.user_id == user_id).delete()
        db.commit()
        return result

    @staticmethod
    async def get_unread_count(db: Session, user_id: int) -> int:
        """Get the count of unread notifications for a user."""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()

    @staticmethod
    async def create_calendar_notification(
        db: Session,
        user_id: int,
        event_id: str,
        action: str,
        event_title: str,
        event_details: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Create a notification for a calendar-related action."""
        action_messages = {
            "created": f"Calendar event '{event_title}' has been created.",
            "updated": f"Calendar event '{event_title}' has been updated.",
            "deleted": f"Calendar event '{event_title}' has been deleted.",
            "reminder": f"Reminder: '{event_title}' is starting soon.",
            "started": f"Event '{event_title}' is starting now!"
        }
        
        action_titles = {
            "created": "Calendar Event Created",
            "updated": "Calendar Event Updated", 
            "deleted": "Calendar Event Deleted",
            "reminder": "Calendar Event Reminder",
            "started": "Calendar Event Started"
        }
        
        notification_type = NotificationType.CALENDAR_REMINDER if action in ["reminder", "started"] else NotificationType.CALENDAR
        priority = NotificationPriority.HIGH if action in ["reminder", "started"] else NotificationPriority.MEDIUM
        
        notification_data = NotificationCreate(
            title=action_titles.get(action, f"Calendar Event {action.title()}"),
            message=action_messages.get(action, f"Calendar event '{event_title}' {action}."),
            type=notification_type,
            priority=priority,
            related_id=event_id,
            related_type="calendar_event",
            action_url=f"/calendar?event={event_id}"
        )
        
        return await NotificationService.create_notification(db, notification_data, user_id)

    @staticmethod
    async def get_user_notification_settings(db: Session, user_id: int) -> Optional[NotificationSettings]:
        """Get user notification settings, creating default if none exist."""
        settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()
        if not settings:
            # Create default settings
            settings = NotificationSettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @staticmethod
    async def update_notification_settings(
        db: Session,
        user_id: int,
        settings_data: Dict[str, Any]
    ) -> NotificationSettings:
        """Update user notification settings."""
        settings = await NotificationService.get_user_notification_settings(db, user_id)
        
        for key, value in settings_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    async def _send_email_notification(db: Session, notification: Notification) -> bool:
        """Send email notification if user has email notifications enabled."""
        try:
            # Always use a fresh session to avoid issues with closed sessions
            db_session = SessionLocal()
            try:
                notification = db_session.query(Notification).filter(Notification.id == notification.id).first()
                if not notification:
                    return False

                user = db_session.query(User).get(notification.user_id)
                if not user:
                    return False

                settings = await NotificationService.get_user_notification_settings(db_session, user.id)
            
                # Check if email notifications are enabled for this type
                email_enabled = NotificationService._is_email_enabled_for_type(settings, notification.type)
                if not email_enabled:
                    return False
                
                # Prepare email content
                subject = f"EnCompliance - {notification.title}"
                body = NotificationService._generate_email_body(notification)
                
                # Send email
                return await NotificationService._send_email(user.email, subject, body)
            finally:
                db_session.close()
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    @staticmethod
    async def _send_push_notification(db: Session, notification: Notification) -> bool:
        """Send push notification if user has push notifications enabled."""
        try:
            db_session = SessionLocal()
            try:
                notification = db_session.query(Notification).filter(Notification.id == notification.id).first()
                if not notification:
                    return False

                user = db_session.query(User).get(notification.user_id)
                if not user:
                    return False

                if not webpush:
                    logger.warning("pywebpush not installed, skipping push notification")
                    return False
                
                user_settings = await NotificationService.get_user_notification_settings(db_session, user.id)
                
                # Check if push notifications are enabled
                if not user_settings or not user_settings.push_enabled:
                    return False
                
                # Check if push notifications are enabled for this type
                push_enabled = NotificationService._is_push_enabled_for_type(user_settings, notification.type)
                if not push_enabled:
                    return False
                
                # Get user's push subscriptions
                subscriptions = db_session.query(PushSubscription).filter(PushSubscription.user_id == user.id).all()
                if not subscriptions:
                    return False
                
                # Prepare push payload
                payload = {
                    "title": notification.title,
                    "body": notification.message,
                    "icon": "/icon-192x192.png",
                    "badge": "/badge-72x72.png",
                    "data": {
                        "notificationId": notification.id,
                        "actionUrl": notification.action_url or "/notifications"
                    }
                }
                
                success_count = 0
                for subscription in subscriptions:
                    try:
                        # Handle different VAPID key formats
                        vapid_private_key = None
                        if settings.VAPID_PRIVATE_KEY_B64URL:
                            vapid_private_key = settings.VAPID_PRIVATE_KEY_B64URL
                        elif settings.VAPID_PRIVATE_KEY_B64:
                            import base64
                            der_bytes = base64.b64decode(settings.VAPID_PRIVATE_KEY_B64)
                            vapid_private_key = base64.urlsafe_b64encode(der_bytes).rstrip(b'=').decode()
                        elif settings.VAPID_PRIVATE_KEY:
                            import base64
                            from cryptography.hazmat.primitives import serialization
                            pem_key = settings.VAPID_PRIVATE_KEY
                            if pem_key.startswith('-----BEGIN'):
                                pem_key = pem_key.replace('\\n', '\n')
                            private_key = serialization.load_pem_private_key(pem_key.encode(), password=None)
                            der_bytes = private_key.private_bytes(
                                encoding=serialization.Encoding.DER,
                                format=serialization.PrivateFormat.PKCS8,
                                encryption_algorithm=serialization.NoEncryption()
                            )
                            vapid_private_key = base64.urlsafe_b64encode(der_bytes).rstrip(b'=').decode()
                        
                        if not vapid_private_key:
                            logger.error("No valid VAPID private key found")
                            continue
                        
                        webpush(
                            subscription_info={
                                "endpoint": subscription.endpoint,
                                "keys": subscription.keys
                            },
                            data=json.dumps(payload),
                            vapid_private_key=vapid_private_key,
                            vapid_claims={"sub": settings.VAPID_EMAIL}
                        )
                        success_count += 1
                    except WebPushException as e:
                        logger.error(f"Failed to send push to subscription {subscription.id}: {e}")
                        if e.response and e.response.status_code in [410, 413]:
                            db_session.delete(subscription)
                            db_session.commit()
                
                return success_count > 0
            finally:
                db_session.close()
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False

    @staticmethod
    def _is_email_enabled_for_type(settings: NotificationSettings, notification_type_str: str) -> bool:
        """Check if email notifications are enabled for a specific type."""
        try:
            notification_type = NotificationType(notification_type_str)  # Convert string to Enum
        except ValueError:
            return False  # Invalid type string
        
        type_mapping = {
            NotificationType.CALENDAR: settings.email_calendar_enabled,
            NotificationType.CALENDAR_REMINDER: settings.email_calendar_reminders_enabled,
            NotificationType.NOTE: settings.email_note_notifications_enabled,
            NotificationType.MESSAGE: settings.email_message_notifications_enabled,
            NotificationType.REGULATORY_UPDATE: settings.email_regulatory_updates_enabled,
            NotificationType.SYSTEM: settings.email_system_notifications_enabled,
            NotificationType.SECURITY: settings.email_system_notifications_enabled,
            NotificationType.SUBSCRIPTION: settings.email_system_notifications_enabled,
        }
        return type_mapping.get(notification_type, False)

    @staticmethod
    def _is_push_enabled_for_type(settings: NotificationSettings, notification_type_str: str) -> bool:
        """Check if push notifications are enabled for a specific type."""
        try:
            notification_type = NotificationType(notification_type_str)  # Convert string to Enum
        except ValueError:
            return False  # Invalid type string
            
        type_mapping = {
            NotificationType.CALENDAR: settings.push_calendar_enabled,
            NotificationType.CALENDAR_REMINDER: settings.push_calendar_reminders_enabled,
            NotificationType.NOTE: settings.push_note_notifications_enabled,
            NotificationType.MESSAGE: settings.push_message_notifications_enabled,
            NotificationType.REGULATORY_UPDATE: settings.push_regulatory_updates_enabled,
            NotificationType.SYSTEM: settings.push_system_notifications_enabled,
            NotificationType.SECURITY: settings.push_system_notifications_enabled,
            NotificationType.SUBSCRIPTION: settings.push_system_notifications_enabled,
        }
        return type_mapping.get(notification_type, False)

    @staticmethod
    def _generate_email_body(notification: Notification) -> str:
        """Generate HTML email body for notification."""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">{notification.title}</h2>
                <p>{notification.message}</p>
                {f'<p><a href="{settings.FRONTEND_URL}{notification.action_url}" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Details</a></p>' if notification.action_url else ''}
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    This is an automated notification from EnCompliance. 
                    You can manage your notification preferences in your account settings.
                </p>
            </div>
        </body>
        </html>
        """

    @staticmethod
    async def _send_email(to_email: str, subject: str, body: str) -> bool:
        """Send email using SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = to_email
            
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    @staticmethod
    async def create_push_subscription(db: Session, user_id: int, subscription_data: Dict[str, Any]) -> PushSubscription:
        """Create a new push subscription for a user."""
        # Check if subscription already exists
        existing = db.query(PushSubscription).filter(
            PushSubscription.endpoint == subscription_data["endpoint"]
        ).first()
        
        if existing:
            # Update existing subscription
            existing.keys = subscription_data["keys"]
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new subscription
        subscription = PushSubscription(
            user_id=user_id,
            endpoint=subscription_data["endpoint"],
            keys=subscription_data["keys"]
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    async def delete_push_subscription(db: Session, user_id: int, endpoint: str) -> bool:
        """Delete a push subscription for a user."""
        subscription = db.query(PushSubscription).filter(
            PushSubscription.user_id == user_id,
            PushSubscription.endpoint == endpoint
        ).first()
        
        if subscription:
            db.delete(subscription)
            db.commit()
            return True
        return False