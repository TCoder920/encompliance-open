"""
Data Import Schemas
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DataImportRequest(BaseModel):
    payload: Dict[str, Any] = Field(..., description="Export payload to import.")
    dry_run: bool = Field(default=True)


class DataImportResult(BaseModel):
    dry_run: bool
    records_created: int
    warnings: Optional[list] = None

