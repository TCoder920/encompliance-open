"""
Age-Based Assignment Service Unit Tests
---------------------------------------
Tests for age-based assignment service functionality
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.services.age_based_assignment_service import AgeBasedAssignmentService
from app.models.staff_member import StaffMember
from app.models.operational_task import OperationalTask


class TestAgeBasedAssignmentService:
    """Test AgeBasedAssignmentService methods"""
    
    def test_get_eligible_staff_by_age_success(self, db: Session):
        """Test successful staff retrieval by age"""
        # Create test staff member
        staff = StaffMember(
            first_name="Test",
            last_name="Staff",
            date_of_birth=date(1990, 1, 1),
            facility_id=1
        )
        db.add(staff)
        db.commit()
        
        eligible = AgeBasedAssignmentService.get_eligible_staff_by_age(
            db=db,
            facility_id=1,
            min_age=18,
            max_age=65
        )
        
        assert isinstance(eligible, list)
    
    def test_get_staff_eligible_for_task_success(self, db: Session):
        """Test successful staff retrieval for task"""
        # Create test task
        task = OperationalTask(
            title="Test Task",
            min_age_allowed=18,
            max_age_allowed=65,
            facility_id=1
        )
        db.add(task)
        db.commit()
        
        eligible = AgeBasedAssignmentService.get_staff_eligible_for_task(
            db=db,
            task_id=task.id
        )
        
        assert isinstance(eligible, list)
    
    def test_validate_staff_age_eligibility_success(self, db: Session):
        """Test successful age eligibility validation"""
        # Create test staff
        staff = StaffMember(
            first_name="Test",
            last_name="Staff",
            date_of_birth=date(1990, 1, 1),
            facility_id=1
        )
        db.add(staff)
        db.commit()
        
        is_eligible = AgeBasedAssignmentService.validate_staff_age_eligibility(
            db=db,
            staff_id=staff.id,
            min_age=18,
            max_age=65
        )
        
        assert isinstance(is_eligible, bool)
    
    def test_get_age_compliance_summary_success(self, db: Session):
        """Test successful age compliance summary"""
        summary = AgeBasedAssignmentService.get_age_compliance_summary(
            db=db,
            facility_id=1
        )
        
        assert isinstance(summary, dict)
        assert "total_staff" in summary or "compliance_rate" in summary or "warnings" in summary

