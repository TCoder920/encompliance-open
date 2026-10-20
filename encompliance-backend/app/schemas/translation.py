"""
Translation Schemas
"""

from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    text: str = Field(..., max_length=4000)
    target_language: str = Field(default="es")
    source_language: str = Field(default="en")


class TranslationResponse(BaseModel):
    translated_text: str
    detected_source: str

