# Support Portal API - Quick Reference Guide

## Base URL
- **Development**: `http://localhost:6050`
- **Production**: Configure via environment variables

## Authentication
```bash
# Get token
curl -X POST http://localhost:6050/auth/token \
  -d "username=your_username&password=your_password"

# Use token
curl -H "Authorization: Bearer <token>" \
  http://localhost:6050/api/v1/support/tickets
```

## Common Endpoints

### Health Checks
```bash
GET /health              # Public health check
GET /health/ready        # Readiness check
```

### Tickets
```bash
GET    /api/v1/support/tickets                    # List tickets
POST   /api/v1/support/tickets                    # Create ticket
GET    /api/v1/support/tickets/{id}               # Get ticket
PUT    /api/v1/support/tickets/{id}               # Update ticket
POST   /api/v1/support/tickets/{id}/assign         # Assign ticket
POST   /api/v1/support/tickets/{id}/escalate       # Escalate ticket
POST   /api/v1/support/tickets/{id}/resolve        # Resolve ticket
POST   /api/v1/support/tickets/{id}/comments       # Add comment
GET    /api/v1/support/tickets/{id}/comments       # List comments
```

### Analytics
```bash
GET /api/v1/support/analytics?date_from=2024-01-01&date_to=2024-01-31
```

### Agents
```bash
GET  /api/v1/support/agents           # List agents
POST /api/v1/support/agents           # Create agent (senior only)
PUT  /api/v1/support/agents/{id}      # Update agent
```

### Customer Context
```bash
GET /api/v1/support/tickets/{id}/customer-context
GET /api/v1/support/tickets/{id}/customer-history
```

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable (readiness check)

## WebSocket
```javascript
const ws = new WebSocket(
  'ws://localhost:6050/api/v1/support/ws/notifications?token=YOUR_TOKEN'
);
```

## Priority Levels
- `low`
- `medium`
- `high`
- `urgent`

## Ticket Status
- `open`
- `in_progress`
- `escalated`
- `resolved`
- `closed`

## Categories
- `billing`
- `technical`
- `training`
- `account`
- `documentation`
- `other`

## Support Tiers
- `beginner`
- `mid`
- `senior`

## Role Permissions

### Beginner
- View low/medium priority tickets
- Create comments
- View assigned tickets

### Mid
- All beginner permissions
- Handle high priority tickets
- Assign tickets
- Escalate tickets

### Senior
- All permissions
- Create/update agent profiles
- Full system access

---

**Full Documentation**: See `SUPPORT_PORTAL_API.md`  
**OpenAPI Spec**: `support-portal-api-spec.json` or `support-portal-api-spec.yaml`

