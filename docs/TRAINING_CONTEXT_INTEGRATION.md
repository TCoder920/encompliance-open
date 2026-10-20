# Training & Certification Context Integration

## Overview

This document describes the implementation of training and certification context integration into the AI assistant, enabling users to query their training data directly in the chat interface.

## Implementation Summary

### ✅ What Was Implemented

1. **Training Context Service** (`app/services/training_context_service.py`)
   - Fetches user training assignments and completions
   - Formats data for AI consumption
   - Respects subscription tier access controls
   - Handles errors gracefully

2. **Enhanced Context Service** (`app/services/context_service.py`)
   - Updated `get_full_user_context()` to include training data
   - Integrates training context with calendar events and notes
   - Maintains backward compatibility

3. **Access Control Integration** (`app/utils/feature_requirements.py`)
   - Added "training" feature to access control matrix
   - Enforces Pro/Enterprise tier requirement
   - Validates user permissions before data access

4. **Comprehensive Testing**
   - Unit tests for all training context service functionality
   - Integration tests for end-to-end functionality
   - Error handling and edge case testing
   - Subscription tier access validation

## Features

### Training Assignments Integration
- **Access Control**: Only Pro and Enterprise users can access training features
- **Data Included**: Staff names, program titles, due dates, status, priority, mandatory flags
- **User Isolation**: Only shows assignments for the current user's facility staff
- **Performance**: Limited to 20 most relevant assignments

### Training Completions & Certifications Integration
- **Access Control**: Only Pro and Enterprise users can access certification features
- **Data Included**: Completion dates, certificate status, expiration dates, scores, certificate numbers
- **Expiration Tracking**: Days until expiry, expired status indicators
- **Performance**: Limited to 15 most recent completions

### AI Context Format
```
=== TRAINING ASSIGNMENTS ===
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
```

## Technical Architecture

### Training Context Service (`TrainingContextService`)

#### Key Methods:
- `get_user_training_assignments()`: Fetches and filters training assignments
- `get_user_training_completions()`: Fetches and formats training completions
- `format_training_context_for_ai()`: Formats data for AI consumption
- `get_full_training_context()`: Orchestrates full training context gathering

#### Access Control:
```python
# Check subscription tier before accessing features
user_tier = get_tier_from_subscription_status(user_subscription_status)
if not can_access_feature(user_tier, "training"):
    return []  # No access for free users
```

#### Database Queries:
```python
# Get staff members for facility administrator
staff_members = db.query(StaffMember).filter(
    StaffMember.facility_administrator_id == user_id,
    StaffMember.status == "active"
).all()

# Get training assignments with joins
assignments = db.query(TrainingAssignment).join(
    TrainingProgram, TrainingAssignment.training_program_id == TrainingProgram.id
).filter(
    TrainingAssignment.staff_member_id.in_(staff_ids),
    TrainingAssignment.status.in_(['assigned', 'in_progress', 'overdue'])
).order_by(
    TrainingAssignment.due_date.asc()
).limit(limit).all()
```

### Context Service Integration

#### Context Gathering:
```python
# Fetch training context alongside calendar and notes
training_context = await TrainingContextService.get_full_training_context(
    db=db,
    user_id=user_id,
    user_subscription_status=user_subscription_status
)
```

#### Context Formatting:
```python
# Include training context in system message
context = ContextService.format_context_for_ai(calendar_events, notes, training_context)
```

## Usage Examples

### User Queries That Now Work:
1. **"What training do I have due this week?"**
   - AI can reference training assignments with due dates
   - Provides specific staff members and programs

2. **"Which staff members have overdue training?"**
   - AI can identify overdue assignments by status
   - Lists specific staff and training programs

3. **"When does my CPR certification expire?"**
   - AI can find specific certifications by name
   - Provides expiration dates and renewal reminders

4. **"What mandatory training is assigned?"**
   - AI can filter by mandatory flag
   - Highlights priority and compliance requirements

5. **"Show me all safety training status"**
   - AI can filter by category
   - Provides comprehensive status overview

## Error Handling

### Graceful Degradation:
- If training context fetching fails, AI continues without training context
- Subscription tier restrictions are enforced at the service level
- Database errors don't break the chat functionality
- Invalid training data is skipped with warnings

### Logging:
```python
logger.info(f"Retrieved training context for user {user_id}: {len(assignments)} assignments, {len(completions)} completions")
logger.warning(f"Error parsing training assignment {assignment_id}: {e}")
logger.error(f"Error fetching training context for user {user_id}: {e}")
```

## Performance Considerations

### Optimization Strategies:
1. **Limited Data Scope**: Only recent/relevant assignments and completions
2. **Result Limiting**: Maximum 20 assignments, 15 completions
3. **Subscription Filtering**: Early return for users without access
4. **Error Isolation**: Training context failures don't impact other context

### Database Performance:
- Proper joins to minimize query count
- Filtering by facility administrator for data isolation
- Ordering by relevance (due dates, completion dates)
- Active staff member filtering

## Security & Privacy

### Data Protection:
- User isolation: Only shows data belonging to the authenticated user's facility
- Subscription enforcement: Access control at multiple levels
- No data leakage: Failed context fetching doesn't expose other users' data

### Access Control Matrix:
| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Training Assignments | ❌ | ✅ | ✅ |
| Training Completions | ❌ | ✅ | ✅ |
| Certification Data | ❌ | ✅ | ✅ |
| AI Training Context | ❌ | ✅ | ✅ |

## Testing

### Test Coverage:
- ✅ Pro user training assignment access
- ✅ Enterprise user training completion access
- ✅ Free user access restriction
- ✅ Training context formatting
- ✅ Empty context handling
- ✅ Full context integration
- ✅ Error handling without chat disruption
- ✅ Performance limits validation

### Test Commands:
```bash
# Unit tests
python -m pytest tests/unit/services/test_training_context_service.py -v

# Integration tests
python -m pytest tests/integration/test_training_ai_context_integration.py -v

# All training context tests
python -m pytest tests/ -k "training_context" -v
```

## API Integration

### Context Service Integration:
The training context is automatically included when the AI assistant generates responses through the existing LLM service integration:

```python
# In app/services/llm_service.py
user_context = await ContextService.get_full_user_context(
    db=db,
    user_id=current_user_id,
    user_subscription_status=user.subscription_status
)
```

### System Message Enhancement:
Training context is included in the AI system message alongside calendar events and notes:

```python
# In app/core/chat_utils.py
system_message = get_compliance_system_message(operation_type, user_context)
```

## Troubleshooting

### Common Issues:

#### 1. Training Context Not Appearing
**Symptoms**: AI doesn't reference training data in responses
**Causes**: 
- User has Free subscription (no access)
- No active staff members in facility
- No training assignments/completions exist
**Solutions**:
- Verify user subscription tier
- Check staff member status and facility association
- Verify training data exists in database

#### 2. Performance Issues
**Symptoms**: Slow chat responses when training context is included
**Causes**:
- Large number of staff members
- Complex database queries
- Network latency
**Solutions**:
- Review database query performance
- Check result limiting is working
- Monitor database connection pool

#### 3. Access Control Errors
**Symptoms**: Users getting access denied for training features
**Causes**:
- Incorrect subscription status
- Feature requirements misconfiguration
- Database permission issues
**Solutions**:
- Verify user subscription status in database
- Check feature_requirements.py configuration
- Validate access control logic

### Debug Logging:
Enable debug logging to troubleshoot training context issues:

```python
import logging
logging.getLogger('app.services.training_context_service').setLevel(logging.DEBUG)
```

## Future Enhancements

### Potential Improvements:
1. **Real-time Updates**: WebSocket integration for live training status updates
2. **Smart Filtering**: AI-driven relevance filtering of training context
3. **Context Summarization**: Summarize large amounts of training data
4. **Training Recommendations**: AI-powered training assignment suggestions
5. **Compliance Alerts**: Proactive compliance violation warnings
6. **Bulk Operations**: Context for bulk training assignments and completions

## Deployment Notes

### Requirements:
- No additional dependencies required
- Backward compatible with existing chat functionality
- Works with current subscription tier system
- Integrates with existing training management APIs

### Configuration:
- No additional configuration required
- Uses existing subscription tier settings
- Leverages current access control system
- Follows established context integration patterns

## Conclusion

The training and certification context integration successfully enables personalized AI responses based on user's training data. The implementation:

- ✅ Respects subscription tiers and access controls
- ✅ Provides comprehensive training context to the AI assistant
- ✅ Maintains system performance and security
- ✅ Includes thorough testing and error handling
- ✅ Enables natural language queries about training data

Users can now ask questions about their training assignments, certifications, and compliance status directly in the chat interface, receiving personalized and contextually relevant responses from the AI assistant. 