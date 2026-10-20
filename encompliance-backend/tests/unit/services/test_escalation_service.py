"""
Escalation Service Unit Tests
------------------------------
Tests for escalation service functionality
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.escalation_service import EscalationService
from app.models.escalation import EscalationPolicy, EscalationIncident


class TestEscalationService:
    """Test EscalationService methods"""
    
    def test_list_policies_success(self, db: Session):
        """Test successful policy listing"""
        policies = EscalationService.list_policies(db, facility_id=1)
        
        assert isinstance(policies, list)
    
    def test_create_policy_success(self, db: Session):
        """Test successful policy creation"""
        from app.models.user import User
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            subscription_status="pro"
        )
        db.add(user)
        db.commit()
        
        policy_data = {
            "name": "Test Policy",
            "incident_type": "test",
            "description": "Test description",
            "steps": []
        }
        
        policy = EscalationService.create_policy(
            db=db,
            facility_id=1,
            created_by_user_id=user.id,
            payload=policy_data
        )
        
        assert policy is not None
        assert policy.name == policy_data["name"]
    
    def test_trigger_incident_success(self, db: Session):
        """Test successful incident triggering"""
        from app.models.user import User
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            subscription_status="pro"
        )
        db.add(user)
        db.commit()
        
        # Create a policy first
        policy = EscalationService.create_policy(
            db=db,
            facility_id=1,
            created_by_user_id=user.id,
            payload={
                "name": "Test Policy",
                "incident_type": "test",
                "description": "Test description",
                "steps": []
            }
        )
        
        incident = EscalationService.trigger_incident(
            db=db,
            policy_id=policy.id,
            incident_type="test",
            description="Test incident"
        )
        
        assert incident is not None
        assert incident.incident_type == "test"
    
    def test_acknowledge_incident_success(self, db: Session):
        """Test successful incident acknowledgment"""
        from app.models.user import User
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            subscription_status="pro"
        )
        db.add(user)
        db.commit()
        
        # Create policy and incident
        policy = EscalationService.create_policy(
            db=db,
            facility_id=1,
            created_by_user_id=user.id,
            payload={
                "name": "Test Policy",
                "incident_type": "test",
                "description": "Test description",
                "steps": []
            }
        )
        
        incident = EscalationService.trigger_incident(
            db=db,
            policy_id=policy.id,
            incident_type="test",
            description="Test incident"
        )
        
        acknowledged = EscalationService.acknowledge_incident(
            db=db,
            incident_id=incident.id
        )
        
        assert acknowledged is not None
        assert acknowledged.acknowledged_at is not None
    
    def test_process_pending_incidents_success(self, db: Session):
        """Test processing pending incidents"""
        count = EscalationService.process_pending_incidents(db)
        
        assert isinstance(count, int)
        assert count >= 0

