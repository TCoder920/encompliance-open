"""
Unit tests for the TrainingContextService.
Purpose: Tests the training context service functionality for AI assistant integration.
Educational Note: Demonstrates testing patterns for context aggregation services with mock data.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.services.training_context_service import TrainingContextService


class TestTrainingContextService:
    """Test cases for TrainingContextService."""

    @pytest.mark.asyncio
    async def test_get_user_training_assignments_pro_user(self):
        """Test that pro users can access training assignments."""
        # Mock database session
        mock_db = Mock()
        
        # Mock staff members
        class MockStaffMember:
            def __init__(self, id, first_name, last_name, role, status):
                self.id = id
                self.first_name = first_name
                self.last_name = last_name
                self.role = role
                self.status = status
        
        mock_staff = [
            MockStaffMember(1, "John", "Doe", "staff", "active"),
            MockStaffMember(2, "Jane", "Smith", "supervisor", "active")
        ]
        
        # Mock training program
        class MockTrainingProgram:
            def __init__(self, title, category, is_mandatory, estimated_duration):
                self.title = title
                self.category = category
                self.is_mandatory = is_mandatory
                self.estimated_duration_minutes = estimated_duration
        
        # Mock training assignments
        class MockTrainingAssignment:
            def __init__(self, id, staff_member_id, status, assigned_date, due_date, priority):
                self.id = id
                self.staff_member_id = staff_member_id
                self.status = status
                self.assigned_date = assigned_date
                self.due_date = due_date
                self.priority = priority
                self.training_program = MockTrainingProgram(
                    "Fire Safety Training", "Safety", True, 60
                )
        
        mock_assignments = [
            MockTrainingAssignment(
                1, 1, "assigned", 
                datetime.now() - timedelta(days=5),
                datetime.now() + timedelta(days=10),
                "high"
            )
        ]
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.return_value = mock_staff
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_assignments
        
        # Test pro user access
        assignments = await TrainingContextService.get_user_training_assignments(
            db=mock_db,
            user_id=1,
            user_subscription_status="pro",
            limit=20
        )
        
        assert len(assignments) == 1
        assert assignments[0]["staff_name"] == "John Doe"
        assert assignments[0]["program_title"] == "Fire Safety Training"
        assert assignments[0]["is_mandatory"] == True
        assert assignments[0]["status"] == "assigned"

    @pytest.mark.asyncio
    async def test_get_user_training_assignments_free_user(self):
        """Test that free users cannot access training assignments."""
        mock_db = Mock()
        
        # Test free user restriction
        assignments = await TrainingContextService.get_user_training_assignments(
            db=mock_db,
            user_id=1,
            user_subscription_status="free",
            limit=20
        )
        
        assert assignments == []

    @pytest.mark.asyncio
    async def test_get_user_training_completions_pro_user(self):
        """Test that pro users can access training completions."""
        mock_db = Mock()
        
        # Mock staff members
        class MockStaffMember:
            def __init__(self, id, first_name, last_name):
                self.id = id
                self.first_name = first_name
                self.last_name = last_name
        
        mock_staff = [MockStaffMember(1, "John", "Doe")]
        
        # Mock training program
        class MockTrainingProgram:
            def __init__(self, title, category):
                self.title = title
                self.category = category
        
        # Mock training completion
        class MockTrainingCompletion:
            def __init__(self, id, staff_member_id, completion_status, completed_date):
                self.id = id
                self.staff_member_id = staff_member_id
                self.completion_status = completion_status
                self.completed_date = completed_date
                self.certificate_status = "issued"
                self.certificate_number = "CERT-001"
                self.expires_date = datetime.now() + timedelta(days=365)
                self.is_expired = False
                self.is_certificate_valid = True
                self.final_score = 95
                self.training_program = MockTrainingProgram("CPR Training", "Safety")
        
        mock_completions = [
            MockTrainingCompletion(1, 1, "completed", datetime.now() - timedelta(days=30))
        ]
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.return_value = mock_staff
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_completions
        
        # Test pro user access
        completions = await TrainingContextService.get_user_training_completions(
            db=mock_db,
            user_id=1,
            user_subscription_status="pro",
            limit=15
        )
        
        assert len(completions) == 1
        assert completions[0]["staff_name"] == "John Doe"
        assert completions[0]["program_title"] == "CPR Training"
        assert completions[0]["completion_status"] == "completed"
        assert completions[0]["certificate_number"] == "CERT-001"
        assert completions[0]["final_score"] == 95

    @pytest.mark.asyncio
    async def test_get_user_training_completions_free_user(self):
        """Test that free users cannot access training completions."""
        mock_db = Mock()
        
        # Test free user restriction
        completions = await TrainingContextService.get_user_training_completions(
            db=mock_db,
            user_id=1,
            user_subscription_status="free",
            limit=15
        )
        
        assert completions == []

    def test_format_training_context_for_ai(self):
        """Test training context formatting for AI."""
        assignments = [
            {
                "program_title": "Fire Safety Training",
                "staff_name": "John Doe",
                "staff_role": "staff",
                "due_date": "2025-06-15T10:00:00",
                "status": "assigned",
                "is_mandatory": True,
                "priority": "high",
                "program_category": "Safety"
            }
        ]
        
        completions = [
            {
                "program_title": "CPR Training",
                "staff_name": "Jane Smith",
                "completed_date": "2025-05-01T14:00:00",
                "completion_status": "completed",
                "certificate_status": "issued",
                "certificate_number": "CERT-001",
                "expires_date": "2026-05-01T14:00:00",
                "days_until_expiry": 300,
                "final_score": 95
            }
        ]
        
        context = TrainingContextService.format_training_context_for_ai(assignments, completions)
        
        assert "=== TRAINING ASSIGNMENTS ===" in context
        assert "=== TRAINING COMPLETIONS & CERTIFICATIONS ===" in context
        assert "=== TRAINING CONTEXT USAGE INSTRUCTIONS ===" in context
        assert "Fire Safety Training" in context
        assert "CPR Training" in context
        assert "John Doe" in context
        assert "Jane Smith" in context
        assert "MANDATORY" in context
        assert "CERT-001" in context

    def test_format_training_context_for_ai_empty(self):
        """Test training context formatting with no data."""
        context = TrainingContextService.format_training_context_for_ai([], [])
        
        assert context == ""

    @pytest.mark.asyncio
    async def test_get_full_training_context(self):
        """Test getting full training context."""
        mock_db = Mock()
        
        # Mock the individual methods
        with patch.object(TrainingContextService, 'get_user_training_assignments') as mock_assignments, \
             patch.object(TrainingContextService, 'get_user_training_completions') as mock_completions, \
             patch.object(TrainingContextService, 'format_training_context_for_ai') as mock_format:
            
            mock_assignments.return_value = [{"program_title": "Test Assignment"}]
            mock_completions.return_value = [{"program_title": "Test Completion"}]
            mock_format.return_value = "Formatted training context"
            
            context = await TrainingContextService.get_full_training_context(
                db=mock_db,
                user_id=1,
                user_subscription_status="pro"
            )
            
            assert context == "Formatted training context"
            mock_assignments.assert_called_once()
            mock_completions.assert_called_once()
            mock_format.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_assignments(self):
        """Test error handling in training assignments retrieval."""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")
        
        assignments = await TrainingContextService.get_user_training_assignments(
            db=mock_db,
            user_id=1,
            user_subscription_status="pro"
        )
        
        assert assignments == []

    @pytest.mark.asyncio
    async def test_error_handling_in_completions(self):
        """Test error handling in training completions retrieval."""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")
        
        completions = await TrainingContextService.get_user_training_completions(
            db=mock_db,
            user_id=1,
            user_subscription_status="pro"
        )
        
        assert completions == []

    @pytest.mark.asyncio
    async def test_no_staff_members_found(self):
        """Test behavior when no staff members are found."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        assignments = await TrainingContextService.get_user_training_assignments(
            db=mock_db,
            user_id=1,
            user_subscription_status="pro"
        )
        
        assert assignments == []

    @pytest.mark.asyncio
    async def test_enterprise_user_access(self):
        """Test that enterprise users can access training context."""
        mock_db = Mock()
        
        # Mock staff members
        class MockStaffMember:
            def __init__(self, id, first_name, last_name, role, status):
                self.id = id
                self.first_name = first_name
                self.last_name = last_name
                self.role = role
                self.status = status
        
        mock_staff = [MockStaffMember(1, "John", "Doe", "staff", "active")]
        
        # Mock training program and assignment
        class MockTrainingProgram:
            def __init__(self):
                self.title = "Enterprise Training"
                self.category = "Compliance"
                self.is_mandatory = False
                self.estimated_duration_minutes = 120
        
        class MockTrainingAssignment:
            def __init__(self):
                self.id = 1
                self.staff_member_id = 1
                self.status = "assigned"
                self.assigned_date = datetime.now()
                self.due_date = datetime.now() + timedelta(days=7)
                self.priority = "medium"
                self.training_program = MockTrainingProgram()
        
        mock_assignments = [MockTrainingAssignment()]
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.return_value = mock_staff
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_assignments
        
        # Test enterprise user access
        assignments = await TrainingContextService.get_user_training_assignments(
            db=mock_db,
            user_id=1,
            user_subscription_status="enterprise"
        )
        
        assert len(assignments) == 1
        assert assignments[0]["program_title"] == "Enterprise Training" 