"""
Chat Functionality Routes
-----------------------
This module defines the chat-related API endpoints for the EnCompliance system.
It provides:
- Real-time chat functionality
- Message history
- Chat room management
- User presence tracking
- Message notifications
- Chat analytics
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from app.services.llm_service import get_llm_response, get_error_response, get_model_by_mode
from app.core.config import get_settings
from app.database import get_db
from app.models.query_log import QueryLog
from app.auth.dependencies import get_current_user, User
from fastapi.responses import JSONResponse, StreamingResponse

from app.utils.tiers import PRO, get_tier_from_subscription_status
import traceback
import datetime
from sqlalchemy import func
import json
import asyncio
from ipaddress import ip_address as ip_parse

router = APIRouter(tags=["chat"])

# Add OPTIONS handler for CORS preflight requests
@router.options("/chat")
async def options_chat():
    """
    Handle OPTIONS requests for chat endpoints.
    """
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:5174",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={}, headers=headers)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    prompt: str
    operation_type: str = "daycare"
    message_history: Optional[List[Dict[str, str]]] = None
    model: Optional[str] = None  # 'basic' or 'pro'
    stream: Optional[bool] = False  # Default to non-streaming to avoid JSON serialization issues
    provider: Optional[str] = "auto"  # Provider selection (auto, openai, anthropic, google)
    api_key: Optional[str] = None # Added api_key field
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    text: str
    error: Optional[str] = None
    thread_id: Optional[str] = None  # Add thread_id to response

class QueryLimitResponse(BaseModel):
    used: int
    limit: int
    subscription_status: str
    reset_time: Optional[str] = None

class ChatHistoryRequest(BaseModel):
    user_message: str
    ai_response: str
    operation_type: str
    conversation_id: Optional[int] = None

@router.get("/chat/query-usage", response_model=QueryLimitResponse)
async def get_query_usage(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the current user's query usage stats.
    Returns the number of queries used in the last 24 hours and the user's limit.
    """
    try:
        # Determine query limit based on subscription status
        subscription_status = current_user.subscription_status or "free"
        
        # Define query limits based on subscription
        if subscription_status == "enterprise":
            limit = float('inf')  # Unlimited
        elif subscription_status == "pro":
            limit = 150
        else:  # Free tier
            limit = 25
            
        # Get queries in the last 24 hours
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        query_logs = db.query(QueryLog).filter(
            QueryLog.user_id == current_user.id,
            QueryLog.created_at >= one_day_ago
        ).order_by(QueryLog.created_at.asc()).all()
        
        query_count = len(query_logs)
        
        # Calculate reset time if there are queries
        reset_time_str = None
        if query_count > 0:
            # The oldest query will be the first to expire
            oldest_query = query_logs[0]
            reset_time = oldest_query.created_at + datetime.timedelta(days=1)
            reset_time_str = reset_time.strftime("%Y-%m-%dT%H:%M:%S") # ISO format for frontend
        
        return {
            "used": query_count,
            "limit": -1 if limit == float('inf') else limit,  # -1 indicates unlimited
            "subscription_status": subscription_status,
            "reset_time": reset_time_str
        }
    except Exception as e:
        print(f"Error getting query usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get query usage: {str(e)}"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    fastapi_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a chat request and return a response from the LLM.
    If streaming is requested, returns a StreamingResponse.
    """
    # Check user's tier against requested mode
    if request.model == "pro": # request.model contains 'basic' or 'pro'
        user_tier = get_tier_from_subscription_status(current_user.subscription_status)
        if user_tier < PRO:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Pro mode is only available to Pro subscribers."
            )

    # Check query limits for non-enterprise users
    if current_user.subscription_status != "enterprise":
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        query_count = db.query(QueryLog).filter(
            QueryLog.user_id == current_user.id,
            QueryLog.created_at >= one_day_ago
        ).count()
        
        # Define limit based on subscription
        limit = 150 if current_user.subscription_status == "pro" else 25
        
        # Return error if limit exceeded
        if query_count >= limit:
            # Find the oldest query in the past 24 hours to calculate reset time
            oldest_query = db.query(QueryLog).filter(
                QueryLog.user_id == current_user.id,
                QueryLog.created_at >= one_day_ago
            ).order_by(QueryLog.created_at.asc()).first()
            
            # Calculate when the limit will reset
            reset_time = oldest_query.created_at + datetime.timedelta(days=1)
            reset_time_str = reset_time.strftime("%Y-%m-%dT%H:%M:%S") # ISO format for frontend
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "text": "",
                    "error": f"You have reached your daily limit. You can start using your assistant again at {reset_time_str}.",
                    "reset_time": reset_time_str
                }
            )
    
    # If streaming is requested, redirect to the streaming endpoint
    if request.stream:
        return await stream_chat(request, fastapi_request, db, current_user)
        
    try:
        # Convert message_history to the expected format if needed
        message_history = request.message_history or []
        
        # Initialize conversation_id_to_log to avoid UnboundLocalError if logging fails
        conversation_id_to_log = request.conversation_id
        
        # Print debug information
        print(f"Chat request: prompt={request.prompt[:50]}..., operation_type={request.operation_type}, model={request.model}")
        print(f"User ID: {current_user.id}")
        
        # Get response from LLM
        response_text = await get_llm_response(
            prompt=request.prompt,
            operation_type=request.operation_type,
            message_history=message_history,
            model=request.model,
            db=db,
            current_user_id=current_user.id,
            stream=False,  # Non-streaming for regular endpoint
            provider=request.provider,
            api_key=request.api_key,
            conversation_id=conversation_id_to_log
        )
        
        # Ensure response is a string (handle case where async generator is returned)
        if hasattr(response_text, '__aiter__'):
            # If an async generator was returned despite stream=False, convert it to string
            collected_response = ""
            async for chunk in response_text:
                collected_response += chunk
            response_text = collected_response
        
        # Log the query
        try:
            # Check if this is a duplicate query (same user, same prompt, within last minute)
            recent_time = func.now() - datetime.timedelta(minutes=1)
            
            # Build query filter conditions
            filter_conditions = [
                QueryLog.user_id == current_user.id,
                QueryLog.query == request.prompt,
                QueryLog.created_at > recent_time
            ]
            
            # Only add conversation_id filter if one was provided in the request
            if request.conversation_id:
                filter_conditions.append(QueryLog.conversation_id == request.conversation_id)
            
            existing_log = db.query(QueryLog).filter(*filter_conditions).first()
            
            if existing_log:
                print(f"Duplicate query detected, skipping log creation. Existing log ID: {existing_log.id}")
            else:
                # --- MODIFIED Conversation ID Logic --- 
                conversation_id_to_log = request.conversation_id # Prioritize ID from request
                if not conversation_id_to_log:
                    # Generate a new ID only if none provided
                    conversation_id_to_log = int(datetime.datetime.now().timestamp())
                    print(f"No conversation_id provided, generated new one: {conversation_id_to_log}")
                else:
                    print(f"Using provided conversation_id: {conversation_id_to_log}")
                # --- END MODIFICATION ---
                
                # Determine user IP (public only)
                user_ip = None
                client_host = fastapi_request.client.host
                if client_host:
                    try:
                        parsed = ip_parse(str(client_host))
                        if not parsed.is_private:
                            user_ip = str(client_host)
                    except ValueError:
                        pass # Ignore if not a valid IP
                
                # Ensure response is a string for database logging
                response_for_log = response_text
                if hasattr(response_text, '__aiter__'):
                    response_for_log = "<async_generator>"  # Placeholder for async generators
                elif not isinstance(response_text, str):
                    response_for_log = str(response_text)
                
                query_log = QueryLog(
                    user_id=current_user.id,
                    query=request.prompt,
                    response=response_for_log,
                    operation_type=request.operation_type,
                    conversation_id=conversation_id_to_log,
                    created_at=datetime.datetime.now(),
                    ip_address=user_ip
                )
                db.add(query_log)
                db.commit()
                db.refresh(query_log)
                print(f"Query log created with ID: {query_log.id}, conversation_id: {query_log.conversation_id}")
        except Exception as log_error:
            print(f"Error logging query: {str(log_error)}")
            # Continue even if logging fails
        
        # Return response with conversation ID header if available
        response_headers = {}
        if conversation_id_to_log:
            response_headers["X-Conversation-Id"] = str(conversation_id_to_log)
            # Expose the header for CORS
            response_headers["Access-Control-Expose-Headers"] = "X-Conversation-Id"
        
        # Get the thread_id associated with this conversation_id if available
        thread_id = None
        try:
            from app.models.thread_map import ThreadMap
            thread_map = db.query(ThreadMap).filter(
                ThreadMap.conversation_id == conversation_id_to_log,
                ThreadMap.user_id == current_user.id
            ).first()
            
            if thread_map:
                thread_id = thread_map.thread_id
                print(f"Found thread_id {thread_id} for conversation_id {conversation_id_to_log}")
        except Exception as thread_map_error:
            print(f"Error retrieving thread_id for conversation: {str(thread_map_error)}")
        
        # Ensure response_text is a string before creating JSONResponse
        if not isinstance(response_text, str):
            response_text = str(response_text)
            
        return JSONResponse(
            content={
                "text": response_text,
                "thread_id": thread_id
            }, 
            headers=response_headers
        )
    except Exception as e:
        print(f"Error processing chat request: {str(e)}")
        print(traceback.format_exc())
        # Return an empty string with the error in the error field
        return {"text": "", "error": str(e)}

@router.post("/chat/stream", response_class=StreamingResponse)
async def stream_chat(
    request: ChatRequest,
    fastapi_request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process a chat request and return a streaming response from the LLM.
    This endpoint streams the response as it's generated by the model.
    """
    # Check query limits for non-enterprise users
    if current_user.subscription_status != "enterprise":
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        query_count = db.query(QueryLog).filter(
            QueryLog.user_id == current_user.id,
            QueryLog.created_at >= one_day_ago
        ).count()
        
        # Define limit based on subscription
        limit = 150 if current_user.subscription_status == "pro" else 25
        
        # Return error if limit exceeded
        if query_count >= limit:
            # Find the oldest query in the past 24 hours to calculate reset time
            oldest_query = db.query(QueryLog).filter(
                QueryLog.user_id == current_user.id,
                QueryLog.created_at >= one_day_ago
            ).order_by(QueryLog.created_at.asc()).first()
            
            # Calculate when the limit will reset
            reset_time = oldest_query.created_at + datetime.timedelta(days=1)
            reset_time_str = reset_time.strftime("%Y-%m-%dT%H:%M:%S") # ISO format for frontend
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "text": "", 
                    "error": f"You have reached your daily limit. You can start using your assistant again at {reset_time_str}.",
                    "reset_time": reset_time_str
                }
            )
    
    try:
        # Convert message_history to the expected format if needed
        message_history = request.message_history or []
        
        # Note: System message and message formatting is now handled by the Assistants API
        # The assistant has its own instructions and manages conversation context
        
        # Select model - prefer the request model, fallback to default
        model = request.model or get_settings().DEFAULT_MODEL
        settings = get_settings()
        
        # Define headers dictionary here to be used later
        response_headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Helpful for Nginx
        }

        async def stream_response():
            collected_response = ""
            log_id_for_update = None 
            conversation_id_to_use = request.conversation_id 
            initial_log_saved = False
            new_id_generated = False
            
            try:
                if not conversation_id_to_use:
                    conversation_id_to_use = int(datetime.datetime.now().timestamp())
                    new_id_generated = True
                    print(f"No conversation_id provided for stream, generated new one: {conversation_id_to_use}")
                    response_headers["X-Conversation-Id"] = str(conversation_id_to_use)
                    response_headers["Access-Control-Expose-Headers"] = "X-Conversation-Id"
                    
                    try:
                        initial_query_log = QueryLog(
                            user_id=current_user.id,
                            query=request.prompt,
                            response=None, 
                            operation_type=request.operation_type,
                            conversation_id=conversation_id_to_use,
                            created_at=datetime.datetime.now()
                        )
                        db.add(initial_query_log)
                        db.commit()
                        db.refresh(initial_query_log)
                        log_id_for_update = initial_query_log.id 
                        initial_log_saved = True
                        print(f"Saved initial log entry ID: {log_id_for_update} for new conversation: {conversation_id_to_use}")
                    except Exception as initial_log_error:
                         print(f"Error saving initial log entry: {initial_log_error}")
                         db.rollback()
                else:
                    print(f"Using provided conversation_id for stream: {conversation_id_to_use}")

                # First send the role marker with empty content
                role_data = json.dumps({
                    "role": "assistant", 
                    "content": "", 
                    "refusal": None
                })
                yield f"data: {role_data}\n\n"

                # Get LLM stream generator
                stream_generator = await get_llm_response(
                    prompt=request.prompt,
                    operation_type=request.operation_type,
                    message_history=message_history,
                    model=model,
                    db=db,
                    current_user_id=current_user.id,
                    stream=True,
                    provider=request.provider,
                    api_key=request.api_key,
                    conversation_id=conversation_id_to_use
                )

                # Yield tokens individually without any batching or accumulation
                async for token in stream_generator:
                    collected_response += token
                    # Send each individual token as a separate SSE event
                    # Format in SSE format with minimal JSON - just the token itself
                    token_data = json.dumps({"content": token})
                    yield f"data: {token_data}\n\n"
                    # Ensure each token is flushed immediately
                    await asyncio.sleep(0)
                
                # Send an empty object to signal the end of the stream
                yield f"data: {{}}\n\n"
                
                # Get the thread_id for this conversation from the database
                try:
                    from app.models.thread_map import ThreadMap
                    thread_map = db.query(ThreadMap).filter(
                        ThreadMap.conversation_id == conversation_id_to_use,
                        ThreadMap.user_id == current_user.id
                    ).first()
                    
                    if thread_map:
                        thread_id = thread_map.thread_id
                        print(f"Found thread_id {thread_id} for conversation_id {conversation_id_to_use}")
                        # Add thread_id to final response
                        thread_data = json.dumps({"thread_id": thread_id})
                        yield f"data: {thread_data}\n\n"
                except Exception as thread_map_error:
                    print(f"Error retrieving thread_id for conversation: {str(thread_map_error)}")
                
                # Logging After Completion (logic remains mostly the same)
                try:
                    if log_id_for_update:
                        db.query(QueryLog).filter(QueryLog.id == log_id_for_update).update(
                            {QueryLog.response: collected_response},
                            synchronize_session=False
                        )
                        db.commit()
                        print(f"Updated log entry ID: {log_id_for_update} with full response.")
                    elif conversation_id_to_use:
                        recent_time = datetime.datetime.now() - datetime.timedelta(minutes=1)
                        if db.bind.dialect.name == 'postgresql':
                            recent_time = func.now() - datetime.timedelta(minutes=1)
                        
                        existing_log = db.query(QueryLog).filter(
                            QueryLog.conversation_id == conversation_id_to_use,
                            QueryLog.user_id == current_user.id, 
                            QueryLog.query == request.prompt,
                            QueryLog.response != None, 
                            QueryLog.created_at > recent_time
                        ).first()
                        
                        if existing_log:
                            print(f"Duplicate prompt detected in conversation {conversation_id_to_use} within 1 min, skipping final log. Existing ID: {existing_log.id}")
                        else:
                            # Determine user IP (public only) for final log
                            user_ip = None
                            client_host = fastapi_request.client.host
                            if client_host:
                                try:
                                    parsed = ip_parse(str(client_host))
                                    if not parsed.is_private:
                                        user_ip = str(client_host)
                                except ValueError:
                                    pass # Ignore if not a valid IP

                            final_query_log = QueryLog(
                                user_id=current_user.id,
                                query=request.prompt,
                                response=collected_response,
                                operation_type=request.operation_type,
                                conversation_id=conversation_id_to_use,
                                created_at=datetime.datetime.now(),
                                ip_address=user_ip
                            )
                            db.add(final_query_log)
                            db.commit()
                            db.refresh(final_query_log)
                            print(f"Saved final log entry ID: {final_query_log.id} for conversation: {conversation_id_to_use}")
                    else:
                        print("No conversation ID available, skipping final log save.")
                except Exception as log_error:
                    db.rollback()
                    print(f"Error saving/updating log after stream completion: {str(log_error)}")
                    print(f"Traceback: {traceback.format_exc()}")
            except Exception as e:
                print(f"Error in streaming response generator: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                error_data = json.dumps({"error": str(e)})
                yield f"data: {error_data}\n\n"
        
        # Return the StreamingResponse, including the potentially modified headers
        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream",
            headers=response_headers
        )
        
    except Exception as e:
        print(f"Error in stream_chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@router.post("/chat/history")
async def save_chat_history(
    request: ChatHistoryRequest,
    fastapi_request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Save chat history to the database
    """
    try:
        # MODIFIED: Prioritize conversation ID from request, only generate new if needed
        conversation_id = None
        if request.conversation_id:
            # Use the conversation ID provided in the request
            conversation_id = request.conversation_id
            print(f"Using conversation ID from request: {conversation_id}")
        else:
            # Try to find most recent conversation for this user
            recent_query = None
            
            recent_query = db.query(QueryLog).filter(
                QueryLog.user_id == current_user.id
            ).order_by(QueryLog.created_at.desc()).first()
            
            if recent_query and recent_query.conversation_id:
                # Check if the recent log is from the last hour (likely the same conversation)
                recent_time = datetime.datetime.now() - datetime.timedelta(hours=1)
                if recent_query.created_at > recent_time:
                    conversation_id = recent_query.conversation_id
                    print(f"Using existing conversation ID from recent log: {conversation_id}")
        
        # If no conversation ID found or provided, generate a new one based on timestamp
        if not conversation_id:
            conversation_id = int(datetime.datetime.now().timestamp())
            print(f"Generated new conversation ID: {conversation_id}")
        
        # Determine user IP (public only)
        user_ip = None
        client_host = fastapi_request.client.host
        if client_host:
            try:
                parsed = ip_parse(str(client_host))
                if not parsed.is_private:
                    user_ip = str(client_host)
            except ValueError:
                pass # Ignore if not a valid IP
        
        # Log the query
        query_log = QueryLog(
            user_id=current_user.id,
            query=request.user_message,
            response=request.ai_response,
            operation_type=request.operation_type,
            conversation_id=conversation_id,
            created_at=datetime.datetime.now(),
            ip_address=user_ip
        )
        db.add(query_log)
        db.commit()
        
        return {"success": True, "message": "Chat history saved successfully", "conversation_id": conversation_id}
    except Exception as e:
        print(f"Error saving chat history: {str(e)}")
        return {"success": False, "error": str(e)} 