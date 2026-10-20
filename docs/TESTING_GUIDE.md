# Testing Guide for EnCompliance Backend

This document provides guidelines for writing and running tests for the EnCompliance backend.

## Overview

The backend testing framework consists of:

- **pytest**: Main testing framework
- **pytest-cov**: For test coverage reporting
- **pytest-asyncio**: For testing asynchronous code
- **SQLAlchemy in-memory SQLite**: For database testing

## Test Types

1. **Unit Tests**: Test individual functions and methods in isolation
   - Located in `tests/unit/`
   - Example: `tests/unit/core/test_openai_utils.py`

2. **Integration Tests**: Test API endpoints and database interactions
   - Located in `tests/integration/`
   - Example: `tests/integration/api/test_me_endpoint.py`

## Running Tests

### Run all tests with coverage

```bash
python -m pytest
```

### Run specific test file

```bash
python -m pytest tests/unit/core/test_openai_utils.py
```

### Run tests with detailed output

```bash
python -m pytest -v
```

### Generate coverage report

```bash
python -m pytest --cov=app --cov-report=html
```

This creates an HTML report in `htmlcov/` directory.

## Test Configuration

- **pytest.ini**: Contains configuration for pytest and coverage thresholds
- **.coveragerc**: Defines which files to include/exclude from coverage reports

## Writing Tests

### Unit Tests

For function testing, follow this pattern:

```python
@pytest.mark.asyncio  # For async functions
async def test_function_name():
    # Arrange
    # Set up test data and dependencies
    
    # Act
    # Call the function under test
    
    # Assert
    # Verify the result
```

### API Tests

For API endpoint testing:

```python
def test_endpoint_name():
    # Arrange
    # Set up test data, authentication, etc.
    
    # Act
    # Make the API request
    response = client.get(
        "/api/v1/endpoint",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    # Check response status and data
    assert response.status_code == 200
    assert response.json()["key"] == expected_value
```

## Mocking

For external services like OpenAI:

```python
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = AsyncMock()
    # Configure mock responses
    return mock_client
```

## Coverage Requirements

The project aims for 90% code coverage. Currently, we're at 32% and need to improve coverage by writing more tests.

Priority areas for testing:
1. Core business logic in services
2. API endpoints
3. Authentication flows

## CI Integration

The test suite is integrated with CI, which will enforce the minimum coverage threshold defined in `pytest.ini`.

## Best Practices

1. Use descriptive test names that explain what is being tested
2. Keep tests independent and isolated
3. Use fixtures for shared setup
4. Mock external services
5. Test both success and failure cases
6. For sensitive operations, test edge cases thoroughly 