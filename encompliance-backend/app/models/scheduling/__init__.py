"""
Scheduling Models Package

This package groups all database models powering the workforce scheduling
experience. Models are separated to keep the main models namespace tidy.

Exports:
- Shift, ShiftStatus, ShiftRecurrencePattern
- StaffAvailability, AvailabilityStatus
- TimeOffRequest, TimeOffStatus, TimeOffCategory
- ShiftSwapRequest, ShiftSwapStatus
"""

from .shift import Shift, ShiftStatus, ShiftRecurrencePattern
from .staff_availability import StaffAvailability, AvailabilityStatus
from .time_off_request import (
    TimeOffRequest,
    TimeOffStatus,
    TimeOffCategory,
)
from .shift_swap_request import ShiftSwapRequest, ShiftSwapStatus

__all__ = [
    "Shift",
    "ShiftStatus",
    "ShiftRecurrencePattern",
    "StaffAvailability",
    "AvailabilityStatus",
    "TimeOffRequest",
    "TimeOffStatus",
    "TimeOffCategory",
    "ShiftSwapRequest",
    "ShiftSwapStatus",
]

