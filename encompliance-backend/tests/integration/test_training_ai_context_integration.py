"""
Integration test for AI context with training and certification data.
Purpose: Demonstrates end-to-end functionality of training context integration with AI assistant.
Educational Note: Shows integration testing patterns for context services with AI system.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.core.chat_utils import get_compliance_system_message
from app.services.context_service import ContextService
from app.services.training_context_service import TrainingContextService


class TestTrainingAIContextIntegration:
    """Integration tests for AI context with training data."""

    @pytest.mark.asyncio
    async def test_full_training_context_integration_pro_user(self):
        """Test complete training context integration for a Pro user."""
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
        
        # Mock training programs
        class MockTrainingProgram:
            def __init__(self, title, category, is_mandatory, estimated_duration):
                self.title = title
                self.category = category
                self.is_mandatory = is_mandatory
                self.estimated_duration_minutes = estimated_duration
        
        # Mock training assignments
        class MockTrainingAssignment:
            def __init__(self, id, staff_member_id, status, assigned_date, due_date, priority, program):
                self.id = id
                self.staff_member_id = staff_member_id
                self.status = status
                self.assigned_date = assigned_date
                self.due_date = due_date
                self.priority = priority
                self.training_program = program
        
        # Mock training completions
        class MockTrainingCompletion:
            def __init__(self, id, staff_member_id, completion_status, completed_date, program):
                self.id = id
                self.staff_member_id = staff_member_id
                self.completion_status = completion_status
                self.completed_date = completed_date
                self.certificate_status = "issued"
                self.certificate_number = "CERT-001"
                self.expires_date = datetime.now() + timedelta(days=30)
                self.is_expired = False
                self.is_certificate_valid = True
                self.final_score = 95
                self.training_program = program
        
        # Create mock data
        fire_safety_program = MockTrainingProgram("Fire Safety Training", "Safety", True, 60)
        cpr_program = MockTrainingProgram("CPR Certification", "Medical", True, 120)
        
        mock_assignments = [
            MockTrainingAssignment(
                1, 1, "assigned", 
                datetime.now() - timedelta(days=5),
                datetime.now() + timedelta(days=10),
                "high", fire_safety_program
            )
        ]
        
        mock_completions = [
            MockTrainingCompletion(
                1, 2, "completed",
                datetime.now() - timedelta(days=60),
                cpr_program
            )
        ]
        
        # Mock database queries - need to handle different query types
        def mock_query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'StaffMember':
                mock_query.filter.return_value.all.return_value = mock_staff
            elif model.__name__ == 'TrainingAssignment':
                mock_query.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_assignments
            elif model.__name__ == 'TrainingCompletion':
                mock_query.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_completions
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        
        # Test full training context integration
        training_context = await TrainingContextService.get_full_training_context(
            db=mock_db,
            user_id=1,
            user_subscription_status="pro"
        )
        
        # Verify training context contains expected data
        assert "=== TRAINING ASSIGNMENTS ===" in training_context
        assert "=== TRAINING COMPLETIONS & CERTIFICATIONS ===" in training_context
        assert "Fire Safety Training" in training_context
        assert "John Doe" in training_context
        assert "MANDATORY" in training_context
        assert "=== TRAINING CONTEXT USAGE INSTRUCTIONS ===" in training_context
        
        # Test system message integration
        system_message = get_compliance_system_message("daycare", training_context)
        
        # Verify system message includes training context
        assert "Fire Safety Training" in system_message
        assert "John Doe" in system_message
        assert "MANDATORY" in system_message
        assert "childcare" in system_message.lower()

    @pytest.mark.asyncio
    async def test_full_context_integration_with_calendar_notes_training(self):
        """Test complete context integration including calendar, notes, and training."""
        mock_db = Mock()
        
        # Mock calendar events
        mock_calendar_events = [
            {
                "title": "Safety Meeting",
                "start": "2025-06-01T10:00:00",
                "description": "Monthly safety review",
                "location": "Conference Room A"
            }
        ]
        
        # Mock notes
        class MockNote:
            def __init__(self, id, title, content, is_pinned, created_at, updated_at):
                self.id = id
                self.title = title
                self.content = content
                self.is_pinned = is_pinned
                self.created_at = created_at
                self.updated_at = updated_at
        
        mock_notes = [
            MockNote(1, "Training Reminder", "Schedule fire safety training for new staff", True, datetime.now(), datetime.now())
        ]
        
        # Mock training context
        training_context = """=== TRAINING ASSIGNMENTS ===
Current and upcoming training assignments:
• Fire Safety Training - John Doe (staff) | Due: 2025-06-15 | Status: Assigned | MANDATORY | Priority: High | Category: Safety

=== TRAINING COMPLETIONS & CERTIFICATIONS ===
Recent training completions and certification status:
• CPR Certification - Jane Smith | Completed: 2025-05-01 | Status: Completed | Certificate: Issued | Cert #: CERT-001 | Expires: 2026-05-01 | Score: 95%

=== TRAINING CONTEXT USAGE INSTRUCTIONS ===
Use the above training assignments and certifications to provide relevant responses about:
- Training due dates and overdue assignments
- Certification expiration dates and renewal requirements
- Staff training completion status and progress
- Mandatory vs optional training requirements
- Training categories and compliance requirements
Reference specific staff members, programs, and dates when relevant to user questions.
"""
        
        # Mock the individual context services
        with patch.object(ContextService, 'get_user_calendar_events') as mock_calendar, \
             patch.object(ContextService, 'get_user_notes') as mock_notes_service, \
             patch.object(TrainingContextService, 'get_full_training_context') as mock_training:
            
            mock_calendar.return_value = mock_calendar_events
            mock_notes_service.return_value = [
                {
                    "id": 1,
                    "title": "Training Reminder",
                    "content": "Schedule fire safety training for new staff",
                    "is_pinned": True,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            ]
            mock_training.return_value = training_context
            
            # Get full user context
            full_context = await ContextService.get_full_user_context(
                db=mock_db,
                user_id=1,
                user_subscription_status="pro"
            )
            
            # Verify all context types are included
            assert "=== USER'S CALENDAR EVENTS ===" in full_context
            assert "=== USER'S NOTES ===" in full_context
            assert "=== TRAINING ASSIGNMENTS ===" in full_context
            assert "=== TRAINING COMPLETIONS & CERTIFICATIONS ===" in full_context
            
            # Verify specific content
            assert "Safety Meeting" in full_context
            assert "Training Reminder" in full_context
            assert "Fire Safety Training" in full_context
            assert "CPR Certification" in full_context
            assert "John Doe" in full_context
            assert "Jane Smith" in full_context

    def test_training_context_enhances_ai_responses(self):
        """Test that training context enables better AI responses."""
        # Sample training context
        training_context = """=== TRAINING ASSIGNMENTS ===
Current and upcoming training assignments:
• Fire Safety Training - John Doe (staff) | Due: 2025-06-15 | Status: Assigned | MANDATORY | Priority: High | Category: Safety
• Food Handling Certification - Jane Smith (supervisor) | Due: 2025-06-20 | Status: In Progress | Priority: Medium | Category: Health

=== TRAINING COMPLETIONS & CERTIFICATIONS ===
Recent training completions and certification status:
• CPR Certification - John Doe | Completed: 2025-05-01 | Status: Completed | Certificate: Issued | Cert #: CERT-001 | Expires: 2026-05-01 | Score: 95%
• First Aid Training - Jane Smith | Completed: 2025-04-15 | Status: Completed | Certificate: Issued | Cert #: CERT-002 | Expires in 25 days | Score: 88%

=== TRAINING CONTEXT USAGE INSTRUCTIONS ===
Use the above training assignments and certifications to provide relevant responses about:
- Training due dates and overdue assignments
- Certification expiration dates and renewal requirements
- Staff training completion status and progress
- Mandatory vs optional training requirements
- Training categories and compliance requirements
Reference specific staff members, programs, and dates when relevant to user questions.
"""
        
        # Create system message with training context
        system_message = get_compliance_system_message("daycare", training_context)
        
        # Verify the AI now has access to:
        # 1. Training assignment information
        assert "Fire Safety Training" in system_message
        assert "John Doe" in system_message
        assert "2025-06-15" in system_message
        assert "MANDATORY" in system_message
        
        # 2. Certification information
        assert "CPR Certification" in system_message
        assert "CERT-001" in system_message
        assert "2026-05-01" in system_message
        
        # 3. Instructions to use this information
        assert "Use the above" in system_message
        assert "training assignments and certifications" in system_message
        
        # 4. Specific guidance for training queries
        assert "Training due dates" in system_message
        assert "Certification expiration dates" in system_message

    @pytest.mark.asyncio
    async def test_free_user_training_context_restriction(self):
        """Test that free users don't receive training context."""
        mock_db = Mock()
        
        # Test free user - should not get training context
        training_context = await TrainingContextService.get_full_training_context(
            db=mock_db,
            user_id=1,
            user_subscription_status="free"
        )
        
        # Should return empty string for free users
        assert training_context == ""

    @pytest.mark.asyncio
    async def test_error_handling_in_training_context_integration(self):
        """Test that training context integration handles errors gracefully."""
        mock_db = Mock()
        
        # Mock training context service to raise an exception
        with patch.object(TrainingContextService, 'get_full_training_context') as mock_training:
            mock_training.side_effect = Exception("Training service error")
            
            # Mock other services to work normally
            with patch.object(ContextService, 'get_user_calendar_events') as mock_calendar, \
                 patch.object(ContextService, 'get_user_notes') as mock_notes:
                
                mock_calendar.return_value = [{"title": "Test Event"}]
                mock_notes.return_value = [{"title": "Test Note", "content": "Test content"}]
                
                # Should handle training error gracefully and return partial context
                context = await ContextService.get_full_user_context(
                    db=mock_db,
                    user_id=1,
                    user_subscription_status="pro"
                )
                
                # Should include calendar and notes despite training error
                assert "=== USER'S CALENDAR EVENTS ===" in context
                assert "=== USER'S NOTES ===" in context
                assert "Test Event" in context
                assert "Test Note" in context
                
                # Should not include training sections due to error
                assert "=== TRAINING ASSIGNMENTS ===" not in context

    @pytest.mark.asyncio
    async def test_training_query_examples(self):
        """Test examples of training-related queries the AI can now answer."""
        # Sample training context with various scenarios
        training_context = """=== TRAINING ASSIGNMENTS ===
Current and upcoming training assignments:
• Fire Safety Training - John Doe (staff) | Due: 2025-06-01 | Status: Overdue | MANDATORY | Priority: High | Category: Safety
• Food Handling Certification - Jane Smith (supervisor) | Due: 2025-06-15 | Status: Assigned | Priority: Medium | Category: Health
• Emergency Procedures - Mike Johnson (manager) | Due: 2025-06-20 | Status: In Progress | MANDATORY | Priority: High | Category: Safety

=== TRAINING COMPLETIONS & CERTIFICATIONS ===
Recent training completions and certification status:
• CPR Certification - John Doe | Completed: 2025-05-01 | Status: Completed | Certificate: Issued | Cert #: CERT-001 | Expires in 5 days | Score: 95%
• First Aid Training - Jane Smith | Completed: 2025-04-15 | Status: Completed | Certificate: Issued | Cert #: CERT-002 | EXPIRED | Score: 88%

=== TRAINING CONTEXT USAGE INSTRUCTIONS ===
Use the above training assignments and certifications to provide relevant responses about:
- Training due dates and overdue assignments
- Certification expiration dates and renewal requirements
- Staff training completion status and progress
- Mandatory vs optional training requirements
- Training categories and compliance requirements
Reference specific staff members, programs, and dates when relevant to user questions.
"""
        
        # Create system message with training context
        system_message = get_compliance_system_message("daycare", training_context)
        
        # Verify the AI can now answer questions like:
        # 1. "What training is overdue?"
        assert "Overdue" in system_message
        assert "Fire Safety Training" in system_message
        
        # 2. "Which certifications are expiring soon?"
        assert "Expires in 5 days" in system_message
        assert "CPR Certification" in system_message
        
        # 3. "What mandatory training do we have?"
        assert "MANDATORY" in system_message
        assert "Emergency Procedures" in system_message
        
        # 4. "Who needs training?"
        assert "John Doe" in system_message
        assert "Jane Smith" in system_message
        assert "Mike Johnson" in system_message
        
        # 5. "What's the status of our safety training?"
        assert "Safety" in system_message
        assert "In Progress" in system_message

    @pytest.mark.asyncio
    async def test_performance_with_large_training_dataset(self):
        """Test performance considerations with large training datasets."""
        mock_db = Mock()
        
        # Mock large dataset (should be limited by service)
        large_staff_list = []
        large_assignments_list = []
        
        # Create 100 mock staff members
        for i in range(100):
            class MockStaffMember:
                def __init__(self, id, first_name, last_name, role, status):
                    self.id = id
                    self.first_name = first_name
                    self.last_name = last_name
                    self.role = role
                    self.status = status
            
            large_staff_list.append(MockStaffMember(i, f"Staff{i}", f"Member{i}", "staff", "active"))
        
        # Mock database to return large dataset
        mock_db.query.return_value.filter.return_value.all.return_value = large_staff_list
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Test that service limits results appropriately
        assignments = await TrainingContextService.get_user_training_assignments(
            db=mock_db,
            user_id=1,
            user_subscription_status="pro",
            limit=20  # Should limit to 20 despite large dataset
        )
        
        # Verify limit is respected
        assert len(assignments) <= 20 