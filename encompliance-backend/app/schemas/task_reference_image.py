"""
Task Reference Image Schemas Module

This module provides Pydantic schemas for task reference image management,
including upload, response, and update operations.

Key functionalities:
- Request validation for image uploads
- Response serialization for API endpoints
- Image metadata management
- File validation and processing

Dependencies:
- pydantic: For data validation and serialization
- typing: For type hints

Educational Note: Implements comprehensive data validation for image management
following Pydantic V2 patterns with proper field validation and serialization.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class TaskReferenceImageBase(BaseModel):
    """Base schema for task reference image with common fields."""
    label: Optional[str] = Field(None, max_length=255, description="Descriptive label for the image")
    description: Optional[str] = Field(None, description="Detailed description of the image")
    display_order: int = Field(default=0, description="Order for displaying images")

class TaskReferenceImageCreate(TaskReferenceImageBase):
    """Schema for creating a new task reference image."""
    operational_task_id: int = Field(..., description="ID of the operational task")
    image_type: str = Field(default="reference", description="Type of image (always 'reference' for task images)")

class TaskReferenceImageUpdate(TaskReferenceImageBase):
    """Schema for updating task reference image metadata."""
    pass

class TaskReferenceImageResponse(TaskReferenceImageBase):
    """Schema for task reference image API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    operational_task_id: int
    image_type: str
    file_name: str
    original_file_name: str
    file_size: int
    original_file_size: Optional[int] = None
    mime_type: str
    original_mime_type: str
    uploaded_by: int
    uploaded_at: datetime
    conversion_status: str
    image_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    total_storage_bytes: int
    requires_conversion: bool
    is_heic_format: bool
    conversion_completed: bool
    
    @classmethod
    def from_orm(cls, obj):
        """Create response from ORM object with computed properties."""
        data = {
            "id": obj.id,
            "operational_task_id": obj.operational_task_id,
            "image_type": obj.image_type,
            "label": obj.label,
            "description": obj.description,
            "display_order": obj.display_order,
            "file_name": obj.file_name,
            "original_file_name": obj.original_file_name,
            "file_size": obj.file_size,
            "original_file_size": obj.original_file_size,
            "mime_type": obj.mime_type,
            "original_mime_type": obj.original_mime_type,
            "uploaded_by": obj.uploaded_by,
            "uploaded_at": obj.uploaded_at,
            "conversion_status": obj.conversion_status,
            "image_metadata": obj.image_metadata,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "total_storage_bytes": obj.total_storage_bytes,
            "requires_conversion": obj.requires_conversion,
            "is_heic_format": obj.is_heic_format,
            "conversion_completed": obj.conversion_completed,
        }
        return cls(**data)

class TaskReferenceImageUploadResponse(BaseModel):
    """Schema for bulk image upload responses."""
    message: str
    uploaded_count: int
    images: List[TaskReferenceImageResponse]

class TaskReferenceImageReorderRequest(BaseModel):
    """Schema for reordering task reference images."""
    image_orders: List[Dict[str, int]] = Field(..., description="List of {id: display_order} mappings") 