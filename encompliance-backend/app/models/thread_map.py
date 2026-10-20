"""
Thread Map Model Module

This module defines the ThreadMap database model for the EnCompliance application.
It manages the mapping between conversation threads and OpenAI thread IDs.

Key functionalities:
- Conversation thread tracking
- OpenAI thread ID mapping
- User conversation association
- Thread usage tracking
- Timestamp-based activity monitoring

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class ThreadMap(Base):
    __tablename__ = "thread_maps"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, unique=True, nullable=False, index=True)
    thread_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ThreadMap(id={self.id}, conversation_id={self.conversation_id}, thread_id='{self.thread_id}')>" 