"""
Export File Service Module

This module provides file generation for data exports in multiple formats.
It handles JSON, CSV, and PDF export file creation from extracted user data.

Key functionalities:
- JSON export with hierarchical structure preservation
- CSV export with multiple files packaged in ZIP
- PDF export with structured document formatting
- File storage in dedicated export directory
- Document library integration with quota exclusion
- Secure file handling and cleanup

Dependencies:
- json: For JSON file generation
- csv: For CSV file creation
- reportlab: For PDF generation
- zipfile: For CSV archive packaging
- pathlib: For file system operations

Educational Note: Implements multiple export formats with proper data serialization
Reference: Python JSON/CSV modules, ReportLab PDF library documentation
"""

import json
import csv
import zipfile
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import logging
import io
import tempfile

from sqlalchemy.orm import Session
from app.models.document import Document
from app.core.config import get_settings

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

logger = logging.getLogger(__name__)
settings = get_settings()

class ExportFileService:
    """Service for generating export files in multiple formats."""
    
    @staticmethod
    def get_export_directory() -> Path:
        """Get or create the export directory path."""
        try:
            # Create exports directory in storage
            project_root = Path(__file__).resolve().parents[3]
            export_dir = project_root / "storage" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir
        except Exception as e:
            logger.error(f"Error creating export directory: {str(e)}")
            # Fallback to temp directory
            return Path(tempfile.gettempdir()) / "encompliance_exports"
    
    @staticmethod
    def generate_export_file(
        extracted_data: Dict[str, Any], 
        format_type: str, 
        export_id: str
    ) -> Optional[Path]:
        """Generate export file in specified format."""
        try:
            export_dir = ExportFileService.get_export_directory()
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            if format_type.lower() == "json":
                return ExportFileService._generate_json_file(
                    extracted_data, export_dir, export_id, timestamp
                )
            elif format_type.lower() == "csv":
                return ExportFileService._generate_csv_archive(
                    extracted_data, export_dir, export_id, timestamp
                )
            elif format_type.lower() == "pdf":
                return ExportFileService._generate_pdf_file(
                    extracted_data, export_dir, export_id, timestamp
                )
            else:
                logger.error(f"Unsupported export format: {format_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating export file: {str(e)}")
            return None
    
    @staticmethod
    def _generate_json_file(
        data: Dict[str, Any], 
        export_dir: Path, 
        export_id: str, 
        timestamp: str
    ) -> Path:
        """Generate JSON export file."""
        filename = f"export_{export_id}_{timestamp}.json"
        file_path = export_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Generated JSON export file: {file_path}")
        return file_path
    
    @staticmethod
    def _generate_csv_archive(
        data: Dict[str, Any], 
        export_dir: Path, 
        export_id: str, 
        timestamp: str
    ) -> Path:
        """Generate CSV export as ZIP archive with multiple CSV files."""
        archive_filename = f"export_{export_id}_{timestamp}.zip"
        archive_path = export_dir / archive_filename
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Create CSV for each data type
            for data_type, records in data.items():
                if data_type == "export_metadata":
                    continue
                
                csv_filename = f"{data_type}.csv"
                csv_content = ExportFileService._convert_to_csv(records, data_type)
                
                # Add CSV to archive
                zipf.writestr(csv_filename, csv_content)
            
            # Add metadata file
            if "export_metadata" in data:
                metadata_csv = ExportFileService._convert_to_csv(
                    [data["export_metadata"]], "export_metadata"
                )
                zipf.writestr("export_metadata.csv", metadata_csv)
        
        logger.info(f"Generated CSV archive: {archive_path}")
        return archive_path
    
    @staticmethod
    def _convert_to_csv(records: Any, data_type: str) -> str:
        """Convert records to CSV format."""
        if not records:
            return f"# No data available for {data_type}\n"
        
        output = io.StringIO()
        
        # Handle different data structures
        if isinstance(records, list) and records:
            # Get headers from first record
            if isinstance(records[0], dict):
                headers = ExportFileService._flatten_dict_keys(records[0])
                writer = csv.DictWriter(output, fieldnames=headers)
                writer.writeheader()
                
                for record in records:
                    flattened = ExportFileService._flatten_dict(record)
                    writer.writerow(flattened)
            else:
                # Simple list
                writer = csv.writer(output)
                writer.writerow([data_type])
                for item in records:
                    writer.writerow([str(item)])
        
        elif isinstance(records, dict):
            # Single dictionary record
            flattened = ExportFileService._flatten_dict(records)
            headers = list(flattened.keys())
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            writer.writerow(flattened)
        
        else:
            # Single value
            writer = csv.writer(output)
            writer.writerow([data_type, str(records)])
        
        return output.getvalue()
    
    @staticmethod
    def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary for CSV export."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(ExportFileService._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to string representation
                items.append((new_key, json.dumps(v) if v else ""))
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    @staticmethod
    def _flatten_dict_keys(d: Dict, parent_key: str = '', sep: str = '_') -> List[str]:
        """Get flattened keys from dictionary."""
        keys = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                keys.extend(ExportFileService._flatten_dict_keys(v, new_key, sep=sep))
            else:
                keys.append(new_key)
        
        return keys
    
    @staticmethod
    def _generate_pdf_file(
        data: Dict[str, Any], 
        export_dir: Path, 
        export_id: str, 
        timestamp: str
    ) -> Optional[Path]:
        """Generate PDF export file."""
        if not HAS_REPORTLAB:
            logger.error("ReportLab not available for PDF generation")
            return None
        
        filename = f"export_{export_id}_{timestamp}.pdf"
        file_path = export_dir / filename
        
        try:
            doc = SimpleDocTemplate(str(file_path), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                textColor=colors.darkblue
            )
            story.append(Paragraph("EnCompliance Data Export", title_style))
            story.append(Spacer(1, 12))
            
            # Export metadata
            if "export_metadata" in data:
                metadata = data["export_metadata"]
                story.append(Paragraph("Export Information", styles['Heading2']))
                
                metadata_data = [
                    ["Export ID", export_id],
                    ["Generated", metadata.get("extraction_timestamp", "Unknown")],
                    ["User ID", str(metadata.get("user_id", "Unknown"))],
                    ["Data Types", ", ".join(metadata.get("data_types_requested", []))]
                ]
                
                metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
                metadata_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(metadata_table)
                story.append(Spacer(1, 20))
            
            # Data sections
            for data_type, records in data.items():
                if data_type == "export_metadata":
                    continue
                
                # Section header
                section_title = data_type.replace("_", " ").title()
                story.append(Paragraph(section_title, styles['Heading2']))
                story.append(Spacer(1, 12))
                
                # Data summary
                if isinstance(records, list):
                    count_text = f"Total records: {len(records)}"
                elif isinstance(records, dict):
                    count_text = "Profile information"
                else:
                    count_text = "Data available"
                
                story.append(Paragraph(count_text, styles['Normal']))
                story.append(Spacer(1, 12))
                
                # Sample data table (first few records)
                if isinstance(records, list) and records:
                    sample_records = records[:5]  # Show first 5 records
                    table_data = ExportFileService._prepare_table_data(sample_records)
                    
                    if table_data:
                        data_table = Table(table_data)
                        data_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        
                        story.append(data_table)
                
                elif isinstance(records, dict):
                    # Profile data
                    profile_data = [[k, str(v)] for k, v in records.items() if k != "notification_settings"]
                    if profile_data:
                        profile_table = Table(profile_data[:10])  # Show first 10 fields
                        profile_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        
                        story.append(profile_table)
                
                story.append(PageBreak())
            
            # Footer note
            story.append(Paragraph(
                f"This export was generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC.",
                styles['Normal']
            ))
            
            # Build PDF
            doc.build(story)
            logger.info(f"Generated PDF export file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return None
    
    @staticmethod
    def _prepare_table_data(records: List[Dict]) -> List[List[str]]:
        """Prepare data for PDF table display."""
        if not records:
            return []
        
        # Get common keys from first few records
        all_keys = set()
        for record in records[:3]:
            if isinstance(record, dict):
                all_keys.update(record.keys())
        
        # Limit to most important keys and truncate values
        important_keys = []
        for key in ["id", "title", "filename", "created_at", "updated_at", "type", "status"]:
            if key in all_keys:
                important_keys.append(key)
        
        # Add other keys up to limit
        remaining_keys = [k for k in all_keys if k not in important_keys]
        important_keys.extend(remaining_keys[:4])  # Limit total columns
        
        if not important_keys:
            return []
        
        # Create table data
        table_data = [important_keys]  # Header row
        
        for record in records:
            if isinstance(record, dict):
                row = []
                for key in important_keys:
                    value = str(record.get(key, ""))
                    # Truncate long values
                    if len(value) > 30:
                        value = value[:27] + "..."
                    row.append(value)
                table_data.append(row)
        
        return table_data
    
    @staticmethod
    def add_to_document_library(
        db: Session, 
        user_id: int, 
        file_path: Path, 
        format_type: str, 
        export_id: str
    ) -> Optional[int]:
        """Add export file to user's document library with quota exclusion."""
        try:
            # Get file info
            file_size = file_path.stat().st_size
            filename = f"data_export_{export_id}.{format_type.lower()}"
            
            # Create document record
            document = Document(
                filename=filename,
                filepath=str(file_path),
                file_type=f"export/{format_type.lower()}",
                file_size=file_size,
                uploaded_by=user_id,
                is_deleted=False
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            logger.info(f"Added export file to document library: {filename} (ID: {document.id})")
            return document.id
            
        except Exception as e:
            logger.error(f"Error adding export to document library: {str(e)}")
            return None
    
    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """Get file size in bytes."""
        try:
            return file_path.stat().st_size
        except Exception:
            return 0
    
    @staticmethod
    def cleanup_export_file(file_path: str) -> bool:
        """Clean up export file from filesystem."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Cleaned up export file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up export file {file_path}: {str(e)}")
            return False 