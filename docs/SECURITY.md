# Encompliance.io Security Documentation

This document outlines the security measures implemented in the Encompliance.io platform to address the OWASP Top 10 vulnerabilities.

## OWASP Top 10 Vulnerabilities and Mitigations

### 1. Broken Access Control
- Implemented role-based access control (RBAC) throughout the application
- API endpoints verify user permissions before granting access to resources
- Authorization checks occur on server-side only, not relying on client-side state

### 2. Cryptographic Failures
- All sensitive data encrypted at rest in the database
- HTTPS enforced for all communications (Strict-Transport-Security header added)
- Password hashing using strong cryptographic algorithms (bcrypt/Argon2)
- No sensitive data exposure in logs or error messages

### 3. Injection
- SQL Injection prevention:
  - Parameterized queries used throughout the application via SQLAlchemy ORM
  - Added `sql_injection_protection` decorator for additional protection
  - Input validation on all user inputs
- XSS prevention:
  - Content Security Policy (CSP) headers implemented
  - HTML sanitization for user-generated content
  - Output encoding enforced

### 4. Insecure Design
- Security requirements defined during design phase
- Regular security code reviews
- Threat modeling conducted for high-risk features
- Principle of least privilege applied throughout the application

### 5. Security Misconfiguration
- Secure default configurations for all environments
- Unnecessary features, documentation, and sample applications removed
- HTTP security headers implemented:
  - Content-Security-Policy
  - X-Content-Type-Options
  - X-Frame-Options
  - X-XSS-Protection
  - Referrer-Policy
  - Strict-Transport-Security
- Regular security scans and audits

### 6. Vulnerable and Outdated Components
- Regular dependency updates and audits
- Automated vulnerability scanning
- Version pinning to prevent unexpected package updates
- Dependency tree pruning to minimize attack surface

### 7. Identification and Authentication Failures
- Strong password policies enforced
- Multi-factor authentication support
- Session management with secure cookies
- Protection against automated attacks:
  - Rate limiting
  - CAPTCHA for sensitive operations
  - Account lockout after failed attempts
- Authentication endpoints are properly isolated and well-documented

### 8. Software and Data Integrity Failures
- Secure CI/CD pipeline with integrity checks
- Software supply chain verified through checksum validation
- Deserialization of untrusted data prevented

### 9. Security Logging and Monitoring Failures
- Comprehensive logging of security events
- Centralized log management system
- Monitoring for suspicious activities
- Alert system for security events
- Audit trails for all sensitive operations

### 10. Server-Side Request Forgery (SSRF)
- Strict input validation for URLs
- Firewall rules and network segmentation
- URL validation against allowed domains/IP ranges
- Preventing access to internal resources

## Implemented Security Controls

### Content Security Policy (CSP)
The application uses Content Security Policy headers to prevent XSS attacks by specifying which dynamic resources are allowed to load.

```python
app.add_middleware(
    CSPMiddleware,
    default_src=["'self'"],
    script_src=["'self'", "'unsafe-inline'"],
    style_src=["'self'", "'unsafe-inline'"],
    img_src=["'self'", "data:", "https://cdn.encompliance.io"],
    font_src=["'self'", "https://fonts.gstatic.com"],
    connect_src=["'self'", "http://localhost:5174", "https://api.encompliance.io"],
    report_only=False  # Set to True initially to test without breaking functionality
)
```

### Cross-Site Request Forgery (CSRF) Protection
CSRF protection has been implemented using a token-based approach:

```python
app.add_middleware(
    CSRFProtection,
    cookie_secure=True,  # For HTTPS environments
    exclude_paths=["/api/v1/auth/login", "/api/v1/auth/signup"]
)
```

### HTTP Security Headers
The following security headers have been added to all responses:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Input Validation and Sanitization
All user inputs are validated and sanitized using the `InputSanitizer` class, which provides methods for:
- HTML sanitization
- Email validation
- Filename sanitization
- SQL query sanitization

### Rate Limiting
Rate limiting has been implemented to prevent brute force attacks against critical endpoints.

#### MCP & External AI Integrations
- `/api/v1/api-keys/*` endpoints enforce per-user sliding window limits (5 creates, 20 reads, 10 revocations per minute).
- `/api/v1/mcp/*` requests are throttled to 60 calls per minute per API key and are logged to `client_logs.log` with the prefix, IP address, and tool invoked.
- API keys can additionally restrict IP ranges via allowlists; violations raise `401/403` immediately.
- All MCP traffic relies on the Model Context Protocol facade in `app/mcp/server.py` which routes calls to existing services (operational tasks, AI form assistant) only when the requested scope is present.

### Password Security
Strong password policies are enforced using the `PasswordPolicy` class, which validates:
- Minimum length
- Character complexity (uppercase, lowercase, numbers, special characters)
- Common password prevention

### Authentication Implementation Details
- The backend provides two login endpoints:
  - `/api/v1/login`: Uses OAuth2PasswordRequestForm (form data)
  - `/api/v1/email-login`: Accepts JSON payload directly
- Frontend uses the email-login endpoint for consistency
- JWT tokens are used for maintaining authentication state
- Tokens are stored in localStorage with appropriate security measures

## Environment-Specific Security Configurations

### Development Environment
- More permissive CSP settings to facilitate development
- CSRF protection disabled by default to streamline testing
- Detailed error messages for debugging

### Production Environment
- Strict CSP settings with minimal use of 'unsafe-*' directives
- CSRF protection fully enabled
- Minimal error information returned to clients
- All security headers enforced
- HTTPS required for all connections

## Troubleshooting Security Features

### Common Issues and Solutions

#### CSP and Meta Tags
- **Issue**: X-Frame-Options and certain other security headers can only be set via HTTP headers, not meta tags
- **Solution**: Use proper HTTP headers for X-Frame-Options and avoid setting them in meta tags

#### Development vs Production Settings
- **Development**: We use more permissive CSP settings and disable CSRF protection to facilitate development
- **Production**: Stricter CSP settings with fewer 'unsafe-*' directives and enabled CSRF protection

#### Authentication Endpoints
- All authentication endpoints should be excluded from CSRF protection to prevent login issues
- Current excluded paths:
  ```
  /api/v1/auth/login
  /api/v1/auth/signup
  /api/v1/login
  /api/auth/login
  /api/v1/token
  /api/token
  /api/v1/users/me
  /api/users/me
  ```

#### Form Input Fields
- All form input fields should have appropriate `autocomplete` attributes to prevent browser warnings
- Email inputs should use `autocomplete="username"`
- Password inputs should use `autocomplete="current-password"` or `autocomplete="new-password"`

## Security Contacts
For security concerns or to report vulnerabilities, please contact:
- security@encompliance.io
- [Security page on our website](https://encompliance.io/security) 