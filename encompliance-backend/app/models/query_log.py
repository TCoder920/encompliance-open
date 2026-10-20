"""
Query Log Model Module

This module defines the QueryLog database model for the EnCompliance application.
It tracks user queries and responses for analytics and debugging purposes.

Key functionalities:
- User query logging
- Response tracking
- Document reference linking
- Conversation context preservation
- IP address recording
- Timestamp-based logging

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class QueryLog(Base):
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    operation_type = Column(String, nullable=True)
    document_reference = Column(String, nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    conversation_id = Column(Integer, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<QueryLog(id={self.id}, user_id={self.user_id}, query='{self.query[:30]}...')>" 