"""
Escalation Policy Models
"""

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class EscalationChannel(enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    PAGER = "pager"


class EscalationIncidentStatus(enum.Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class EscalationPolicy(Base):
    __tablename__ = "escalation_policies"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    incident_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    facility = relationship("Facility")
    created_by_user = relationship("User")
    steps = relationship("EscalationStep", back_populates="policy", cascade="all, delete-orphan", order_by="EscalationStep.step_number")
    incidents = relationship("EscalationIncident", back_populates="policy", cascade="all, delete-orphan")


class EscalationStep(Base):
    __tablename__ = "escalation_steps"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("escalation_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    delay_minutes = Column(Integer, nullable=False, default=0)
    channel = Column(Enum(EscalationChannel), nullable=False, default=EscalationChannel.EMAIL)
    target_role = Column(String(50), nullable=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    custom_recipient = Column(String(255), nullable=True)
    message_template = Column(Text, nullable=True)

    policy = relationship("EscalationPolicy", back_populates="steps")
    target_user = relationship("User")


class EscalationIncident(Base):
    __tablename__ = "escalation_incidents"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("escalation_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(EscalationIncidentStatus), default=EscalationIncidentStatus.PENDING, nullable=False, index=True)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    last_step_sent = Column(Integer, nullable=True)
    incident_metadata = Column("metadata", JSON, nullable=True)

    policy = relationship("EscalationPolicy", back_populates="incidents")

