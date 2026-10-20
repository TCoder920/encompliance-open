"""
Assignment Image Schemas Module

This module defines Pydantic schemas for assignment image API operations
including upload responses, metadata updates, and image information.

Key functionalities:
- Image upload response schemas
- Image metadata update schemas
- Image information display schemas
- HEIC conversion status tracking
- Storage usage reporting

Dependencies:
- pydantic: For data validation and serialization
- datetime: For timestamp handling
- typing: For type annotations

Educational Note: Implements comprehensive data validation and serialization
for assignment image operations with support for HEIC format metadata
and storage tracking for billing purposes.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class AssignmentImageBase(BaseModel):
    """Base schema for assignment image data."""
    label: Optional[str] = Field(None, max_length=255, description="Optional image label")
    description: Optional[str] = Field(None, description="Optional image description")
    display_order: int = Field(0, ge=0, description="Display order for image sorting")

class AssignmentImageUpdate(BaseModel):
    """Schema for updating assignment image metadata."""
    label: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)

class AssignmentImageResponse(AssignmentImageBase):
    """Schema for assignment image API responses."""
    id: int
    assignment_id: int
    image_type: str = Field(..., description="Image type: before, after, or progress")
    
    # File information
    file_name: str
    original_file_name: str
    file_size: int = Field(..., description="Web version file size in bytes")
    original_file_size: Optional[int] = Field(None, description="Original file size in bytes")
    mime_type: str = Field(..., description="Web version MIME type")
    original_mime_type: str = Field(..., description="Original file MIME type")
    
    # Upload tracking
    uploaded_by: int
    uploaded_at: datetime
    
    # HEIC conversion tracking
    conversion_status: str = Field(..., description="Conversion status: none, pending, completed, failed")
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    total_storage_bytes: int = Field(..., description="Total storage used (original + converted)")
    requires_conversion: bool = Field(..., description="Whether image required format conversion")
    is_heic_format: bool = Field(..., description="Whether original file is HEIC/HEIF format")
    conversion_completed: bool = Field(..., description="Whether conversion completed successfully")
    
    class Config:
        from_attributes = True

class ImageUploadResponse(BaseModel):
    """Schema for image upload operation response."""
    message: str
    uploaded_count: int = Field(..., ge=0, description="Number of images successfully uploaded")
    images: List[AssignmentImageResponse] = Field(..., description="List of uploaded image records")

class AssignmentImageFilter(BaseModel):
    """Schema for filtering assignment images."""
    assignment_id: Optional[int] = None
    image_type: Optional[str] = Field(None, pattern="^(before|after|progress)$")
    uploaded_by: Optional[int] = None
    conversion_status: Optional[str] = Field(None, pattern="^(none|pending|completed|failed)$")
    has_label: Optional[bool] = None
    
class AssignmentImageStats(BaseModel):
    """Schema for assignment image statistics."""
    total_images: int = Field(..., ge=0)
    before_images: int = Field(..., ge=0)
    after_images: int = Field(..., ge=0)
    progress_images: int = Field(..., ge=0)
    total_storage_bytes: int = Field(..., ge=0)
    heic_images: int = Field(..., ge=0)
    conversion_pending: int = Field(..., ge=0)
    conversion_failed: int = Field(..., ge=0)

class ImageReorderRequest(BaseModel):
    """Schema for bulk image reordering."""
    images: List[dict] = Field(..., description="List of image ID and display_order pairs")
    
    @validator('images')
    def validate_images(cls, v):
        """Validate image reorder data structure."""
        for item in v:
            if not isinstance(item, dict):
                raise ValueError('Each item must be a dictionary')
            if 'id' not in item or 'display_order' not in item:
                raise ValueError('Each item must have id and display_order fields')
            if not isinstance(item['id'], int) or not isinstance(item['display_order'], int):
                raise ValueError('id and display_order must be integers')
            if item['display_order'] < 0:
                raise ValueError('display_order must be non-negative')
        return v 