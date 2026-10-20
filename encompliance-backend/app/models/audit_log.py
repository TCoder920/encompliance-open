"""
Audit Log Model Module

This module defines the AuditLog database model for the EnCompliance application.
It tracks administrative actions and system events for security and compliance.

Key functionalities:
- Administrative action logging
- User activity tracking
- IP address recording (both public and private)
- Detailed event context storage
- Timestamp-based event tracking
- Admin user relationship management

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import SupportPortalBase
from sqlalchemy.orm import relationship

class AuditLog(SupportPortalBase):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    support_account_id = Column(
        Integer,
        ForeignKey("support_portal_users.id"),
        nullable=True,
    )
    action = Column(String, nullable=False, index=True) # e.g., 'login', 'create_user', 'view_logs', 'view_file_tree'
    target = Column(String, nullable=True) # e.g., 'user:123', 'file:/path/to/file'
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    ip_address = Column(String, nullable=True)
    internal_ip_address = Column(String, nullable=True)  # New column for internal/private IP tracking
    details = Column(JSON, nullable=True) # Any additional context

    support_account = relationship("SupportPortalAccount")

    def __repr__(self):
        return f"<AuditLog id={self.id} account={self.support_account_id} action={self.action} ts={self.timestamp}>"