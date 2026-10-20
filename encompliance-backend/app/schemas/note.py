"""
Description: Pydantic schemas for Note objects.
Purpose: Defines data validation and serialization for Note objects in the API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone


class NoteBase(BaseModel):
    """Base schema for Note objects."""
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    is_pinned: bool = False
    is_archived: bool = False


class NoteCreate(NoteBase):
    """Schema for creating a new Note."""
    pass


class NoteUpdate(BaseModel):
    """Schema for updating an existing Note."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


class NoteInDB(NoteBase):
    """Schema for Note as stored in the database."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z') if dt.tzinfo is None 
                                else dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        }


class Note(NoteInDB):
    """Schema for Note responses."""
    pass


class NoteList(BaseModel):
    """Schema for a list of Notes."""
    notes: List[Note]
    total: int


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation responses."""
    count: int
    message: str 