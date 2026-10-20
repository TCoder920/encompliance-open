"""
Training Notification Service Module

This module provides push notification functionality for training and certification management.
It integrates with the existing notification system to deliver real-time training updates.

Key functionalities:
- Training assignment notifications
- Due date reminders with escalation
- Completion confirmations
- Certification expiration alerts
- Bulk notification management
- Push notification scheduling

Dependencies:
- app.services.notification_service: For core notification functionality
- app.models.push_subscription: For push notification delivery
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.notification import NotificationType, NotificationPriority
from app.models.notification_settings import NotificationSettings
from app.models.staff_member import StaffMember
from app.models.training_program import TrainingProgram
from app.models.training_assignment import TrainingAssignment
from app.models.training_completion import TrainingCompletion
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationCreate

logger = logging.getLogger(__name__)

class TrainingNotificationService:
    """Service for handling training-related notifications and push notifications."""
    
    @staticmethod
    async def send_training_assignment_notification(
        db: Session,
        staff_member_id: int,
        training_program_title: str,
        due_date: datetime,
        assigned_by: str,
        assignment_id: int
    ) -> bool:
        """Send push notification when training is assigned to staff member."""
        try:
            # Get staff member details
            staff_member = db.query(StaffMember).filter(StaffMember.id == staff_member_id).first()
            if not staff_member:
                logger.error(f"Staff member {staff_member_id} not found")
                return False
            
            # Check notification preferences
            settings = await NotificationService.get_user_notification_settings(
                db, staff_member.facility_administrator_id
            )
            
            if not settings or not settings.push_training_assignments_enabled:
                logger.info(f"Training assignment notifications disabled for staff member {staff_member_id}")
                return False
            
            # Create notification
            notification_data = NotificationCreate(
                title="New Training Assignment",
                message=f"You have been assigned '{training_program_title}' training. Due: {due_date.strftime('%B %d, %Y')}",
                type=NotificationType.TRAINING_ASSIGNED,
                priority=NotificationPriority.MEDIUM,
                related_id=str(assignment_id),
                related_type="training_assignment",
                action_url=f"/training/assignments/{assignment_id}"
            )
            
            await NotificationService.create_notification(
                db, notification_data, staff_member.facility_administrator_id
            )
            
            logger.info(f"Training assignment notification sent to staff member {staff_member_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending training assignment notification: {str(e)}")
            return False
    
    @staticmethod
    async def send_training_due_reminder(
        db: Session,
        staff_member_id: int,
        training_program_title: str,
        days_until_due: int,
        assignment_id: int
    ) -> bool:
        """Send push notification for upcoming training due dates."""
        try:
            staff_member = db.query(StaffMember).filter(StaffMember.id == staff_member_id).first()
            if not staff_member:
                return False
            
            settings = await NotificationService.get_user_notification_settings(
                db, staff_member.facility_administrator_id
            )
            
            if not settings or not settings.push_training_reminders_enabled:
                return False
            
            # Determine urgency based on days until due
            if days_until_due <= 1:
                priority = NotificationPriority.HIGH
                urgency_text = "due tomorrow" if days_until_due == 1 else "due today"
            elif days_until_due <= 7:
                priority = NotificationPriority.MEDIUM
                urgency_text = f"due in {days_until_due} days"
            else:
                priority = NotificationPriority.LOW
                urgency_text = f"due in {days_until_due} days"
            
            notification_data = NotificationCreate(
                title="Training Due Reminder",
                message=f"'{training_program_title}' training is {urgency_text}",
                type=NotificationType.TRAINING_DUE,
                priority=priority,
                related_id=str(assignment_id),
                related_type="training_assignment",
                action_url=f"/training/assignments/{assignment_id}"
            )
            
            await NotificationService.create_notification(
                db, notification_data, staff_member.facility_administrator_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending training due reminder: {str(e)}")
            return False
    
    @staticmethod
    async def send_training_overdue_notification(
        db: Session,
        staff_member_id: int,
        training_program_title: str,
        days_overdue: int,
        assignment_id: int
    ) -> bool:
        """Send push notification for overdue training."""
        try:
            staff_member = db.query(StaffMember).filter(StaffMember.id == staff_member_id).first()
            if not staff_member:
                return False
            
            notification_data = NotificationCreate(
                title="Training Overdue",
                message=f"'{training_program_title}' training is {days_overdue} days overdue. Please complete immediately.",
                type=NotificationType.TRAINING_OVERDUE,
                priority=NotificationPriority.HIGH,
                related_id=str(assignment_id),
                related_type="training_assignment",
                action_url=f"/training/assignments/{assignment_id}"
            )
            
            await NotificationService.create_notification(
                db, notification_data, staff_member.facility_administrator_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending training overdue notification: {str(e)}")
            return False
    
    @staticmethod
    async def send_certification_expiration_alert(
        db: Session,
        staff_member_id: int,
        certification_name: str,
        expiration_date: datetime,
        completion_id: int
    ) -> bool:
        """Send push notification for expiring certifications."""
        try:
            staff_member = db.query(StaffMember).filter(StaffMember.id == staff_member_id).first()
            if not staff_member:
                return False
            
            settings = await NotificationService.get_user_notification_settings(
                db, staff_member.facility_administrator_id
            )
            
            if not settings or not settings.push_certification_expiring_enabled:
                return False
            
            days_until_expiry = (expiration_date - datetime.now()).days
            
            if days_until_expiry <= 7:
                priority = NotificationPriority.HIGH
            elif days_until_expiry <= 30:
                priority = NotificationPriority.MEDIUM
            else:
                priority = NotificationPriority.LOW
            
            notification_data = NotificationCreate(
                title="Certification Expiring",
                message=f"Your '{certification_name}' certification expires on {expiration_date.strftime('%B %d, %Y')}",
                type=NotificationType.CERTIFICATION_EXPIRING,
                priority=priority,
                related_id=str(completion_id),
                related_type="training_completion",
                action_url=f"/training/certifications/{completion_id}"
            )
            
            await NotificationService.create_notification(
                db, notification_data, staff_member.facility_administrator_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending certification expiration alert: {str(e)}")
            return False
    
    @staticmethod
    async def send_training_completion_notification(
        db: Session,
        staff_member_id: int,
        training_program_title: str,
        completion_id: int,
        certificate_generated: bool = False
    ) -> bool:
        """Send push notification when training is completed."""
        try:
            staff_member = db.query(StaffMember).filter(StaffMember.id == staff_member_id).first()
            if not staff_member:
                return False
            
            settings = await NotificationService.get_user_notification_settings(
                db, staff_member.facility_administrator_id
            )
            
            if not settings or not settings.push_training_completed_enabled:
                return False
            
            message = f"Congratulations! You have completed '{training_program_title}' training."
            if certificate_generated:
                message += " Your certificate is ready for download."
            
            notification_data = NotificationCreate(
                title="Training Completed",
                message=message,
                type=NotificationType.TRAINING_COMPLETED,
                priority=NotificationPriority.MEDIUM,
                related_id=str(completion_id),
                related_type="training_completion",
                action_url=f"/training/completions/{completion_id}"
            )
            
            await NotificationService.create_notification(
                db, notification_data, staff_member.facility_administrator_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending training completion notification: {str(e)}")
            return False
    
    @staticmethod
    async def send_bulk_training_notifications(
        db: Session,
        staff_member_ids: List[int],
        notification_type: str,
        training_data: Dict[str, Any]
    ) -> int:
        """Send bulk push notifications for training updates."""
        success_count = 0
        
        try:
            for staff_member_id in staff_member_ids:
                if notification_type == "assignment":
                    success = await TrainingNotificationService.send_training_assignment_notification(
                        db, staff_member_id, **training_data
                    )
                elif notification_type == "reminder":
                    success = await TrainingNotificationService.send_training_due_reminder(
                        db, staff_member_id, **training_data
                    )
                elif notification_type == "overdue":
                    success = await TrainingNotificationService.send_training_overdue_notification(
                        db, staff_member_id, **training_data
                    )
                else:
                    logger.warning(f"Unknown notification type: {notification_type}")
                    continue
                
                if success:
                    success_count += 1
            
            logger.info(f"Sent {success_count}/{len(staff_member_ids)} bulk training notifications")
            return success_count
            
        except Exception as e:
            logger.error(f"Error sending bulk training notifications: {str(e)}")
            return success_count
    
    @staticmethod
    async def send_facility_admin_update(
        db: Session,
        facility_admin_id: int,
        update_type: str,
        staff_member_name: str,
        training_program_title: str,
        details: Dict[str, Any]
    ) -> bool:
        """Send notification to facility administrator about staff training updates."""
        try:
            notification_data = NotificationCreate(
                title=f"Staff Training Update",
                message=f"{staff_member_name} has {update_type} '{training_program_title}' training",
                type=NotificationType.STAFF_TRAINING_UPDATE,
                priority=NotificationPriority.LOW,
                related_id=details.get("related_id"),
                related_type=details.get("related_type"),
                action_url=details.get("action_url")
            )
            
            await NotificationService.create_notification(
                db, notification_data, facility_admin_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending facility admin update: {str(e)}")
            return False 