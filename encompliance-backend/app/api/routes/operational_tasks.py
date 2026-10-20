"""
Operational Tasks API Routes Module

This module provides REST API endpoints for operational task and chore management.
Supports age-based assignment, recurring task scheduling, and comprehensive task management.

Key functionalities:
- Operational task CRUD operations
- Age-based staff assignment and validation
- Recurring task scheduling and management
- Task assignment creation and tracking
- Dashboard and analytics endpoints

Dependencies:
- fastapi: For REST API framework
- sqlalchemy: For database operations
- pydantic: For request/response validation

Educational Note: Implements comprehensive task management API following FastAPI
best practices with proper error handling, pagination, and filtering. Supports
age-based assignment validation for compliance with child labor regulations.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func, case

from app.database import get_db
from app.auth.dependencies import get_current_user, require_facility_admin
from app.models.user import User
from app.models.operational_task import OperationalTask, TaskType, TaskPriority
from app.models.task_assignment import TaskAssignment, TaskAssignmentStatus, TaskAssignmentPriority
from app.models.staff_member import StaffMember, StaffStatus
from app.schemas.task_management import (
    OperationalTaskCreate, OperationalTaskUpdate, OperationalTaskResponse,
    TaskAssignmentCreate, TaskAssignmentUpdate, TaskAssignmentResponse,
    AgeBasedAssignmentResponse, TaskDashboard, EligibleStaffMember
)
from app.services.age_based_assignment_service import AgeBasedAssignmentService
from app.services.recurring_task_scheduler import RecurringTaskScheduler
from app.services.task_calendar_integration_service import TaskCalendarIntegrationService

router = APIRouter(prefix="/operational-tasks", tags=["operational-tasks"])
logger = logging.getLogger(__name__)

@router.post("/tasks", response_model=OperationalTaskResponse)
async def create_operational_task(
    task_data: OperationalTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Create a new operational task with age-based assignment criteria."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        # Convert enum values to strings for database storage
        task_dict = task_data.dict()
        
        # Convert enum fields to string values
        if 'task_type' in task_dict and task_dict['task_type'] is not None:
            task_dict['task_type'] = task_dict['task_type'].value if hasattr(task_dict['task_type'], 'value') else task_dict['task_type']
        
        if 'priority' in task_dict and task_dict['priority'] is not None:
            task_dict['priority'] = task_dict['priority'].value if hasattr(task_dict['priority'], 'value') else task_dict['priority']
        
        if 'recurrence_pattern' in task_dict and task_dict['recurrence_pattern'] is not None:
            task_dict['recurrence_pattern'] = task_dict['recurrence_pattern'].value if hasattr(task_dict['recurrence_pattern'], 'value') else task_dict['recurrence_pattern']
        
        task = OperationalTask(
            **task_dict,
            facility_id=facility.id,
            created_by=current_user.id
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Create calendar event for the task
        try:
            if task.task_type == TaskType.RECURRING.value:
                # For recurring tasks, create multiple calendar events based on recurrence pattern
                await TaskCalendarIntegrationService.create_recurring_task_calendar_events(
                    db=db,
                    task=task,
                    created_by_user=current_user
                )
                logger.info(f"Created recurring calendar events for task {task.id}")
            else:
                # For one-time tasks, create a single calendar event
                await TaskCalendarIntegrationService.create_task_calendar_event(
                    db=db,
                    task=task,
                    created_by_user=current_user
                )
                logger.info(f"Created calendar event for task {task.id}")
        except Exception as e:
            logger.error(f"Failed to create calendar event for task {task.id}: {str(e)}")
            # Don't fail the entire request if calendar creation fails
        
        # For recurring tasks, immediately generate initial assignments
        if task.task_type == TaskType.RECURRING.value:
            try:
                initial_assignments = await RecurringTaskScheduler._generate_task_assignments(
                    db=db,
                    task=task,
                    current_time=datetime.now()
                )
                
                if initial_assignments:
                    # Create calendar events for the assignments
                    await TaskCalendarIntegrationService.create_assignment_calendar_events(
                        db=db,
                        assignments=initial_assignments,
                        task=task,
                        assigned_by_user=current_user
                    )
                    logger.info(f"Created {len(initial_assignments)} initial assignments for recurring task {task.id}")
                else:
                    logger.warning(f"No eligible staff found for recurring task {task.id}")
                    
            except Exception as e:
                logger.error(f"Failed to create initial assignments for recurring task {task.id}: {str(e)}")
                # Don't fail the entire request if assignment creation fails
        
        logger.info(f"Created operational task {task.id} by user {current_user.id}")
        return task
        
    except Exception as e:
        logger.error(f"Error creating operational task: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create operational task"
        )

@router.get("/tasks", response_model=List[OperationalTaskResponse])
async def get_operational_tasks(
    task_type: Optional[TaskType] = None,
    category: Optional[str] = None,
    priority: Optional[TaskPriority] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Get operational tasks for facility administrator."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        query = db.query(OperationalTask).filter(
            OperationalTask.facility_id == facility.id
        )
        
        if task_type:
            query = query.filter(OperationalTask.task_type == task_type.value)
        if category:
            query = query.filter(OperationalTask.category == category)
        if priority:
            query = query.filter(OperationalTask.priority == priority.value)
        if is_active is not None:
            query = query.filter(OperationalTask.is_active == is_active)
        
        offset = (page - 1) * per_page
        tasks = query.order_by(desc(OperationalTask.created_at)).offset(offset).limit(per_page).all()
        
        return tasks
        
    except Exception as e:
        logger.error(f"Error retrieving operational tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve operational tasks"
        )

@router.get("/tasks/{task_id}", response_model=OperationalTaskResponse)
async def get_operational_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Get a specific operational task by ID."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        task = db.query(OperationalTask).filter(
            OperationalTask.id == task_id,
            OperationalTask.facility_id == facility.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return task
        
    except Exception as e:
        logger.error(f"Error retrieving operational task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve operational task"
        )

@router.get("/tasks/{task_id}/eligible-staff", response_model=AgeBasedAssignmentResponse)
async def get_eligible_staff_for_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Get staff members eligible for a task based on age criteria."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        task = db.query(OperationalTask).filter(
            OperationalTask.id == task_id,
            OperationalTask.facility_id == facility.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return AgeBasedAssignmentService.get_staff_eligible_for_task(db, task)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting eligible staff for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get eligible staff"
        )

@router.get("/assignments", response_model=List[TaskAssignmentResponse])
async def get_task_assignments(
    operational_task_id: Optional[int] = None,
    staff_member_id: Optional[int] = None,
    status: Optional[TaskAssignmentStatus] = None,
    priority: Optional[TaskAssignmentPriority] = None,
    is_overdue: Optional[bool] = None,
    due_date_from: Optional[datetime] = None,
    due_date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Get task assignments with optional filters."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        query = db.query(TaskAssignment).options(
            joinedload(TaskAssignment.staff_member),
            joinedload(TaskAssignment.operational_task)
        ).join(
            OperationalTask, TaskAssignment.operational_task_id == OperationalTask.id
        ).filter(
            OperationalTask.facility_id == facility.id
        )
        
        # Apply filters
        if operational_task_id:
            query = query.filter(TaskAssignment.operational_task_id == operational_task_id)
        
        if staff_member_id:
            query = query.filter(TaskAssignment.staff_member_id == staff_member_id)
        
        if status:
            query = query.filter(TaskAssignment.status == status.value)
        
        if priority:
            query = query.filter(TaskAssignment.priority == priority.value)
        
        if is_overdue is not None:
            if is_overdue:
                query = query.filter(
                    TaskAssignment.due_date < datetime.now(),
                    TaskAssignment.status != TaskAssignmentStatus.COMPLETED.value
                )
            else:
                query = query.filter(
                    or_(
                        TaskAssignment.due_date >= datetime.now(),
                        TaskAssignment.status == TaskAssignmentStatus.COMPLETED.value
                    )
                )
        
        if due_date_from:
            query = query.filter(TaskAssignment.due_date >= due_date_from)
        
        if due_date_to:
            query = query.filter(TaskAssignment.due_date <= due_date_to)
        
        # Order by due date (overdue first, then by date)
        query = query.order_by(
            case(
                (TaskAssignment.due_date < datetime.now(), 0),
                else_=1
            ),
            TaskAssignment.due_date
        )
        
        # Apply pagination
        offset = (page - 1) * per_page
        assignments = query.offset(offset).limit(per_page).all()
        
        # Relationships are eagerly loaded via joinedload; no additional processing needed
        
        logger.info(f"Retrieved {len(assignments)} task assignments for facility {facility.id}")
        return assignments
        
    except Exception as e:
        logger.error(f"Error getting task assignments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task assignments"
        )

@router.post("/assignments", response_model=List[TaskAssignmentResponse])
async def create_task_assignments(
    assignment_data: TaskAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Create task assignments for multiple staff members."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        task = db.query(OperationalTask).filter(
            OperationalTask.id == assignment_data.operational_task_id,
            OperationalTask.facility_id == facility.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        staff_members = db.query(StaffMember).filter(
            StaffMember.id.in_(assignment_data.staff_member_ids),
            StaffMember.facility_administrator_id == current_user.id,
            StaffMember.status == StaffStatus.ACTIVE.value
        ).all()
        
        if len(staff_members) != len(assignment_data.staff_member_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some staff members not found or inactive"
            )
        
        assignments = []
        for staff_member in staff_members:
            eligibility = AgeBasedAssignmentService.validate_staff_age_eligibility(
                db, staff_member.id, task
            )
            
            if not eligibility["eligible"]:
                logger.warning(f"Staff {staff_member.id} not eligible for task {task.id}: {eligibility['reason']}")
                continue
            
            # Handle priority value - could be enum or string
            priority_value = assignment_data.priority
            if hasattr(priority_value, 'value'):
                priority_value = priority_value.value
            
            assignment = TaskAssignment(
                operational_task_id=task.id,
                staff_member_id=staff_member.id,
                assigned_by=current_user.id,
                due_date=assignment_data.due_date,
                priority=priority_value,
                assignment_notes=assignment_data.assignment_notes
            )
            
            db.add(assignment)
            assignments.append(assignment)
        
        db.commit()
        
        for assignment in assignments:
            db.refresh(assignment)
        
        # Create calendar events for the assignments
        try:
            await TaskCalendarIntegrationService.create_assignment_calendar_events(
                db=db,
                assignments=assignments,
                task=task,
                assigned_by_user=current_user
            )
            logger.info(f"Created calendar events for {len(assignments)} task assignments")
        except Exception as e:
            logger.error(f"Failed to create calendar events for assignments: {str(e)}")
            # Don't fail the entire request if calendar creation fails
        
        logger.info(f"Created {len(assignments)} task assignments by user {current_user.id}")
        return assignments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task assignments: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task assignments"
        )

@router.put("/assignments/{assignment_id}", response_model=TaskAssignmentResponse)
async def update_task_assignment(
    assignment_id: int,
    assignment_data: TaskAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Update a task assignment."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        assignment = db.query(TaskAssignment).join(
            OperationalTask, TaskAssignment.operational_task_id == OperationalTask.id
        ).filter(
            TaskAssignment.id == assignment_id,
            OperationalTask.facility_id == facility.id
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        # Update only provided fields
        update_data = assignment_data.dict(exclude_unset=True)
        
        # Convert enum fields to string values
        if 'status' in update_data and update_data['status'] is not None:
            update_data['status'] = update_data['status'].value if hasattr(update_data['status'], 'value') else update_data['status']
        
        if 'priority' in update_data and update_data['priority'] is not None:
            update_data['priority'] = update_data['priority'].value if hasattr(update_data['priority'], 'value') else update_data['priority']
        
        for field, value in update_data.items():
            setattr(assignment, field, value)
        
        db.commit()
        db.refresh(assignment)
        
        # Update calendar event for the assignment
        try:
            task = db.query(OperationalTask).filter(
                OperationalTask.id == assignment.operational_task_id
            ).first()
            
            if task:
                await TaskCalendarIntegrationService.update_assignment_calendar_event(
                    db=db,
                    assignment=assignment,
                    task=task
                )
                logger.info(f"Updated calendar event for assignment {assignment_id}")
        except Exception as e:
            logger.error(f"Failed to update calendar event for assignment {assignment_id}: {str(e)}")
            # Don't fail the entire request if calendar update fails
        
        logger.info(f"Updated task assignment {assignment_id} by user {current_user.id}")
        return assignment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task assignment {assignment_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task assignment"
        )

@router.get("/dashboard", response_model=TaskDashboard)
async def get_task_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Get task management dashboard data."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        total_tasks = db.query(OperationalTask).filter(
            OperationalTask.facility_id == facility.id
        ).count()
        
        active_tasks = db.query(OperationalTask).filter(
            OperationalTask.facility_id == facility.id,
            OperationalTask.is_active == True
        ).count()
        
        recurring_tasks = db.query(OperationalTask).filter(
            OperationalTask.facility_id == facility.id,
            OperationalTask.task_type == TaskType.RECURRING.value,
            OperationalTask.is_active == True
        ).count()
        
        assignment_query = db.query(TaskAssignment).join(
            OperationalTask, TaskAssignment.operational_task_id == OperationalTask.id
        ).filter(
            OperationalTask.facility_id == facility.id
        )
        
        total_assignments = assignment_query.count()
        pending_assignments = assignment_query.filter(
            TaskAssignment.status == TaskAssignmentStatus.ASSIGNED.value
        ).count()
        
        in_progress_assignments = assignment_query.filter(
            TaskAssignment.status == TaskAssignmentStatus.IN_PROGRESS.value
        ).count()
        
        completed_assignments = assignment_query.filter(
            TaskAssignment.status == TaskAssignmentStatus.COMPLETED.value
        ).count()
        
        overdue_assignments = assignment_query.filter(
            TaskAssignment.due_date < datetime.now(),
            TaskAssignment.status != TaskAssignmentStatus.COMPLETED.value
        ).count()
        
        completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
        
        upcoming_due_dates = assignment_query.filter(
            TaskAssignment.due_date >= datetime.now(),
            TaskAssignment.due_date <= datetime.now() + timedelta(days=7),
            TaskAssignment.status.in_([
                TaskAssignmentStatus.ASSIGNED.value,
                TaskAssignmentStatus.IN_PROGRESS.value
            ])
        ).order_by(TaskAssignment.due_date).limit(10).all()
        
        recent_completions = assignment_query.filter(
            TaskAssignment.status == TaskAssignmentStatus.COMPLETED.value
        ).order_by(desc(TaskAssignment.completed_date)).limit(10).all()
        
        return TaskDashboard(
            total_tasks=total_tasks,
            active_tasks=active_tasks,
            recurring_tasks=recurring_tasks,
            total_assignments=total_assignments,
            pending_assignments=pending_assignments,
            in_progress_assignments=in_progress_assignments,
            completed_assignments=completed_assignments,
            overdue_assignments=overdue_assignments,
            completion_rate=round(completion_rate, 1),
            average_completion_time=0.0,
            upcoming_due_dates=upcoming_due_dates,
            recent_completions=recent_completions
        )
        
    except Exception as e:
        logger.error(f"Error getting task dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task dashboard"
        )

@router.put("/tasks/{task_id}", response_model=OperationalTaskResponse)
async def update_operational_task(
    task_id: int,
    task_data: OperationalTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Update an operational task and its calendar event."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        task = db.query(OperationalTask).filter(
            OperationalTask.id == task_id,
            OperationalTask.facility_id == facility.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Convert enum values to strings for database storage
        update_dict = task_data.dict(exclude_unset=True)
        
        # Convert enum fields to string values
        if 'task_type' in update_dict and update_dict['task_type'] is not None:
            update_dict['task_type'] = update_dict['task_type'].value if hasattr(update_dict['task_type'], 'value') else update_dict['task_type']
        
        if 'priority' in update_dict and update_dict['priority'] is not None:
            update_dict['priority'] = update_dict['priority'].value if hasattr(update_dict['priority'], 'value') else update_dict['priority']
        
        if 'recurrence_pattern' in update_dict and update_dict['recurrence_pattern'] is not None:
            update_dict['recurrence_pattern'] = update_dict['recurrence_pattern'].value if hasattr(update_dict['recurrence_pattern'], 'value') else update_dict['recurrence_pattern']
        
        # Update task fields
        for field, value in update_dict.items():
            setattr(task, field, value)
        
        db.commit()
        db.refresh(task)
        
        # Update calendar event
        try:
            if task.task_type == TaskType.RECURRING.value:
                # For recurring tasks, update all recurring calendar events
                await TaskCalendarIntegrationService.update_recurring_task_calendar_events(
                    db=db,
                    task=task,
                    updated_by_user=current_user
                )
                logger.info(f"Updated recurring calendar events for task {task.id}")
            else:
                # For one-time tasks, update the single calendar event
                await TaskCalendarIntegrationService.update_task_calendar_event(
                    db=db,
                    task=task
                )
                logger.info(f"Updated calendar event for task {task.id}")
        except Exception as e:
            logger.error(f"Failed to update calendar event for task {task.id}: {str(e)}")
            # Don't fail the entire request if calendar update fails
        
        logger.info(f"Updated operational task {task.id} by user {current_user.id}")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating operational task {task_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update operational task"
        )

@router.delete("/tasks/{task_id}")
async def delete_operational_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Delete an operational task and its associated calendar events."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        task = db.query(OperationalTask).filter(
            OperationalTask.id == task_id,
            OperationalTask.facility_id == facility.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Delete associated calendar events first
        try:
            await TaskCalendarIntegrationService.delete_task_calendar_events(
                db=db,
                task_id=task_id,
                facility_id=facility.id
            )
            logger.info(f"Deleted calendar events for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to delete calendar events for task {task_id}: {str(e)}")
            # Continue with task deletion even if calendar cleanup fails
        
        # Delete the task (this will cascade delete assignments due to the relationship)
        db.delete(task)
        db.commit()
        
        logger.info(f"Deleted operational task {task_id} by user {current_user.id}")
        return {"message": "Task deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting operational task {task_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete operational task"
        )

@router.delete("/assignments/{assignment_id}")
async def delete_task_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """Delete a task assignment and its calendar event."""
    try:
        facility = current_user.administered_facility
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        assignment = db.query(TaskAssignment).join(
            OperationalTask, TaskAssignment.operational_task_id == OperationalTask.id
        ).filter(
            TaskAssignment.id == assignment_id,
            OperationalTask.facility_id == facility.id
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        # Delete associated calendar event first
        try:
            await TaskCalendarIntegrationService.delete_assignment_calendar_event(
                db=db,
                assignment_id=assignment_id
            )
            logger.info(f"Deleted calendar event for assignment {assignment_id}")
        except Exception as e:
            logger.error(f"Failed to delete calendar event for assignment {assignment_id}: {str(e)}")
            # Continue with assignment deletion even if calendar cleanup fails
        
        # Delete the assignment
        db.delete(assignment)
        db.commit()
        
        logger.info(f"Deleted task assignment {assignment_id} by user {current_user.id}")
        return {"message": "Assignment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task assignment {assignment_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task assignment"
        ) 