"""
Export Quota Model Module

This module defines the ExportQuota database model for the EnCompliance application.
It tracks quarterly export usage limits for Pro/Enterprise users.

Key functionalities:
- Quarterly export tracking per user
- Export usage counting and data size tracking
- Automatic quota reset each quarter
- User export history management

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class ExportQuota(Base):
    __tablename__ = "export_quotas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quarter_year = Column(String(7), nullable=False, index=True)  # Format: "2024-Q1"
    exports_used = Column(Integer, nullable=False, default=0)
    last_export_date = Column(DateTime(timezone=True), nullable=True)
    total_data_size = Column(BigInteger, nullable=False, default=0)  # Total bytes exported this quarter
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="export_quotas")
    
    def __repr__(self):
        return f"<ExportQuota(id={self.id}, user_id={self.user_id}, quarter={self.quarter_year}, used={self.exports_used})>" 