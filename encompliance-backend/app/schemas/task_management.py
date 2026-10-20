"""
Task Management Schemas Module

This module defines Pydantic schemas for task management API operations.
Provides request/response models for operational tasks and task assignments.

Key functionalities:
- Operational task CRUD schemas
- Task assignment management schemas
- Age-based assignment filtering schemas
- Recurring task scheduling schemas
- Progress tracking and completion verification

Dependencies:
- pydantic: For data validation and serialization
- datetime: For timestamp handling

Educational Note: Implements comprehensive task management validation following
FastAPI best practices for data validation and serialization. Supports age-based
assignment criteria validation for compliance with child labor regulations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from app.models.operational_task import TaskType, TaskStatus, TaskPriority, RecurrencePattern
from app.models.task_assignment import TaskAssignmentStatus, TaskAssignmentPriority

def _parse_datetime_value(value, field_name: str, required: bool = False):
    """
    Normalize date-only strings (YYYY-MM-DD) produced by the UI into datetimes so
    backend DateTime columns accept them without validation errors.
    """
    if value in (None, "", []):
        if required:
            raise ValueError(f"{field_name} is required")
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        value = value.strip()
        if not value:
            if required:
                raise ValueError(f"{field_name} is required")
            return None
        try:
            if "T" in value or " " in value:
                return datetime.fromisoformat(value)
            return datetime.combine(date.fromisoformat(value), datetime.min.time())
        except ValueError as exc:
            raise ValueError(f"Invalid {field_name} format. Use ISO datetime or YYYY-MM-DD.") from exc
    return value

# Base schemas
class OperationalTaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task description")
    category: Optional[str] = Field(None, max_length=100, description="Task category")
    task_type: TaskType = Field(default=TaskType.ONE_TIME, description="Task type")
    recurrence_pattern: Optional[RecurrencePattern] = Field(None, description="Recurrence pattern for recurring tasks")
    recurrence_interval: int = Field(default=1, ge=1, le=365, description="Recurrence interval")
    min_age_required: Optional[int] = Field(None, ge=14, le=100, description="Minimum age required for assignment")
    max_age_allowed: Optional[int] = Field(None, ge=14, le=100, description="Maximum age allowed for assignment")
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Estimated duration in minutes")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    requires_supervision: bool = Field(default=False, description="Whether task requires supervision")
    special_instructions: Optional[str] = Field(None, max_length=2000, description="Special instructions")
    location: Optional[str] = Field(None, max_length=255, description="Task location")
    required_equipment: Optional[List[str]] = Field(None, description="Required equipment list")
    # Photo requirements - photo uploads are optional
    requires_before_photos: bool = Field(default=False, description="Whether task requires before photos")
    requires_after_photos: bool = Field(default=False, description="Whether task requires after photos") 
    photo_instructions: Optional[str] = Field(None, max_length=2000, description="Instructions for photo taking")
    start_date: datetime = Field(..., description="Task start date")
    end_date: Optional[datetime] = Field(None, description="Task end date for recurring tasks")

    @validator('max_age_allowed')
    def validate_age_range(cls, v, values):
        """Validate that max_age_allowed is greater than min_age_required."""
        if v is not None and 'min_age_required' in values and values['min_age_required'] is not None:
            if v <= values['min_age_required']:
                raise ValueError('max_age_allowed must be greater than min_age_required')
        return v

    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate that end_date is after start_date for recurring tasks."""
        if v is not None and 'start_date' in values:
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v

    @validator('recurrence_pattern')
    def validate_recurrence_pattern(cls, v, values):
        """Validate recurrence pattern is set for recurring tasks."""
        if 'task_type' in values and values['task_type'] == TaskType.RECURRING:
            if v is None:
                raise ValueError('recurrence_pattern is required for recurring tasks')
        return v

    @validator('start_date', pre=True)
    def parse_start_date(cls, v):
        return _parse_datetime_value(v, "start_date", required=True)

    @validator('end_date', pre=True)
    def parse_end_date(cls, v):
        return _parse_datetime_value(v, "end_date", required=False)

class OperationalTaskCreate(OperationalTaskBase):
    pass

class OperationalTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    min_age_required: Optional[int] = Field(None, ge=14, le=100)
    max_age_allowed: Optional[int] = Field(None, ge=14, le=100)
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    priority: Optional[TaskPriority] = None
    requires_supervision: Optional[bool] = None
    special_instructions: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=255)
    required_equipment: Optional[List[str]] = None
    requires_before_photos: Optional[bool] = None
    requires_after_photos: Optional[bool] = None
    photo_instructions: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None

class OperationalTaskResponse(OperationalTaskBase):
    id: int
    facility_id: int
    created_by: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Photo requirements - photo uploads are optional
    requires_before_photos: bool
    requires_after_photos: bool
    photo_instructions: Optional[str]
    
    # Computed properties
    is_recurring: bool
    has_age_restrictions: bool
    age_range_description: str
    
    class Config:
        from_attributes = True

# Task Assignment Schemas
class TaskAssignmentBase(BaseModel):
    due_date: datetime = Field(..., description="Assignment due date")
    priority: TaskAssignmentPriority = Field(default=TaskAssignmentPriority.MEDIUM, description="Assignment priority")
    assignment_notes: Optional[str] = Field(None, max_length=2000, description="Assignment notes")

    @validator('due_date', pre=True)
    def parse_due_date(cls, v):
        return _parse_datetime_value(v, "due_date", required=True)

class TaskAssignmentCreate(TaskAssignmentBase):
    operational_task_id: int = Field(..., description="Operational task ID")
    staff_member_ids: List[int] = Field(..., min_items=1, description="List of staff member IDs to assign")

    @validator('staff_member_ids')
    def validate_staff_member_ids(cls, v):
        """Validate staff member IDs list is not empty."""
        if not v:
            raise ValueError('At least one staff member must be assigned')
        return v

class TaskAssignmentUpdate(BaseModel):
    status: Optional[TaskAssignmentStatus] = None
    priority: Optional[TaskAssignmentPriority] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    time_spent_minutes: Optional[int] = Field(None, ge=0)
    completion_notes: Optional[str] = Field(None, max_length=2000)
    supervisor_notes: Optional[str] = Field(None, max_length=2000)
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    efficiency_rating: Optional[int] = Field(None, ge=1, le=5)
    requires_followup: Optional[bool] = None

# Staff member data for assignment responses
class AssignmentStaffMember(BaseModel):
    id: int
    first_name: str
    last_name: str
    full_name: str
    email: str
    role: str
    
    class Config:
        from_attributes = True

# Operational task data for assignment responses  
class AssignmentOperationalTask(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    location: Optional[str]
    requires_before_photos: bool
    requires_after_photos: bool
    photo_instructions: Optional[str]
    
    class Config:
        from_attributes = True

class TaskAssignmentResponse(TaskAssignmentBase):
    id: int
    operational_task_id: int
    staff_member_id: int
    assigned_by: int
    status: TaskAssignmentStatus
    assigned_date: datetime
    started_date: Optional[datetime]
    completed_date: Optional[datetime]
    progress_percentage: int
    time_spent_minutes: int
    last_accessed: Optional[datetime]
    completion_verified: bool
    verification_notes: Optional[str]
    completion_photo_url: Optional[str]
    verification_method: Optional[str]
    reminder_sent_dates: Optional[List[str]]
    escalation_sent: bool
    escalation_date: Optional[datetime]
    completion_notes: Optional[str]
    supervisor_notes: Optional[str]
    quality_rating: Optional[int]
    efficiency_rating: Optional[int]
    requires_followup: bool
    created_at: datetime
    updated_at: datetime
    
    # Related data
    staff_member: Optional[AssignmentStaffMember] = None
    operational_task: Optional[AssignmentOperationalTask] = None
    
    # Computed properties
    is_overdue: bool
    days_until_due: Optional[int]
    days_overdue: int
    is_completed: bool
    is_in_progress: bool
    completion_time_minutes: int
    has_photo_verification: bool
    
    class Config:
        from_attributes = True

# Age-based assignment schemas
class AgeBasedAssignmentCriteria(BaseModel):
    min_age: Optional[int] = Field(None, ge=14, le=100, description="Minimum age for assignment")
    max_age: Optional[int] = Field(None, ge=14, le=100, description="Maximum age for assignment")
    
    @validator('max_age')
    def validate_age_range(cls, v, values):
        """Validate that max_age is greater than min_age."""
        if v is not None and 'min_age' in values and values['min_age'] is not None:
            if v <= values['min_age']:
                raise ValueError('max_age must be greater than min_age')
        return v

class EligibleStaffMember(BaseModel):
    id: int
    first_name: str
    last_name: str
    full_name: str
    email: str
    role: str
    department: Optional[str]
    age: Optional[int]
    is_active: bool
    
    class Config:
        from_attributes = True

class AgeBasedAssignmentResponse(BaseModel):
    eligible_staff: List[EligibleStaffMember]
    total_staff: int
    eligible_count: int
    age_criteria: AgeBasedAssignmentCriteria

# Filter and pagination schemas
class TaskFilter(BaseModel):
    task_type: Optional[TaskType] = None
    category: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    has_age_restrictions: Optional[bool] = None
    is_active: Optional[bool] = None
    created_by: Optional[int] = None

class TaskAssignmentFilter(BaseModel):
    operational_task_id: Optional[int] = None
    staff_member_id: Optional[int] = None
    status: Optional[TaskAssignmentStatus] = None
    priority: Optional[TaskAssignmentPriority] = None
    is_overdue: Optional[bool] = None
    assigned_by: Optional[int] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None

# Dashboard and analytics schemas
class TaskDashboard(BaseModel):
    total_tasks: int
    active_tasks: int
    recurring_tasks: int
    total_assignments: int
    pending_assignments: int
    in_progress_assignments: int
    completed_assignments: int
    overdue_assignments: int
    completion_rate: float
    average_completion_time: float
    upcoming_due_dates: List[TaskAssignmentResponse]
    recent_completions: List[TaskAssignmentResponse]

class TaskAnalytics(BaseModel):
    completion_rates_by_category: Dict[str, float]
    completion_rates_by_staff: Dict[str, float]
    average_completion_time_by_task: Dict[str, float]
    overdue_trends: List[Dict[str, Any]]
    productivity_metrics: Dict[str, Any]

# Bulk operations schemas
class BulkTaskAssignmentCreate(BaseModel):
    operational_task_ids: List[int] = Field(..., min_items=1)
    staff_member_ids: List[int] = Field(..., min_items=1)
    due_date: datetime
    priority: TaskAssignmentPriority = TaskAssignmentPriority.MEDIUM
    assignment_notes: Optional[str] = None

class BulkTaskAssignmentResponse(BaseModel):
    created_assignments: List[TaskAssignmentResponse]
    failed_assignments: List[Dict[str, Any]]
    total_created: int
    total_failed: int

# Photo verification schema
class PhotoVerificationUpload(BaseModel):
    task_assignment_id: int
    photo_data: str = Field(..., description="Base64 encoded photo data")
    verification_notes: Optional[str] = Field(None, max_length=1000)

class PhotoVerificationResponse(BaseModel):
    task_assignment_id: int
    photo_url: str
    verification_status: str
    upload_timestamp: datetime 