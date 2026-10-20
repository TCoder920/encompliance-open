# Support Portal API Documentation

## Overview

The Support Portal API provides a comprehensive interface for customer support operations, ticket management, analytics, and agent administration. This API is designed for internal support staff use and requires authentication.

**Base URL**: `http://localhost:6050` (development)  
**API Version**: `0.1.0`  
**Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

---

## Authentication

All endpoints (except `/health` and `/health/ready`) require JWT Bearer <TOKEN> authentication.

### Getting an Access Token

```bash
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

**Response:**
```json
{
  "access_token": "<TOKEN>",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header:
```
Authorization: Bearer <TOKEN>
```

---

## Health Check Endpoints

### GET /health
Public health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "service": "support-portal",
  "version": "0.1.0",
  "database": "healthy"
}
```

### GET /health/ready
Readiness check endpoint (no authentication required).

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": true,
    "timestamp": "2024-01-15T10:30:00.000Z"
  }
}
```

---

## Authentication Endpoints

### POST /auth/token
Authenticate and receive an access token.

**Request Body** (form-data):
- `username` (string, required)
- `password` (string, required)

**Response:** `200 OK`
```json
{
  "access_token": "<TOKEN>",
  "token_type": "bearer"
}
```

### GET /auth/me
Get current authenticated account information.

**Headers:**
- `Authorization: Bearer <TOKEN>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "support_agent",
  "email": "agent@example.com",
  "roles": ["mid"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

---

## Ticket Management

### Create Ticket
**POST** `/api/v1/support/tickets`

**Request Body:**
```json
{
  "subject": "Customer Issue",
  "description": "Detailed description of the issue",
  "category": "technical",
  "priority": "medium",
  "facility_id": 123,
  "tags": ["urgent", "billing"],
  "attachments": []
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "ticket_number": "TKT-A133E291C3",
  "subject": "Customer Issue",
  "status": "open",
  "priority": "medium",
  "category": "technical",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List Tickets
**GET** `/api/v1/support/tickets`

**Query Parameters:**
- `status_filter` (optional): `open`, `in_progress`, `escalated`, `resolved`, `closed`
- `priority_filter` (optional): `low`, `medium`, `high`, `urgent`
- `category_filter` (optional): `billing`, `technical`, `training`, `account`, `documentation`, `other`
- `assigned_to_me` (boolean, optional): Filter tickets assigned to current agent
- `unassigned` (boolean, optional): Filter unassigned tickets
- `skip` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Pagination limit (default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "ticket_number": "TKT-A133E291C3",
    "subject": "Customer Issue",
    "status": "open",
    "priority": "medium",
    "category": "technical",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Get Ticket
**GET** `/api/v1/support/tickets/{ticket_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "ticket_number": "TKT-A133E291C3",
  "subject": "Customer Issue",
  "description": "Detailed description",
  "status": "open",
  "priority": "medium",
  "category": "technical",
  "assigned_to_account_id": 2,
  "assigned_to_username": "agent_name",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Update Ticket
**PUT** `/api/v1/support/tickets/{ticket_id}`

**Request Body:**
```json
{
  "subject": "Updated Subject",
  "description": "Updated description",
  "status": "in_progress",
  "priority": "high"
}
```

**Response:** `200 OK` (returns updated ticket)

---

## Ticket Comments

### Add Comment
**POST** `/api/v1/support/tickets/{ticket_id}/comments`

**Request Body:**
```json
{
  "comment_text": "This is a comment",
  "is_internal": false
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "ticket_id": 1,
  "comment_text": "This is a comment",
  "commenter_type": "support",
  "commenter_name": "agent_name",
  "is_internal": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List Comments
**GET** `/api/v1/support/tickets/{ticket_id}/comments`

**Query Parameters:**
- `include_internal` (boolean, optional): Include internal comments (default: false)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "ticket_id": 1,
    "comment_text": "This is a comment",
    "commenter_type": "support",
    "is_internal": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

## Ticket Operations

### Assign Ticket
**POST** `/api/v1/support/tickets/{ticket_id}/assign`

**Request Body:**
```json
{
  "assigned_to_account_id": 2
}
```

**Response:** `200 OK` (returns updated ticket)

### Escalate Ticket
**POST** `/api/v1/support/tickets/{ticket_id}/escalate`

**Request Body:**
```json
{
  "target_tier": "senior",
  "escalation_reason": "Complex issue requiring senior support"
}
```

**Response:** `200 OK` (returns updated ticket)

### Resolve Ticket
**POST** `/api/v1/support/tickets/{ticket_id}/resolve`

**Request Body:**
```json
{
  "internal_notes": "Issue resolved successfully"
}
```

**Response:** `200 OK` (returns updated ticket)

---

## Customer Context

### Get Customer Context
**GET** `/api/v1/support/tickets/{ticket_id}/customer-context`

Returns comprehensive customer information including user details, facility, subscription, and ticket history.

**Response:** `200 OK`
```json
{
  "user": {
    "id": 1,
    "username": "customer",
    "email": "customer@example.com",
    "full_name": "John Doe",
    "subscription_status": "pro"
  },
  "facility": {
    "id": 1,
    "facility_name": "Test Facility",
    "facility_address": "123 Main St"
  },
  "subscription": {
    "id": 1,
    "status": "active",
    "seat_count": 5
  },
  "ticket_count": 5,
  "open_ticket_count": 2
}
```

### Get Customer History
**GET** `/api/v1/support/tickets/{ticket_id}/customer-history`

Returns a timeline of all tickets and interactions for the customer.

**Response:** `200 OK`
```json
[
  {
    "type": "ticket_created",
    "ticket_id": 1,
    "ticket_number": "TKT-A133E291C3",
    "subject": "Customer Issue",
    "timestamp": "2024-01-15T10:30:00Z",
    "description": "Ticket TKT-A133E291C3 created: Customer Issue"
  }
]
```

---

## Analytics

### Get Analytics
**GET** `/api/v1/support/analytics`

**Query Parameters:**
- `date_from` (string, optional): ISO 8601 date string (e.g., "2024-01-01T00:00:00Z")
- `date_to` (string, optional): ISO 8601 date string (e.g., "2024-01-31T23:59:59Z")

**Response:** `200 OK`
```json
{
  "total_tickets": 100,
  "open_tickets": 25,
  "in_progress_tickets": 15,
  "resolved_tickets": 50,
  "closed_tickets": 10,
  "escalated_tickets": 5,
  "tickets_by_priority": {
    "low": 20,
    "medium": 50,
    "high": 25,
    "urgent": 5
  },
  "tickets_by_category": {
    "technical": 40,
    "billing": 30,
    "account": 20,
    "other": 10
  },
  "average_resolution_time_hours": 24.5,
  "sla_breached_tickets": 3,
  "sla_compliance_rate": 97.0,
  "tickets_requiring_attention": 8
}
```

---

## Agent Management

### List Agents
**GET** `/api/v1/support/agents`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "account_id": 2,
    "account_username": "agent_name",
    "account_email": "agent@example.com",
    "support_tier": "mid",
    "specialization_tags": ["technical", "billing"],
    "max_concurrent_tickets": 10,
    "is_active": true
  }
]
```

### Create Agent Profile
**POST** `/api/v1/support/agents` (Requires senior role)

**Request Body:**
```json
{
  "account_id": 2,
  "support_tier": "mid",
  "specialization_tags": ["technical", "billing"],
  "max_concurrent_tickets": 10,
  "is_active": true
}
```

**Response:** `201 Created`

### Update Agent Profile
**PUT** `/api/v1/support/agents/{agent_id}`

**Request Body:**
```json
{
  "support_tier": "senior",
  "max_concurrent_tickets": 15
}
```

**Response:** `200 OK`

---

## Support Portal Operations

### Get Service Status
**GET** `/support/service-status` (Requires agent role)

Returns status of support portal and dependent services.

**Response:** `200 OK`
```json
{
  "support_portal_status": "Running",
  "support_database_status": "Connected",
  "user_api_status": "Running",
  "user_database_status": "Connected"
}
```

### Get Audit Logs
**GET** `/support/audit-logs` (Requires agent role)

**Query Parameters:**
- `skip` (integer, optional)
- `limit` (integer, optional)
- `action` (string, optional): Filter by action type

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "support_account_id": 1,
    "action": "login_success",
    "target": "username",
    "timestamp": "2024-01-15T10:30:00Z",
    "ip_address": "127.0.0.1"
  }
]
```

### Get Users
**GET** `/support/users` (Requires agent role)

List support portal accounts.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "username": "agent",
    "email": "agent@example.com",
    "roles": ["mid"],
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Get User Data
**GET** `/support/user-data` (Requires agent role)

Get aggregated customer data for support purposes.

**Response:** `200 OK`
```json
{
  "total_users": 1000,
  "active_users": 850,
  "total_facilities": 200
}
```

---

## WebSocket Notifications

### Connect to WebSocket
**WebSocket** `/api/v1/support/ws/notifications?token=<jwt_token>`

Real-time notifications for ticket events.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:6050/api/v1/support/ws/notifications?token=YOUR_TOKEN');
```

**Event Types:**
- `ticket_created`
- `ticket_assigned`
- `ticket_escalated`
- `ticket_resolved`
- `ticket_comment`
- `connection` (on connect)
- `heartbeat` (periodic)

**Example Event:**
```json
{
  "type": "ticket_assigned",
  "data": {
    "ticket": {
      "id": 1,
      "ticket_number": "TKT-A133E291C3",
      "subject": "Customer Issue"
    },
    "assigned_to_account_id": 2
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Operation requires one of the following roles: ['senior']"
}
```

### 404 Not Found
```json
{
  "detail": "Ticket not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred",
  "error_type": "ExceptionName"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

---

## Best Practices

1. **Token Management**: Store tokens securely and refresh before expiration
2. **Error Handling**: Always check response status codes and handle errors appropriately
3. **Pagination**: Use `skip` and `limit` parameters for large result sets
4. **WebSocket**: Implement reconnection logic for WebSocket connections
5. **Filtering**: Use query parameters to filter results server-side rather than client-side

---

## Support

For issues or questions about the Support Portal API, contact the development team or refer to the main project documentation.

---

**Last Updated**: 2024-01-15  
**API Version**: 0.1.0

