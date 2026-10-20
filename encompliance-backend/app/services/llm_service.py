"""
LLM Service Module

This module provides services for interacting with large language models (LLMs),
including OpenAI Assistants, in the EnCompliance application. It manages thread
mappings, user-specific assistants, and streaming LLM responses.

Key functionalities:
- LLM response generation and streaming
- OpenAI Assistants API integration
- User-specific assistant and vector store management
- Conversation and thread mapping
- User context integration (calendar events and notes)
- Error handling and logging for LLM operations

Dependencies:
- openai: For LLM and Assistants API
- sqlalchemy: For database operations
- httpx: For HTTP requests
- asyncio: For async operations
"""

import httpx
import json
import os
import asyncio
from typing import List, Optional, Dict, Any, AsyncGenerator, Union
from app.core.config import get_settings
from app.core.chat_utils import (
    format_chat_history
)
from app.core.openai_utils import get_user_assistant_id, get_or_create_user_vector_store
from app.services.context_service import ContextService
from sqlalchemy.orm import Session
import traceback
from openai import AsyncOpenAI
from app.models.user import User
from app.models.thread_map import ThreadMap
import logging
import openai
from openai import AssistantEventHandler
from typing_extensions import override
from sqlalchemy.sql import func

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Functions to manage thread mappings
async def get_thread_id_for_conversation(conversation_id: int, current_user_id: int, db: Session) -> Optional[str]:
    """
    Get the thread ID for a given conversation ID and user ID.
    
    Args:
        conversation_id: The conversation ID
        current_user_id: The user ID
        db: Database session
        
    Returns:
        The thread ID if found, None otherwise
    """
    try:
        thread_map = db.query(ThreadMap).filter(
            ThreadMap.conversation_id == conversation_id,
            ThreadMap.user_id == current_user_id
        ).first()
        
        if thread_map:
            return thread_map.thread_id
        return None
    except Exception as e:
        logger.error(f"Error getting thread ID for conversation {conversation_id}: {e}")
        return None

async def store_thread_mapping(conversation_id: int, thread_id: str, current_user_id: int, db: Session) -> None:
    """
    Store the mapping between conversation ID and thread ID.
    
    Args:
        conversation_id: The conversation ID
        thread_id: The thread ID
        current_user_id: The user ID
        db: Database session
    """
    try:
        # Check if mapping already exists
        existing = db.query(ThreadMap).filter(
            ThreadMap.conversation_id == conversation_id,
            ThreadMap.user_id == current_user_id
        ).first()
        
        if not existing:
            thread_map = ThreadMap(
                conversation_id=conversation_id,
                thread_id=thread_id,
                user_id=current_user_id
            )
            db.add(thread_map)
            db.commit()
            logger.info(f"Stored thread mapping: conversation {conversation_id} -> thread {thread_id}")
    except Exception as e:
        logger.error(f"Error storing thread mapping: {e}")
        db.rollback()

def get_model_by_mode(mode: str) -> str:
    """
    Get the OpenAI model ID based on the frontend mode selection.
    
    Args:
        mode: The mode ('basic' or 'pro')
        
    Returns:
        The OpenAI model ID
    """
    if mode == 'pro':
        return 'gpt-4.1-mini'  # Pro mode gets web search capabilities
    else:
        return 'gpt-4.1-nano'  # Basic mode without web search


async def handle_active_runs(thread_id: str):
    """
    Check for active runs on a thread and cancel them if necessary.
    This prevents the "Can't add messages while a run is active" error.
    """
    try:
        # List all runs for the thread
        runs = await openai_client.beta.threads.runs.list(thread_id=thread_id)
        
        for run in runs.data:
            if run.status in ["queued", "in_progress", "requires_action"]:
                logger.info(f"Found active run {run.id} with status {run.status} on thread {thread_id}, cancelling...")
                try:
                    cancelled_run = await openai_client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    logger.info(f"Successfully cancelled run {run.id}, new status: {cancelled_run.status}")
                except Exception as cancel_error:
                    logger.warning(f"Failed to cancel run {run.id}: {str(cancel_error)}")
                    # Continue with other runs even if one fails to cancel
        
    except Exception as e:
        logger.error(f"Error checking/cancelling active runs for thread {thread_id}: {str(e)}")
        raise


async def get_llm_response(
    prompt: str,
    operation_type: str,
    message_history: List[Dict[str, str]] = None,
    document_ids: Optional[List[int]] = None,
    model: str = None,
    db: Optional[Session] = None,
    current_user_id: Optional[int] = None,
    stream: bool = True,
    provider: Optional[str] = None,  # Ignored, kept for backward compatibility
    api_key: Optional[str] = None,   # Ignored, using settings key
    conversation_id: Optional[int] = None
) -> Union[str, AsyncGenerator[str, None]]:
    """
    Get a response from an LLM using the OpenAI Assistants API.
    Uses a user-specific assistant if current_user_id is provided.
    Includes user context (calendar events and notes) for personalized responses.

    Args:
        prompt: The user's query
        operation_type: The type of operation (daycare, residential, etc.)
        message_history: Previous messages in the conversation
        document_ids: IDs of documents to reference (Currently unused with Assistants API)
        model: The LLM model mode to use ('basic' or 'pro') (Currently unused with Assistants API)
        db: Database session (required if current_user_id provided)
        current_user_id: ID of the current user (for user-specific assistant/vector store)
        stream: Whether to stream the response
        provider: Ignored, kept for backward compatibility
        api_key: Ignored, using key from settings
        conversation_id: ID of the conversation for thread management

    Returns:
        The LLM's response as a string or an async generator of response chunks if streaming
    """
    try:
        # Check for OpenAI API key
        if not settings.OPENAI_API_KEY:
            error_msg = "OpenAI API key is not configured in settings or environment variables."
            logger.error(error_msg)
            if stream:
                async def stream_error():
                    yield f"[Error: {error_msg}]"
                return stream_error()
            else:
                return get_error_response(error_msg)
        
        # --- User Context Gathering ---
        user_context = ""
        if current_user_id and db:
            try:
                # Get user information for context gathering
                user = db.query(User).filter(User.id == current_user_id).first()
                if user:
                    # Fetch user context (calendar events and notes)
                    user_context = await ContextService.get_full_user_context(
                        db=db,
                        user_id=current_user_id,
                        user_subscription_status=user.subscription_status
                    )
                    logger.info(f"Retrieved user context for user {current_user_id}: {len(user_context)} characters")
            except Exception as e:
                logger.warning(f"Error fetching user context for user {current_user_id}: {e}")
                # Continue without context rather than failing
        
        # --- User-Specific Assistant and Vector Store Handling ---
        user_assistant_id = None
        user_vs_id = None
        tool_resources = None

        if current_user_id and db:
            try:
                # Get existing assistant ID (no creation/update during chat)
                user_assistant_id = await get_user_assistant_id(current_user_id, db)
                
                if not user_assistant_id:
                    error_msg = f"No assistant found for user {current_user_id}. Assistant should be created during registration."
                    logger.error(error_msg)
                    if stream:
                        async def stream_error():
                            yield f"[Error: {error_msg}]"
                        return stream_error()
                    else:
                        return get_error_response(error_msg)
                
                logger.info(f"Using existing Assistant ID: {user_assistant_id} for user {current_user_id}")

                # Get user's vector store ID
                user = db.query(User).filter(User.id == current_user_id).first()
                if user and user.openai_vector_store_id:
                    user_vs_id = user.openai_vector_store_id
                    logger.info(f"Found Vector Store ID for user {current_user_id}: {user_vs_id}")
                    # Prepare tool_resources for the run, ensuring the user's VS is used
                    tool_resources = {
                        "file_search": {
                            "vector_store_ids": [user_vs_id]
                        }
                    }
                    logger.info(f"Configured tool_resources for run using Vector Store {user_vs_id}")
                else:
                    logger.warning(f"No Vector Store ID found for user {current_user_id}, file_search might be limited.")

            except Exception as e:
                error_msg = f"Error getting assistant for user {current_user_id}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                if stream:
                    async def stream_error():
                        yield f"[Error: {error_msg}]"
                    return stream_error()
                else:
                    return get_error_response(error_msg)
        else:
            # Fallback or specific logic if no user context
            logger.warning("No current_user_id provided. Using global assistant if configured, or failing.")
            # Use the global assistant ID from settings ONLY IF no user is specified
            if settings.OPENAI_ASSISTANT_ID:
                 user_assistant_id = settings.OPENAI_ASSISTANT_ID
                 logger.info(f"Using global Assistant ID: {user_assistant_id}")
                 # Note: Cannot use file_search effectively without a user vector store
            else:
                 error_msg = "No current_user_id provided and no global OPENAI_ASSISTANT_ID configured."
                 logger.error(error_msg)
                 if stream:
                     async def stream_error():
                         yield f"[Error: {error_msg}]"
                     return stream_error()
                 else:
                     return get_error_response(error_msg)
        # --- End User-Specific Handling ---

        # Thread Management
        thread_id = None
        new_thread_created = False # Flag to track if we created a new thread

        # Check if we have both conversation_id and current_user_id for thread lookup
        if conversation_id and current_user_id and db:
            # Look up thread_id from the database by conversation_id and user_id
            thread_id = await get_thread_id_for_conversation(conversation_id, current_user_id, db)
            
            if thread_id:
                logger.info(f"Found existing thread ID {thread_id} for conversation {conversation_id}")
                
                # Verify the thread still exists in OpenAI
                try:
                    await openai_client.beta.threads.retrieve(thread_id)
                    logger.info(f"Verified thread {thread_id} exists in OpenAI")
                except Exception as e:
                    logger.warning(f"Thread {thread_id} not found in OpenAI despite being in our database. Will create a new one. Error: {e}")
                    thread_id = None

        # Create a new thread if needed
        if not thread_id:
            try:
                thread_create_params = {}
                # Add tool_resources during thread creation if available
                if tool_resources:
                    thread_create_params["tool_resources"] = tool_resources
                    logger.info(f"Passing tool_resources to new thread creation: {tool_resources}")

                thread = await openai_client.beta.threads.create(**thread_create_params)
                thread_id = thread.id
                new_thread_created = True
                logger.info(f"Created new thread: {thread_id}")
                
                # Store the mapping between conversation_id and thread_id
                if conversation_id and current_user_id and db:
                    await store_thread_mapping(conversation_id, thread_id, current_user_id, db)
            except Exception as e:
                error_msg = f"Error creating thread: {str(e)}"
                logger.error(error_msg, exc_info=True)
                if stream:
                    async def stream_error():
                        yield f"[Error: {error_msg}]"
                    return stream_error()
                else:
                    return get_error_response(error_msg)

        # If thread already existed and we have tool_resources, update the thread
        elif not new_thread_created and tool_resources:
            try:
                 logger.info(f"Updating existing thread {thread_id} with tool_resources: {tool_resources}")
                 await openai_client.beta.threads.update(
                     thread_id=thread_id,
                     tool_resources=tool_resources
                 )
                 logger.info(f"Successfully updated tool_resources for thread {thread_id}")
            except Exception as e:
                 # Log error but continue, maybe the thread update isn't critical or fails rarely
                 logger.error(f"Error updating tool_resources for existing thread {thread_id}: {str(e)}", exc_info=True)


        # Check for and handle any active runs on the thread before adding messages
        try:
            await handle_active_runs(thread_id)
        except Exception as e:
            logger.warning(f"Warning handling active runs for thread {thread_id}: {str(e)}")
            # Continue anyway, the message creation will fail with a clearer error if needed

        # Add the user's message to the thread
        try:
            message = await openai_client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )
            logger.info(f"Added user message {message.id} to thread: {thread_id}")
            user_message_id = message.id
        except Exception as e:
            error_msg = f"Error adding message to thread: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if stream:
                async def stream_error():
                    yield f"[Error: {error_msg}]"
                return stream_error()
            else:
                return get_error_response(error_msg)
        
        # Prepare additional instructions that include user context
        additional_instructions = ""
        if user_context and user_context.strip():
            from datetime import datetime
            # Add current date/time context
            current_datetime = datetime.now()
            current_date_str = current_datetime.strftime("%A, %B %d, %Y")
            current_time_str = current_datetime.strftime("%I:%M %p")
            
            additional_instructions = f"""

=== CURRENT DATE AND TIME ===
Current Date: {current_date_str}
Current Time: {current_time_str}

=== USER PERSONAL CONTEXT ===
{user_context}

IMPORTANT: Use the above personal context to provide more relevant and personalized responses. 
When the user asks about their schedule, meetings, notes, training, or related topics, reference this information directly.
This context is provided dynamically for each conversation and should take priority for personalized queries.
"""
        
        # Prepare arguments for run creation
        run_args = {
            "thread_id": thread_id,
            "assistant_id": user_assistant_id
        }
        
        # Add additional instructions if we have user context
        if additional_instructions:
            run_args["additional_instructions"] = additional_instructions
            logger.info(f"Including user context in run instructions for user {current_user_id}")
        else:
            logger.info(f"No user context available for user {current_user_id}")
            # Note: No additional instructions - let the assistant use its built-in instructions only
        
        # Handle streaming or non-streaming
        if stream:
            logger.info(f"Initiating streaming run for thread {thread_id} with assistant {user_assistant_id}")

            # Define the event handler inline or use a class if more complex handling is needed
            async def stream_run() -> AsyncGenerator[str, None]:
                try:
                    # Use the context manager for the stream with run_args (includes additional_instructions if available)
                    stream_params = {
                        "thread_id": thread_id,
                        "assistant_id": user_assistant_id
                    }
                    # Add additional instructions if they exist
                    if "additional_instructions" in run_args:
                        stream_params["additional_instructions"] = run_args["additional_instructions"]
                    
                    async with openai_client.beta.threads.runs.stream(**stream_params) as stream_handler:
                        async for event in stream_handler:
                            # Log all events for debugging
                            logger.debug(f"Received event: {event.event}")
                            
                            if event.event == 'thread.message.delta':
                                delta = event.data.delta
                                if delta.content:
                                    for content_part in delta.content:
                                        if content_part.type == 'text' and content_part.text:
                                            # Split the chunk into individual characters and yield each one separately
                                            for char in content_part.text.value:
                                                logger.debug(f"Streaming token: {char}")
                                                # Yield individual characters for true token-by-token display
                                                yield char
                                                # Small delay to ensure proper streaming rhythm
                                                await asyncio.sleep(0)
                            elif event.event == 'thread.run.requires_action':
                                # Handle function calls (like web search)
                                run_data = event.data
                                if run_data.required_action and run_data.required_action.type == "submit_tool_outputs":
                                    tool_outputs = []
                                    for tool_call in run_data.required_action.submit_tool_outputs.tool_calls:
                                        if tool_call.function.name == "web_search":
                                            try:
                                                # Parse function arguments
                                                import json
                                                args = json.loads(tool_call.function.arguments)
                                                query = args.get("query", "")
                                                count = args.get("count", 3)  # Reduced default for performance
                                                
                                                # Perform enhanced web search with actual content
                                                from app.services.web_search_service import enhanced_web_search, format_enhanced_search_results
                                                search_results = await enhanced_web_search(query, count)
                                                
                                                # Format search results for the assistant
                                                formatted_results = format_enhanced_search_results(search_results)
                                                
                                                # Add explicit reminder to include search results in response
                                                reminder = "\n\nREMINDER: You MUST include these search results at the end of your response in the exact format specified in your instructions. Copy the titles, URLs, and descriptions exactly as shown above."
                                                
                                                tool_outputs.append({
                                                    "tool_call_id": tool_call.id,
                                                    "output": formatted_results + reminder
                                                })
                                                
                                                logger.info(f"Performed enhanced web search for: {query}")
                                                
                                            except Exception as e:
                                                logger.error(f"Error in enhanced web search: {str(e)}")
                                                tool_outputs.append({
                                                    "tool_call_id": tool_call.id,
                                                    "output": f"Error performing web search: {str(e)}"
                                                })
                                    
                                    # Submit tool outputs to continue the run
                                    if tool_outputs:
                                        logger.info(f"Submitting tool outputs for run {run_data.id}")
                                        await openai_client.beta.threads.runs.submit_tool_outputs(
                                            thread_id=thread_id,
                                            run_id=run_data.id,
                                            tool_outputs=tool_outputs
                                        )
                                        logger.info(f"Tool outputs submitted successfully for run {run_data.id}")
                                        
                                        # After submitting tool outputs, we need to manually continue polling for the response
                                        # since the streaming context manager doesn't handle this automatically
                                        await asyncio.sleep(1)  # Brief pause to let the run process
                                        
                                        # Poll for the run completion and stream the assistant's response
                                        while True:
                                            run_status = await openai_client.beta.threads.runs.retrieve(
                                                thread_id=thread_id,
                                                run_id=run_data.id
                                            )
                                            
                                            if run_status.status == "completed":
                                                # Get the assistant's final message
                                                messages = await openai_client.beta.threads.messages.list(
                                                    thread_id=thread_id,
                                                    after=user_message_id,
                                                    order="asc"
                                                )
                                                
                                                # Stream the assistant's response
                                                for message in messages.data:
                                                    if message.role == "assistant":
                                                        for content_part in message.content:
                                                            if content_part.type == "text":
                                                                # Yield the response character by character for streaming effect
                                                                for char in content_part.text.value:
                                                                    yield char
                                                                    await asyncio.sleep(0.01)  # Small delay for streaming effect
                                                break
                                            elif run_status.status == "failed":
                                                yield f"[Error: Run failed - {run_status.last_error}]"
                                                break
                                            elif run_status.status == "expired":
                                                yield f"[Error: Run expired]"
                                                break
                                            else:
                                                # Continue polling
                                                await asyncio.sleep(1)
                            elif event.event == 'thread.run.failed':
                                run_data = event.data
                                error_msg = f"Run failed: {run_data.last_error.code} - {run_data.last_error.message}"
                                logger.error(error_msg)
                                yield f"[Error: {error_msg}]"
                                break # Exit the loop on failure
                            elif event.event == 'thread.run.cancelled':
                                logger.warning(f"Run cancelled: {event.data.id}")
                                yield "[Run Cancelled]"
                                break
                            elif event.event == 'thread.run.expired':
                                logger.error(f"Run expired: {event.data.id}")
                                yield "[Run Expired]"
                                break
                            elif event.event == 'thread.run.completed':
                                logger.info(f"Run completed: {event.data.id}")
                                # The run is complete, the stream should end naturally
                            elif event.event == 'thread.run.step.completed':
                                logger.debug(f"Run step completed: {event.data.id}")
                            # Add handling for other event types if needed

                        # You might want to retrieve the final run status after the stream for logging
                        final_run = await stream_handler.get_final_run()
                        logger.info(f"Streaming run {final_run.id} completed with status: {final_run.status}")

                except Exception as e:
                    error_msg = f"Error during streaming run: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    yield f"[Error: {error_msg}]"

            return stream_run() # Return the async generator

        else: # Non-streaming case
            logger.info(f"Initiating non-streaming run for thread {thread_id} with assistant {user_assistant_id}")
            try:
                # Create run without streaming
                run = await openai_client.beta.threads.runs.create(**run_args)
                logger.info(f"Created non-streaming run {run.id}")
                # Poll until completion (using the existing function)
                # Pass the user_message_id if get_assistant_response still needs it
                return await get_assistant_response(thread_id, run.id, user_message_id)
            except Exception as e:
                 error_msg = f"Error creating non-streaming run: {str(e)}"
                 logger.error(error_msg, exc_info=True)
                 return get_error_response(error_msg)
            
    except Exception as e:
        error_msg = f"Error getting LLM response: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        if stream:
            async def stream_error():
                yield f"[Error: {error_msg}]"
            return stream_error()
        else:
            return get_error_response(error_msg)

async def get_assistant_response(thread_id: str, run_id: str, last_user_message_id: str) -> str:
    """
    Poll for the completion of a run and return the assistant's response.
    
    Args:
        thread_id: The thread ID
        run_id: The run ID
        last_user_message_id: The ID of the last message added by the user before the run.
        
    Returns:
        The assistant's response as a string
    """
    try:
        # Poll for run completion
        while True:
            run = await openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status == "completed":
                print(f"Run completed: {run_id}")
                break
            elif run.status == "requires_action":
                # Handle function calls
                if run.required_action and run.required_action.type == "submit_tool_outputs":
                    tool_outputs = []
                    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                        if tool_call.function.name == "web_search":
                            try:
                                # Parse function arguments
                                import json
                                args = json.loads(tool_call.function.arguments)
                                query = args.get("query", "")
                                count = args.get("count", 3)  # Reduced default for performance
                                
                                # Perform enhanced web search with actual content
                                from app.services.web_search_service import enhanced_web_search, format_enhanced_search_results
                                search_results = await enhanced_web_search(query, count)
                                
                                # Format search results for the assistant
                                formatted_results = format_enhanced_search_results(search_results)
                                
                                # Add explicit reminder to include search results in response
                                reminder = "\n\nREMINDER: You MUST include these search results at the end of your response in the exact format specified in your instructions. Copy the titles, URLs, and descriptions exactly as shown above."
                                
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": formatted_results + reminder
                                })
                                
                                logger.info(f"Performed enhanced web search for: {query}")
                                
                            except Exception as e:
                                logger.error(f"Error in enhanced web search: {str(e)}")
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": f"Error performing web search: {str(e)}"
                                })
                    
                    # Submit tool outputs to continue the run
                    if tool_outputs:
                        await openai_client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread_id,
                            run_id=run_id,
                            tool_outputs=tool_outputs
                        )
            elif run.status in ["failed", "cancelled", "expired"]:
                error_msg = f"Run {run_id} {run.status}: {run.last_error}"
                print(error_msg)
                return get_error_response(error_msg)
            
            # Wait before polling again
            await asyncio.sleep(1)
        
        # Get messages from the thread added after the user's last message
        messages = await openai_client.beta.threads.messages.list(
            thread_id=thread_id,
            order="asc",
            after=last_user_message_id # Use the user message ID here
        )
        
        # Extract content from assistant messages
        response_text = ""
        for message in messages.data:
            if message.role == "assistant":
                for content in message.content:
                    if content.type == "text":
                        response_text += content.text.value + "\n"
        
        return response_text.strip()
    except Exception as e:
        error_msg = f"Error getting assistant response: {str(e)}"
        print(error_msg)
        print(f"Traceback: {traceback.format_exc()}")
        return get_error_response(error_msg)

def get_error_response(error_msg: str) -> str:
    """Return a formatted error response"""
    return f"I apologize, but I encountered an error while processing your request: {error_msg}"

def format_search_results(search_results: dict) -> str:
    """
    Format Brave search results for the assistant.
    
    Args:
        search_results: Raw search results from Brave API
        
    Returns:
        Formatted string with search results
    """
    try:
        if not search_results or 'web' not in search_results:
            return "No search results found."
        
        web_results = search_results['web']
        if not web_results or 'results' not in web_results:
            return "No web results found."
        
        results = web_results['results']
        if not results:
            return "No search results found."
        
        formatted = "Web Search Results:\n\n"
        
        for i, result in enumerate(results[:5], 1):  # Limit to top 5 results
            title = result.get('title', 'No title')
            url = result.get('url', '')
            description = result.get('description', 'No description available')
            
            formatted += f"{i}. **{title}**\n"
            formatted += f"   URL: {url}\n"
            formatted += f"   {description}\n\n"
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting search results: {str(e)}")
        return f"Error formatting search results: {str(e)}"