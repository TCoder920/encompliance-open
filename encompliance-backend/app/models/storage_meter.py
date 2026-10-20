"""
Storage Meter Models Module

Purpose:
    Track facility-level document storage consumption with granular usage events
    so billing tiers and quota alerts can be enforced on the backend.

Key Entities:
    - StorageMeter: Aggregated bytes used per facility per billing period.
    - StorageUsageEvent: Immutable event log for uploads/deletions that impact storage.

Dependencies:
    - sqlalchemy: ORM for model definitions.
    - datetime: Timestamp handling for billing windows and auditability.
"""

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StorageMeter(Base):
    """
    Aggregated storage usage for a facility within a billing period.
    """

    __tablename__ = "storage_meters"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    billing_period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    billing_period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    tier_name = Column(String(32), nullable=False, default="pro")
    included_bytes = Column(BigInteger, nullable=False, default=25 * 1024 * 1024 * 1024)  # 25 GB default
    used_bytes = Column(BigInteger, nullable=False, default=0)
    overage_bytes = Column(BigInteger, nullable=False, default=0)
    alert_level = Column(String(32), nullable=True)
    last_alert_sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    facility = relationship("Facility", backref="storage_meters")
    usage_events = relationship("StorageUsageEvent", back_populates="meter", cascade="all, delete-orphan")

    def in_current_period(self, now: datetime) -> bool:
        """
        Helper to check if the meter is active for the current timestamp.
        """
        return self.billing_period_start <= now < self.billing_period_end


class StorageUsageEvent(Base):
    """
    Immutable event log capturing every storage delta for auditing.
    """

    __tablename__ = "storage_usage_events"

    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("storage_meters.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(Integer, nullable=False)
    delta_bytes = Column(BigInteger, nullable=False)
    source = Column(String(32), nullable=False, default="document")
    event_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    meter = relationship("StorageMeter", back_populates="usage_events")


