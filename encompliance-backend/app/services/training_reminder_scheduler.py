"""
Training Reminder Scheduler Module

This module provides automated scheduling for training-related push notifications.
It integrates with the existing calendar reminder system for comprehensive notification management.

Key functionalities:
- Automated training due date reminders
- Certification expiration notifications
- Escalation notifications for overdue training
- Batch processing for multiple staff members
- Integration with user notification preferences

Dependencies:
- app.services.calendar_reminder_service: For scheduling infrastructure
- app.services.training_notification_service: For training-specific notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.training_assignment import TrainingAssignment, AssignmentStatus
from app.models.training_completion import TrainingCompletion
from app.models.staff_member import StaffMember
from app.models.training_program import TrainingProgram
from app.models.notification_settings import NotificationSettings
from app.services.training_notification_service import TrainingNotificationService

logger = logging.getLogger(__name__)

class TrainingReminderScheduler:
    """Service for automated training reminder scheduling and notification management."""
    
    @staticmethod
    async def check_and_send_training_reminders():
        """Check for training due dates and send push notifications."""
        try:
            db = next(get_db())
            current_time = datetime.now()
            
            # Get all active training assignments
            assignments = db.query(TrainingAssignment).filter(
                TrainingAssignment.status.in_([
                    AssignmentStatus.ASSIGNED.value,
                    AssignmentStatus.IN_PROGRESS.value
                ])
            ).all()
            
            reminders_sent = 0
            
            for assignment in assignments:
                try:
                    # Get training program details
                    training_program = db.query(TrainingProgram).filter(
                        TrainingProgram.id == assignment.training_program_id
                    ).first()
                    
                    if not training_program or not training_program.is_active:
                        continue
                    
                    # Calculate days until due
                    days_until_due = (assignment.due_date - current_time).days
                    
                    # Get reminder schedule from training program or use default
                    reminder_days = training_program.reminder_schedule_days or [30, 14, 7, 1]
                    
                    # Check if reminder should be sent
                    should_send_reminder = False
                    for reminder_day in reminder_days:
                        if days_until_due == reminder_day:
                            should_send_reminder = True
                            break
                    
                    if should_send_reminder:
                        # Check if reminder already sent for this day
                        reminder_sent_dates = assignment.reminder_sent_dates or []
                        reminder_key = f"{current_time.strftime('%Y-%m-%d')}_{days_until_due}"
                        
                        if reminder_key not in reminder_sent_dates:
                            # Send reminder notification
                            success = await TrainingReminderScheduler._send_training_reminder(
                                db, assignment, training_program, days_until_due
                            )
                            
                            if success:
                                # Update reminder sent tracking
                                reminder_sent_dates.append(reminder_key)
                                assignment.reminder_sent_dates = reminder_sent_dates
                                db.commit()
                                reminders_sent += 1
                
                except Exception as e:
                    logger.error(f"Error processing training assignment {assignment.id}: {str(e)}")
                    continue
            
            logger.info(f"Sent {reminders_sent} training due reminders")
            db.close()
            
        except Exception as e:
            logger.error(f"Error in training reminder check: {str(e)}")
    
    @staticmethod
    async def check_and_send_overdue_notifications():
        """Check for overdue training and send escalation notifications."""
        try:
            db = next(get_db())
            current_time = datetime.now()
            
            # Get overdue assignments
            overdue_assignments = db.query(TrainingAssignment).filter(
                TrainingAssignment.due_date < current_time,
                TrainingAssignment.status.in_([
                    AssignmentStatus.ASSIGNED.value,
                    AssignmentStatus.IN_PROGRESS.value
                ])
            ).all()
            
            overdue_notifications_sent = 0
            
            for assignment in overdue_assignments:
                try:
                    # Update status to overdue if not already
                    if assignment.status != AssignmentStatus.OVERDUE.value:
                        assignment.status = AssignmentStatus.OVERDUE.value
                        db.commit()
                    
                    # Send overdue notification if not already sent
                    if not assignment.escalation_sent:
                        training_program = db.query(TrainingProgram).filter(
                            TrainingProgram.id == assignment.training_program_id
                        ).first()
                        
                        if training_program:
                            days_overdue = (current_time - assignment.due_date).days
                            
                            success = await TrainingNotificationService.send_training_overdue_notification(
                                db, assignment.staff_member_id, training_program.title,
                                days_overdue, assignment.id
                            )
                            
                            if success:
                                assignment.escalation_sent = True
                                db.commit()
                                overdue_notifications_sent += 1
                
                except Exception as e:
                    logger.error(f"Error processing overdue assignment {assignment.id}: {str(e)}")
                    continue
            
            logger.info(f"Sent {overdue_notifications_sent} overdue training notifications")
            db.close()
            
        except Exception as e:
            logger.error(f"Error in overdue training check: {str(e)}")
    
    @staticmethod
    async def check_and_send_certification_expiry_reminders():
        """Check for expiring certifications and send push notifications."""
        try:
            db = next(get_db())
            current_time = datetime.now()
            
            # Get certifications that are expiring
            expiring_completions = db.query(TrainingCompletion).filter(
                TrainingCompletion.expires_date.isnot(None),
                TrainingCompletion.expires_date > current_time,
                TrainingCompletion.renewal_reminder_sent == False
            ).all()
            
            expiry_reminders_sent = 0
            
            for completion in expiring_completions:
                try:
                    days_until_expiry = (completion.expires_date - current_time).days
                    
                    # Get user's reminder preferences
                    staff_member = db.query(StaffMember).filter(
                        StaffMember.id == completion.staff_member_id
                    ).first()
                    
                    if not staff_member:
                        continue
                    
                    settings = db.query(NotificationSettings).filter(
                        NotificationSettings.user_id == staff_member.facility_administrator_id
                    ).first()
                    
                    reminder_days = [60, 30, 14, 7, 1]  # Default
                    if settings and settings.certification_expiry_reminder_days:
                        reminder_days = settings.certification_expiry_reminder_days
                    
                    # Check if reminder should be sent
                    if days_until_expiry in reminder_days:
                        training_program = db.query(TrainingProgram).filter(
                            TrainingProgram.id == completion.training_program_id
                        ).first()
                        
                        if training_program:
                            success = await TrainingNotificationService.send_certification_expiration_alert(
                                db, completion.staff_member_id, training_program.title,
                                completion.expires_date, completion.id
                            )
                            
                            if success and days_until_expiry <= 30:
                                # Mark reminder as sent for 30 days or less
                                completion.renewal_reminder_sent = True
                                db.commit()
                                expiry_reminders_sent += 1
                
                except Exception as e:
                    logger.error(f"Error processing certification expiry {completion.id}: {str(e)}")
                    continue
            
            logger.info(f"Sent {expiry_reminders_sent} certification expiry reminders")
            db.close()
            
        except Exception as e:
            logger.error(f"Error in certification expiry check: {str(e)}")
    
    @staticmethod
    async def _send_training_reminder(
        db: Session,
        assignment: TrainingAssignment,
        training_program: TrainingProgram,
        days_until_due: int
    ) -> bool:
        """Send training reminder notification."""
        try:
            return await TrainingNotificationService.send_training_due_reminder(
                db, assignment.staff_member_id, training_program.title,
                days_until_due, assignment.id
            )
        except Exception as e:
            logger.error(f"Error sending training reminder: {str(e)}")
            return False
    
    @staticmethod
    async def start_training_reminder_scheduler():
        """Start the background task for checking training reminders."""
        logger.info("Starting training reminder scheduler")
        
        while True:
            try:
                # Check training due reminders
                await TrainingReminderScheduler.check_and_send_training_reminders()
                
                # Check overdue training
                await TrainingReminderScheduler.check_and_send_overdue_notifications()
                
                # Check certification expiry
                await TrainingReminderScheduler.check_and_send_certification_expiry_reminders()
                
                # Check every 6 hours (21600 seconds)
                await asyncio.sleep(21600)
                
            except Exception as e:
                logger.error(f"Error in training reminder scheduler: {str(e)}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)
    
    @staticmethod
    async def process_daily_training_digest():
        """Process daily training digest for facility administrators.
        
        Note: Facility administrators are users with a pro subscription who manage facility operations.
        """
        try:
            db = next(get_db())
            current_time = datetime.now()
            
            # Get all facility administrators (users with pro subscription)
            facility_admins = db.query(StaffMember).filter(
                StaffMember.role == "administrator"
            ).all()
            
            for admin in facility_admins:
                try:
                    # Get training summary for this facility
                    summary = await TrainingReminderScheduler._get_facility_training_summary(
                        db, admin.facility_administrator_id
                    )
                    
                    if summary["total_assignments"] > 0:
                        # Send digest notification
                        await TrainingReminderScheduler._send_training_digest(
                            db, admin.facility_administrator_id, summary
                        )
                
                except Exception as e:
                    logger.error(f"Error processing digest for admin {admin.id}: {str(e)}")
                    continue
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error in daily training digest: {str(e)}")
    
    @staticmethod
    async def _get_facility_training_summary(db: Session, facility_admin_id: int) -> Dict[str, Any]:
        """Get training summary for a facility."""
        try:
            # Get all staff for this facility
            staff_members = db.query(StaffMember).filter(
                StaffMember.facility_administrator_id == facility_admin_id
            ).all()
            
            staff_ids = [staff.id for staff in staff_members]
            
            if not staff_ids:
                return {"total_assignments": 0}
            
            # Get assignment counts
            total_assignments = db.query(TrainingAssignment).filter(
                TrainingAssignment.staff_member_id.in_(staff_ids)
            ).count()
            
            overdue_assignments = db.query(TrainingAssignment).filter(
                TrainingAssignment.staff_member_id.in_(staff_ids),
                TrainingAssignment.status == AssignmentStatus.OVERDUE.value
            ).count()
            
            due_soon_assignments = db.query(TrainingAssignment).filter(
                TrainingAssignment.staff_member_id.in_(staff_ids),
                TrainingAssignment.due_date <= datetime.now() + timedelta(days=7),
                TrainingAssignment.status.in_([
                    AssignmentStatus.ASSIGNED.value,
                    AssignmentStatus.IN_PROGRESS.value
                ])
            ).count()
            
            completed_this_week = db.query(TrainingAssignment).filter(
                TrainingAssignment.staff_member_id.in_(staff_ids),
                TrainingAssignment.status == AssignmentStatus.COMPLETED.value,
                TrainingAssignment.completed_date >= datetime.now() - timedelta(days=7)
            ).count()
            
            return {
                "total_assignments": total_assignments,
                "overdue_assignments": overdue_assignments,
                "due_soon_assignments": due_soon_assignments,
                "completed_this_week": completed_this_week,
                "total_staff": len(staff_members)
            }
            
        except Exception as e:
            logger.error(f"Error getting facility training summary: {str(e)}")
            return {"total_assignments": 0}
    
    @staticmethod
    async def _send_training_digest(
        db: Session,
        facility_admin_id: int,
        summary: Dict[str, Any]
    ) -> bool:
        """Send training digest notification to facility administrator.
        
        Note: Facility administrators are users with a pro subscription who manage facility operations.
        """
        try:
            message = f"Training Summary: {summary['overdue_assignments']} overdue, "
            message += f"{summary['due_soon_assignments']} due soon, "
            message += f"{summary['completed_this_week']} completed this week"
            
            return await TrainingNotificationService.send_facility_admin_update(
                db, facility_admin_id, "digest", "Facility Staff", "Training Summary",
                {
                    "related_id": None,
                    "related_type": "training_digest",
                    "action_url": "/training/dashboard"
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending training digest: {str(e)}")
            return False 