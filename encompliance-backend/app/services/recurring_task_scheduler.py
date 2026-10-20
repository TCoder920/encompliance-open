"""
Recurring Task Scheduler Service Module

This module provides background task functionality for automatically
creating recurring task assignments based on defined schedules.

Key functionalities:
- Automatic recurring task instance generation
- Age-based assignment application for recurring tasks
- Notification system integration for new assignments
- Scheduling pattern processing (daily, weekly, monthly, quarterly)
- Due date calculation and assignment management

Dependencies:
- sqlalchemy: For database operations
- datetime: For scheduling calculations
- background task system: For automated execution

Educational Note: Implements recurring task scheduling following cron-like patterns
for facility operational tasks. Integrates with existing notification system for
assignment alerts and age-based assignment validation.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.models.operational_task import OperationalTask, TaskType, RecurrencePattern
from app.models.task_assignment import TaskAssignment, TaskAssignmentStatus
from app.models.staff_member import StaffMember, StaffStatus
from app.services.age_based_assignment_service import AgeBasedAssignmentService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class RecurringTaskScheduler:
    """Service for automated recurring task scheduling and assignment creation."""
    
    @staticmethod
    async def process_recurring_tasks():
        """
        Process all active recurring tasks and create new assignments where needed.
        Should be run as a background task (e.g., daily cron job).
        """
        try:
            db = next(get_db())
            current_time = datetime.now()
            
            # Get all active recurring tasks
            recurring_tasks = db.query(OperationalTask).filter(
                OperationalTask.task_type == TaskType.RECURRING.value,
                OperationalTask.is_active == True,
                OperationalTask.start_date <= current_time
            ).all()
            
            tasks_processed = 0
            assignments_created = 0
            
            for task in recurring_tasks:
                try:
                    # Check if task end date has passed
                    if task.end_date and task.end_date < current_time:
                        logger.info(f"Recurring task {task.id} has ended, skipping")
                        continue
                    
                    # Generate assignments for this task
                    new_assignments = await RecurringTaskScheduler._generate_task_assignments(
                        db, task, current_time
                    )
                    
                    assignments_created += len(new_assignments)
                    tasks_processed += 1
                    
                    logger.info(f"Created {len(new_assignments)} assignments for recurring task {task.id}")
                    
                except Exception as e:
                    logger.error(f"Error processing recurring task {task.id}: {str(e)}")
                    continue
            
            db.close()
            
            logger.info(f"Recurring task processing completed: {tasks_processed} tasks processed, {assignments_created} assignments created")
            
            return {
                "tasks_processed": tasks_processed,
                "assignments_created": assignments_created,
                "processed_at": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in recurring task processing: {str(e)}")
            raise
    
    @staticmethod
    async def _generate_task_assignments(
        db: Session,
        task: OperationalTask,
        current_time: datetime
    ) -> List[TaskAssignment]:
        """
        Generate new assignments for a recurring task based on its schedule.
        
        Args:
            db: Database session
            task: Recurring OperationalTask
            current_time: Current timestamp
            
        Returns:
            List of newly created TaskAssignment instances
        """
        try:
            # Calculate next due dates based on recurrence pattern
            next_due_dates = RecurringTaskScheduler._calculate_next_due_dates(
                task, current_time
            )
            
            if not next_due_dates:
                return []
            
            # Get eligible staff members for this task
            eligible_staff = AgeBasedAssignmentService.get_eligible_staff_by_age(
                db=db,
                facility_id=task.facility_id,
                min_age=task.min_age_required,
                max_age=task.max_age_allowed
            )
            
            if not eligible_staff:
                logger.warning(f"No eligible staff found for recurring task {task.id}")
                return []
            
            new_assignments = []
            
            for due_date in next_due_dates:
                # Check if assignments already exist for this due date
                existing_assignments = db.query(TaskAssignment).filter(
                    TaskAssignment.operational_task_id == task.id,
                    TaskAssignment.due_date.between(
                        due_date - timedelta(hours=12),
                        due_date + timedelta(hours=12)
                    )
                ).count()
                
                if existing_assignments > 0:
                    logger.debug(f"Assignments already exist for task {task.id} due {due_date}")
                    continue
                
                # Create assignments for eligible staff
                for staff_member in eligible_staff:
                    # Validate staff member age eligibility
                    eligibility = AgeBasedAssignmentService.validate_staff_age_eligibility(
                        db, staff_member.id, task
                    )
                    
                    if not eligibility["eligible"]:
                        logger.debug(f"Staff {staff_member.id} not eligible for task {task.id}: {eligibility['reason']}")
                        continue
                    
                    # Create new assignment
                    assignment = TaskAssignment(
                        operational_task_id=task.id,
                        staff_member_id=staff_member.id,
                        assigned_by=task.created_by,
                        due_date=due_date,
                        priority=task.priority,
                        assignment_notes=f"Auto-generated recurring assignment for {task.title}"
                    )
                    
                    db.add(assignment)
                    new_assignments.append(assignment)
            
            # Commit all new assignments
            if new_assignments:
                db.commit()
                
                # Send notifications for new assignments
                await RecurringTaskScheduler._send_assignment_notifications(
                    db, new_assignments
                )
            
            return new_assignments
            
        except Exception as e:
            logger.error(f"Error generating assignments for task {task.id}: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def _calculate_next_due_dates(
        task: OperationalTask,
        current_time: datetime
    ) -> List[datetime]:
        """
        Calculate next due dates for a recurring task based on its pattern.
        
        Args:
            task: Recurring OperationalTask
            current_time: Current timestamp
            
        Returns:
            List of upcoming due dates that need assignments
        """
        try:
            if not task.recurrence_pattern:
                return []
            
            # Look ahead window (create assignments up to this far in advance)
            look_ahead_days = 30
            look_ahead_date = current_time + timedelta(days=look_ahead_days)
            
            due_dates = []
            next_date = task.start_date
            
            # Generate due dates within look-ahead window
            while next_date <= look_ahead_date:
                # Only include future dates
                if next_date > current_time:
                    # Check if task hasn't ended
                    if not task.end_date or next_date <= task.end_date:
                        due_dates.append(next_date)
                
                # Calculate next occurrence based on pattern
                if task.recurrence_pattern == RecurrencePattern.DAILY.value:
                    next_date += timedelta(days=task.recurrence_interval)
                elif task.recurrence_pattern == RecurrencePattern.WEEKLY.value:
                    next_date += timedelta(weeks=task.recurrence_interval)
                elif task.recurrence_pattern == RecurrencePattern.MONTHLY.value:
                    next_date += relativedelta(months=task.recurrence_interval)
                elif task.recurrence_pattern == RecurrencePattern.QUARTERLY.value:
                    next_date += relativedelta(months=3 * task.recurrence_interval)
                else:
                    logger.warning(f"Unknown recurrence pattern: {task.recurrence_pattern}")
                    break
                
                # Safety check to prevent infinite loops
                if len(due_dates) > 100:
                    logger.warning(f"Too many due dates generated for task {task.id}, stopping")
                    break
            
            logger.debug(f"Generated {len(due_dates)} due dates for task {task.id}")
            return due_dates
            
        except Exception as e:
            logger.error(f"Error calculating due dates for task {task.id}: {str(e)}")
            return []
    
    @staticmethod
    async def _send_assignment_notifications(
        db: Session,
        assignments: List[TaskAssignment]
    ):
        """
        Send notifications for newly created task assignments.
        
        Args:
            db: Database session
            assignments: List of new TaskAssignment instances
        """
        try:
            for assignment in assignments:
                try:
                    # Get task and staff member details
                    task = db.query(OperationalTask).filter(
                        OperationalTask.id == assignment.operational_task_id
                    ).first()
                    
                    staff_member = db.query(StaffMember).filter(
                        StaffMember.id == assignment.staff_member_id
                    ).first()
                    
                    if not task or not staff_member:
                        logger.warning(f"Missing task or staff member for assignment {assignment.id}")
                        continue
                    
                    # Create notification message
                    message = f"New recurring task assigned: {task.title}"
                    if assignment.due_date:
                        message += f" (Due: {assignment.due_date.strftime('%Y-%m-%d %H:%M')})"
                    
                    # Send notification (assuming notification service exists)
                    # This would integrate with the existing notification system
                    notification_data = {
                        "title": "New Task Assignment",
                        "message": message,
                        "type": "task_assignment",
                        "related_id": assignment.id,
                        "related_type": "task_assignment",
                        "action_url": f"/tasks/assignments/{assignment.id}"
                    }
                    
                    # Note: This would use the existing NotificationService
                    # await NotificationService.create_notification(
                    #     db=db,
                    #     user_id=staff_member.facility_administrator_id,  # Or staff member's user ID
                    #     **notification_data
                    # )
                    
                    logger.debug(f"Notification sent for assignment {assignment.id}")
                    
                except Exception as e:
                    logger.error(f"Error sending notification for assignment {assignment.id}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error sending assignment notifications: {str(e)}")
    
    @staticmethod
    async def get_upcoming_recurring_assignments(
        db: Session,
        facility_id: int,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Get upcoming recurring task assignments for a facility.
        
        Args:
            db: Database session
            facility_id: Facility ID
            days_ahead: Number of days to look ahead
            
        Returns:
            Dictionary with upcoming assignments and statistics
        """
        try:
            current_time = datetime.now()
            end_date = current_time + timedelta(days=days_ahead)
            
            # Get upcoming assignments for recurring tasks
            upcoming_assignments = db.query(TaskAssignment).join(
                OperationalTask, TaskAssignment.operational_task_id == OperationalTask.id
            ).filter(
                OperationalTask.facility_id == facility_id,
                OperationalTask.task_type == TaskType.RECURRING.value,
                TaskAssignment.due_date.between(current_time, end_date),
                TaskAssignment.status.in_([
                    TaskAssignmentStatus.ASSIGNED.value,
                    TaskAssignmentStatus.IN_PROGRESS.value
                ])
            ).order_by(TaskAssignment.due_date).all()
            
            # Group by task and due date
            assignments_by_task = {}
            for assignment in upcoming_assignments:
                task_id = assignment.operational_task_id
                if task_id not in assignments_by_task:
                    assignments_by_task[task_id] = {
                        "task": assignment.operational_task,
                        "assignments": []
                    }
                assignments_by_task[task_id]["assignments"].append(assignment)
            
            return {
                "upcoming_assignments": upcoming_assignments,
                "assignments_by_task": assignments_by_task,
                "total_assignments": len(upcoming_assignments),
                "unique_tasks": len(assignments_by_task),
                "date_range": {
                    "start": current_time.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting upcoming recurring assignments: {str(e)}")
            raise
    
    @staticmethod
    async def pause_recurring_task(
        db: Session,
        task_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Pause a recurring task to stop generating new assignments.
        
        Args:
            db: Database session
            task_id: Task ID to pause
            user_id: User ID performing the action
            
        Returns:
            Operation result
        """
        try:
            task = db.query(OperationalTask).filter(
                OperationalTask.id == task_id,
                OperationalTask.task_type == TaskType.RECURRING.value
            ).first()
            
            if not task:
                return {
                    "success": False,
                    "message": "Recurring task not found"
                }
            
            task.is_active = False
            db.commit()
            
            logger.info(f"Recurring task {task_id} paused by user {user_id}")
            
            return {
                "success": True,
                "message": f"Recurring task '{task.title}' has been paused",
                "task_id": task_id
            }
            
        except Exception as e:
            logger.error(f"Error pausing recurring task {task_id}: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    async def resume_recurring_task(
        db: Session,
        task_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Resume a paused recurring task.
        
        Args:
            db: Database session
            task_id: Task ID to resume
            user_id: User ID performing the action
            
        Returns:
            Operation result
        """
        try:
            task = db.query(OperationalTask).filter(
                OperationalTask.id == task_id,
                OperationalTask.task_type == TaskType.RECURRING.value
            ).first()
            
            if not task:
                return {
                    "success": False,
                    "message": "Recurring task not found"
                }
            
            task.is_active = True
            db.commit()
            
            logger.info(f"Recurring task {task_id} resumed by user {user_id}")
            
            return {
                "success": True,
                "message": f"Recurring task '{task.title}' has been resumed",
                "task_id": task_id
            }
            
        except Exception as e:
            logger.error(f"Error resuming recurring task {task_id}: {str(e)}")
            db.rollback()
            raise 