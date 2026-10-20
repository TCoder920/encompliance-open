"""
Facility Task Notification Service Module

This module provides automated notification functionality for facility task management
and operational reminders in Pro Mode facility administrator environments.

Key functionalities:
- Scheduled task reminder notifications
- Overdue task escalation alerts
- Task assignment notifications
- Task completion confirmations
- Integration with existing notification and task management systems

Dependencies:
- app.models.operational_task: Task management models
- app.models.task_assignment: Task assignment tracking
- app.services.notification_service: Core notification functionality
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.operational_task import OperationalTask, TaskType, TaskStatus
from app.models.task_assignment import TaskAssignment, TaskAssignmentStatus
from app.models.user import User
from app.models.facility import Facility
from app.models.staff_member import StaffMember
from app.models.notification_settings import NotificationSettings
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationCreate
from app.models.notification import NotificationType, NotificationPriority

logger = logging.getLogger(__name__)

class FacilityTaskNotificationService:
    """Service for automated facility task notification management."""
    
    @staticmethod
    async def check_and_send_task_reminders():
        """Check for upcoming tasks and send reminder notifications to facility administrators."""
        try:
            db = next(get_db())
            current_time = datetime.now()
            
            # Get all active task assignments that are due soon
            upcoming_assignments = db.query(TaskAssignment).join(OperationalTask).filter(
                TaskAssignment.status.in_([
                    TaskAssignmentStatus.ASSIGNED.value,
                    TaskAssignmentStatus.IN_PROGRESS.value
                ]),
                TaskAssignment.due_date > current_time,
                OperationalTask.is_active == True
            ).all()
            
            reminders_sent = 0
            
            for assignment in upcoming_assignments:
                try:
                    # Calculate days until due
                    days_until_due = (assignment.due_date - current_time).days
                    
                    # Get facility administrator
                    task = assignment.operational_task
                    facility = db.query(Facility).filter(Facility.id == task.facility_id).first()
                    if not facility:
                        continue
                    
                    admin_user = db.query(User).filter(User.id == facility.admin_user_id).first()
                    if not admin_user:
                        continue
                    
                    # Get user's notification preferences
                    settings = db.query(NotificationSettings).filter(
                        NotificationSettings.user_id == admin_user.id
                    ).first()
                    
                    if not settings or not settings.facility_task_reminders_enabled:
                        continue
                    
                    # Check if we should send a reminder based on user preferences
                    reminder_days = settings.facility_task_reminder_days or [7, 3, 1]
                    
                    if days_until_due in reminder_days:
                        success = await FacilityTaskNotificationService._send_task_reminder_notification(
                            db, assignment, admin_user, days_until_due
                        )
                        
                        if success:
                            reminders_sent += 1
                
                except Exception as e:
                    logger.error(f"Error processing task reminder {assignment.id}: {str(e)}")
                    continue
            
            logger.info(f"Sent {reminders_sent} task reminder notifications")
            db.close()
            
        except Exception as e:
            logger.error(f"Error in task reminder check: {str(e)}")
    
    @staticmethod
    async def check_and_send_overdue_task_notifications():
        """Check for overdue tasks and send escalation notifications to facility administrators."""
        try:
            db = next(get_db())
            current_time = datetime.now()
            
            # Get all overdue task assignments
            overdue_assignments = db.query(TaskAssignment).join(OperationalTask).filter(
                TaskAssignment.status.in_([
                    TaskAssignmentStatus.ASSIGNED.value,
                    TaskAssignmentStatus.IN_PROGRESS.value
                ]),
                TaskAssignment.due_date < current_time,
                OperationalTask.is_active == True
            ).all()
            
            overdue_notifications_sent = 0
            
            for assignment in overdue_assignments:
                try:
                    # Calculate days overdue
                    days_overdue = (current_time - assignment.due_date).days
                    
                    # Get facility administrator
                    task = assignment.operational_task
                    facility = db.query(Facility).filter(Facility.id == task.facility_id).first()
                    if not facility:
                        continue
                    
                    admin_user = db.query(User).filter(User.id == facility.admin_user_id).first()
                    if not admin_user:
                        continue
                    
                    # Get user's notification preferences
                    settings = db.query(NotificationSettings).filter(
                        NotificationSettings.user_id == admin_user.id
                    ).first()
                    
                    if not settings or not settings.task_overdue_notifications_enabled:
                        continue
                    
                    # Send overdue notification (limit to once per day to avoid spam)
                    if days_overdue == 1 or days_overdue % 7 == 0:  # Day 1, then weekly
                        success = await FacilityTaskNotificationService._send_overdue_task_notification(
                            db, assignment, admin_user, days_overdue
                        )
                        
                        if success:
                            overdue_notifications_sent += 1
                
                except Exception as e:
                    logger.error(f"Error processing overdue task {assignment.id}: {str(e)}")
                    continue
            
            logger.info(f"Sent {overdue_notifications_sent} overdue task notifications")
            db.close()
            
        except Exception as e:
            logger.error(f"Error in overdue task check: {str(e)}")
    
    @staticmethod
    async def _send_task_reminder_notification(
        db: Session,
        assignment: TaskAssignment,
        admin_user: User,
        days_until_due: int
    ) -> bool:
        """Send task reminder notification to facility administrator."""
        try:
            task = assignment.operational_task
            staff_member = db.query(StaffMember).filter(StaffMember.id == assignment.staff_member_id).first()
            
            # Determine priority based on urgency
            if days_until_due <= 1:
                priority = NotificationPriority.HIGH
                urgency_text = "due tomorrow" if days_until_due == 1 else "due today"
            elif days_until_due <= 3:
                priority = NotificationPriority.MEDIUM
                urgency_text = f"due in {days_until_due} days"
            else:
                priority = NotificationPriority.LOW
                urgency_text = f"due in {days_until_due} days"
            
            # Create notification message
            staff_name = f"{staff_member.first_name} {staff_member.last_name}" if staff_member else "Staff member"
            message = f"Task '{task.title}' assigned to {staff_name} is {urgency_text}"
            
            notification_data = NotificationCreate(
                title="Task Due Reminder",
                message=message,
                type=NotificationType.TASK_DUE,
                priority=priority,
                related_id=str(assignment.id),
                related_type="task_assignment",
                action_url=f"/tasks/assignments/{assignment.id}"
            )
            
            await NotificationService.create_notification(
                db, notification_data, admin_user.id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending task reminder notification: {str(e)}")
            return False
    
    @staticmethod
    async def _send_overdue_task_notification(
        db: Session,
        assignment: TaskAssignment,
        admin_user: User,
        days_overdue: int
    ) -> bool:
        """Send overdue task notification to facility administrator."""
        try:
            task = assignment.operational_task
            staff_member = db.query(StaffMember).filter(StaffMember.id == assignment.staff_member_id).first()
            
            # Create notification message
            staff_name = f"{staff_member.first_name} {staff_member.last_name}" if staff_member else "Staff member"
            message = f"Task '{task.title}' assigned to {staff_name} is {days_overdue} day{'s' if days_overdue != 1 else ''} overdue"
            
            notification_data = NotificationCreate(
                title="Task Overdue",
                message=message,
                type=NotificationType.TASK_OVERDUE,
                priority=NotificationPriority.HIGH,
                related_id=str(assignment.id),
                related_type="task_assignment",
                action_url=f"/tasks/assignments/{assignment.id}"
            )
            
            await NotificationService.create_notification(
                db, notification_data, admin_user.id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending overdue task notification: {str(e)}")
            return False
    
    @staticmethod
    async def send_task_assignment_notification(
        db: Session,
        assignment: TaskAssignment,
        admin_user: User
    ) -> bool:
        """Send notification when a new task is assigned."""
        try:
            task = assignment.operational_task
            staff_member = db.query(StaffMember).filter(StaffMember.id == assignment.staff_member_id).first()
            
            staff_name = f"{staff_member.first_name} {staff_member.last_name}" if staff_member else "Staff member"
            due_date_str = assignment.due_date.strftime('%B %d, %Y') if assignment.due_date else "No due date"
            
            notification_data = NotificationCreate(
                title="Task Assigned",
                message=f"Task '{task.title}' assigned to {staff_name}. Due: {due_date_str}",
                type=NotificationType.TASK_ASSIGNED,
                priority=NotificationPriority.MEDIUM,
                related_id=str(assignment.id),
                related_type="task_assignment",
                action_url=f"/tasks/assignments/{assignment.id}"
            )
            
            await NotificationService.create_notification(
                db, notification_data, admin_user.id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending task assignment notification: {str(e)}")
            return False
    
    @staticmethod
    async def send_task_completion_notification(
        db: Session,
        assignment: TaskAssignment,
        admin_user: User
    ) -> bool:
        """Send notification when a task is completed."""
        try:
            task = assignment.operational_task
            staff_member = db.query(StaffMember).filter(StaffMember.id == assignment.staff_member_id).first()
            
            staff_name = f"{staff_member.first_name} {staff_member.last_name}" if staff_member else "Staff member"
            
            notification_data = NotificationCreate(
                title="Task Completed",
                message=f"Task '{task.title}' completed by {staff_name}",
                type=NotificationType.TASK_COMPLETED,
                priority=NotificationPriority.LOW,
                related_id=str(assignment.id),
                related_type="task_assignment",
                action_url=f"/tasks/assignments/{assignment.id}"
            )
            
            await NotificationService.create_notification(
                db, notification_data, admin_user.id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending task completion notification: {str(e)}")
            return False
    
    @staticmethod
    async def generate_daily_facility_digest(
        db: Session,
        facility_id: int
    ) -> Dict[str, Any]:
        """Generate daily digest of facility tasks and notifications."""
        try:
            current_time = datetime.now()
            tomorrow = current_time + timedelta(days=1)
            
            # Get facility information
            facility = db.query(Facility).filter(Facility.id == facility_id).first()
            if not facility:
                return {}
            
            admin_user = db.query(User).filter(User.id == facility.admin_user_id).first()
            if not admin_user:
                return {}
            
            # Get tasks due tomorrow
            tasks_due_tomorrow = db.query(TaskAssignment).join(OperationalTask).filter(
                OperationalTask.facility_id == facility_id,
                TaskAssignment.due_date.between(tomorrow.replace(hour=0, minute=0, second=0),
                                               tomorrow.replace(hour=23, minute=59, second=59)),
                TaskAssignment.status.in_([
                    TaskAssignmentStatus.ASSIGNED.value,
                    TaskAssignmentStatus.IN_PROGRESS.value
                ])
            ).count()
            
            # Get overdue tasks
            overdue_tasks = db.query(TaskAssignment).join(OperationalTask).filter(
                OperationalTask.facility_id == facility_id,
                TaskAssignment.due_date < current_time,
                TaskAssignment.status.in_([
                    TaskAssignmentStatus.ASSIGNED.value,
                    TaskAssignmentStatus.IN_PROGRESS.value
                ])
            ).count()
            
            # Get completed tasks today
            today_start = current_time.replace(hour=0, minute=0, second=0)
            completed_today = db.query(TaskAssignment).join(OperationalTask).filter(
                OperationalTask.facility_id == facility_id,
                TaskAssignment.status == TaskAssignmentStatus.COMPLETED.value,
                TaskAssignment.updated_at >= today_start
            ).count()
            
            # Check if we should send digest
            settings = db.query(NotificationSettings).filter(
                NotificationSettings.user_id == admin_user.id
            ).first()
            
            if not settings or not settings.facility_daily_digest_enabled:
                return {}
            
            # Create digest notification if there's activity
            if tasks_due_tomorrow > 0 or overdue_tasks > 0 or completed_today > 0:
                digest_message = f"Daily Facility Digest:\n"
                if tasks_due_tomorrow > 0:
                    digest_message += f"• {tasks_due_tomorrow} task{'s' if tasks_due_tomorrow != 1 else ''} due tomorrow\n"
                if overdue_tasks > 0:
                    digest_message += f"• {overdue_tasks} overdue task{'s' if overdue_tasks != 1 else ''}\n"
                if completed_today > 0:
                    digest_message += f"• {completed_today} task{'s' if completed_today != 1 else ''} completed today"
                
                notification_data = NotificationCreate(
                    title="Daily Facility Digest",
                    message=digest_message,
                    type=NotificationType.FACILITY_DIGEST,
                    priority=NotificationPriority.LOW,
                    related_id=str(facility_id),
                    related_type="facility",
                    action_url="/tasks"
                )
                
                await NotificationService.create_notification(
                    db, notification_data, admin_user.id
                )
                
                return {
                    "facility_id": facility_id,
                    "tasks_due_tomorrow": tasks_due_tomorrow,
                    "overdue_tasks": overdue_tasks,
                    "completed_today": completed_today,
                    "digest_sent": True
                }
            
            return {
                "facility_id": facility_id,
                "tasks_due_tomorrow": tasks_due_tomorrow,
                "overdue_tasks": overdue_tasks,
                "completed_today": completed_today,
                "digest_sent": False
            }
            
        except Exception as e:
            logger.error(f"Error generating daily facility digest: {str(e)}")
            return {} 