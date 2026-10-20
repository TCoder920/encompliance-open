"""
Query Management Routes
---------------------
This module defines the query management API endpoints for the EnCompliance system.
It provides:
- Query execution and management
- Query history tracking
- Query optimization
- Query results caching
- Query analytics
- Query performance monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, desc, asc, select, literal_column, case, text, and_
from typing import List, Optional
from app.database import get_db
from app.models.query_log import QueryLog
from app.auth.dependencies import get_current_user
from datetime import datetime
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(tags=["queries"])

# Define response models for clarity
class ConversationSummary(BaseModel):
    conversation_id: int
    first_query_text: Optional[str] = None
    last_updated_at: datetime
    message_count: int
    document_reference: Optional[str] = None
    operation_type: Optional[str] = None

class GetConversationsResponse(BaseModel):
    conversations: List[ConversationSummary]
    total: int
    limit: int
    skip: int

# Add OPTIONS handler for CORS preflight requests
@router.options("/query-logs")
@router.options("/conversations/{conversation_id}")
@router.options("/query/{query_id}")
@router.options("/queries/all")
async def options_queries():
    """
    Handle OPTIONS requests for query endpoints.
    """
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:5174",
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={}, headers=headers)

@router.get("/query-logs", response_model=GetConversationsResponse)
async def get_conversations_list(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    limit: int = 20,
    skip: int = 0
):
    """
    Get a list of conversation summaries for the current user,
    ordered by the most recently updated conversation.
    Only returns groups of conversations, not individual messages.
    """
    try:
        print(f"Getting conversation list for user: {current_user.id}, limit={limit}, skip={skip}")

        # Subquery to aggregate and filter empty conversations *before* pagination
        subquery = (
            db.query(
                QueryLog.conversation_id,
                func.max(QueryLog.created_at).label("last_updated_at"),
                func.count(QueryLog.id).label("total_messages"),
                func.count(case((QueryLog.query == 'SESSION_START', 1))).label("session_start_count"),
                func.max(QueryLog.document_reference).label("document_reference"),
                func.max(QueryLog.operation_type).label("operation_type")
            )
            .filter(QueryLog.user_id == current_user.id)
            .filter(QueryLog.conversation_id != None)
            .group_by(QueryLog.conversation_id)
            .having(func.count(QueryLog.id) > func.count(case((QueryLog.query == 'SESSION_START', 1)))) # Ensure message_count > 0
            .subquery('valid_conversations')
        )

        # Get the total count of *valid* conversations
        total_valid_count_query = db.query(func.count(subquery.c.conversation_id))
        total_count = total_valid_count_query.scalar() or 0
        print(f"Total VALID conversations found: {total_count}")

        # Apply ordering and pagination to the subquery
        paginated_query = (
            db.query(subquery)
            .order_by(desc(subquery.c.last_updated_at))
            .offset(skip)
            .limit(limit)
        )

        aggregated_results = paginated_query.all()
        print(f"Fetched {len(aggregated_results)} valid conversations for this page.")

        # Get conversation IDs on the current page
        conversation_ids_on_page = [row.conversation_id for row in aggregated_results]
        
        # Fetch the first query text for conversations on this page (minor optimization)
        first_query_texts = {}
        if conversation_ids_on_page:
            # Subquery to find the minimum created_at for non-SESSION_START messages per conversation
            first_msg_subquery = (
                 db.query(
                     QueryLog.conversation_id,
                     func.min(QueryLog.created_at).label('first_message_time')
                 )
                 .filter(QueryLog.conversation_id.in_(conversation_ids_on_page))
                 .filter(QueryLog.user_id == current_user.id)
                 .filter(QueryLog.query != 'SESSION_START')
                 .group_by(QueryLog.conversation_id)
                 .subquery('first_times')
             )
             
            # Join to get the actual message text
            first_msgs_query = (
                 db.query(QueryLog.conversation_id, QueryLog.query)
                 .join(
                     first_msg_subquery, 
                     and_(
                         QueryLog.conversation_id == first_msg_subquery.c.conversation_id,
                         QueryLog.created_at == first_msg_subquery.c.first_message_time
                     )
                 )
                 .filter(QueryLog.user_id == current_user.id) # Ensure user context
             )
             
            first_query_texts = {row.conversation_id: row.query for row in first_msgs_query.all()}
            print(f"Fetched first query texts for {len(first_query_texts)} conversations.")

        # Format the final response (no more filtering needed here)
        conversations_data = []
        for row in aggregated_results:
            message_count = row.total_messages - row.session_start_count
            first_text = first_query_texts.get(row.conversation_id)
            
            # We already filtered in the subquery, so we assume message_count > 0
            conversations_data.append(
                ConversationSummary(
                    conversation_id=row.conversation_id,
                    first_query_text=first_text,
                    last_updated_at=row.last_updated_at,
                    message_count=message_count,
                    document_reference=row.document_reference,
                    operation_type=row.operation_type,
                )
            )

        print(f"Returning {len(conversations_data)} conversation summaries to client")

        return GetConversationsResponse(
            conversations=conversations_data,
            total=total_count, # Use the count of VALID conversations
            limit=limit,
            skip=skip
        )

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error getting conversation list: {str(e)}")
        print(f"Traceback: {error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation list: {str(e)}"
        )

@router.get("/query/{query_id}")
async def get_query_details(
    query_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get details for a specific query.
    """
    try:
        print(f"Getting query details for ID: {query_id}, user: {current_user.id}")
        
        # Get the query
        query = db.query(QueryLog).filter(
            QueryLog.id == query_id,
            QueryLog.user_id == current_user.id
        ).first()
        
        if not query:
            print(f"Query with ID {query_id} not found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {query_id} not found"
            )
        
        print(f"Found query: id={query.id}, query={query.query[:30]}..., document_id={query.document_id}, conversation_id={query.conversation_id}")
        
        # Format the response
        response_data = {
            "id": query.id,
            "query_text": query.query,
            "response_text": query.response,
            "created_at": query.created_at.isoformat(),
            "document_reference": query.document_reference,
            "conversation_id": query.conversation_id,
            "full_conversation": query.conversation_id is not None,
            "documentIds": [query.document_id] if query.document_id and query.document_id > 0 else []
        }
        
        print(f"Returning query details: {response_data}")
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        # Log the error
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error getting query details: {str(e)}")
        print(f"Traceback: {error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get query details: {str(e)}"
        )

@router.delete("/query/{query_id}")
async def delete_query(
    query_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a specific query log.
    """
    try:
        print(f"Deleting query with ID: {query_id}, user: {current_user.id}")
        
        # Find the query
        query = db.query(QueryLog).filter(
            QueryLog.id == query_id,
            QueryLog.user_id == current_user.id
        ).first()
        
        if not query:
            print(f"Query with ID {query_id} not found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {query_id} not found"
            )
        
        # Delete the query
        db.delete(query)
        db.commit()
        
        print(f"Successfully deleted query with ID: {query_id}")
        return {"message": f"Query with ID {query_id} has been deleted"}
    except HTTPException:
        raise
    except Exception as e:
        # Log the error
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error deleting query: {str(e)}")
        print(f"Traceback: {error_traceback}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete query: {str(e)}"
        )

@router.delete("/queries/all")
async def delete_all_queries(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete all query logs for the current user.
    """
    try:
        print(f"Deleting all queries for user: {current_user.id}")
        
        # Find and count all queries for this user
        query_count = db.query(QueryLog).filter(
            QueryLog.user_id == current_user.id
        ).count()
        
        # Delete all queries for this user
        result = db.query(QueryLog).filter(
            QueryLog.user_id == current_user.id
        ).delete(synchronize_session=False)
        
        # Commit the transaction
        db.commit()
        
        print(f"Successfully deleted {result} queries for user {current_user.id}")
        return {"message": f"Successfully deleted {result} queries", "count": result}
    except Exception as e:
        # Log the error
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error deleting all queries: {str(e)}")
        print(f"Traceback: {error_traceback}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete all queries: {str(e)}"
        )

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete all query logs associated with a specific conversation ID for the current user.
    """
    try:
        print(f"Deleting conversation with ID: {conversation_id} for user: {current_user.id}")

        # Find and count logs for this conversation and user
        logs_to_delete = db.query(QueryLog).filter(
            QueryLog.conversation_id == conversation_id,
            QueryLog.user_id == current_user.id
        )
        
        count = logs_to_delete.count()

        if count == 0:
            print(f"No logs found for conversation ID {conversation_id} and user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation with ID {conversation_id} not found or does not belong to the user"
            )

        # Perform the deletion
        # synchronize_session='fetch' might be safer if there are relationships, but 'False' is faster
        result = logs_to_delete.delete(synchronize_session=False)
        db.commit()

        print(f"Successfully deleted {result} logs for conversation ID: {conversation_id}")
        return {"message": f"Conversation with ID {conversation_id} ({result} messages) has been deleted", "deleted_count": result}

    except HTTPException: # Re-raise HTTPExceptions
        raise
    except Exception as e:
        # Log the error and rollback
        db.rollback()
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error deleting conversation: {str(e)}")
        print(f"Traceback: {error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all details for a specific conversation, including all messages in order.
    """
    try:
        print(f"Getting conversation details for ID: {conversation_id}, user: {current_user.id}")
        
        # Get all messages for this conversation in chronological order
        messages = db.query(QueryLog).filter(
            QueryLog.conversation_id == conversation_id,
            QueryLog.user_id == current_user.id
        ).order_by(QueryLog.created_at.asc()).all()
        
        if not messages or len(messages) == 0:
            print(f"Conversation with ID {conversation_id} not found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation with ID {conversation_id} not found"
            )
        
        # Get any document IDs associated with this conversation
        document_ids = []
        document_references = []
        operation_type = None
        
        for msg in messages:
            if msg.document_id and msg.document_id not in document_ids:
                document_ids.append(msg.document_id)
            if msg.document_reference and msg.document_reference not in document_references:
                document_references.append(msg.document_reference)
            if not operation_type and msg.operation_type:
                operation_type = msg.operation_type
        
        # Format messages for response
        formatted_messages = []
        for msg in messages:
            # Skip SESSION_START entries
            if msg.query == 'SESSION_START':
                continue
                
            if msg.query:  # User message
                formatted_messages.append({
                    "id": msg.id,
                    "role": "user",
                    "content": msg.query,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None
                })
            
            if msg.response:  # AI message
                formatted_messages.append({
                    "id": f"{msg.id}-response",
                    "role": "assistant",
                    "content": msg.response,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None
                })
        
        # Format the response
        response_data = {
            "conversation_id": conversation_id,
            "messages": formatted_messages,
            "document_ids": document_ids,
            "document_references": document_references,
            "operation_type": operation_type,
            "message_count": len(formatted_messages)
        }
        
        print(f"Returning {len(formatted_messages)} messages for conversation {conversation_id}")
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        # Log the error
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error getting conversation details: {str(e)}")
        print(f"Traceback: {error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation details: {str(e)}"
        ) 