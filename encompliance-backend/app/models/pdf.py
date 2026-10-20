"""
PDF Model Module

This module provides backward compatibility for PDF document handling in the EnCompliance application.
It aliases the Document model to maintain compatibility with existing code.

Key functionalities:
- Backward compatibility layer
- PDF document type support
- Document model aliasing

Dependencies:
- app.models.document: For Document model import
"""

# Import Document from document.py for backward compatibility
from app.models.document import Document

# Keep the old PDF class name for backward compatibility
PDF = Document 