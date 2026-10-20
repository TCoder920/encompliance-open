
"""
Task Calendar Integration Service

This service handles the integration between operational tasks and calendar events.
It automatically creates, updates, and manages calendar events when tasks are created or assigned.

Key functionalities:
- Create calendar events when operational tasks are created
- Create individual calendar events for task assignments
- Update calendar events when task assignments change
- Clean up calendar events when tasks are deleted
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.operational_task import OperationalTask, TaskType, RecurrencePattern
from app.models.task_assignment import TaskAssignment
from app.models.calendar_event import CalendarEvent
from app.models.staff_member import StaffMember
from app.models.user import User
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class TaskCalendarIntegrationService:
    """Service for integrating operational tasks with calendar events."""
    
    @staticmethod
    async def create_task_calendar_event(
        db: Session,
        task: OperationalTask,
        created_by_user: User
    ) -> Optional[CalendarEvent]:
        """
        Create a calendar event for a newly created operational task.
        This creates a general task event for the facility administrator.
        """
        try:
            # Create calendar event for the task
            event_id = str(uuid.uuid4())
            
            # Calculate event end time (start_date + estimated_duration)
            start_time = task.start_date
            if task.estimated_duration_minutes:
                end_time = start_time + timedelta(minutes=task.estimated_duration_minutes)
            else:
                # Default to 1 hour if no duration specified
                end_time = start_time + timedelta(hours=1)
            
            # Create description with task details
            description = f"Operational Task: {task.title}"
            if task.description:
                description += f"\n\nDescription: {task.description}"
            if task.category:
                description += f"\nCategory: {task.category}"
            if task.priority:
                description += f"\nPriority: {task.priority.title()}"
            if task.special_instructions:
                description += f"\n\nSpecial Instructions: {task.special_instructions}"
            if task.required_equipment:
                equipment_list = ", ".join(task.required_equipment)
                description += f"\nRequired Equipment: {equipment_list}"
            
            calendar_event = CalendarEvent(
                id=event_id,
                user_id=created_by_user.id,
                title=f"Task: {task.title}",
                start=start_time.isoformat(),
                end=end_time.isoformat(),
                description=description,
                location=task.location,
                all_day=False,
                facility_id=task.facility_id,
                created_by_admin=True,
                is_editable_by_user=False,  # Admin-only event
                operational_task_id=task.id,
                event_type='task'
            )
            
            db.add(calendar_event)
            db.commit()
            db.refresh(calendar_event)
            
            logger.info(f"Created calendar event {event_id} for task {task.id}")
            return calendar_event
            
        except Exception as e:
            logger.error(f"Error creating calendar event for task {task.id}: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    async def create_recurring_task_calendar_events(
        db: Session,
        task: OperationalTask,
        created_by_user: User
    ) -> List[CalendarEvent]:
        """
        Create multiple calendar events for a recurring task based on its recurrence pattern.
        This creates calendar events for each occurrence of the recurring task.
        """
        try:
            if task.task_type != TaskType.RECURRING.value or not task.recurrence_pattern:
                logger.warning(f"Task {task.id} is not a recurring task or missing recurrence pattern")
                return []
            
            created_events = []
            
            # Calculate recurring dates - use task end date if provided, otherwise 36 months default
            if task.end_date:
                # Use the user-specified end date
                end_date = task.end_date
                logger.info(f"Using user-specified end date for task {task.id}: {end_date}")
            else:
                # Default to 36 months when no end date is specified
                default_look_ahead_months = 36
                end_date = datetime.now() + relativedelta(months=default_look_ahead_months)
                logger.info(f"No end date specified for task {task.id}, using 36-month default: {end_date}")
            
            current_date = task.start_date
            occurrence_count = 0
            max_occurrences = 100  # Safety limit
            
            while current_date <= end_date and occurrence_count < max_occurrences:
                # Check if a calendar event already exists for this date
                existing_event = db.query(CalendarEvent).filter(
                    CalendarEvent.operational_task_id == task.id,
                    CalendarEvent.event_type == 'task',
                    CalendarEvent.start >= current_date.isoformat(),
                    CalendarEvent.start < (current_date + timedelta(days=1)).isoformat()
                ).first()
                
                if existing_event:
                    logger.debug(f"Calendar event already exists for task {task.id} on {current_date.date()}")
                    # Calculate next occurrence and continue
                    if task.recurrence_pattern == RecurrencePattern.DAILY.value:
                        current_date += timedelta(days=task.recurrence_interval)
                    elif task.recurrence_pattern == RecurrencePattern.WEEKLY.value:
                        current_date += timedelta(weeks=task.recurrence_interval)
                    elif task.recurrence_pattern == RecurrencePattern.MONTHLY.value:
                        current_date += relativedelta(months=task.recurrence_interval)
                    elif task.recurrence_pattern == RecurrencePattern.QUARTERLY.value:
                        current_date += relativedelta(months=3 * task.recurrence_interval)
                    occurrence_count += 1
                    continue
                
                # Create calendar event for this occurrence
                event_id = str(uuid.uuid4())
                
                # Calculate event end time (start_date + estimated_duration)
                start_time = current_date
                if task.estimated_duration_minutes:
                    end_time = start_time + timedelta(minutes=task.estimated_duration_minutes)
                else:
                    # Default to 1 hour if no duration specified
                    end_time = start_time + timedelta(hours=1)
                
                # Create description with task details and occurrence info
                description = f"Recurring Task: {task.title}"
                description += f"\nOccurrence: {occurrence_count + 1}"
                description += f"\nRecurrence: {task.recurrence_pattern.title()} (every {task.recurrence_interval})"
                
                if task.description:
                    description += f"\n\nDescription: {task.description}"
                if task.category:
                    description += f"\nCategory: {task.category}"
                if task.priority:
                    description += f"\nPriority: {task.priority.title()}"
                if task.special_instructions:
                    description += f"\n\nSpecial Instructions: {task.special_instructions}"
                if task.required_equipment:
                    equipment_list = ", ".join(task.required_equipment)
                    description += f"\nRequired Equipment: {equipment_list}"
                
                calendar_event = CalendarEvent(
                    id=event_id,
                    user_id=created_by_user.id,
                    title=f"Recurring Task: {task.title}",
                    start=start_time.isoformat(),
                    end=end_time.isoformat(),
                    description=description,
                    location=task.location,
                    all_day=False,
                    facility_id=task.facility_id,
                    created_by_admin=True,
                    is_editable_by_user=False,  # Admin-only event
                    operational_task_id=task.id,
                    event_type='task'
                )
                
                db.add(calendar_event)
                created_events.append(calendar_event)
                
                # Calculate next occurrence based on recurrence pattern
                if task.recurrence_pattern == RecurrencePattern.DAILY.value:
                    current_date += timedelta(days=task.recurrence_interval)
                elif task.recurrence_pattern == RecurrencePattern.WEEKLY.value:
                    current_date += timedelta(weeks=task.recurrence_interval)
                elif task.recurrence_pattern == RecurrencePattern.MONTHLY.value:
                    current_date += relativedelta(months=task.recurrence_interval)
                elif task.recurrence_pattern == RecurrencePattern.QUARTERLY.value:
                    current_date += relativedelta(months=3 * task.recurrence_interval)
                else:
                    logger.warning(f"Unknown recurrence pattern: {task.recurrence_pattern}")
                    break
                
                occurrence_count += 1
            
            # Commit all events
            db.commit()
            
            for event in created_events:
                db.refresh(event)
            
            logger.info(f"Created {len(created_events)} recurring calendar events for task {task.id}")
            return created_events
            
        except Exception as e:
            logger.error(f"Error creating recurring calendar events for task {task.id}: {str(e)}")
            db.rollback()
            return []
    
    @staticmethod
    async def create_assignment_calendar_events(
        db: Session,
        assignments: List[TaskAssignment],
        task: OperationalTask,
        assigned_by_user: User
    ) -> List[CalendarEvent]:
        """
        Create calendar events for task assignments.
        This creates individual calendar events for each assigned staff member.
        """
        created_events = []
        
        try:
            for assignment in assignments:
                # Get staff member details
                staff_member = db.query(StaffMember).filter(
                    StaffMember.id == assignment.staff_member_id
                ).first()
                
                if not staff_member:
                    logger.warning(f"Staff member {assignment.staff_member_id} not found for assignment {assignment.id}")
                    continue
                
                # Get the user associated with the staff member
                staff_user = db.query(User).filter(
                    User.id == staff_member.user_id
                ).first() if hasattr(staff_member, 'user_id') and staff_member.user_id else None
                
                # If no user associated, create event for facility admin to track
                target_user_id = staff_user.id if staff_user else assigned_by_user.id
                
                # Create calendar event for the assignment
                event_id = str(uuid.uuid4())
                
                # Calculate event times based on due date and estimated duration
                due_date = assignment.due_date
                if task.estimated_duration_minutes:
                    start_time = due_date - timedelta(minutes=task.estimated_duration_minutes)
                    end_time = due_date
                else:
                    # Default to 1 hour before due date
                    start_time = due_date - timedelta(hours=1)
                    end_time = due_date
                
                # Create description with assignment details
                description = f"Task Assignment: {task.title}"
                description += f"\nAssigned to: {staff_member.first_name} {staff_member.last_name}"
                description += f"\nDue: {due_date.strftime('%Y-%m-%d %H:%M')}"
                description += f"\nPriority: {assignment.priority.title()}"
                
                if task.description:
                    description += f"\n\nTask Description: {task.description}"
                if assignment.assignment_notes:
                    description += f"\n\nAssignment Notes: {assignment.assignment_notes}"
                if task.special_instructions:
                    description += f"\n\nSpecial Instructions: {task.special_instructions}"
                if task.required_equipment:
                    equipment_list = ", ".join(task.required_equipment)
                    description += f"\nRequired Equipment: {equipment_list}"
                
                calendar_event = CalendarEvent(
                    id=event_id,
                    user_id=target_user_id,
                    title=f"Assignment: {task.title}",
                    start=start_time.isoformat(),
                    end=end_time.isoformat(),
                    description=description,
                    location=task.location,
                    all_day=False,
                    facility_id=task.facility_id,
                    created_by_admin=True,
                    is_editable_by_user=False,  # Admin-only event
                    operational_task_id=task.id,
                    task_assignment_id=assignment.id,
                    event_type='assignment'
                )
                
                db.add(calendar_event)
                created_events.append(calendar_event)
                
                # Create notification for the assignment
                try:
                    await NotificationService.create_calendar_notification(
                        db=db,
                        user_id=target_user_id,
                        event_id=event_id,
                        action="created",
                        event_title=f"Assignment: {task.title}"
                    )
                except Exception as e:
                    logger.error(f"Error creating notification for assignment {assignment.id}: {str(e)}")
            
            db.commit()
            
            for event in created_events:
                db.refresh(event)
            
            logger.info(f"Created {len(created_events)} calendar events for task assignments")
            return created_events
            
        except Exception as e:
            logger.error(f"Error creating calendar events for assignments: {str(e)}")
            db.rollback()
            return []
    
    @staticmethod
    async def update_assignment_calendar_event(
        db: Session,
        assignment: TaskAssignment,
        task: OperationalTask
    ) -> Optional[CalendarEvent]:
        """
        Update calendar event when a task assignment is updated.
        """
        try:
            # Find existing calendar event for this assignment
            calendar_event = db.query(CalendarEvent).filter(
                CalendarEvent.task_assignment_id == assignment.id
            ).first()
            
            if not calendar_event:
                # Create new event if none exists
                return await TaskCalendarIntegrationService.create_assignment_calendar_events(
                    db, [assignment], task, 
                    db.query(User).filter(User.id == task.created_by).first()
                )
            
            # Update existing event
            due_date = assignment.due_date
            if task.estimated_duration_minutes:
                start_time = due_date - timedelta(minutes=task.estimated_duration_minutes)
                end_time = due_date
            else:
                start_time = due_date - timedelta(hours=1)
                end_time = due_date
            
            calendar_event.start = start_time.isoformat()
            calendar_event.end = end_time.isoformat()
            calendar_event.title = f"Assignment: {task.title} ({assignment.status.title()})"
            
            # Update description with current status
            description = f"Task Assignment: {task.title}"
            description += f"\nAssigned to: {assignment.staff_member.first_name} {assignment.staff_member.last_name}"
            description += f"\nStatus: {assignment.status.title()}"
            description += f"\nDue: {due_date.strftime('%Y-%m-%d %H:%M')}"
            description += f"\nPriority: {assignment.priority.title()}"
            description += f"\nProgress: {assignment.progress_percentage}%"
            
            if assignment.time_spent_minutes > 0:
                description += f"\nTime Spent: {assignment.time_spent_minutes} minutes"
            
            calendar_event.description = description
            
            db.commit()
            db.refresh(calendar_event)
            
            logger.info(f"Updated calendar event for assignment {assignment.id}")
            return calendar_event
            
        except Exception as e:
            logger.error(f"Error updating calendar event for assignment {assignment.id}: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    async def delete_task_calendar_events(
        db: Session,
        task_id: int,
        facility_id: int
    ) -> bool:
        """
        Delete all calendar events related to a task when the task is deleted.
        """
        try:
            # Find all calendar events related to this task using the operational_task_id
            calendar_events = db.query(CalendarEvent).filter(
                CalendarEvent.operational_task_id == task_id
            ).all()
            
            deleted_count = len(calendar_events)
            
            # Delete all events related to this task
            for event in calendar_events:
                db.delete(event)
            
            db.commit()
            logger.info(f"Deleted {deleted_count} calendar events for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting calendar events for task {task_id}: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    async def delete_assignment_calendar_event(
        db: Session,
        assignment_id: int
    ) -> bool:
        """
        Delete calendar event when a task assignment is deleted.
        """
        try:
            # Find calendar event for this assignment
            calendar_event = db.query(CalendarEvent).filter(
                CalendarEvent.task_assignment_id == assignment_id
            ).first()
            
            if calendar_event:
                db.delete(calendar_event)
                db.commit()
                logger.info(f"Deleted calendar event for assignment {assignment_id}")
                return True
            else:
                logger.info(f"No calendar event found for assignment {assignment_id}")
                return True
            
        except Exception as e:
            logger.error(f"Error deleting calendar event for assignment {assignment_id}: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    async def update_task_calendar_event(
        db: Session,
        task: OperationalTask
    ) -> Optional[CalendarEvent]:
        """
        Update calendar event when an operational task is updated.
        """
        try:
            # Find existing calendar event for this task
            calendar_event = db.query(CalendarEvent).filter(
                CalendarEvent.operational_task_id == task.id,
                CalendarEvent.event_type == 'task'
            ).first()
            
            if not calendar_event:
                logger.info(f"No calendar event found for task {task.id}")
                return None
            
            # Calculate event end time (start_date + estimated_duration)
            start_time = task.start_date
            if task.estimated_duration_minutes:
                end_time = start_time + timedelta(minutes=task.estimated_duration_minutes)
            else:
                # Default to 1 hour if no duration specified
                end_time = start_time + timedelta(hours=1)
            
            # Update event details
            calendar_event.title = f"Task: {task.title}"
            calendar_event.start = start_time.isoformat()
            calendar_event.end = end_time.isoformat()
            calendar_event.location = task.location
            
            # Update description with task details
            description = f"Operational Task: {task.title}"
            if task.description:
                description += f"\n\nDescription: {task.description}"
            if task.category:
                description += f"\nCategory: {task.category}"
            if task.priority:
                description += f"\nPriority: {task.priority.title()}"
            if task.special_instructions:
                description += f"\n\nSpecial Instructions: {task.special_instructions}"
            if task.required_equipment:
                equipment_list = ", ".join(task.required_equipment)
                description += f"\nRequired Equipment: {equipment_list}"
            
            calendar_event.description = description
            
            db.commit()
            db.refresh(calendar_event)
            
            logger.info(f"Updated calendar event for task {task.id}")
            return calendar_event
            
        except Exception as e:
            logger.error(f"Error updating calendar event for task {task.id}: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    async def update_recurring_task_calendar_events(
        db: Session,
        task: OperationalTask,
        updated_by_user: User
    ) -> List[CalendarEvent]:
        """
        Update recurring calendar events when a recurring task is modified.
        This deletes existing events and creates new ones based on the updated recurrence pattern.
        """
        try:
            if task.task_type != TaskType.RECURRING.value:
                logger.warning(f"Task {task.id} is not a recurring task")
                return []
            
            # Delete existing calendar events for this task
            existing_events = db.query(CalendarEvent).filter(
                CalendarEvent.operational_task_id == task.id,
                CalendarEvent.event_type == 'task'
            ).all()
            
            for event in existing_events:
                db.delete(event)
            
            db.commit()
            logger.info(f"Deleted {len(existing_events)} existing calendar events for recurring task {task.id}")
            
            # Create new recurring calendar events with updated settings
            new_events = await TaskCalendarIntegrationService.create_recurring_task_calendar_events(
                db=db,
                task=task,
                created_by_user=updated_by_user
            )
            
            logger.info(f"Updated recurring calendar events for task {task.id}: {len(new_events)} new events created")
            return new_events
            
        except Exception as e:
            logger.error(f"Error updating recurring calendar events for task {task.id}: {str(e)}")
            db.rollback()
            return [] 