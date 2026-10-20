"""
Export Request Model Module

This module defines the ExportRequest database model for the EnCompliance application.
It manages individual export requests and their processing status.

Key functionalities:
- Export request tracking and status management
- File format and data type selection
- Size estimation and fee calculation
- Download link management with expiration
- Support ticket integration for additional requests

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
- uuid: For unique request identification
"""

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Boolean, Numeric, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid

# Export status constants
class ExportStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Export format constants
class ExportFormat:
    CSV = "csv"
    PDF = "pdf"
    JSON = "json"

class ExportRequest(Base):
    __tablename__ = "export_requests"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=ExportStatus.PENDING, index=True)
    format = Column(String(10), nullable=False)  # csv, pdf, json
    data_types = Column(JSON, nullable=False)  # Array of selected data types
    estimated_size = Column(BigInteger, nullable=False, default=0)  # Estimated size in bytes
    actual_size = Column(BigInteger, nullable=True)  # Actual size after generation
    requires_fee = Column(Boolean, nullable=False, default=False)
    fee_amount = Column(Numeric(10, 2), nullable=True)  # Fee amount in USD
    support_ticket_id = Column(String(100), nullable=True)  # Reference to support system
    file_path = Column(String(500), nullable=True)  # Path to generated file
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)  # Document library reference
    download_expires_at = Column(DateTime(timezone=True), nullable=True)  # 24-hour expiration
    error_message = Column(Text, nullable=True)  # Error details if failed
    progress_percentage = Column(Integer, nullable=False, default=0)  # Progress tracking 0-100
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="export_requests")
    document = relationship("Document", backref="export_request", foreign_keys=[document_id])
    
    def __repr__(self):
        return f"<ExportRequest(id={self.id}, user_id={self.user_id}, status={self.status}, format={self.format})>" 