"""
Task Reference Image Model Module

This module defines the TaskReferenceImage database model for tracking
reference images associated with operational tasks for guidance and examples.

Key functionalities:
- Multiple reference image storage per task
- HEIC format support with conversion tracking
- Image labeling and descriptions
- Unlimited file size support
- Storage tracking for billing

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling

Educational Note: Implements comprehensive reference image management for operational tasks
with support for Apple's HEIC format and automatic conversion to web-compatible
formats. Tracks storage usage for future billing implementation.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class ConversionStatus(enum.Enum):
    NONE = "none"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskReferenceImage(Base):
    __tablename__ = "task_reference_images"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Task relationship
    operational_task_id = Column(Integer, ForeignKey("operational_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Image classification - always "reference" for task reference photos
    image_type = Column(String(20), nullable=False, default="reference", index=True)
    
    # File storage paths
    file_path = Column(String(500), nullable=False)  # Web-compatible version
    original_file_path = Column(String(500), nullable=True)  # Original file (for HEIC)
    
    # File metadata
    file_name = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Web version size
    original_file_size = Column(BigInteger, nullable=True)  # Original file size
    mime_type = Column(String(100), nullable=False)  # Web version mime type
    original_mime_type = Column(String(100), nullable=False)  # Original mime type
    
    # Upload tracking
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Image labeling and organization
    label = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, index=True)
    
    # HEIC conversion tracking
    conversion_status = Column(String(20), default=ConversionStatus.NONE.value)
    
    # Additional metadata
    image_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    operational_task = relationship("OperationalTask", back_populates="reference_images")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    @property
    def total_storage_bytes(self):
        """Calculate total storage used by this image (original + converted)."""
        total = self.file_size
        if self.original_file_size:
            total += self.original_file_size
        return total
    
    @property
    def requires_conversion(self):
        """Check if image required format conversion."""
        return self.conversion_status != ConversionStatus.NONE.value
    
    @property
    def is_heic_format(self):
        """Check if original file is HEIC/HEIF format."""
        return self.original_mime_type in ['image/heic', 'image/heif']
    
    @property
    def conversion_completed(self):
        """Check if conversion process completed successfully."""
        return self.conversion_status == ConversionStatus.COMPLETED.value
    
    def __repr__(self):
        return f"<TaskReferenceImage(id={self.id}, operational_task_id={self.operational_task_id}, label={self.label})>" 