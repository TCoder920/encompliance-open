"""
Chat Utilities Module

This module provides utilities for handling chat interactions and message formatting
in the EnCompliance application's chat interface.

Key functionalities:
- Chat history formatting for LLM interactions
- System message generation for different operation types
- Document filename extraction from filepaths
- Operation-specific instruction customization
- User context integration (calendar events and notes)
- Current date/time context for temporal awareness

Dependencies:
- os: For file path operations
- sqlalchemy: For database session handling
- datetime: For current date/time context
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.config import get_settings
from sqlalchemy.orm import Session

settings = get_settings()

def get_document_filename_from_path(filepath: str) -> str:
    """Get the original filename from a filepath"""
    return os.path.basename(filepath).split("_", 1)[1] if "_" in os.path.basename(filepath) else os.path.basename(filepath)

def format_chat_history(
    messages: List[Dict[str, str]], 
    system_message: str
) -> List[Dict[str, str]]:
    """
    Format chat history for the LLM
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        system_message: System message to include
        
    Returns:
        Formatted list of messages
    """
    formatted_messages = []
    
    # Add system message
    formatted_messages.append({
        "role": "system",
        "content": system_message
    })
    
    # Add conversation history
    for msg in messages:
        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
            # Ensure role is valid
            role = msg['role'].lower()
            if role not in ['system', 'user', 'assistant']:
                role = 'user' if role == 'human' else 'assistant'
            
            formatted_messages.append({
                "role": role,
                "content": msg['content']
            })
    
    return formatted_messages

def get_compliance_system_message(operation_type: str, user_context: str = "") -> str:
    """
    Get the system message for compliance assistant (Legacy function for testing)
    
    Note: This function is kept for backward compatibility and testing purposes.
    The main application now uses OpenAI Assistants API with instructions set directly on the assistant.
    
    Args:
        operation_type: Type of operation (daycare, residential, etc.)
        user_context: Additional user context (calendar events, notes, etc.)
        
    Returns:
        System message with current date/time and user context included
    """
    # Legacy system instructions for testing purposes
    system_instructions = """
    You answer questions using uploaded documents and general knowledge. Distinguish clearly between general knowledge and regulatory content unless otherwise requested. Your objective is to provide precise, relevant information only.

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
    Use | for tables with headers and separators

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
    Respond in mission critical tone. Use camelCase in code. Modularize all code. Add inline comments to complex logic. Never ask follow-up questions. Never refer to yourself.
    """
    
    # Get current date and time information
    current_datetime = datetime.now()
    current_date_str = current_datetime.strftime("%A, %B %d, %Y")
    current_time_str = current_datetime.strftime("%I:%M %p")
    current_iso = current_datetime.isoformat()
    day_of_week = current_datetime.strftime("%A")
    week_of_year = current_datetime.isocalendar()[1]
    month_year = current_datetime.strftime("%B %Y")
    
    # Start with current date/time context
    system_message = f"""=== CURRENT DATE AND TIME INFORMATION ===
Current Date: {current_date_str}
Current Time: {current_time_str}
ISO Format: {current_iso}
Day of Week: {day_of_week}
Week of Year: Week {week_of_year}
Month: {month_year}
Timezone: Local system time

IMPORTANT: Use this current date and time information when:
- Answering questions about "today", "now", "this week", "this month"
- Calculating relative dates (e.g., "next week", "in 3 days", "last Monday")
- Scheduling or time-sensitive compliance matters
- Providing context-aware responses about deadlines or timeframes
- Determining business days, weekends, or holiday considerations

{system_instructions}"""
    
    # Add user context if provided
    if user_context and user_context.strip():
        system_message += f"""

=== USER PERSONAL CONTEXT ===
{user_context}

IMPORTANT: Use the above personal context to provide more relevant and personalized responses. 
When the user asks about their schedule, meetings, notes, or related topics, reference this information directly.
"""
    
    # Add operation-specific instructions
    if operation_type.lower() == "daycare":
        system_message += """
        
Specific to Childcare Facilities:
- Focus on childcare facility regulations and compliance requirements.
- Consider state-specific regulations when mentioned.
- Provide practical implementation advice for compliance measures.
- When discussing safety measures, prioritize child welfare above all else.
"""
    elif operation_type.lower() == "residential":
        system_message += """
        
Specific to Residential Care Facilities:
- Focus on residential care facility regulations and compliance requirements.
- Consider both federal and state-specific regulations when applicable.
- Provide practical implementation advice for compliance measures.
- When discussing safety measures, prioritize resident welfare and dignity.
"""
    else:
        system_message += f"""
        
Specific to {operation_type.title()} Operations:
- Focus on {operation_type} regulations and compliance requirements.
- Consider both federal and state-specific regulations when applicable.
- Provide practical implementation advice for compliance measures.
"""
    
    return system_message 