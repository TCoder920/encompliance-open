# Document Labeling Feature

## Overview
The document labeling feature allows users to assign custom labels to uploaded documents, helping categorize files such as 'Policy', 'Training', or 'Rosters'. These labels are user-defined rather than auto-generated and enhance document organization and identification.

## Implementation Details

### Backend Changes

#### 1. Database Schema
- **Table**: `documents`
- **New Field**: `custom_label` (String, nullable)
- **Migration**: `94dbc744764b_add_custom_label_to_documents_only.py`

#### 2. Models & Schemas
- **Document Model**: Added `custom_label` field
- **DocumentBase Schema**: Added optional `custom_label` field
- **DocumentLabelUpdate Schema**: New schema for label updates

#### 3. API Endpoints

##### Upload with Label
- **Endpoint**: `POST /documents/upload`
- **Parameters**: 
  - `file`: UploadFile (required)
  - `custom_label`: Optional[str] (Form data, max 255 chars)
- **Validation**: Label length validation, trimming, null handling

##### Update Label
- **Endpoint**: `PUT /documents/{document_id}/label`
- **Body**: `DocumentLabelUpdate` schema
- **Authorization**: User must own the document
- **Validation**: Label length validation, permission checks

##### List Documents
- **Endpoint**: `GET /documents/list`
- **Response**: Includes `custom_label` field in document objects

### Frontend Changes

#### 1. Document Upload Component
- **File**: `src/components/DocumentUploader.tsx`
- **Features**:
  - Optional custom label input field
  - Real-time validation (255 char limit)
  - Placeholder suggestions: 'Policy', 'Training', 'Rosters'
  - Enhanced upload workflow with label support

#### 2. Document Label Editor
- **File**: `src/components/DocumentLabelEditor.tsx`
- **Features**:
  - Inline label editing with hover UI
  - Save/cancel actions with keyboard shortcuts
  - Real-time validation and error handling
  - Click-to-edit functionality

#### 3. Document Display Logic
- **Primary Title**: Custom label (if exists) or filename
- **Subtitle**: Original filename (when custom label exists)
- **Fallback**: Filename as primary title when no label

#### 4. Service Layer Updates
- **documentService.ts**: Added `uploadDocument(file, customLabel?)` and `updateDocumentLabel()`
- **pdfService.ts**: Updated `uploadPDF()` to support labels
- **Document Interface**: Added `custom_label?` field

## User Experience

### Upload Flow
1. User selects file for upload
2. Optional: User enters custom label (e.g., "Policy", "Training")
3. System validates label (max 255 characters)
4. Document uploads with label metadata

### Display & Management
1. **With Label**: Label appears as main title, filename as subtitle
2. **Without Label**: Filename appears as main title
3. **Edit Label**: Hover over document → click edit icon → inline editing
4. **Remove Label**: Edit and clear text → reverts to filename display

### Label Examples
- `Policy` → "Employee Handbook.pdf"
- `Training` → "Safety_Training_Manual.docx"
- `Rosters` → "Staff_Schedule_Q1.xlsx"
- `Compliance` → "OSHA_Requirements.pdf"

## Technical Features

### Validation
- Maximum 255 characters
- Automatic trimming of whitespace
- Empty strings converted to null
- Prevents duplicate processing

### Security
- User ownership validation
- Permission-based label updates
- SQL injection protection
- XSS prevention through proper encoding

### Performance
- Minimal database impact (single nullable column)
- Efficient queries with proper indexing
- Cached document lists for frontend performance

### Error Handling
- Graceful degradation when labels fail to load
- User-friendly error messages
- Backend validation with detailed responses

## Database Migration
```sql
-- Migration: 94dbc744764b_add_custom_label_to_documents_only
ALTER TABLE documents ADD COLUMN custom_label VARCHAR(255) NULL;
```

## API Examples

### Upload with Label
```bash
curl -X POST /documents/upload \
  -F "file=@policy.pdf" \
  -F "custom_label=Policy" \
  -H "Authorization: Bearer <token>"
```

### Update Label
```bash
curl -X PUT /documents/123/label \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"custom_label": "Training Materials"}'
```

### Response Format
```json
{
  "id": 123,
  "filename": "employee_handbook.pdf",
  "custom_label": "Policy",
  "file_type": "pdf",
  "file_size": 2048576,
  "uploaded_at": "2025-06-01T12:00:00Z"
}
```

## Future Enhancements
- Label suggestions based on file content
- Label categories and color coding
- Bulk label operations
- Label-based search and filtering
- Label usage analytics 