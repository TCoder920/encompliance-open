from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.regulation import Regulation

class UserDocumentBase(BaseModel):
    user_id: int
    regulation_id: int

class UserDocumentCreate(UserDocumentBase):
    pass

class UserDocument(UserDocumentBase):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class UserDocumentWithRegulation(BaseModel):
    id: int
    regulation: Regulation
    timestamp: datetime
    
    class Config:
        from_attributes = True

class UserDocumentsResponse(BaseModel):
    documents: List[Regulation] 