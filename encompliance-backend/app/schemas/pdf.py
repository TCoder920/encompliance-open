# Import from document schema for backwards compatibility
from app.schemas.document import DocumentBase, DocumentCreate, DocumentResponse, DocumentList
from pydantic import BaseModel

# Alias classes for backwards compatibility
PDFBase = DocumentBase
PDFCreate = DocumentCreate
PDFResponse = DocumentResponse

class PDFList(BaseModel):
    pdfs: list[PDFResponse] 