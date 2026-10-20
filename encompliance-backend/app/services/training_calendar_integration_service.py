"""
Training Calendar Integration Service

Purpose: Handles automatic calendar event creation for training programs, assignments, 
and certification renewals. Mirrors task calendar integration patterns.
Description: Manages lifecycle of training-related calendar events including creation,
updates, and cleanup. Integrates with existing calendar infrastructure.

Key functionalities:
- Create calendar events when training assignments are created
- Update calendar events when assignment details change
- Create certification renewal reminders
- Clean up calendar events when assignments are deleted

Educational Note: Service pattern following FastAPI dependency injection
Reference: FastAPI docs on dependency injection patterns

Dependencies:
- sqlalchemy: For database operations
- datetime: For timestamp handling
- models: For training and calendar models
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.training_assignment import TrainingAssignment
from app.models.training_program import TrainingProgram
from app.models.training_completion import TrainingCompletion
from app.models.calendar_event import CalendarEvent
from app.models.staff_member import StaffMember
from app.models.user import User
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class TrainingCalendarIntegrationService:
    """Service for integrating training assignments with calendar events."""
    
    @staticmethod
    async def create_training_assignment_calendar_event(
        db: Session,
        assignment: TrainingAssignment,
        training_program: TrainingProgram,
        assigned_by_user: User
    ) -> Optional[CalendarEvent]:
        """
        Create a calendar event for a training assignment.
        Creates an event with the assignment due date and training details.
        """
        try:
            # Get staff member details
            staff_member = db.query(StaffMember).filter(
                StaffMember.id == assignment.staff_member_id
            ).first()
            
            if not staff_member:
                logger.warning(f"Staff member {assignment.staff_member_id} not found for assignment {assignment.id}")
                return None
            
            # Get the user associated with the staff member
            staff_user = db.query(User).filter(
                User.id == staff_member.user_id
            ).first() if hasattr(staff_member, 'user_id') and staff_member.user_id else None
            
            # If no user associated, create event for facility admin to track
            target_user_id = staff_user.id if staff_user else assigned_by_user.id
            
            # Create calendar event ID
            event_id = str(uuid.uuid4())
            
            # Calculate event times based on due date and estimated duration
            due_date = assignment.due_date
            if training_program.estimated_duration_minutes:
                start_time = due_date - timedelta(minutes=training_program.estimated_duration_minutes)
                end_time = due_date
            else:
                # Default to 1 hour before due date
                start_time = due_date - timedelta(hours=1)
                end_time = due_date
            
            # Create description with assignment details
            description = f"Training Assignment: {training_program.title}"
            description += f"\nAssigned to: {staff_member.first_name} {staff_member.last_name}"
            description += f"\nDue: {due_date.strftime('%Y-%m-%d %H:%M')}"
            description += f"\nPriority: {assignment.priority.title()}"
            
            if training_program.description:
                description += f"\n\nProgram Description: {training_program.description}"
            if assignment.assignment_notes:
                description += f"\n\nAssignment Notes: {assignment.assignment_notes}"
            if training_program.category:
                description += f"\nCategory: {training_program.category}"
            if training_program.delivery_method:
                description += f"\nDelivery Method: {training_program.delivery_method}"
            
            calendar_event = CalendarEvent(
                id=event_id,
                user_id=target_user_id,
                title=f"Training: {training_program.title}",
                start=start_time.isoformat(),
                end=end_time.isoformat(),
                description=description,
                location=None,  # Training location can be added later if needed
                all_day=False,
                facility_id=assignment.facility_id,
                created_by_admin=True,
                is_editable_by_user=False,  # Admin-only event
                training_assignment_id=assignment.id,
                training_program_id=training_program.id,
                event_type='training_assignment'
            )
            
            db.add(calendar_event)
            db.commit()
            db.refresh(calendar_event)
            
            # Create notification for the assignment
            try:
                await NotificationService.create_calendar_notification(
                    db=db,
                    user_id=target_user_id,
                    event_id=event_id,
                    action="created",
                    event_title=f"Training: {training_program.title}"
                )
            except Exception as e:
                logger.error(f"Error creating notification for training assignment {assignment.id}: {str(e)}")
            
            logger.info(f"Created calendar event {event_id} for training assignment {assignment.id}")
            return calendar_event
            
        except Exception as e:
            logger.error(f"Error creating calendar event for training assignment {assignment.id}: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    async def create_bulk_assignment_calendar_events(
        db: Session,
        assignments: List[TrainingAssignment],
        training_program: TrainingProgram,
        assigned_by_user: User
    ) -> List[CalendarEvent]:
        """
        Create calendar events for multiple training assignments.
        Used for bulk assignment operations.
        """
        created_events = []
        
        try:
            for assignment in assignments:
                calendar_event = await TrainingCalendarIntegrationService.create_training_assignment_calendar_event(
                    db=db,
                    assignment=assignment,
                    training_program=training_program,
                    assigned_by_user=assigned_by_user
                )
                
                if calendar_event:
                    created_events.append(calendar_event)
            
            logger.info(f"Created {len(created_events)} calendar events for bulk training assignments")
            return created_events
            
        except Exception as e:
            logger.error(f"Error creating bulk calendar events for training assignments: {str(e)}")
            db.rollback()
            return []
    
    @staticmethod
    async def update_training_assignment_calendar_event(
        db: Session,
        assignment: TrainingAssignment,
        training_program: TrainingProgram
    ) -> Optional[CalendarEvent]:
        """
        Update calendar event when a training assignment is updated.
        """
        try:
            # Find existing calendar event for this assignment
            calendar_event = db.query(CalendarEvent).filter(
                CalendarEvent.training_assignment_id == assignment.id
            ).first()
            
            if not calendar_event:
                logger.info(f"No calendar event found for training assignment {assignment.id}")
                return None
            
            # Update event times based on new due date
            due_date = assignment.due_date
            if training_program.estimated_duration_minutes:
                start_time = due_date - timedelta(minutes=training_program.estimated_duration_minutes)
                end_time = due_date
            else:
                start_time = due_date - timedelta(hours=1)
                end_time = due_date
            
            calendar_event.start = start_time.isoformat()
            calendar_event.end = end_time.isoformat()
            calendar_event.title = f"Training: {training_program.title} ({assignment.status.title()})"
            
            # Update description with current status
            staff_member = db.query(StaffMember).filter(
                StaffMember.id == assignment.staff_member_id
            ).first()
            
            description = f"Training Assignment: {training_program.title}"
            if staff_member:
                description += f"\nAssigned to: {staff_member.first_name} {staff_member.last_name}"
            description += f"\nStatus: {assignment.status.title()}"
            description += f"\nDue: {due_date.strftime('%Y-%m-%d %H:%M')}"
            description += f"\nPriority: {assignment.priority.title()}"
            description += f"\nProgress: {assignment.progress_percentage}%"
            
            if assignment.time_spent_minutes > 0:
                description += f"\nTime Spent: {assignment.time_spent_minutes} minutes"
            
            calendar_event.description = description
            
            db.commit()
            db.refresh(calendar_event)
            
            logger.info(f"Updated calendar event for training assignment {assignment.id}")
            return calendar_event
            
        except Exception as e:
            logger.error(f"Error updating calendar event for training assignment {assignment.id}: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    async def create_certification_renewal_calendar_event(
        db: Session,
        completion: TrainingCompletion,
        training_program: TrainingProgram,
        staff_member: StaffMember
    ) -> Optional[CalendarEvent]:
        """
        Create a calendar event for certification renewal reminder.
        Creates event before certification expires based on program settings.
        """
        try:
            if not training_program.requires_certification or not completion.expires_date:
                logger.debug(f"No certification renewal needed for completion {completion.id}")
                return None
            
            # Get the user associated with the staff member
            staff_user = db.query(User).filter(
                User.id == staff_member.user_id
            ).first() if hasattr(staff_member, 'user_id') and staff_member.user_id else None
            
            if not staff_user:
                logger.warning(f"No user found for staff member {staff_member.id}")
                return None
            
            # Create renewal reminder event 30 days before expiry
            reminder_date = completion.expires_date - timedelta(days=30)
            event_id = str(uuid.uuid4())
            
            # Create description with certification details
            description = f"Certification Renewal Reminder: {training_program.title}"
            description += f"\nCertification expires: {completion.expires_date.strftime('%Y-%m-%d')}"
            if completion.certificate_number:
                description += f"\nCertificate Number: {completion.certificate_number}"
            description += f"\nAction Required: Renew certification before expiry"
            
            calendar_event = CalendarEvent(
                id=event_id,
                user_id=staff_user.id,
                title=f"Renewal Due: {training_program.title}",
                start=reminder_date.isoformat(),
                end=(reminder_date + timedelta(hours=1)).isoformat(),
                description=description,
                location=None,
                all_day=False,
                facility_id=completion.facility_id if hasattr(completion, 'facility_id') else None,
                created_by_admin=True,
                is_editable_by_user=False,
                training_completion_id=completion.id,
                training_program_id=training_program.id,
                event_type='certification_renewal'
            )
            
            db.add(calendar_event)
            db.commit()
            db.refresh(calendar_event)
            
            logger.info(f"Created certification renewal calendar event {event_id} for completion {completion.id}")
            return calendar_event
            
        except Exception as e:
            logger.error(f"Error creating certification renewal calendar event for completion {completion.id}: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    async def delete_training_assignment_calendar_event(
        db: Session,
        assignment_id: int
    ) -> bool:
        """
        Delete calendar event when a training assignment is deleted.
        """
        try:
            # Find calendar event for this assignment
            calendar_event = db.query(CalendarEvent).filter(
                CalendarEvent.training_assignment_id == assignment_id
            ).first()
            
            if calendar_event:
                db.delete(calendar_event)
                db.commit()
                logger.info(f"Deleted calendar event for training assignment {assignment_id}")
                return True
            else:
                logger.info(f"No calendar event found for training assignment {assignment_id}")
                return True
            
        except Exception as e:
            logger.error(f"Error deleting calendar event for training assignment {assignment_id}: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    async def delete_training_program_calendar_events(
        db: Session,
        program_id: int
    ) -> bool:
        """
        Delete all calendar events related to a training program when it's deleted.
        """
        try:
            # Find all calendar events related to this training program
            calendar_events = db.query(CalendarEvent).filter(
                CalendarEvent.training_program_id == program_id
            ).all()
            
            deleted_count = len(calendar_events)
            
            # Delete all events related to this program
            for event in calendar_events:
                db.delete(event)
            
            db.commit()
            logger.info(f"Deleted {deleted_count} calendar events for training program {program_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting calendar events for training program {program_id}: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    async def create_training_deadline_reminder_events(
        db: Session,
        assignment: TrainingAssignment,
        training_program: TrainingProgram,
        reminder_days: List[int] = [7, 3, 1]
    ) -> List[CalendarEvent]:
        """
        Create multiple reminder events before training assignment due date.
        """
        created_events = []
        
        try:
            staff_member = db.query(StaffMember).filter(
                StaffMember.id == assignment.staff_member_id
            ).first()
            
            if not staff_member:
                return []
            
            staff_user = db.query(User).filter(
                User.id == staff_member.user_id
            ).first() if hasattr(staff_member, 'user_id') and staff_member.user_id else None
            
            if not staff_user:
                return []
            
            for days_before in reminder_days:
                reminder_date = assignment.due_date - timedelta(days=days_before)
                
                # Skip if reminder date is in the past
                if reminder_date < datetime.now():
                    continue
                
                event_id = str(uuid.uuid4())
                
                description = f"Training Deadline Reminder: {training_program.title}"
                description += f"\nDue in {days_before} day{'s' if days_before > 1 else ''}: {assignment.due_date.strftime('%Y-%m-%d %H:%M')}"
                description += f"\nProgress: {assignment.progress_percentage}%"
                description += f"\nPriority: {assignment.priority.title()}"
                
                calendar_event = CalendarEvent(
                    id=event_id,
                    user_id=staff_user.id,
                    title=f"Training Due in {days_before} day{'s' if days_before > 1 else ''}: {training_program.title}",
                    start=reminder_date.isoformat(),
                    end=(reminder_date + timedelta(minutes=30)).isoformat(),
                    description=description,
                    location=None,
                    all_day=False,
                    facility_id=assignment.facility_id,
                    created_by_admin=True,
                    is_editable_by_user=False,
                    training_assignment_id=assignment.id,
                    training_program_id=training_program.id,
                    event_type='training_deadline'
                )
                
                db.add(calendar_event)
                created_events.append(calendar_event)
            
            db.commit()
            
            for event in created_events:
                db.refresh(event)
            
            logger.info(f"Created {len(created_events)} deadline reminder events for training assignment {assignment.id}")
            return created_events
            
        except Exception as e:
            logger.error(f"Error creating deadline reminder events for training assignment {assignment.id}: {str(e)}")
            db.rollback()
            return [] 