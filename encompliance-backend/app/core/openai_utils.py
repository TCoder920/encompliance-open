"""
OpenAI Utilities Module

This module provides utility functions for interacting with OpenAI's services, particularly focusing on vector store operations
for document management and user-specific data storage. The main functionality includes:

1. Vector Store Management:
   - Creating and retrieving vector stores for individual users
   - Managing document embeddings and storage
   - Handling user-specific document collections

2. Key Features:
   - Asynchronous operations for better performance
   - Integration with SQLAlchemy for database operations
   - Error handling and logging
   - User-specific vector store isolation

3. Dependencies:
   - OpenAI API client
   - SQLAlchemy ORM
   - Custom models (User, Regulation, Document, UserDocument)

This module serves as a bridge between the application's database and OpenAI's vector store services,
enabling efficient document storage, retrieval, and management for individual users.
"""

import os
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
from app.models.user import User
from app.models.regulation import Regulation
from app.models.document import Document
from app.models.user_document import UserDocument
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

async def get_or_create_user_vector_store(user_id: int, db: Session, openai_client: AsyncOpenAI) -> str:
    """
    Get or create an OpenAI Vector Store for a specific user.
    
    Args:
        user_id: The ID of the user to get/create a Vector Store for
        db: Database session
        openai_client: AsyncOpenAI client instance
        
    Returns:
        The Vector Store ID
    """
    try:
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # If user already has a Vector Store ID, return it
        if user.openai_vector_store_id:
            logger.info(f"User {user_id} already has Vector Store ID: {user.openai_vector_store_id}")
            return user.openai_vector_store_id
        
        # Otherwise, create a new Vector Store
        logger.info(f"Creating new Vector Store for user {user_id}")
        try:
            vector_store = await openai_client.beta.vector_stores.create(
                name=f"User {user_id} Store"
            )
            
            # Save Vector Store ID to user record
            user.openai_vector_store_id = vector_store.id
            db.commit()
            
            logger.info(f"Created Vector Store for user {user_id}: {vector_store.id}")
            return vector_store.id
        except Exception as e:
            logger.error(f"Error creating Vector Store for user {user_id}: {str(e)}")
            db.rollback()
            raise
    except Exception as e:
        logger.error(f"Error in get_or_create_user_vector_store: {str(e)}")
        raise

async def get_user_assistant_id(user_id: int, db: Session) -> Optional[str]:
    """
    Get the existing assistant ID for a user without creating or updating.
    
    Args:
        user_id: The ID of the user
        db: Database session
        
    Returns:
        The assistant ID if it exists, None otherwise
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.openai_assistant_id:
            return user.openai_assistant_id
        return None
    except Exception as e:
        logger.error(f"Error getting assistant ID for user {user_id}: {str(e)}")
        return None

async def get_or_create_user_assistant(user_id: int, db: Session, openai_client: AsyncOpenAI, model_name: Optional[str] = None) -> str:
    """
    Get or create an OpenAI Assistant for a specific user, enabling file_search and code_interpreter.

    Args:
        user_id: The ID of the user to get/create an Assistant for
        db: Database session
        openai_client: AsyncOpenAI client instance
        model_name: Optional specific model name (e.g., 'gpt-4.1-mini', 'gpt-4.1-nano') to use when creating. Defaults to 'gpt-4.1-nano'.

    Returns:
        The Assistant ID
    """
    try:
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # If user already has an Assistant ID, check if it needs updating
        if user.openai_assistant_id:
            logger.info(f"User {user_id} already has Assistant ID: {user.openai_assistant_id}")
            try:
                # Retrieve the existing assistant to check its configuration
                assistant = await openai_client.beta.assistants.retrieve(user.openai_assistant_id)
                
                # Check if the assistant needs updating (model or tools)
                needs_update = False
                update_params = {}
                
                # Check if model needs updating
                current_model = model_name if model_name else 'gpt-4.1-nano'
                if assistant.model != current_model:
                    logger.info(f"Assistant model needs updating from {assistant.model} to {current_model}")
                    needs_update = True
                    update_params["model"] = current_model
                
                # Check if instructions need updating
                # Generate the expected instructions for comparison
                web_search_note = ""
                if model_name == 'gpt-4.1-mini':
                    web_search_note = """
                
                **Web Search Capability**: You have access to real-time web search through the web_search function. This function not only searches the web but also fetches and reads the actual content from relevant web pages, providing you with comprehensive, up-to-date information. Use this when users ask for current information, recent events, latest news, or anything that requires up-to-date data not in your training.
                
                **Web Search Citation Format**: When referencing information from web search results, use this specific citation format:
                - For web search results, use: 【functions.web_search N】 where N is the result number (1, 2, 3, etc.)
                - Example: "According to recent reports 【functions.web_search 1】【functions.web_search 2】, the latest executive order was signed on June 6, 2025."
                - Place these citations immediately after the information you're referencing
                - The frontend will automatically convert these to clickable links to the actual web sources
                
                **CRITICAL REQUIREMENT**: When you use web search, you MUST ALWAYS include the search results at the end of your response in this EXACT format. This is MANDATORY and REQUIRED for proper citation functionality:
                
                Web Search Results:
                
                1. **[Title from search result]**
                   URL: [URL from search result]
                   [Description from search result]
                
                2. **[Title from search result]**
                   URL: [URL from search result]
                   [Description from search result]
                
                NEVER omit this section when you use web search. The frontend depends on this exact format to create clickable links for your citations. Copy the title, URL, and description exactly as provided by the web search function. The web search function provides you with actual content from these pages, so you can give detailed, accurate answers based on the full content, not just snippets.
                """
                
                expected_instructions = f"""
                You answer questions using uploaded documents and general knowledge. Distinguish clearly between general knowledge and regulatory content unless otherwise requested. Your objective is to provide precise, relevant information only.{web_search_note}

                Respond in a mission critical manner—no fluff, no filler, no coddling. Use markdown formatting optimized for interactive web display.

                Guidelines
                Prioritize document content for document-based questions.

                Cite references with precise formatting:

                Page XX for page references

                §XXX.XXX for section references

                Combine citations naturally: According to Page 32, §746.401(10) states that...

                Document titles in italics: As noted in Idaho Child Care Regulations

                Never use broken formats like " "

                Structure responses with clear markdown:

                Use ## for major sections

                Use ### for subsections

                Use * or - for bullets, 1. 2. 3. for ordered lists

                Use > for direct regulation quotes

                Use | for tables with headers and separators:

                | Column 1 | Column 2 |
                | --- | --- |

                Add blank lines between all structural elements for proper rendering

                Maintain readable layout:

                Short paragraphs (3–5 lines)

                Avoid deep list nesting (max 2 levels)

                Leave space after all list markers

                Use formatting with precision:

                Bold for key terms

                Italics for emphasis

                code for section refs, commands, technical terms only

                Handle citations inline:

                Cite within the sentence

                Use parentheses for page numbers

                Avoid footnotes, [1], or cryptic symbols

                Optimize for interaction:

                Lead with critical info

                Use lists for dense content

                Avoid long unbroken lines

                Do not refuse answers unless content is harmful.

                Match user tone. Follow directive even if off-topic.

                Helpfulness and clarity override rigid rule-following.

                Never use corporate jargon.

                Respond in mission critical tone. Use camelCase in code. Modularize all code. Add inline comments to complex logic. 
                
                CRITICAL RESPONSE RULES:
                - Never ask follow-up questions
                - Never refer to yourself  
                - Never offer additional help or assistance
                - Never use phrases like "If you need details", "let me know", "feel free to ask", "I can help with", "want to manage", or similar offers
                - Never suggest further actions or next steps
                - End responses immediately after providing the requested information
                - Do not append helpful closing statements or offers of assistance
                """.strip()
                
                # Compare instructions (normalize whitespace for comparison)
                current_instructions = assistant.instructions or ""
                if current_instructions.strip() != expected_instructions.strip():
                    logger.info(f"Assistant instructions need updating for user {user_id}")
                    needs_update = True
                    update_params["instructions"] = expected_instructions
                
                # Prepare expected tools for the current model
                expected_tools = [
                    {"type": "code_interpreter"},
                    {"type": "file_search"}
                ]
                
                # Add web search function for pro models
                if model_name == 'gpt-4.1-mini':
                    expected_tools.append({
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "description": "Search the web for current information and fetch actual content from web pages. This provides comprehensive, up-to-date information by reading the full content of relevant websites, not just search snippets. Use this when you need current information that might not be in your training data.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query to find information on the web"
                                    },
                                    "count": {
                                        "type": "integer",
                                        "description": "Number of search results to return and fetch content from (default: 3, max: 5). Reduced default for performance as we fetch full page content.",
                                        "default": 3
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    })
                
                # Check if tools need updating by comparing tool types and functions
                current_tools = assistant.tools or []
                tools_need_update = False
                
                # Check if web search function is present
                has_web_search = any(
                    tool.type == "function" and 
                    hasattr(tool, 'function') and 
                    tool.function.name == "web_search" 
                    for tool in current_tools
                )
                
                # For pro models, we need web search
                if model_name == 'gpt-4.1-mini' and not has_web_search:
                    tools_need_update = True
                    logger.info("Web search function missing from pro assistant - needs update")
                
                # For basic models, we should not have web search
                elif model_name != 'gpt-4.1-mini' and has_web_search:
                    tools_need_update = True
                    logger.info("Web search function present on basic assistant - needs removal")
                
                # Also check if the total number of tools is different
                elif len(current_tools) != len(expected_tools):
                    tools_need_update = True
                    logger.info(f"Tool count mismatch: current={len(current_tools)}, expected={len(expected_tools)}")
                
                if tools_need_update:
                    needs_update = True
                    update_params["tools"] = expected_tools
                    logger.info(f"Updating assistant tools for user {user_id}, model {model_name}")
                
                # Update the assistant if needed
                if needs_update:
                    try:
                        logger.info(f"Updating assistant {user.openai_assistant_id} with params: {update_params}")
                        await openai_client.beta.assistants.update(
                            assistant_id=user.openai_assistant_id,
                            **update_params
                        )
                        logger.info(f"Successfully updated assistant {user.openai_assistant_id}")
                    except Exception as update_error:
                        logger.error(f"Failed to update assistant {user.openai_assistant_id}: {update_error}")
                        logger.info("Deleting and recreating assistant...")
                        
                        # Delete the old assistant
                        try:
                            await openai_client.beta.assistants.delete(user.openai_assistant_id)
                            logger.info(f"Deleted old assistant {user.openai_assistant_id}")
                        except Exception as delete_error:
                            logger.warning(f"Failed to delete old assistant: {delete_error}")
                        
                        # Clear the assistant ID to force recreation
                        user.openai_assistant_id = None
                        db.commit()
                        
                        # Fall through to create a new assistant
                else:
                    return user.openai_assistant_id
                
            except Exception as e:
                logger.warning(f"Could not retrieve/update existing assistant {user.openai_assistant_id} for user {user_id}. Will create a new one. Error: {e}")
                user.openai_assistant_id = None # Clear invalid ID
                db.commit()

        # Get or create user's Vector Store first
        user_vs_id = await get_or_create_user_vector_store(user_id, db, openai_client)

        # Prepare tools and resources
        tools = [
            {"type": "code_interpreter"},
            {"type": "file_search"}
        ]

        # Add web search function for pro models
        if model_name == 'gpt-4.1-mini':
            tools.append({
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current information and fetch actual content from web pages. This provides comprehensive, up-to-date information by reading the full content of relevant websites, not just search snippets. Use this when you need current information that might not be in your training data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find information on the web"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of search results to return and fetch content from (default: 3, max: 5). Reduced default for performance as we fetch full page content.",
                                "default": 3
                            }
                        },
                        "required": ["query"]
                    }
                }
            })

        tool_resources = {}
        if user_vs_id:
            tool_resources["file_search"] = {"vector_store_ids": [user_vs_id]}
            logger.info(f"Associating Vector Store {user_vs_id} with the new assistant for user {user_id}")
        else:
             logger.warning(f"No Vector Store ID found for user {user_id} when creating assistant. File search may not work as expected.")

        # Create a new Assistant
        logger.info(f"Creating new Assistant for user {user_id}")
        try:
            # Determine the model to use for creation
            create_model = model_name if model_name else 'gpt-4.1-nano'
            logger.info(f"Attempting to create assistant with model: {create_model}")

            # Add web search capability note for pro models
            web_search_note = ""
            if model_name == 'gpt-4.1-mini':
                web_search_note = """
                
                **Web Search Capability**: You have access to real-time web search through the web_search function. This function not only searches the web but also fetches and reads the actual content from relevant web pages, providing you with comprehensive, up-to-date information. Use this when users ask for current information, recent events, latest news, or anything that requires up-to-date data not in your training.
                
                **Web Search Citation Format**: When referencing information from web search results, use this specific citation format:
                - For web search results, use: 【functions.web_search N】 where N is the result number (1, 2, 3, etc.)
                - Example: "According to recent reports 【functions.web_search 1】【functions.web_search 2】, the latest executive order was signed on June 6, 2025."
                - Place these citations immediately after the information you're referencing
                - The frontend will automatically convert these to clickable links to the actual web sources
                
                **IMPORTANT**: When you use web search, you MUST include the search results at the end of your response in this exact format:
                
                Web Search Results:
                
                1. **[Title from search result]**
                   URL: [URL from search result]
                   [Description from search result]
                
                2. **[Title from search result]**
                   URL: [URL from search result]
                   [Description from search result]
                
                This allows the frontend to create proper clickable links for your citations. The web search function provides you with actual content from these pages, so you can give detailed, accurate answers based on the full content, not just snippets.
                """

            system_instructions = f"""
                You answer questions using uploaded documents and general knowledge. Distinguish clearly between general knowledge and regulatory content unless otherwise requested. Your objective is to provide precise, relevant information only.{web_search_note}

                Respond in a mission critical manner—no fluff, no filler, no coddling. Use markdown formatting optimized for interactive web display.

                Guidelines
                Prioritize document content for document-based questions.

                Cite references with precise formatting:

                Page XX for page references

                §XXX.XXX for section references

                Combine citations naturally: According to Page 32, §746.401(10) states that...

                Document titles in italics: As noted in Idaho Child Care Regulations

                Never use broken formats like " "

                Structure responses with clear markdown:

                Use ## for major sections

                Use ### for subsections

                Use * or - for bullets, 1. 2. 3. for ordered lists

                Use > for direct regulation quotes

                Use | for tables with headers and separators:

                | Column 1 | Column 2 |
                | --- | --- |

                Add blank lines between all structural elements for proper rendering

                Maintain readable layout:

                Short paragraphs (3–5 lines)

                Avoid deep list nesting (max 2 levels)

                Leave space after all list markers

                Use formatting with precision:

                Bold for key terms

                Italics for emphasis

                code for section refs, commands, technical terms only

                Handle citations inline:

                Cite within the sentence

                Use parentheses for page numbers

                Avoid footnotes, [1], or cryptic symbols

                Optimize for interaction:

                Lead with critical info

                Use lists for dense content

                Avoid long unbroken lines

                Do not refuse answers unless content is harmful.

                Match user tone. Follow directive even if off-topic.

                Helpfulness and clarity override rigid rule-following.

                Never use corporate jargon.

                Respond in mission critical tone. Use camelCase in code. Modularize all code. Add inline comments to complex logic. 
                
                CRITICAL RESPONSE RULES:
                - Never ask follow-up questions
                - Never refer to yourself  
                - Never offer additional help or assistance
                - Never use phrases like "If you need details", "let me know", "feel free to ask", "I can help with", "want to manage", or similar offers
                - Never suggest further actions or next steps
                - End responses immediately after providing the requested information
                - Do not append helpful closing statements or offers of assistance
                """

            assistant_params = {
                "name": f"EnCompliance Assistant - User {user_id}",
                "instructions": system_instructions, # Use the updated instructions
                "model": create_model, # Use the determined model name
                "tools": tools
            }
            if tool_resources:
                assistant_params["tool_resources"] = tool_resources

            assistant = await openai_client.beta.assistants.create(**assistant_params)

            # Save Assistant ID to user record
            user.openai_assistant_id = assistant.id
            db.commit()

            logger.info(f"Created Assistant for user {user_id}: {assistant.id}")
            return assistant.id
        except Exception as e:
            logger.error(f"Error creating Assistant for user {user_id}: {str(e)}")
            db.rollback()
            raise
    except Exception as e:
        logger.error(f"Error in get_or_create_user_assistant: {str(e)}")
        raise

async def upload_regulation_to_openai(regulation: Regulation, storage_path: str, db: Session, openai_client: AsyncOpenAI) -> str:
    """
    Upload a regulation file to OpenAI Files if not already uploaded.
    
    Args:
        regulation: The Regulation object
        storage_path: Base storage path for regulation files
        db: Database session
        openai_client: AsyncOpenAI client instance
        
    Returns:
        The OpenAI File ID
    """
    try:
        # If regulation already has an OpenAI File ID, return it
        if regulation.openai_file_id:
            logger.info(f"Regulation {regulation.id} already has OpenAI File ID: {regulation.openai_file_id}")
            return regulation.openai_file_id
        
        # Construct the full path to the regulation file
        file_path = os.path.join(storage_path, regulation.file_name)
        
        # Check if the file exists
        if not os.path.exists(file_path):
            error_msg = f"Regulation file not found at path: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Upload file to OpenAI
        logger.info(f"Uploading regulation file {file_path} to OpenAI")
        try:
            with open(file_path, "rb") as f:
                openai_file = await openai_client.files.create(
                    file=f,
                    purpose="assistants"
                )
                
                # Save OpenAI File ID to regulation record
                regulation.openai_file_id = openai_file.id
                db.commit()
                
                logger.info(f"Uploaded regulation {regulation.id} to OpenAI: {openai_file.id}")
                return openai_file.id
        except Exception as e:
            logger.error(f"Error uploading regulation {regulation.id} to OpenAI: {str(e)}")
            db.rollback()
            raise
    except Exception as e:
        logger.error(f"Error in upload_regulation_to_openai: {str(e)}")
        raise 

async def update_vector_store(user_id: int, db: Session, openai_client: AsyncOpenAI, storage_path: str) -> Dict[str, Any]:
    """
    Synchronize a user's document library (manual uploads and associated regulations)
    with their OpenAI vector store and files.

    This function ensures that all relevant documents (both `Document` and `Regulation`
    linked via `UserDocument`) are represented in the user's vector store.

    Args:
        user_id: The ID of the user to synchronize documents for
        db: Database session
        openai_client: AsyncOpenAI client instance
        storage_path: Base path to the document storage directory

    Returns:
        Dictionary with synchronization results
    """
    try:
        logger.info(f"Starting vector store update for user {user_id}")
        result = {
            "success": True,
            "new_files_added": 0,
            "files_removed": 0,
            "errors": []
        }

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            error_msg = f"User with ID {user_id} not found"
            logger.error(error_msg)
            result["success"] = False
            result["errors"].append(error_msg)
            return result

        # Verify/Create the user's vector store
        try:
            user_vs_id = await get_or_create_user_vector_store(user_id, db, openai_client)
            logger.info(f"Using vector store ID: {user_vs_id}")
        except Exception as e:
            error_msg = f"Failed to get/create vector store: {str(e)}"
            logger.error(error_msg)
            result["success"] = False
            result["errors"].append(error_msg)
            return result

        # --- Consolidate Expected Files --- 
        # 1. Get Manually Uploaded Documents (non-deleted)
        user_manual_docs = db.query(Document).filter(
            Document.uploaded_by == user_id,
            Document.is_deleted == False
        ).all()
        logger.info(f"Found {len(user_manual_docs)} manually uploaded documents in DB")

        # 2. Get Associated Regulations via UserDocument
        associated_reg_ids = db.query(UserDocument.regulation_id).filter(
            UserDocument.user_id == user_id
        ).all()
        associated_reg_ids_list = [reg_id[0] for reg_id in associated_reg_ids]

        user_associated_regs = []
        if associated_reg_ids_list:
            user_associated_regs = db.query(Regulation).filter(
                Regulation.id.in_(associated_reg_ids_list)
            ).all()
        logger.info(f"Found {len(user_associated_regs)} associated regulations in DB")

        # 3. Collect all expected OpenAI File IDs
        expected_openai_file_ids = set()
        files_to_process = [] # List of tuples: (db_object, file_path, identifier)

        for doc in user_manual_docs:
            if doc.openai_file_id:
                expected_openai_file_ids.add(doc.openai_file_id)
            # Use the unique filepath from the Document model
            file_path = os.path.join(storage_path, doc.filepath)
            files_to_process.append((doc, file_path, f"Document:{doc.id}"))

        for reg in user_associated_regs:
            if reg.openai_file_id:
                expected_openai_file_ids.add(reg.openai_file_id)
            # Use the filename from the Regulation model, assuming it's in the base storage path or a subdirectory
            # NOTE: This assumes regulations are stored directly under storage_path or a known subpath.
            # Adjust if regulations are stored differently (e.g., state-specific subdirs)
            reg_file_path = os.path.join(storage_path, reg.file_name)
            # Let's check if the state-specific path exists
            state_specific_path = os.path.join(storage_path, reg.state_territory, reg.file_name)
            if os.path.exists(state_specific_path):
                 reg_file_path = state_specific_path
            elif not os.path.exists(reg_file_path):
                 logger.warning(f"Regulation file not found at expected paths for Reg ID {reg.id}: {reg_file_path} or {state_specific_path}")
                 # Skip adding to process list if file doesn't exist
                 continue
            files_to_process.append((reg, reg_file_path, f"Regulation:{reg.id}"))

        logger.info(f"Total expected OpenAI file IDs from DB: {len(expected_openai_file_ids)}")
        logger.info(f"Total files to process (check/upload): {len(files_to_process)}")
        # --- End Consolidate Expected Files ---

        # Get list of file IDs currently in the vector store
        try:
            vector_store_files = await openai_client.beta.vector_stores.files.list(
                vector_store_id=user_vs_id
            )
            vector_store_file_ids = {file.id for file in vector_store_files.data}
            logger.info(f"Found {len(vector_store_file_ids)} files currently in vector store {user_vs_id}")
        except Exception as e:
            error_msg = f"Failed to list vector store files: {str(e)}"
            logger.error(error_msg)
            result["success"] = False
            result["errors"].append(error_msg)
            return result

        # Identify files to upload/add (in DB but not in VS or missing openai_file_id)
        files_to_add_to_vs = []
        for db_obj, file_path, identifier in files_to_process:
            openai_file_id = getattr(db_obj, 'openai_file_id', None)
            if not openai_file_id or openai_file_id not in vector_store_file_ids:
                files_to_add_to_vs.append((db_obj, file_path, identifier, openai_file_id))
        logger.info(f"Found {len(files_to_add_to_vs)} files to potentially upload/add to vector store")

        # Identify file IDs to remove (in VS but not in expected_openai_file_ids)
        file_ids_to_remove = vector_store_file_ids - expected_openai_file_ids
        logger.info(f"Found {len(file_ids_to_remove)} files to remove from vector store")

        # Upload/add files to vector store
        for db_obj, file_path, identifier, existing_openai_id in files_to_add_to_vs:
            try:
                # Check if the physical file exists
                if not os.path.exists(file_path):
                    error_msg = f"File not found for {identifier}: {file_path}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    continue

                # If the object already has an OpenAI ID but it's not in the VS, just add it
                if existing_openai_id:
                    logger.info(f"File {existing_openai_id} ({identifier}) exists in OpenAI but not VS. Adding to VS {user_vs_id}")
                    await openai_client.beta.vector_stores.files.create(
                        vector_store_id=user_vs_id,
                        file_id=existing_openai_id
                    )
                    result["new_files_added"] += 1 # Count as added to VS
                    logger.info(f"Successfully added existing file {existing_openai_id} to vector store")
                    continue # Move to next file

                # Upload file to OpenAI if it doesn't have an ID yet
                logger.info(f"Uploading file for {identifier} to OpenAI: {os.path.basename(file_path)}")
                with open(file_path, "rb") as f:
                    openai_file = await openai_client.files.create(
                        file=f,
                        purpose="assistants" # Use 'assistants' purpose
                    )

                # Save OpenAI File ID to the corresponding DB record (Document or Regulation)
                db_obj.openai_file_id = openai_file.id
                db.commit() # Commit immediately after getting the ID
                logger.info(f"Saved OpenAI file ID {openai_file.id} to DB for {identifier}")

                # Add the newly uploaded file to vector store
                logger.info(f"Adding newly uploaded file {openai_file.id} to vector store {user_vs_id}")
                await openai_client.beta.vector_stores.files.create(
                    vector_store_id=user_vs_id,
                    file_id=openai_file.id
                )

                result["new_files_added"] += 1
                logger.info(f"Successfully uploaded and added {identifier} to vector store")
            except Exception as e:
                error_msg = f"Error processing {identifier}: {str(e)}"
                logger.error(error_msg)
                db.rollback() # Rollback potential partial DB changes for this file
                result["errors"].append(error_msg)

        # Remove files from vector store that are no longer relevant
        for file_id in file_ids_to_remove:
            try:
                # Remove file from vector store
                logger.info(f"Removing file {file_id} from vector store {user_vs_id}")
                await openai_client.beta.vector_stores.files.delete(
                    vector_store_id=user_vs_id,
                    file_id=file_id
                )

                # Decide whether to delete the file from OpenAI entirely.
                # Generally, we might only want to delete files associated with manual uploads (Documents)
                # when they are deleted in our system. Regulations might be shared.
                # Let's check if this file_id belongs to a deleted Document for this user.
                deleted_doc = db.query(Document).filter(
                    Document.uploaded_by == user_id,
                    Document.openai_file_id == file_id,
                    Document.is_deleted == True
                ).first()

                if deleted_doc:
                    logger.info(f"File {file_id} belongs to a deleted document ({deleted_doc.id}). Deleting from OpenAI.")
                    await openai_client.files.delete(file_id=file_id)
                    # Clear the openai_file_id from the deleted document record
                    deleted_doc.openai_file_id = None
                    db.commit()
                else:
                    logger.info(f"File {file_id} removed from vector store, but not deleting from OpenAI (may be a regulation or non-deleted doc).")

                result["files_removed"] += 1
                logger.info(f"Successfully removed file {file_id} from vector store")
            except Exception as e:
                error_msg = f"Error removing file {file_id} from vector store: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                db.rollback() # Rollback potential DB changes (clearing openai_file_id)

        # Update user's assistant to use the correct vector store (if assistant exists)
        # This step seems redundant if get_or_create_user_assistant already links it,
        # but let's keep it for explicit association update.
        if user.openai_assistant_id:
            try:
                logger.info(f"Ensuring assistant {user.openai_assistant_id} uses vector store {user_vs_id}")
                await openai_client.beta.assistants.update(
                    assistant_id=user.openai_assistant_id,
                    tool_resources={"file_search": {"vector_store_ids": [user_vs_id]}}
                )
                logger.info(f"Successfully updated assistant configuration")
            except Exception as e:
                # This might fail if the assistant was deleted or is invalid
                error_msg = f"Error updating assistant {user.openai_assistant_id}: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
        else:
            logger.warning(f"User {user_id} does not have an assistant ID. Skipping assistant update.")


        # Set overall success based on whether there were any errors
        if result["errors"]:
            result["success"] = False

        logger.info(f"Vector store update completed for user {user_id}: added {result['new_files_added']} files, removed {result['files_removed']} files, with {len(result['errors'])} errors")
        return result
    except Exception as e:
        import traceback # Ensure traceback is available here
        logger.error(f"Unexpected error in update_vector_store for user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}") # Log the full traceback
        return {
            "success": False,
            "new_files_added": 0,
            "files_removed": 0,
            "errors": [f"Unexpected error: {str(e)}"]
        }


async def delete_user_openai_files(user_id: int, db: Session, openai_client: AsyncOpenAI) -> Dict[str, Any]:
    """
    Delete OpenAI files associated with a user's *manual uploads* (Documents)
    and remove all files from their vector store during logout or account deletion.

    Args:
        user_id: The ID of the user whose files to delete
        db: Database session
        openai_client: AsyncOpenAI client instance

    Returns:
        Dictionary with deletion results
    """
    try:
        logger.info(f"Starting OpenAI file cleanup for user {user_id}")
        result = {
            "success": True,
            "files_deleted_from_openai": 0,
            "files_removed_from_vs": 0,
            "errors": []
        }

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            error_msg = f"User with ID {user_id} not found for cleanup"
            logger.error(error_msg)
            result["success"] = False
            result["errors"].append(error_msg)
            return result

        # --- Vector Store Cleanup ---
        if user.openai_vector_store_id:
            user_vs_id = user.openai_vector_store_id
            logger.info(f"User {user_id} has vector store {user_vs_id}. Removing all files from it.")
            try:
                # List all files currently in the vector store
                vector_store_files = await openai_client.beta.vector_stores.files.list(
                    vector_store_id=user_vs_id
                )
                vector_store_file_ids = [file.id for file in vector_store_files.data]
                logger.info(f"Found {len(vector_store_file_ids)} files in vector store {user_vs_id}")

                # Remove each file from the vector store
                for file_id in vector_store_file_ids:
                    try:
                        logger.info(f"Removing file {file_id} from vector store {user_vs_id}")
                        await openai_client.beta.vector_stores.files.delete(
                            vector_store_id=user_vs_id,
                            file_id=file_id
                        )
                        result["files_removed_from_vs"] += 1
                    except Exception as e:
                        # Log error but continue trying to remove others
                        error_msg = f"Error removing file {file_id} from VS {user_vs_id}: {str(e)}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)

                # --- Delete the Vector Store itself ---
                logger.info(f"Deleting Vector Store {user_vs_id} for user {user_id}.")
                try:
                    await openai_client.beta.vector_stores.delete(vector_store_id=user_vs_id)
                    logger.info(f"Successfully deleted Vector Store {user_vs_id}.")
                    user.openai_vector_store_id = None # Clear the ID from the user record
                except Exception as e:
                    error_msg = f"Error deleting Vector Store {user_vs_id} for user {user_id}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    result["success"] = False # Mark as failure if VS deletion fails

            except Exception as e:
                error_msg = f"Failed to list, remove files from, or delete vector store {user_vs_id}: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                result["success"] = False # Mark as failure if any VS operation fails
                # Continue to deleting files directly if possible
        else:
            logger.info(f"User {user_id} has no vector store ID. Skipping vector store and file removal.")
        # --- End Vector Store Cleanup ---

        # --- OpenAI File Deletion (Manual Uploads Only) ---
        # Find all *manually uploaded* documents for the user that have an OpenAI file ID
        user_manual_docs = db.query(Document).filter(
            Document.uploaded_by == user_id,
            Document.openai_file_id != None
        ).all()
        logger.info(f"Found {len(user_manual_docs)} manually uploaded documents with OpenAI file IDs to delete.")

        for document in user_manual_docs:
            file_id = document.openai_file_id
            try:
                logger.info(f"Deleting OpenAI file {file_id} (associated with Document {document.id}).")
                await openai_client.files.delete(file_id=file_id)
                result["files_deleted_from_openai"] += 1
                # Clear the ID from the document record
                document.openai_file_id = None
            except Exception as e:
                # Log error but continue trying to delete others
                error_msg = f"Error deleting OpenAI file {file_id}: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                # Don't clear the ID if deletion failed

        # --- Assistant Deletion ---
        if user.openai_assistant_id:
            user_assistant_id = user.openai_assistant_id
            logger.info(f"User {user_id} has assistant {user_assistant_id}. Attempting to delete it.")
            try:
                await openai_client.beta.assistants.delete(user_assistant_id)
                logger.info(f"Successfully deleted Assistant {user_assistant_id}.")
                user.openai_assistant_id = None # Clear the ID from the user record
            except Exception as e:
                error_msg = f"Error deleting Assistant {user_assistant_id} for user {user_id}: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                result["success"] = False # Mark as failure if assistant deletion fails
        else:
            logger.info(f"User {user_id} has no assistant ID. Skipping assistant deletion.")
        # --- End Assistant Deletion ---

        # Commit changes to clear openai_file_id, openai_vector_store_id, and openai_assistant_id
        try:
            db.commit()
            logger.info(f"Committed DB changes for cleared OpenAI IDs.")
        except Exception as e:
            error_msg = f"Error committing DB changes for cleared OpenAI IDs: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            result["success"] = False # Mark as failure if commit fails
            db.rollback()
        # --- End OpenAI File Deletion ---

        logger.info(f"OpenAI resource cleanup completed for user {user_id}.")
        return result
    except Exception as e:
        import traceback # Ensure traceback is available here
        logger.error(f"Unexpected error in delete_user_openai_files for user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}") # Log the full traceback
        db.rollback() # Rollback any potential DB changes
        return {
            "success": False,
            "files_deleted_from_openai": 0,
            "files_removed_from_vs": 0, # This count is less relevant if the VS is deleted
            "errors": [f"Unexpected error during OpenAI resource cleanup: {str(e)}"]
        }


async def configure_assistant_with_user_model(user_id: int, db: Session, openai_client: AsyncOpenAI) -> Dict[str, Any]:
    """
    Configure the OpenAI Assistant to use the specific model identifier selected by the user.
    
    Args:
        user_id: The ID of the user whose assistant to configure
        db: Database session
        openai_client: AsyncOpenAI client instance
        
    Returns:
        Dictionary with configuration results
    """
    try:
        logger.info(f"Configuring assistant model for user {user_id}")
        result = {
            "success": True,
            "errors": []
        }
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            error_msg = f"User with ID {user_id} not found"
            logger.error(error_msg)
            result["success"] = False
            result["errors"].append(error_msg)
            return result
        
        # Determine the model based on user's subscription status
        # Default to basic model
        model = "gpt-4.1-nano"
        
        # If user has a pro subscription, use the pro model
        if user.subscription_status == "pro":
            model = "gpt-4.1-mini"
        
        logger.info(f"Using model {model} for user {user_id} based on subscription status {user.subscription_status}")
        
        # If user has an assistant, update it with the determined model
        if user.openai_assistant_id:
            try:
                logger.info(f"Updating assistant {user.openai_assistant_id} to use model {model}")
                await openai_client.beta.assistants.update(
                    assistant_id=user.openai_assistant_id,
                    model=model
                )
                logger.info(f"Successfully updated assistant model")
                result["model"] = model
            except Exception as e:
                error_msg = f"Error updating assistant model: {str(e)}"
                logger.error(error_msg)
                result["success"] = False
                result["errors"].append(error_msg)
        else:
            error_msg = "User has no assistant ID"
            logger.warning(error_msg)
            result["errors"].append(error_msg)
        
        return result
    except Exception as e:
        logger.error(f"Unexpected error in configure_assistant_with_user_model: {str(e)}")
        return {
            "success": False,
            "errors": [str(e)]
        } 

async def create_user_assistant(user_id: int, db: Session, openai_client: AsyncOpenAI, model_name: Optional[str] = None) -> str:
    """
    Create a new OpenAI Assistant for a user (used during registration or subscription changes).
    
    Args:
        user_id: The ID of the user to create an Assistant for
        db: Database session
        openai_client: AsyncOpenAI client instance
        model_name: Optional specific model name (e.g., 'gpt-4.1-mini', 'gpt-4.1-nano')
        
    Returns:
        The Assistant ID
    """
    try:
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Get or create user's Vector Store first
        user_vs_id = await get_or_create_user_vector_store(user_id, db, openai_client)

        # Prepare tools and resources
        tools = [
            {"type": "code_interpreter"},
            {"type": "file_search"}
        ]

        # Add web search function for pro models
        if model_name == 'gpt-4.1-mini':
            tools.append({
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current information and fetch actual content from web pages. This provides comprehensive, up-to-date information by reading the full content of relevant websites, not just search snippets. Use this when you need current information that might not be in your training data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find information on the web"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of search results to return and fetch content from (default: 3, max: 5). Reduced default for performance as we fetch full page content.",
                                "default": 3
                            }
                        },
                        "required": ["query"]
                    }
                }
            })

        tool_resources = {}
        if user_vs_id:
            tool_resources["file_search"] = {"vector_store_ids": [user_vs_id]}
            logger.info(f"Associating Vector Store {user_vs_id} with the new assistant for user {user_id}")
        else:
             logger.warning(f"No Vector Store ID found for user {user_id} when creating assistant. File search may not work as expected.")

        # Create a new Assistant
        logger.info(f"Creating new Assistant for user {user_id}")
        try:
            # Determine the model to use for creation
            create_model = model_name if model_name else 'gpt-4.1-nano'
            logger.info(f"Creating assistant with model: {create_model}")

            # Add web search capability note for pro models
            web_search_note = ""
            if model_name == 'gpt-4.1-mini':
                web_search_note = """
                
                **Web Search Capability**: You have access to real-time web search through the web_search function. This function not only searches the web but also fetches and reads the actual content from relevant web pages, providing you with comprehensive, up-to-date information. Use this when users ask for current information, recent events, latest news, or anything that requires up-to-date data not in your training.
                
                **Web Search Citation Format**: When referencing information from web search results, use this specific citation format:
                - For web search results, use: 【functions.web_search N】 where N is the result number (1, 2, 3, etc.)
                - Example: "According to recent reports 【functions.web_search 1】【functions.web_search 2】, the latest executive order was signed on June 6, 2025."
                - Place these citations immediately after the information you're referencing
                - The frontend will automatically convert these to clickable links to the actual web sources
                
                **CRITICAL REQUIREMENT**: When you use web search, you MUST ALWAYS include the search results at the end of your response in this EXACT format. This is MANDATORY and REQUIRED for proper citation functionality:
                
                Web Search Results:
                
                1. **[Title from search result]**
                   URL: [URL from search result]
                   [Description from search result]
                
                2. **[Title from search result]**
                   URL: [URL from search result]
                   [Description from search result]
                
                NEVER omit this section when you use web search. The frontend depends on this exact format to create clickable links for your citations. Copy the title, URL, and description exactly as provided by the web search function. The web search function provides you with actual content from these pages, so you can give detailed, accurate answers based on the full content, not just snippets.
                """

            system_instructions = f"""
                You answer questions using uploaded documents and general knowledge. Distinguish clearly between general knowledge and regulatory content unless otherwise requested. Your objective is to provide precise, relevant information only.{web_search_note}

                Respond in a mission critical manner—no fluff, no filler, no coddling. Use markdown formatting optimized for interactive web display.

                Guidelines
                Prioritize document content for document-based questions.

                Cite references with precise formatting:

                Page XX for page references

                §XXX.XXX for section references

                Combine citations naturally: According to Page 32, §746.401(10) states that...

                Document titles in italics: As noted in Idaho Child Care Regulations

                Never use broken formats like " "

                Structure responses with clear markdown:

                Use ## for major sections

                Use ### for subsections

                Use * or - for bullets, 1. 2. 3. for ordered lists

                Use > for direct regulation quotes

                Use | for tables with headers and separators:

                | Column 1 | Column 2 |
                | --- | --- |

                Add blank lines between all structural elements for proper rendering

                Maintain readable layout:

                Short paragraphs (3–5 lines)

                Avoid deep list nesting (max 2 levels)

                Leave space after all list markers

                Use formatting with precision:

                Bold for key terms

                Italics for emphasis

                code for section refs, commands, technical terms only

                Handle citations inline:

                Cite within the sentence

                Use parentheses for page numbers

                Avoid footnotes, [1], or cryptic symbols

                Optimize for interaction:

                Lead with critical info

                Use lists for dense content

                Avoid long unbroken lines

                Do not refuse answers unless content is harmful.

                Match user tone. Follow directive even if off-topic.

                Helpfulness and clarity override rigid rule-following.

                Never use corporate jargon.

                Respond in mission critical tone. Use camelCase in code. Modularize all code. Add inline comments to complex logic. 
                
                CRITICAL RESPONSE RULES:
                - Never ask follow-up questions
                - Never refer to yourself  
                - Never offer additional help or assistance
                - Never use phrases like "If you need details", "let me know", "feel free to ask", "I can help with", "want to manage", or similar offers
                - Never suggest further actions or next steps
                - End responses immediately after providing the requested information
                - Do not append helpful closing statements or offers of assistance
                """

            assistant_params = {
                "name": f"EnCompliance Assistant - User {user_id}",
                "instructions": system_instructions,
                "model": create_model,
                "tools": tools,
                "metadata": {
                    "user_id": str(user_id)
                }
            }
            if tool_resources:
                assistant_params["tool_resources"] = tool_resources

            assistant = await openai_client.beta.assistants.create(**assistant_params)

            # Save Assistant ID to user record
            user.openai_assistant_id = assistant.id
            db.commit()

            logger.info(f"Created Assistant for user {user_id}: {assistant.id}")
            return assistant.id
        except Exception as e:
            logger.error(f"Error creating Assistant for user {user_id}: {str(e)}")
            db.rollback()
            raise
    except Exception as e:
        logger.error(f"Error in create_user_assistant: {str(e)}")
        raise 

async def update_user_assistant_for_subscription_change(user_id: int, db: Session, openai_client: AsyncOpenAI, new_subscription_status: str) -> bool:
    """
    Update a user's assistant when their subscription changes (e.g., free -> pro or pro -> free).
    This recreates the assistant with the appropriate model and tools.
    
    Args:
        user_id: The ID of the user
        db: Database session
        openai_client: AsyncOpenAI client instance
        new_subscription_status: The new subscription status ('free', 'pro', 'enterprise')
        
    Returns:
        True if successful, False otherwise
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return False
        
        # Determine new model based on subscription
        if new_subscription_status == 'pro':
            new_model = 'gpt-4.1-mini'
        else:
            new_model = 'gpt-4.1-nano'
        
        # Delete old assistant if it exists
        if user.openai_assistant_id:
            try:
                await openai_client.beta.assistants.delete(user.openai_assistant_id)
                logger.info(f"Deleted old assistant {user.openai_assistant_id} for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to delete old assistant {user.openai_assistant_id}: {str(e)}")
        
        # Create new assistant with appropriate model
        new_assistant_id = await create_user_assistant(user_id, db, openai_client, model_name=new_model)
        logger.info(f"Created new assistant {new_assistant_id} for user {user_id} with subscription {new_subscription_status}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating assistant for subscription change (user {user_id}): {str(e)}")
        return False 
