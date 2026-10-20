"""
Training Material Model Module

This module defines the TrainingMaterial database model for storing
training content and resources.

Key functionalities:
- Training content storage (documents, videos, links)
- Material versioning
- Access control
- Progress tracking
- Quiz and assessment integration
- Completion requirements

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class MaterialType(enum.Enum):
    DOCUMENT = "document"
    VIDEO = "video"
    LINK = "link"
    QUIZ = "quiz"
    ASSESSMENT = "assessment"
    PRESENTATION = "presentation"
    INTERACTIVE = "interactive"

class MaterialStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    UNDER_REVIEW = "under_review"

class TrainingMaterial(Base):
    __tablename__ = "training_materials"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Material identification
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    material_type = Column(String(20), nullable=False)
    
    # Content details
    file_path = Column(String(500), nullable=True)  # For uploaded files
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    
    # External content
    external_url = Column(String(500), nullable=True)  # For links and external videos
    embed_code = Column(Text, nullable=True)  # For embedded content
    
    # Content metadata
    duration_minutes = Column(Integer, nullable=True)  # For videos and timed content
    reading_time_minutes = Column(Integer, nullable=True)  # Estimated reading time
    difficulty_level = Column(String(20), nullable=True)  # beginner, intermediate, advanced
    
    # Versioning and status
    version = Column(String(20), default="1.0")
    status = Column(String(20), default=MaterialStatus.DRAFT.value)
    is_required = Column(Boolean, default=True)  # Required for completion
    
    # Ordering and organization
    sort_order = Column(Integer, default=0)
    section = Column(String(100), nullable=True)  # Section within training program
    
    # Quiz/Assessment specific fields
    quiz_questions = Column(JSON, nullable=True)  # For quiz materials
    passing_score = Column(Integer, nullable=True)  # Minimum score to pass
    max_attempts = Column(Integer, default=3)  # Maximum attempts allowed
    
    # Access control
    access_restrictions = Column(JSON, nullable=True)  # Role-based access rules
    
    # Relationships
    training_program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    training_program = relationship("TrainingProgram", back_populates="training_materials")
    creator = relationship("User", foreign_keys=[created_by])
    
    @property
    def is_active(self):
        return self.status == MaterialStatus.ACTIVE.value
    
    @property
    def is_quiz_or_assessment(self):
        return self.material_type in [MaterialType.QUIZ.value, MaterialType.ASSESSMENT.value]
    
    @property
    def file_extension(self):
        if self.file_name:
            return self.file_name.split('.')[-1].lower() if '.' in self.file_name else None
        return None
    
    def __repr__(self):
        return f"<TrainingMaterial(id={self.id}, title={self.title}, type={self.material_type})>" 