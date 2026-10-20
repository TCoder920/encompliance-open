"""
Scheduling Schemas Module

Defines all Pydantic schemas for shift scheduling, availability tracking,
time-off workflows, and shift swaps. Schemas strictly validate time ranges,
recurrence settings, and workflow transitions before they reach the service
layer.

Educational Note: Schema validation references best practices from FastAPI's
Advanced User Guide and enforces OWASP input validation recommendations.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from pydantic import FieldValidationInfo

from app.models.scheduling import (
    ShiftStatus,
    ShiftRecurrencePattern,
    AvailabilityStatus,
    TimeOffStatus,
    TimeOffCategory,
    ShiftSwapStatus,
)


class ShiftBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    role: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    start_time: datetime
    end_time: datetime
    break_minutes: Optional[int] = Field(0, ge=0, le=180)
    timezone: Optional[str] = Field(None, max_length=64)
    status: ShiftStatus = Field(default=ShiftStatus.DRAFT)
    color_code: Optional[str] = Field(None, max_length=20)
    coverage_tags: Optional[List[str]] = None
    compliance_notes: Optional[str] = Field(None, max_length=1000)
    recurrence_pattern: ShiftRecurrencePattern = Field(default=ShiftRecurrencePattern.NONE)
    recurrence_interval: Optional[int] = Field(1, ge=1, le=52)
    recurrence_days: Optional[List[str]] = Field(None, description="Day names for recurring weekly patterns")
    recurrence_ends_at: Optional[datetime] = None
    staff_member_id: Optional[int] = Field(None, description="If assigned at creation time")

    @field_validator('end_time')
    def validate_date_order(cls, value, info: FieldValidationInfo):
        start_time = info.data.get('start_time')
        if start_time and value <= start_time:
            raise ValueError("end_time must be after start_time")
        return value

    @field_validator('recurrence_days')
    def validate_recurrence_days(cls, value, info: FieldValidationInfo):
        recurrence_pattern = info.data.get('recurrence_pattern')
        if value and recurrence_pattern == ShiftRecurrencePattern.NONE:
            raise ValueError("recurrence_days requires a recurrence pattern")
        return value


class ShiftCreate(ShiftBase):
    facility_id: int


class ShiftUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    role: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    break_minutes: Optional[int] = Field(None, ge=0, le=180)
    timezone: Optional[str] = Field(None, max_length=64)
    status: Optional[ShiftStatus] = None
    color_code: Optional[str] = Field(None, max_length=20)
    coverage_tags: Optional[List[str]] = None
    compliance_notes: Optional[str] = Field(None, max_length=1000)
    recurrence_pattern: Optional[ShiftRecurrencePattern] = None
    recurrence_interval: Optional[int] = Field(None, ge=1, le=52)
    recurrence_days: Optional[List[str]] = None
    recurrence_ends_at: Optional[datetime] = None
    staff_member_id: Optional[int] = None
    is_locked: Optional[bool] = None
    is_deleted: Optional[bool] = None


class ShiftResponse(ShiftBase):
    id: int
    facility_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    conflict_code: Optional[str]
    conflict_reason: Optional[str]
    is_locked: bool
    is_deleted: bool

    class Config:
        from_attributes = True


class StaffAvailabilityBase(BaseModel):
    staff_member_id: int
    day_of_week: str = Field(..., description="Lowercase weekday name, e.g., monday")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    preference_level: Optional[int] = Field(3, ge=1, le=5)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    status: AvailabilityStatus = Field(default=AvailabilityStatus.ACTIVE)
    exception_dates: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator('end_time')
    def validate_time_range(cls, value, info: FieldValidationInfo):
        start_time = info.data.get('start_time')
        if start_time and value <= start_time:
            raise ValueError("end_time must follow start_time")
        return value


class StaffAvailabilityCreate(StaffAvailabilityBase):
    facility_id: int


class StaffAvailabilityUpdate(BaseModel):
    day_of_week: Optional[str] = None
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    preference_level: Optional[int] = Field(None, ge=1, le=5)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    status: Optional[AvailabilityStatus] = None
    exception_dates: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=500)


class StaffAvailabilityResponse(StaffAvailabilityBase):
    id: int
    facility_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimeOffRequestBase(BaseModel):
    staff_member_id: int
    start_date: datetime
    end_date: datetime
    category: TimeOffCategory = Field(default=TimeOffCategory.PTO)
    requested_hours: Optional[int] = Field(None, ge=1, le=240)
    is_paid: bool = Field(default=True)
    reason: Optional[str] = Field(None, max_length=1000)
    supporting_files: Optional[list] = None

    @field_validator('end_date')
    def validate_timeframe(cls, value, info: FieldValidationInfo):
        start_date = info.data.get('start_date')
        if start_date and value <= start_date:
            raise ValueError("end_date must be after start_date")
        return value


class TimeOffRequestCreate(TimeOffRequestBase):
    facility_id: int


class TimeOffRequestUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[TimeOffStatus] = None
    category: Optional[TimeOffCategory] = None
    requested_hours: Optional[int] = Field(None, ge=1, le=240)
    is_paid: Optional[bool] = None
    reason: Optional[str] = Field(None, max_length=1000)
    supporting_files: Optional[list] = None
    decision_notes: Optional[str] = Field(None, max_length=1000)


class TimeOffRequestResponse(TimeOffRequestBase):
    id: int
    facility_id: int
    status: TimeOffStatus
    requested_by: int
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    decision_notes: Optional[str]
    audit_trail: Optional[list]
    overlaps_shift_ids: Optional[list]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShiftSwapRequestBase(BaseModel):
    shift_id: int
    requested_by_staff_id: int
    requested_to_staff_id: Optional[int] = None
    reason: Optional[str] = Field(None, max_length=1000)


class ShiftSwapRequestCreate(ShiftSwapRequestBase):
    facility_id: int


class ShiftSwapRequestUpdate(BaseModel):
    status: Optional[ShiftSwapStatus] = None
    requested_to_staff_id: Optional[int] = None
    admin_notes: Optional[str] = Field(None, max_length=1000)


class ShiftSwapRequestResponse(ShiftSwapRequestBase):
    id: int
    facility_id: int
    status: ShiftSwapStatus
    admin_notes: Optional[str]
    requested_at: datetime
    responded_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConflictCheckResponse(BaseModel):
    has_conflict: bool
    conflict_reason: Optional[str]
    conflicting_shift_ids: List[int] = Field(default_factory=list)
    conflicting_time_off_ids: List[int] = Field(default_factory=list)

