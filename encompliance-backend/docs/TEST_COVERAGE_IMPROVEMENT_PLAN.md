# Test Coverage Improvement Plan

## Current Status

**Coverage: 43.20%** (Target: 90%)
**Progress: +3.64% from baseline (39.56%)**

## Completed Work

### Phase 1: High-Impact Test Creation ✅

1. **Authentication Routes Tests** (`tests/integration/api/test_auth_routes.py`)
   - Login/logout flows
   - Session-based signup
   - Email verification
   - Password validation
   - Error handling

2. **Document Service Tests** (`tests/unit/services/test_document_service.py`)
   - PDF text extraction
   - File type detection
   - MIME type detection
   - Error handling

3. **Document Routes Tests** (`tests/integration/api/test_documents_routes.py`)
   - Document upload
   - Document listing
   - Document download
   - Document deletion
   - Label updates

4. **Payment Processor Service Tests** (`tests/unit/services/test_payment_processor_service.py`)
   - Checkout session processing
   - Seat changes
   - Subscription upgrades
   - Error handling

## Remaining Work

### Phase 2: Critical Business Logic (Target: +15% coverage → 58%)

#### Priority 1: API Routes (Target: +10%)
- [ ] `tests/integration/api/test_training_routes.py` - Training CRUD operations
- [ ] `tests/integration/api/test_facilities_routes.py` - Facility management
- [ ] `tests/integration/api/test_payments_routes.py` - Payment processing
- [ ] `tests/integration/api/test_calendar_routes.py` - Calendar operations (partial)
- [ ] `tests/integration/api/test_chat_routes.py` - Chat/AI endpoints

#### Priority 2: Service Layer (Target: +5%)
- [ ] `tests/unit/services/test_stripe_service.py` - Stripe integration
- [ ] `tests/unit/services/test_export_service.py` - Data export
- [ ] `tests/unit/services/test_llm_service.py` - LLM integration
- [ ] `tests/unit/services/test_subscription_downgrade_service.py` - Subscription management

### Phase 3: Complete Coverage (Target: +32% coverage → 90%)

#### Background Services (Target: +5%)
- [ ] `tests/unit/services/test_document_expiration_service.py`
- [ ] `tests/unit/services/test_training_notification_service.py`
- [ ] `tests/unit/services/test_training_reminder_scheduler.py`
- [ ] `tests/unit/services/test_facility_task_notification_service.py`

#### Utility Functions (Target: +5%)
- [ ] `tests/unit/utils/test_email_utils.py`
- [ ] `tests/unit/utils/test_user_data_export.py`
- [ ] `tests/unit/utils/test_tiers.py`
- [ ] `tests/unit/utils/test_access_control.py`

#### Remaining API Routes (Target: +10%)
- [ ] `tests/integration/api/test_operational_tasks_routes.py`
- [ ] `tests/integration/api/test_policy_routes.py`
- [ ] `tests/integration/api/test_team_members_routes.py`
- [ ] `tests/integration/api/test_notes_routes.py`
- [ ] `tests/integration/api/test_notifications_routes.py`

#### Edge Cases & Error Paths (Target: +12%)
- [ ] Error handling in all services
- [ ] Boundary conditions
- [ ] Integration failures
- [ ] Authentication/authorization edge cases

## Test Writing Guidelines

### Best Practices

1. **Follow AAA Pattern** (Arrange, Act, Assert)
   ```python
   def test_example():
       # Arrange
       user = create_test_user()
       
       # Act
       result = service.process(user)
       
       # Assert
       assert result.status == "success"
   ```

2. **Test Both Success and Failure Paths**
   - Happy path
   - Error conditions
   - Edge cases
   - Boundary values

3. **Use Proper Mocking**
   - Mock external services (Stripe, OpenAI)
   - Mock file system operations
   - Mock database queries when testing business logic

4. **Keep Tests Independent**
   - Each test should be able to run alone
   - Use fixtures for common setup
   - Clean up after tests

5. **Meaningful Test Names**
   - `test_login_success` ✅
   - `test_login_invalid_password` ✅
   - `test_thing` ❌

### Test File Structure

```python
"""
Module Description Tests
------------------------
Brief description of what this test file covers
"""

import pytest
from unittest.mock import patch, MagicMock
from app.service import ServiceClass

class TestServiceMethod:
    """Test specific service method"""
    
    def test_method_success(self):
        """Test successful execution"""
        pass
    
    def test_method_error_condition(self):
        """Test error handling"""
        pass
```

## Quick Wins

### High ROI Test Areas

1. **Simple Utility Functions** (Easy, good coverage boost)
   - File type detection
   - Validation functions
   - Format conversion

2. **Error Handlers** (Critical, often untested)
   - 400/401/404/500 responses
   - Exception handling
   - Validation errors

3. **CRUD Operations** (Standard patterns)
   - Create operations
   - Read operations
   - Update operations
   - Delete operations

4. **Business Logic** (High value)
   - Subscription calculations
   - Access control checks
   - Data transformations

## Running Tests

```bash
# Run all tests with coverage
python3 -m pytest --cov=app --cov-report=html

# Run specific test file
python3 -m pytest tests/unit/services/test_document_service.py -v

# Run with coverage for specific module
python3 -m pytest tests/unit/services/ --cov=app.services.document_service --cov-report=term-missing

# See coverage report
open htmlcov/index.html
```

## Coverage Tracking

### Current Coverage by Module

- **API Routes**: ~20-30% (needs significant work)
- **Services**: ~15-25% (needs significant work)
- **Utils**: ~0-50% (varies widely)
- **Models**: ~85-100% (mostly complete)

### Target Coverage by Module

- **API Routes**: 85%+
- **Services**: 85%+
- **Utils**: 80%+
- **Models**: 90%+ (already good)

## Next Steps

1. **Fix existing test failures** in newly created test files
2. **Create training routes tests** (high business value)
3. **Create facilities routes tests** (high business value)
4. **Create stripe service tests** (critical payment logic)
5. **Continue with remaining services and routes**

## Estimated Effort

- **Phase 2**: 2-3 weeks (critical business logic)
- **Phase 3**: 3-4 weeks (complete coverage)
- **Total**: 5-7 weeks to reach 90% coverage

## Notes

- Some tests may need adjustment based on actual implementation
- Focus on business-critical paths first
- Don't test implementation details, test behavior
- Keep tests maintainable and readable

