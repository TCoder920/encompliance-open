"""
Maryland Regulation Processing Service

This service processes extracted COMAR regulations and converts them
to the application's standard format with PDF generation.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.units import inch
from sqlalchemy.orm import Session
from app.models.regulation import Regulation
from app.models.facility_type import FacilityType
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class MarylandRegulationProcessor:
    """Process Maryland COMAR regulations into application format"""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.maryland_dir = os.path.join(storage_path, "regulations_by_state", "Maryland")
        os.makedirs(self.maryland_dir, exist_ok=True)
    
    def process_regulations(
        self, 
        regulations: List[Dict], 
        db: Session
    ) -> List[Dict]:
        """
        Process extracted regulations and create PDF documents
        
        Args:
            regulations: List of regulation dictionaries from COMAR extraction
            db: Database session
            
        Returns:
            List of processed regulation metadata
        """
        processed_regulations = []
        
        for reg_data in regulations:
            try:
                logger.info(f"Processing regulation: {reg_data.get('title', 'Unknown')}")
                
                # Generate PDF document
                pdf_filename = self._generate_pdf_document(reg_data)
                
                # Create regulation record
                regulation_record = self._create_regulation_record(
                    reg_data, pdf_filename, db
                )
                
                if regulation_record:
                    processed_regulations.append({
                        "id": regulation_record.id,
                        "filename": pdf_filename,
                        "title": regulation_record.document_title,
                        "subtitle_code": reg_data.get("subtitle_code"),
                        "facility_type": reg_data.get("facility_type")
                    })
                    logger.info(f"Successfully processed: {pdf_filename}")
                    
            except Exception as e:
                logger.error(f"Error processing regulation {reg_data.get('title', 'Unknown')}: {str(e)}")
                continue
        
        return processed_regulations
    
    def create_regulation_pdf(self, reg_data: Dict) -> str:
        """
        Public method to create a PDF from regulation data
        
        Args:
            reg_data: Regulation dictionary with content and metadata
            
        Returns:
            Full path to the generated PDF file
        """
        filename = self._generate_pdf_document(reg_data)
        return os.path.join(self.maryland_dir, filename)
    
    def _generate_pdf_document(self, reg_data: Dict) -> str:
        """Generate PDF document from regulation data"""
        
        # Create filename based on subtitle code
        subtitle_code = reg_data.get("subtitle_code", "").replace("_", "")
        subtitle_name = self._get_subtitle_name(subtitle_code)
        filename = f"MD_COMAR_{subtitle_code.upper()}_{subtitle_name}.pdf"
        filepath = os.path.join(self.maryland_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(
            filepath, 
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Build document content
        content = []
        
        # Title
        content.append(Paragraph("Maryland Code of Regulations (COMAR)", title_style))
        content.append(Paragraph(f"Title 13A: State Board of Education", title_style))
        content.append(Paragraph(f"{reg_data.get('title', '')}", title_style))
        content.append(Spacer(1, 30))
        
        # Metadata section
        content.append(Paragraph("Document Information", heading_style))
        content.append(Paragraph(f"<b>Document Type:</b> {reg_data.get('document_type', 'Regulation')}", info_style))
        content.append(Paragraph(f"<b>Facility Type:</b> {reg_data.get('facility_type', '')}", info_style))
        content.append(Paragraph(f"<b>State/Territory:</b> {reg_data.get('state_territory', 'Maryland')}", info_style))
        content.append(Paragraph(f"<b>Last Updated:</b> {reg_data.get('last_updated', '')}", info_style))
        content.append(Paragraph(f"<b>Source URL:</b> {reg_data.get('source_url', '')}", info_style))
        content.append(Paragraph(f"<b>Last Accessed:</b> {reg_data.get('last_accessed', '')}", info_style))
        content.append(Spacer(1, 30))
        
        # Content section
        content.append(Paragraph("Regulation Content", heading_style))
        content.append(Spacer(1, 12))
        
        # Process the regulation content
        text_content = reg_data.get('content', '')
        if text_content:
            # Split content into manageable paragraphs
            paragraphs = self._split_content_into_paragraphs(text_content)
            
            for para in paragraphs:
                if para.strip():
                    # Check if this looks like a section header
                    if self._is_section_header(para):
                        content.append(Spacer(1, 12))
                        try:
                            content.append(Paragraph(para.strip(), heading_style))
                        except Exception as e:
                            # If paragraph fails, add as plain text
                            logger.warning(f"Failed to add header paragraph: {str(e)}")
                            content.append(Paragraph(self._clean_text_for_pdf(para.strip()), heading_style))
                        content.append(Spacer(1, 6))
                    else:
                        try:
                            content.append(Paragraph(para.strip(), styles['Normal']))
                        except Exception as e:
                            # If paragraph fails, add as plain text
                            logger.warning(f"Failed to add paragraph: {str(e)}")
                            content.append(Paragraph(self._clean_text_for_pdf(para.strip()), styles['Normal']))
                        content.append(Spacer(1, 6))
        else:
            content.append(Paragraph("Content extraction in progress. Please refer to the source URL for complete regulations.", styles['Normal']))
        
        # Build PDF
        try:
            doc.build(content)
            logger.info(f"PDF generated successfully: {filepath}")
        except Exception as e:
            logger.error(f"Error building PDF {filepath}: {str(e)}")
            raise
        
        return filename
    
    def _get_subtitle_name(self, subtitle_code: str) -> str:
        """Get clean subtitle name for filename"""
        name_mapping = {
            "13a15": "Family_Child_Care",
            "13a16": "Child_Care_Centers", 
            "13a17": "Letters_of_Compliance",
            "13a18": "Large_Family_Child_Care_Homes"
        }
        return name_mapping.get(subtitle_code.lower(), "Unknown")
    
    def _clean_text_for_pdf(self, text: str) -> str:
        """Clean text to avoid XML parsing errors in ReportLab"""
        # Escape XML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        
        # Remove any unclosed tags or problematic patterns
        import re
        # Remove standalone < or > that aren't part of entities
        text = re.sub(r'(?<!&lt)(?<!&gt)(?<!&amp)(?<!&quot)(?<!&apos);', ';', text)
        
        return text
    
    def _split_content_into_paragraphs(self, content: str) -> List[str]:
        """Split content into manageable paragraphs"""
        
        # Clean the content first
        content = self._clean_text_for_pdf(content)
        
        # Split by double newlines first
        paragraphs = content.split('\n\n')
        
        # Further split very long paragraphs
        final_paragraphs = []
        for para in paragraphs:
            if len(para) > 1000:  # If paragraph is too long
                # Split by sentences
                sentences = para.split('. ')
                current_para = ""
                for sentence in sentences:
                    if len(current_para + sentence) > 800:
                        if current_para:
                            final_paragraphs.append(current_para.strip())
                        current_para = sentence
                    else:
                        current_para += sentence + ". " if not sentence.endswith('.') else sentence + " "
                if current_para:
                    final_paragraphs.append(current_para.strip())
            else:
                final_paragraphs.append(para)
        
        return final_paragraphs
    
    def _is_section_header(self, text: str) -> bool:
        """Determine if text looks like a section header"""
        
        # Check for common section header patterns
        header_patterns = [
            r'^\d+[a-z]*\.\d+\.\d+',  # COMAR numbering like 13A.15.01
            r'^Chapter \d+',
            r'^Section \d+',
            r'^[A-Z][A-Z\s]+$',  # All caps text
        ]
        
        import re
        for pattern in header_patterns:
            if re.match(pattern, text.strip()):
                return True
        
        # Check if it's short and looks like a title
        if len(text.strip()) < 100 and text.strip().isupper():
            return True
            
        return False
    
    def _create_regulation_record(
        self, 
        reg_data: Dict, 
        pdf_filename: str, 
        db: Session
    ) -> Optional[Regulation]:
        """Create regulation database record"""
        
        try:
            # Check if regulation already exists
            existing = db.query(Regulation).filter(
                Regulation.state_territory == "Maryland",
                Regulation.file_name == pdf_filename
            ).first()
            
            if existing:
                logger.info(f"Regulation {pdf_filename} already exists, updating...")
                existing.document_title = reg_data.get('title', '')
                existing.last_updated = datetime.strptime(reg_data.get('last_updated', '02/05/2024'), '%m/%d/%Y').date()
                db.commit()
                return existing
            
            # Create new regulation
            regulation = Regulation(
                state_territory="Maryland",
                document_title=reg_data.get('title', ''),
                document_type=reg_data.get('document_type', 'Regulation'),
                file_name=pdf_filename,
                last_updated=datetime.strptime(reg_data.get('last_updated', '02/05/2024'), '%m/%d/%Y').date()
            )
            
            db.add(regulation)
            db.flush()  # Get ID without committing
            
            # Associate with facility type
            facility_type_name = reg_data.get('facility_type', '')
            if facility_type_name:
                facility_type = db.query(FacilityType).filter(
                    FacilityType.name == facility_type_name
                ).first()
                
                if not facility_type:
                    # Create new facility type if it doesn't exist
                    facility_type = FacilityType(name=facility_type_name)
                    db.add(facility_type)
                    db.flush()
                    logger.info(f"Created new facility type: {facility_type_name}")
                
                regulation.facility_types.append(facility_type)
            
            db.commit()
            logger.info(f"Created regulation record: {regulation.id}")
            return regulation
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating regulation record: {str(e)}")
            return None 