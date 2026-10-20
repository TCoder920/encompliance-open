# Contributing to Encompliance.io

Thank you for your interest in contributing to Encompliance.io! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate when interacting with other contributors. We aim to maintain a positive and inclusive environment for everyone.

## Branching Strategy

We follow a feature-branch workflow:

1. **Main Branch**: `main` - The production-ready branch. Always stable and deployable.
2. **Development Branch**: `dev` - Integration branch for features and bug fixes.
3. **Feature Branches**: `feature/feature-name` - For developing new features.
4. **Bug Fix Branches**: `fix/bug-name` - For fixing bugs.
5. **Hotfix Branches**: `hotfix/issue-name` - For critical production fixes.

## Pull Request Process

1. Create a new branch from `dev` (or `main` for hotfixes).
2. Make your changes in the branch.
3. Ensure your code follows the project's style guidelines.
4. Run tests to make sure your changes don't break existing functionality.
5. Submit a pull request to the `dev` branch (or `main` for hotfixes).
6. Request a review from at least one maintainer.
7. Address any feedback or requested changes.
8. Once approved, your PR will be merged.

## Commit Message Guidelines

We follow conventional commits format to maintain a clear and traceable history:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Changes that don't affect code functionality (formatting, etc.)
- **refactor**: Code changes that neither fix bugs nor add features
- **test**: Adding or modifying tests
- **chore**: Changes to build process, tools, etc.

### Example
```
feat(auth): implement password reset functionality

- Add reset password endpoint
- Send reset email functionality
- Update user schema for reset token

Closes #123
```

## Testing Guidelines

- All new features should include appropriate tests.
- All bug fixes should include tests that reproduce the bug.
- Aim for high test coverage on critical components.
- Backend tests use pytest: `pytest`
- Frontend tests use Jest: `npm test`

## Code Style

### Backend (Python)
- Follow PEP 8 style guide
- Use Black for code formatting
- Use isort for import sorting
- Use Flake8 for linting

### Frontend (TypeScript/React)
- Follow ESLint configuration
- Use Prettier for code formatting
- Sort imports
- Prefer functional components with hooks

## Documentation

- Update documentation when changing functionality.
- Write clear, concise comments for complex code sections.
- Add JSDoc/docstring comments for functions/methods.

## Development Environment Setup

See the main [README.md](../README.md) for instructions on setting up your development environment.

## Questions?

If you have any questions or need help, please open an issue or contact the maintainers.

Thank you for contributing to Encompliance.io! 