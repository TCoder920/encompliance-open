"""
Assignment Image Model Module

This module defines the AssignmentImage database model for tracking
images associated with task assignments including before/after photos.

Key functionalities:
- Multiple image storage per assignment
- HEIC format support with conversion tracking
- Image labeling and descriptions
- Unlimited file size support
- Storage tracking for billing

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling

Educational Note: Implements comprehensive image management for task assignments
with support for Apple's HEIC format and automatic conversion to web-compatible
formats. Tracks storage usage for future billing implementation.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class ImageType(enum.Enum):
    BEFORE = "before"
    AFTER = "after"
    PROGRESS = "progress"

class ConversionStatus(enum.Enum):
    NONE = "none"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class AssignmentImage(Base):
    __tablename__ = "assignment_images"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Assignment relationship
    assignment_id = Column(Integer, ForeignKey("task_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Image classification
    image_type = Column(String(20), nullable=False, index=True)
    
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
    assignment = relationship("TaskAssignment", back_populates="images")
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
        return f"<AssignmentImage(id={self.id}, assignment_id={self.assignment_id}, type={self.image_type}, label={self.label})>" 