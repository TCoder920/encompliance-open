from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    filepath: str
    file_type: str
    file_size: int
    custom_label: Optional[str] = None  # User-defined label for document categorization

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    uploaded_at: datetime
    uploaded_by: int
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None

    class Config:
        from_attributes = True

class DocumentList(BaseModel):
    documents: list[DocumentResponse]

class DocumentLabelUpdate(BaseModel):
    custom_label: Optional[str] = None  # Allow updating or removing label 