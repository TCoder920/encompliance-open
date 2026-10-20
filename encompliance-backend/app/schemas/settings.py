from pydantic import BaseModel
from typing import Optional

class UserLLMSettings(BaseModel):
    """Schema for LLM settings that are stored encrypted per user."""
    provider: Optional[str] = None  # 'auto', 'openai', 'anthropic', 'google', 'other'
    api_key: Optional[str] = None
    localModelUrl: Optional[str] = None 
    otherApiUrl: Optional[str] = None  # For provider='other' 