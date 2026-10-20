# CI Pipeline Documentation

## Overview

The EnCompliance project uses GitHub Actions for continuous integration to ensure code quality, test coverage, and security. This document explains how the CI pipeline works and how to interact with it.

## Workflow Structure

Our CI pipeline is defined in `.github/workflows/ci.yml` and consists of two primary jobs:

1. **Frontend CI**: Validates the React frontend code
2. **Backend CI**: Validates the FastAPI backend code

## What the CI Pipeline Checks

### Frontend CI

- **Linting**: Ensures code follows the ESLint rules
- **Unit Tests**: Runs Jest tests including accessibility checks
- **Build**: Verifies the application builds successfully
- **Vulnerability Scan**: Identifies security vulnerabilities in dependencies

### Backend CI

- **Linting**: Runs Flake8 to catch Python syntax and style issues
- **Code Formatting**: Uses Black to verify consistent code formatting
- **Import Ordering**: Uses isort to check import ordering
- **Unit & Integration Tests**: Runs pytest with coverage requirements (90%)
- **Vulnerability Scan**: Uses pip-audit to identify security vulnerabilities

## How to Work with the CI Pipeline

### Local Development

Before pushing changes, it's recommended to run the same checks locally:

**Frontend:**
```bash
cd encompliance-frontend
npm run lint
npm test
npm run build
npm audit
```

**Backend:**
```bash
cd encompliance-backend
flake8 .
black --check .
isort --check-only --profile black .
pytest
pip-audit
```

### Pull Requests

1. The CI pipeline runs automatically on all pull requests targeting the `main` branch
2. All checks must pass before merging is allowed
3. Any failed checks will be reported in the PR with details about the failure

### Branch Protection

The repository has branch protection rules configured for the `main` branch:

- All CI checks must pass before merging
- At least one approval is required for each PR
- Conversations must be resolved before merging
- Linear history is enforced (no merge commits)

## Troubleshooting Common Issues

### Frontend CI Failures

- **Lint Errors**: Run `npm run lint` locally to identify and fix issues
- **Test Failures**: Run `npm test` locally to debug failing tests
- **Build Failures**: Check for correct imports and component usage

### Backend CI Failures

- **Lint Errors**: Run `flake8 .` locally to identify issues
- **Black Formatting**: Run `black .` to automatically fix formatting
- **Import Order**: Run `isort .` to automatically fix import order
- **Test Failures**: Run `pytest -v` to see detailed test output

## Adding New Checks

To add new checks to the CI pipeline:

1. Update the `.github/workflows/ci.yml` file
2. Test the changes on a feature branch
3. Update this documentation to reflect the new checks

## Setting Up Branch Protection

We've provided a script to help set up branch protection rules using the GitHub CLI:

```bash
# Make the script executable
chmod +x .github/setup-branch-protection.sh

# Run the script with your GitHub owner and repo name
.github/setup-branch-protection.sh <owner> <repo>
```

The script will configure the following rules for the `main` branch:
- Required status checks (CI pipeline must pass)
- At least one approving review required
- No force pushes or deletions allowed
- Pull request conversations must be resolved before merging
- Linear history required (no merge commits)

Alternatively, you can manually configure these settings in the GitHub repository settings:
1. Navigate to the repository on GitHub
2. Go to Settings > Branches
3. Click "Add rule" next to "Branch protection rules"
4. Configure the rules as documented in `.github/branch-protection.yml`

## CI Pipeline Metrics

- **Average Run Time**: ~5-8 minutes
- **Coverage Requirements**: 90% code coverage minimum
- **Required Checks**: All checks must pass for merge 