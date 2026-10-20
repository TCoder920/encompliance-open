"""
Training Schemas Module

This module defines Pydantic schemas for training and certification management API endpoints.
It provides data validation and serialization for all training-related operations.

Key functionalities:
- Training program schemas
- Staff member schemas
- Training assignment schemas
- Training material schemas
- Training completion schemas
- Push notification schemas

Dependencies:
- pydantic: For data validation and serialization
- datetime: For date/time handling
- typing: For type hints
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum

# Enums for training system
class StaffRole(str, Enum):
    STAFF = "staff"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    ADMINISTRATOR = "administrator"

class StaffStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"

class AssignmentStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class AssignmentPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class MaterialType(str, Enum):
    DOCUMENT = "document"
    VIDEO = "video"
    LINK = "link"
    QUIZ = "quiz"
    ASSESSMENT = "assessment"
    PRESENTATION = "presentation"
    INTERACTIVE = "interactive"

class MaterialStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    UNDER_REVIEW = "under_review"

class CompletionStatus(str, Enum):
    COMPLETED = "completed"
    VERIFIED = "verified"
    EXPIRED = "expired"
    REVOKED = "revoked"

class CertificateStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    ISSUED = "issued"
    EXPIRED = "expired"
    REVOKED = "revoked"

# Base schemas
class TrainingProgramBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    is_mandatory: bool = False
    requires_certification: bool = False
    certification_valid_months: int = 12
    estimated_duration_minutes: Optional[int] = None
    delivery_method: str = Field("online", max_length=50)
    prerequisites: Optional[List[int]] = None
    reminder_schedule_days: List[int] = Field(default=[30, 14, 7, 1])
    auto_assign_new_staff: bool = False
    is_active: bool = True

class TrainingProgramCreate(TrainingProgramBase):
    facility_type_ids: Optional[List[int]] = None

class TrainingProgramUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    is_mandatory: Optional[bool] = None
    requires_certification: Optional[bool] = None
    certification_valid_months: Optional[int] = None
    estimated_duration_minutes: Optional[int] = None
    delivery_method: Optional[str] = Field(None, max_length=50)
    prerequisites: Optional[List[int]] = None
    reminder_schedule_days: Optional[List[int]] = None
    auto_assign_new_staff: Optional[bool] = None
    is_active: Optional[bool] = None
    facility_type_ids: Optional[List[int]] = None

class TrainingProgram(TrainingProgramBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    facility_types: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True

# Staff Member schemas
class StaffMemberBase(BaseModel):
    employee_id: Optional[str] = Field(None, max_length=50)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20)
    role: StaffRole = StaffRole.STAFF
    department: Optional[str] = Field(None, max_length=100)
    position_title: Optional[str] = Field(None, max_length=100)
    hire_date: Optional[datetime] = None
    status: StaffStatus = StaffStatus.ACTIVE
    facility_name: Optional[str] = Field(None, max_length=255)
    facility_location: Optional[str] = Field(None, max_length=255)
    notification_preferences: Optional[Dict[str, Any]] = None

    @validator("hire_date", pre=True)
    def parse_hire_date(cls, value):
        """
        Accept date-only strings (YYYY-MM-DD) from the UI and convert them to
        midnight-aware datetimes so the database DateTime column can persist the value.
        """
        if value in (None, "", []):
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                # Allow full ISO datetimes or plain dates
                if "T" in value or " " in value:
                    return datetime.fromisoformat(value)
                return datetime.combine(date.fromisoformat(value), datetime.min.time())
            except ValueError as exc:
                raise ValueError("Invalid hire date format. Use YYYY-MM-DD.") from exc
        return value

class StaffMemberCreate(StaffMemberBase):
    pass

class StaffMemberUpdate(BaseModel):
    employee_id: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    role: Optional[StaffRole] = None
    department: Optional[str] = Field(None, max_length=100)
    position_title: Optional[str] = Field(None, max_length=100)
    hire_date: Optional[datetime] = None
    status: Optional[StaffStatus] = None
    facility_name: Optional[str] = Field(None, max_length=255)
    facility_location: Optional[str] = Field(None, max_length=255)
    notification_preferences: Optional[Dict[str, Any]] = None

class StaffMember(StaffMemberBase):
    id: int
    facility_administrator_id: int
    training_completion_rate: int = 0
    certifications_current: int = 0
    certifications_expired: int = 0
    last_training_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Training Material schemas
class TrainingMaterialBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    material_type: MaterialType
    file_path: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=255)
    external_url: Optional[str] = Field(None, max_length=500)
    embed_code: Optional[str] = None
    duration_minutes: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    difficulty_level: Optional[str] = Field(None, max_length=20)
    version: str = Field("1.0", max_length=20)
    status: MaterialStatus = MaterialStatus.DRAFT
    is_required: bool = True
    sort_order: int = 0
    section: Optional[str] = Field(None, max_length=100)
    quiz_questions: Optional[List[Dict[str, Any]]] = None
    passing_score: Optional[int] = None
    max_attempts: int = 3
    access_restrictions: Optional[Dict[str, Any]] = None

class TrainingMaterialCreate(TrainingMaterialBase):
    training_program_id: int

class TrainingMaterialUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    material_type: Optional[MaterialType] = None
    file_path: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=255)
    external_url: Optional[str] = Field(None, max_length=500)
    embed_code: Optional[str] = None
    duration_minutes: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    difficulty_level: Optional[str] = Field(None, max_length=20)
    version: Optional[str] = Field(None, max_length=20)
    status: Optional[MaterialStatus] = None
    is_required: Optional[bool] = None
    sort_order: Optional[int] = None
    section: Optional[str] = Field(None, max_length=100)
    quiz_questions: Optional[List[Dict[str, Any]]] = None
    passing_score: Optional[int] = None
    max_attempts: Optional[int] = None
    access_restrictions: Optional[Dict[str, Any]] = None

class TrainingMaterial(TrainingMaterialBase):
    id: int
    training_program_id: int
    created_by: int
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Training Assignment schemas
class TrainingAssignmentBase(BaseModel):
    due_date: datetime
    priority: AssignmentPriority = AssignmentPriority.MEDIUM
    assignment_notes: Optional[str] = None
    training_url: Optional[str] = Field(None, max_length=500)

class TrainingAssignmentCreate(TrainingAssignmentBase):
    training_program_id: int
    staff_member_id: int

class TrainingAssignmentBulkCreate(BaseModel):
    training_program_id: int
    staff_member_ids: List[int]
    due_date: datetime
    priority: AssignmentPriority = AssignmentPriority.MEDIUM
    assignment_notes: Optional[str] = None
    training_url: Optional[str] = Field(None, max_length=500)

class TrainingAssignmentUpdate(BaseModel):
    due_date: Optional[datetime] = None
    priority: Optional[AssignmentPriority] = None
    status: Optional[AssignmentStatus] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    assignment_notes: Optional[str] = None
    completion_notes: Optional[str] = None
    training_url: Optional[str] = Field(None, max_length=500)

class TrainingAssignment(TrainingAssignmentBase):
    id: int
    training_program_id: int
    staff_member_id: int
    assigned_by: int
    status: AssignmentStatus = AssignmentStatus.ASSIGNED
    assigned_date: datetime
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    progress_percentage: int = 0
    time_spent_minutes: int = 0
    last_accessed: Optional[datetime] = None
    completion_verified: bool = False
    verification_method: Optional[str] = None
    verification_score: Optional[int] = None
    verification_notes: Optional[str] = None
    reminder_sent_dates: Optional[List[str]] = None
    escalation_sent: bool = False
    completion_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_overdue: bool = False
    days_until_due: Optional[int] = None
    
    class Config:
        from_attributes = True

# Training Completion schemas
class TrainingCompletionBase(BaseModel):
    completion_method: Optional[str] = Field(None, max_length=50)
    final_score: Optional[int] = None
    attempts_taken: int = 1
    time_spent_minutes: Optional[int] = None
    verification_notes: Optional[str] = None
    compliance_notes: Optional[str] = None

class TrainingCompletionCreate(TrainingCompletionBase):
    training_assignment_id: int
    completed_date: datetime = Field(default_factory=datetime.now)

class TrainingCompletionUpdate(BaseModel):
    completion_status: Optional[CompletionStatus] = None
    verification_notes: Optional[str] = None
    final_score: Optional[int] = None
    compliance_notes: Optional[str] = None
    certificate_status: Optional[CertificateStatus] = None

class TrainingCompletion(TrainingCompletionBase):
    id: int
    training_assignment_id: int
    staff_member_id: int
    training_program_id: int
    completion_status: CompletionStatus = CompletionStatus.COMPLETED
    completed_date: datetime
    verified_by: Optional[int] = None
    verification_date: Optional[datetime] = None
    passing_score_required: Optional[int] = None
    certificate_status: CertificateStatus = CertificateStatus.PENDING
    certificate_number: Optional[str] = None
    certificate_file_path: Optional[str] = None
    certificate_issued_date: Optional[datetime] = None
    expires_date: Optional[datetime] = None
    renewal_required: bool = False
    renewal_reminder_sent: bool = False
    audit_trail: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_expired: bool = False
    days_until_expiry: Optional[int] = None
    is_certificate_valid: bool = False
    
    class Config:
        from_attributes = True

# Dashboard and Analytics schemas
class TrainingDashboard(BaseModel):
    total_staff: int
    total_programs: int
    total_assignments: int
    completed_assignments: int
    overdue_assignments: int
    due_soon_assignments: int
    completion_rate: float
    certifications_expiring: int
    recent_completions: List[TrainingCompletion]
    upcoming_due_dates: List[TrainingAssignment]

class StaffTrainingProgress(BaseModel):
    staff_member: StaffMember
    assigned_trainings: List[TrainingAssignment]
    completed_trainings: List[TrainingCompletion]
    overdue_count: int
    completion_rate: float
    next_due_date: Optional[datetime]

class TrainingAnalytics(BaseModel):
    completion_rates_by_program: Dict[str, float]
    completion_rates_by_department: Dict[str, float]
    average_completion_time: Dict[str, float]
    overdue_trends: List[Dict[str, Any]]
    certification_expiry_forecast: List[Dict[str, Any]]

# Push Notification schemas
class TrainingNotificationCreate(BaseModel):
    staff_member_id: int
    notification_type: str
    training_program_title: str
    message_data: Dict[str, Any]

class BulkTrainingNotification(BaseModel):
    staff_member_ids: List[int]
    notification_type: str
    training_data: Dict[str, Any]

# File Upload schemas
class TrainingMaterialUpload(BaseModel):
    title: str
    description: Optional[str] = None
    material_type: MaterialType
    training_program_id: int
    is_required: bool = True
    section: Optional[str] = None

# Search and Filter schemas
class TrainingProgramFilter(BaseModel):
    category: Optional[str] = None
    is_mandatory: Optional[bool] = None
    requires_certification: Optional[bool] = None
    facility_type_id: Optional[int] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None

class StaffMemberFilter(BaseModel):
    role: Optional[StaffRole] = None
    status: Optional[StaffStatus] = None
    department: Optional[str] = None
    search: Optional[str] = None

class TrainingAssignmentFilter(BaseModel):
    status: Optional[AssignmentStatus] = None
    priority: Optional[AssignmentPriority] = None
    training_program_id: Optional[int] = None
    staff_member_id: Optional[int] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    overdue_only: bool = False

# Response schemas
class TrainingProgramListResponse(BaseModel):
    programs: List[TrainingProgram]
    total: int
    page: int
    per_page: int

class StaffMemberListResponse(BaseModel):
    staff_members: List[StaffMember]
    total: int
    page: int
    per_page: int

class TrainingAssignmentListResponse(BaseModel):
    assignments: List[TrainingAssignment]
    total: int
    page: int
    per_page: int 