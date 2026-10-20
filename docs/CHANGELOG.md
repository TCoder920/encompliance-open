# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **AI Assistant Date/Time Context**: AI assistant now has access to real-time date and time information for temporal awareness
  - Current date, time, and multiple time formats included in system context
  - Enables accurate responses to time-sensitive queries ("today", "this week", "next Monday")
  - Supports relative date calculations and scheduling assistance
  - Comprehensive test coverage for date/time functionality
  - Documentation in `docs/AI_DATETIME_CONTEXT.md`

## [1.0.0] - 2024-08-15

### Added
- Semantic release integration for automated versioning and changelog generation
- GitHub Actions workflow for releases

### Improved
- Project structure and organization
- Development environment setup
- Documentation with updated README and contribution guides
- Frontend dependencies upgraded and pinned
- Backend dependencies upgraded and pinned
- Code linting and formatting tools
- Testing infrastructure for both frontend and backend
- Accessibility compliance
- Docker containerization
- CI/CD pipeline configuration

### Security
- Fixed critical vulnerabilities in dependencies
- Added security headers and best practices
- OWASP Top 10 protections implemented 