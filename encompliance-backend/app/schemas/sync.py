"""
Description: Pydantic schemas for real-time synchronization API endpoints.
Purpose: Defines request/response models for sync events, ensuring type safety
and validation for real-time data synchronization between admins and team members.

Educational Note: Pydantic V2 provides runtime validation and serialization
for API data models, ensuring data integrity in sync operations.
Reference: https://docs.pydantic.dev/latest/
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SyncEventResponse(BaseModel):
    """
    Description: Response schema for synchronization events.
    Purpose: Standardizes sync event data structure for SSE and polling responses.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_type: str = Field(..., description="Type of sync event (account_update, document_update, etc.)")
    event_data: Dict[str, Any] = Field(..., description="Event payload data")
    facility_id: int = Field(..., description="Target facility ID")
    target_user_id: Optional[int] = Field(None, description="Specific user ID or null for all team members")
    created_at: datetime = Field(..., description="Event creation timestamp")
    delivered: bool = Field(..., description="Whether event was successfully delivered")


class SyncDataResponse(BaseModel):
    """
    Description: Response schema for sync data endpoints.
    Purpose: Standardizes data structure for force sync operations.
    """
    model_config = ConfigDict(from_attributes=True)
    
    type: str = Field(..., description="Data type being synchronized")
    data: Dict[str, Any] = Field(..., description="Synchronized data payload")
    timestamp: str = Field(..., description="Sync timestamp in ISO format")
    facility_id: int = Field(..., description="Source facility ID")


class AccountOverviewData(BaseModel):
    """
    Description: Schema for account overview sync data.
    Purpose: Defines structure for facility account information synchronization.
    """
    model_config = ConfigDict(from_attributes=True)
    
    operation_name: Optional[str] = Field(None, description="Facility operation name")
    facility_types: List[str] = Field(default_factory=list, description="List of facility types")
    state: Optional[str] = Field(None, description="Facility state/territory")
    subscription_status: str = Field(..., description="Current subscription status")
    facility_name: Optional[str] = Field(None, description="Facility name")


class DocumentLibraryData(BaseModel):
    """
    Description: Schema for document library sync data.
    Purpose: Defines structure for document library synchronization.
    """
    model_config = ConfigDict(from_attributes=True)
    
    total_documents: int = Field(..., description="Total number of documents")
    total_size_bytes: int = Field(..., description="Total size of all documents")
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="List of accessible documents")


class CalendarEventData(BaseModel):
    """
    Description: Schema for calendar events sync data.
    Purpose: Defines structure for calendar event synchronization.
    """
    model_config = ConfigDict(from_attributes=True)
    
    events: List[Dict[str, Any]] = Field(default_factory=list, description="List of calendar events")
    upcoming_count: int = Field(0, description="Number of upcoming events")


class TrainingData(BaseModel):
    """
    Description: Schema for training data sync.
    Purpose: Defines structure for training assignments and progress synchronization.
    """
    model_config = ConfigDict(from_attributes=True)
    
    assignments: List[Dict[str, Any]] = Field(default_factory=list, description="Training assignments")
    completions: List[Dict[str, Any]] = Field(default_factory=list, description="Training completions")
    programs: List[Dict[str, Any]] = Field(default_factory=list, description="Available training programs")
    progress_summary: Dict[str, Any] = Field(default_factory=dict, description="Overall progress summary")


class SyncTriggerRequest(BaseModel):
    """
    Description: Request schema for triggering sync events.
    Purpose: Validates data when facility admins trigger synchronization events.
    """
    model_config = ConfigDict(from_attributes=True)
    
    facility_id: int = Field(..., description="Facility ID to sync")
    event_type: str = Field(..., description="Type of sync event to trigger")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    target_user_ids: Optional[List[int]] = Field(None, description="Specific user IDs to target")


class SyncStatusResponse(BaseModel):
    """
    Description: Response schema for sync operation status.
    Purpose: Provides feedback on sync operation success/failure.
    """
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field(..., description="Operation status (success/error)")
    message: Optional[str] = Field(None, description="Status message")
    notified_users: int = Field(0, description="Number of users notified")
    event_id: Optional[int] = Field(None, description="Created sync event ID") 