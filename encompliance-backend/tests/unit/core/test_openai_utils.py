import pytest
from unittest.mock import AsyncMock, patch
import logging

from app.core.openai_utils import get_or_create_user_vector_store


@pytest.mark.asyncio
async def test_get_existing_user_vector_store(db_session, test_user, mock_openai_client):
    """Test that the function returns the existing vector store ID for a user who already has one."""
    # Setup test user with an existing vector store ID
    vector_store_id = "existing-vector-store-id"
    test_user.openai_vector_store_id = vector_store_id
    db_session.commit()
    
    # Call the function
    result = await get_or_create_user_vector_store(test_user.id, db_session, mock_openai_client)
    
    # Verify the function returned the existing vector store ID
    assert result == vector_store_id
    # Assert the OpenAI client was not called to create a new vector store
    mock_openai_client.beta.vector_stores.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_new_user_vector_store(db_session, test_user, mock_openai_client):
    """Test that the function creates a new vector store for a user who doesn't have one."""
    # Ensure the test user doesn't have a vector store ID
    test_user.openai_vector_store_id = None
    db_session.commit()
    
    # Expected new vector store ID from the mock
    expected_vector_store_id = "mock-vector-store-id"
    
    # Call the function
    result = await get_or_create_user_vector_store(test_user.id, db_session, mock_openai_client)
    
    # Verify the function returned the new vector store ID
    assert result == expected_vector_store_id
    # Assert the OpenAI client was called to create a new vector store
    mock_openai_client.beta.vector_stores.create.assert_called_once()
    # Assert the user's vector store ID was updated in the database
    db_session.refresh(test_user)
    assert test_user.openai_vector_store_id == expected_vector_store_id


@pytest.mark.asyncio
async def test_user_not_found(db_session, mock_openai_client):
    """Test that the function raises an error when the user is not found."""
    # Call the function with a non-existent user ID
    non_existent_user_id = 9999
    
    # The function should raise ValueError
    with pytest.raises(ValueError, match=f"User with ID {non_existent_user_id} not found"):
        await get_or_create_user_vector_store(non_existent_user_id, db_session, mock_openai_client)


@pytest.mark.asyncio
async def test_vector_store_creation_fails(db_session, test_user, mock_openai_client):
    """Test that the function handles API errors when creating a vector store."""
    # Setup test user without a vector store ID
    test_user.openai_vector_store_id = None
    db_session.commit()
    
    # Set up the mock to simulate an API error
    mock_openai_client.beta.vector_stores.create.side_effect = Exception("API Error")
    
    # The function should propagate the exception
    with pytest.raises(Exception, match="API Error"):
        await get_or_create_user_vector_store(test_user.id, db_session, mock_openai_client)
    
    # Assert the user's vector store ID wasn't updated
    db_session.refresh(test_user)
    assert test_user.openai_vector_store_id is None


@pytest.mark.asyncio
async def test_logging(db_session, test_user, mock_openai_client, caplog):
    """Test that the function logs appropriate messages."""
    # Setup test user without a vector store ID
    test_user.openai_vector_store_id = None
    db_session.commit()
    
    # Set up logging capture
    caplog.set_level(logging.INFO)
    
    # Call the function
    await get_or_create_user_vector_store(test_user.id, db_session, mock_openai_client)
    
    # Verify the appropriate log messages were recorded
    assert f"Creating new Vector Store for user {test_user.id}" in caplog.text
    assert f"Created Vector Store for user {test_user.id}" in caplog.text 