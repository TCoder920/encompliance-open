# EnCompliance Project

## Purpose
This project is a comprehensive compliance management system that helps organizations track, manage, and maintain regulatory compliance requirements. It provides a user-friendly interface for compliance officers and administrators to monitor compliance status, generate reports, and manage documentation.

## Components

### Frontend (encompliance-frontend)
The frontend is built with Vue.js and provides the user interface for both regular users and administrators. It includes:
- User dashboard for compliance tracking
- Document management system
- Report generation interface
- Administrative controls

### Backend (encompliance-backend)
The backend is built with Python and Flask, providing:
- RESTful API endpoints
- Database management
- Document processing
- Authentication and authorization
- Integration with external services

### Database
PostgreSQL database for storing:
- User information
- Compliance records
- Document metadata
- System configurations

### Storage
Dedicated storage system for:
- Compliance documents
- Generated reports
- User uploads

## Project Structure

The application consists of two main components:

- **Frontend** (`encompliance-frontend/`) - React/TypeScript SPA using Vite and Tailwind CSS
- **Backend** (`encompliance-backend/`) - Python FastAPI application with PostgreSQL

## Security Features

This application implements comprehensive security measures following OWASP best practices:

- Content Security Policy (CSP) headers
- CSRF protection
- Secure authentication with JWT tokens
- Input sanitization and validation
- SQL injection protection
- Secure password policies

For detailed security documentation, see [`docs/SECURITY.md`](docs/SECURITY.md).

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- PostgreSQL 14+

### Backend Setup

```bash
cd encompliance-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The backend will start on http://localhost:8000

### Frontend Setup

```bash
cd encompliance-frontend
npm install
npm run dev
```

The frontend will start on http://localhost:5174

## Authentication

The application uses JWT token-based authentication with the following flow:

1. User submits credentials via login form
2. Backend validates credentials and issues a JWT token
3. Frontend stores the token in localStorage
4. Token is included in subsequent API requests

The backend provides two authentication endpoints:
- `/api/v1/login` - Form-based OAuth2 authentication
- `/api/v1/email-login` - JSON-based authentication (recommended for frontend apps)

## API Routes

The backend exposes the following API routes:

- Authentication: `/api/v1/login`, `/api/v1/email-login`, `/api/v1/signup`
- User management: `/api/v1/users/*`
- Document handling: `/api/v1/documents/*`
- Chat: `/api/v1/chat/*`
- Settings: `/api/v1/settings/*`

## Development Guidelines

- Follow the established coding style in each repository
- Add proper JSDoc/docstring comments to all new code
- Maintain test coverage for critical functionality
- Ensure all frontend components have appropriate accessibility attributes

## Production Deployment

For production deployment, ensure:

1. All environment variables are properly set
2. Security features are fully enabled
3. Debug logging is disabled
4. HTTPS is enforced for all connections

## License

[Proprietary] - All rights reserved.

## Features

- FastAPI-based REST API
- PostgreSQL database for user authentication
- JWT-based authentication
- Local LLM integration
- PDF document processing

## Configuration

- **Database URL**: Set via `DATABASE_URL` environment variable.
- **JWT Secret**: Set via `JWT_SECRET_KEY` environment variable.
- **Document Storage**: Configured via `PDF_STORAGE_PATH` in `app/core/config.py`. The default location is the `storage/encompliance-documents` directory at the project root.

### Database

- The application uses PostgreSQL for storing user information and document metadata.
- Metadata includes filename, upload time, user association, etc., but the actual files are stored in the `storage/encompliance-documents` directory with timestamped filenames to prevent collisions.

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL
- LM Studio (for local model support)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/encompliance-backend.git
cd encompliance-backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the PostgreSQL database:
```bash
# Create a new PostgreSQL database
createdb encompliance

# Initialize the database with tables and admin user
python init_db.py
```

5. Configure environment variables:
   - Copy the `.env.example` file to `.env`
   - Update the values in the `.env` file with your configuration

6. Start the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Authentication

The API uses JWT-based authentication. To access protected endpoints:

1. Register a new user:
```bash
curl -X POST http://localhost:8000/api/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "testuser", "password": "password123"}'
```

2. Login to get a JWT token:
```bash
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

3. Use the token to access protected endpoints:
```bash
curl -X GET http://localhost:8000/api/v1/me \
  -H "Authorization: Bearer <TOKEN>"
```

## License

[MIT License](LICENSE)

## OpenAI Integration

This section describes the OpenAI integration implemented in the EnCompliance backend.

### Overview

The EnCompliance project integrates with OpenAI for document management and Retrieval-Augmented Generation (RAG) chat capabilities. The integration follows these core principles:

1.  **User-Specific Vector Stores**: Each user has a dedicated OpenAI Vector Store associated with them.
2.  **Document Handling**: All documents relevant to a user (manual uploads and assigned regulations) are uploaded to OpenAI Files and added to the user's Vector Store.
3.  **Chat**: Chat queries use the OpenAI Assistants API with the `file_search` tool, restricted to query only the Vector Store belonging to the currently interacting user.
4.  **Asynchronous Operations**: All OpenAI API calls are made using `async`/`await` compatible with the FastAPI framework.

### Features

#### Vector Stores

-   Each user gets a dedicated Vector Store in OpenAI.
-   The Vector Store ID is stored in the `openai_vector_store_id` field of the User model.
-   A helper function `get_or_create_user_vector_store` handles creating Vector Stores when needed.

#### Document Handling

-   When a user uploads a document, it's also uploaded to OpenAI Files.
-   The OpenAI File ID is stored in the `openai_file_id` field of the Document model.
-   The file is added to the user's Vector Store.
-   When a document is deleted, it's also deleted from OpenAI Files.

#### Regulation Handling

-   When a user is associated with a regulation, the regulation file is uploaded to OpenAI Files if not already uploaded.
-   The OpenAI File ID is stored in the `openai_file_id` field of the Regulation model.
-   The file is added to the user's Vector Store.
-   When a user is no longer associated with a regulation, the file is removed from the user's Vector Store (but not deleted from OpenAI Files).

#### Chat

-   Chat uses the OpenAI Assistants API with the `file_search` tool.
-   The Assistant ID is configured in the `OPENAI_ASSISTANT_ID` setting.
-   Each conversation creates a thread in the Assistants API.
-   The `conversation_id` is used to link chats to threads.
-   The chat queries are restricted to the user's Vector Store.

### Configuration

The following environment variables need to be set in the `.env` file:

```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENAI_ASSISTANT_ID=your_assistant_id
```

### Setup for OpenAI Integration

1.  Create an Assistant in the OpenAI platform with the `file_search` tool enabled.
2.  Add the Assistant ID to the `OPENAI_ASSISTANT_ID` variable in the `.env` file.
3.  Ensure the database migrations are up-to-date: `python -m alembic upgrade head`

### Database Schema Changes

The following fields were added to the database for OpenAI integration:

-   **User**: `openai_vector_store_id` (String) - The ID of the user's Vector Store in OpenAI.
-   **Document**: `openai_file_id` (String) - The ID of the document in OpenAI Files.
-   **Regulation**: `openai_file_id` (String) - The ID of the regulation file in OpenAI Files.

### Implementation Details

#### OpenAI Utilities (`app/core/openai_utils.py`)

-   `get_or_create_user_vector_store`: Creates a Vector Store for a user if one doesn't exist.
-   `upload_regulation_to_openai`: Uploads a regulation file to OpenAI Files.

#### Document Routes (`app/api/routes/documents.py`)

-   `upload_document`: Uploads files to OpenAI and adds them to the user's Vector Store.
-   `delete_document`: Deletes files from OpenAI.

#### User-Regulation Association (`app/api/routes/auth.py`)

-   `associate_user_documents`: Handles creating and removing associations, including uploading regulation files to OpenAI and adding/removing them from the user's Vector Store.

#### LLM Service (`app/services/llm_service.py`)

-   `get_llm_response`: Uses the Assistants API to generate responses.
-   `get_assistant_response`: Handles polling for non-streaming responses.
-   `stream_assistant_response`: Handles streaming responses. 

## Overview

The system maintains a synchronized copy of each user's document library in their dedicated OpenAI vector store. This allows OpenAI Assistants to reference and search through user-specific documents when answering queries.

## Key Components

### 1. Vector Store Synchronization (`update_vector_store`)

The `update_vector_store` function ensures that:
- Each user has a dedicated OpenAI vector store
- All documents in the user's library are uploaded to OpenAI and linked to their vector store
- Any OpenAI files that no longer exist in the user's library are removed from the vector store and deleted from OpenAI

```python
async def update_vector_store(user_id: int, db: Session, openai_client: AsyncOpenAI, storage_path: str) -> Dict[str, Any]:
    # Logic to synchronize user's documents with their OpenAI vector store
```

### 2. Logout File Cleanup (`delete_user_openai_files`)

When a user logs out, the `delete_user_openai_files` function is triggered to:
- Delete all OpenAI files associated with the user from OpenAI storage
- Remove those file IDs from the user's vector store
- Clear OpenAI file IDs from the user's document records in the database

```python
async def delete_user_openai_files(user_id: int, db: Session, openai_client: AsyncOpenAI) -> Dict[str, Any]:
    # Logic to delete OpenAI files during logout
```

### 3. Assistant Model Configuration (`configure_assistant_with_user_model`)

This function ensures that when the OpenAI Assistant is created or updated for a user, it uses the correct model based on the user's subscription:
- Basic users get `gpt-4.1-nano`
- Pro users get `gpt-4.1-mini`

```python
async def configure_assistant_with_user_model(user_id: int, db: Session, openai_client: AsyncOpenAI) -> Dict[str, Any]:
    # Logic to configure the model for the user's assistant
```

## Integration Points

The vector store synchronization is automatically triggered at these key points:

1. **User Signup**: After successful user signup, `update_vector_store` is called to initialize the user's vector store.

2. **User Login**: When a user logs in, `update_vector_store` is called to ensure their vector store is up-to-date.

3. **Document Upload**: When a user uploads a new document, `update_vector_store` is called to add the document to their vector store.

4. **Document Deletion**: When a user deletes a document, `update_vector_store` is called to remove the document from their vector store.

5. **User Logout**: When a user logs out, `delete_user_openai_files` is called to clean up their OpenAI files.

## Database Schema

The integration relies on these fields in the database:

1. `User.openai_vector_store_id`: Stores the ID of the user's OpenAI vector store.
2. `User.openai_assistant_id`: Stores the ID of the user's OpenAI assistant.
3. `Document.openai_file_id`: Stores the ID of the OpenAI file corresponding to each document.

## Error Handling

All functions include robust error handling to ensure that:
- Errors during vector store operations don't interrupt critical user flows (signup, login, etc.)
- Detailed logs are generated for debugging purposes
- Success/failure status and error details are returned for potential UI feedback

## Usage in Client Code

To manually trigger a vector store update (if needed):

```python
from app.core.openai_utils import update_vector_store
from app.core.config import get_settings
from openai import AsyncOpenAI

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Get storage path
storage_path = get_settings().PDF_STORAGE_PATH

# Update vector store
result = await update_vector_store(user_id, db, openai_client, storage_path)
if not result["success"]:
    print(f"Errors occurred: {result['errors']}")
else:
    print(f"Added {result['new_files_added']} files, removed {result['files_removed']} files")
```

## Encompliance Citation System

This section explains the implementation of the citation system in Encompliance, which allows the AI assistant to reference specific sources with clickable links.

### Overview

The citation system allows the AI to reference specific documents, pages, and sections using a standardized format: `【documentIndex:pageNumber†sourceName】`. These citations are automatically transformed into clickable components that link directly to the referenced material.

### Components

The citation system consists of several components:

1.  **Backend Implementation:**
    *   Updated system instructions in `encompliance-backend/app/core/config.py` to guide the AI to use the citation format
    *   Updated validation in `encompliance-backend/app/utils/response_validation.py` to accept and enforce the citation format
    *   Modified `encompliance-backend/app/core/chat_utils.py` to include citation format in operation-specific prompts

2.  **Frontend Implementation:**
    *   `encompliance-frontend/src/components/SourceCitation.tsx`: React component that renders individual citations as clickable links
    *   `encompliance-frontend/src/components/CitationRenderer.tsx`: Custom renderer for ReactMarkdown that processes citation markers
    *   `encompliance-frontend/src/utils/citationUtils.ts`: Utility functions for parsing and handling citation formats
    *   Integration with the `encompliance-frontend/src/components/AIChat.tsx` component to use the citation renderer

3.  **Testing and Documentation:**
    *   `encompliance-frontend/src/pages/CitationTestPage.tsx`: Test page to visualize and experiment with citation formats
    *   `encompliance-frontend/src/docs/CitationFormat.md`: Documentation for content authors and developers

### Citation Format

The citation format is:

```
【documentIndex:pageNumber†sourceName】
```

Where:
-   `documentIndex` is the numerical index of the document (e.g., 1, 2, 3) passed in the context to the AI.
-   `pageNumber` is the specific page within the document.
-   `sourceName` (optional) is the name of the source document.

Examples:
-   `【1:42†Texas Daycare Manual】` - Document 1, page 42, source "Texas Daycare Manual"
-   `【2:15】` - Document 2, page 15, no source name specified

### How It Works

1.  The AI responds with citations in the standardized format.
2.  The frontend (`CitationRenderer.tsx` using `citationUtils.ts`) parses these citations using regex patterns.
3.  Each citation is converted to a `SourceCitation` component.
4.  Clicking a citation component should trigger navigation to the `DocumentViewerPage` with the appropriate document ID and page number.

### Usage for Developers (Frontend)

To use the citation system in a new component rendering Markdown:

```tsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import createCitationRenderer from '../components/CitationRenderer';

// Assuming 'navigateTo' function is available for handling navigation
// and 'documentMap' provides mapping from docIndex to actual document ID/data

// In your component:
<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  components={createCitationRenderer(navigateTo, documentMap)} // Pass necessary props
>
  {markdownTextWithCitations}
</ReactMarkdown>
```

### Testing

You can test the citation system using the Citation Test Page, typically accessible at `/citation-test` in development mode. This page provides a live editor and preview to see how citations are rendered.

### Future Improvements

Potential enhancements for the citation system:

1.  Integration with document viewer to scroll to specific locations/sections.
2.  Support for section references in addition to page numbers.
3.  Custom styling options for citations.
4.  Citation summary view showing all references in a response.
5.  Document cache integration to ensure references are available offline

### Resources

-   [ReactMarkdown Documentation](https://github.com/remarkjs/react-markdown)
-   [OpenAI Documentation on Citations](https://platform.openai.com/docs/guides/function-calling) 

## Running the Application

### Backend (Main API)

```bash
cd encompliance-backend
# Install dependencies
pip install -r requirements.txt
# Set up environment variables (copy .env.example to .env and fill)
# Run database migrations (if using Alembic)
# alembic upgrade head 
# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Backend (Customer Support Portal API)

**Important Security Note:** The support portal API provides privileged access. **Do not expose port 8001 directly to the public internet.** Access should be restricted to trusted networks, ideally via a VPN or secure internal network configuration. Consider implementing IP allowlisting or mTLS at the infrastructure level.

```bash
cd encompliance-backend
# Ensure dependencies are installed (pip install -r requirements.txt)
# Ensure environment variables are set (check .env for SUPPORT_PORTAL secrets etc.)
# The support portal database (admin.db by default) will be created automatically on first run.
# For production, consider proper database setup and migrations.
# Run the support portal server
uvicorn app.support_portal_main:support_portal_app --host 0.0.0.0 --port 8001 --reload
```

### Frontend

```bash
cd encompliance-frontend
# Install dependencies
npm install
# Run the development server
npm run dev
```

## Security Considerations

*   **Environment Variables:** Never commit sensitive information like API keys or secret keys directly into the codebase. Use environment variables (`.env` file locally, system environment variables in production) and load them via `python-dotenv` (backend) or Vite's env handling (frontend).
*   **Input Validation:** Always validate and sanitize user input on both the frontend and backend to prevent injection attacks (SQLi, XSS, etc.). Use Pydantic for backend validation.
*   **Authentication & Authorization:** Use strong password hashing (bcrypt), JWT for stateless authentication, and implement role-based access control (RBAC) for sensitive endpoints.
*   **HTTPS:** Always use HTTPS in production to encrypt communication between the client and server.
*   **Dependencies:** Regularly update dependencies (`requirements.txt`, `package.json`) to patch known vulnerabilities. Use tools like `pip-audit` or `npm audit`.
*   **Admin API Security:** As mentioned above, the Admin API requires extra security measures. Restrict network access (VPN, firewall rules, IP allowlisting), use strong authentication (consider 2FA), enforce least privilege for admin roles, and monitor audit logs closely.
*   **Rate Limiting:** Implement rate limiting on APIs (especially login and public-facing endpoints) to prevent brute-force attacks.
*   **CORS:** Configure CORS policies carefully to only allow expected origins. 

## Admin Database Backup & Restore

To avoid committing large binary files, the admin database (`admin.db`) is ignored by git. Instead, we use a text-based SQL backup for version control.

### How to Backup the Admin Database

Run the following script to create a backup of the current `admin.db`:

```
./backup_admin_db.sh
```

This will update `encompliance-backend/admin_db_backup.sql` with the latest database state.

### How to Restore the Admin Database

To recreate `admin.db` from the backup SQL file, run:

```
./restore_admin_db.sh
```

### Version Control Policy

- **Do NOT commit `admin.db`** (it is listed in `.gitignore`).
- **Commit `admin_db_backup.sql`** and the backup/restore scripts to git.
- This keeps your repository small, fast, and easy to collaborate on.

### Why?

- Binary database files are large and change often, making them unsuitable for git.
- SQL backups are text-based, diffable, and much smaller.
- This workflow allows you to track and restore database state easily.

## New Features: Calendar and Paywall Integration

### Calendar Feature

The EnCompliance platform now includes a calendar system for scheduling and managing compliance-related events. This feature is available to Pro and Enterprise subscribers only.

#### Frontend Setup

1. Install the required dependencies:
```bash
cd encompliance-frontend
npm install @fullcalendar/react @fullcalendar/core @fullcalendar/daygrid @fullcalendar/timegrid @fullcalendar/interaction
```

2. The calendar component is available at:
```
encompliance-frontend/src/components/ui/Calendar/Calendar.tsx
```

3. You can import and use the Calendar component in your pages:
```tsx
import Calendar from '../components/ui/Calendar/Calendar';

function CalendarPage() {
  return (
    <div>
      <h1>Compliance Calendar</h1>
      <Calendar />
    </div>
  );
}
```

### AI Scheduling 

Pro and Enterprise users can use natural language to create calendar events. For example:
- "Schedule a compliance review meeting next Tuesday at a 2pm"
- "Set up quarterly compliance audit on July 15th at 10am"

### Paywall Implementation

Access to premium features is controlled by user subscription tier:

- **FREE**: Basic functionality only
- **PRO**: Access to calendar and AI scheduling
- **ENTERPRISE**: Access to all features including calendar and AI scheduling

The paywall logic is implemented in:
- Frontend: 
  - `src/utils/tiers.ts`
  - `src/utils/featureRequirements.ts`
  - `src/utils/accessControl.ts`
- Backend:
  - `app/utils/tiers.py`
  - `app/utils/feature_requirements.py`
  - `app/utils/access_control.py`

#### Adding New Premium Features

To add a new premium feature with paywall restrictions:

1. Add the feature to the feature requirements mapping:
   ```ts
   // Frontend - featureRequirements.ts
   export const featureRequirements: Record<string, Tier> = {
     calendar: Tier.PRO,
     ai_pro_mode: Tier.PRO,
     your_new_feature: Tier.PRO // or Tier.ENTERPRISE
   };
   ```

   ```python
   # Backend - feature_requirements.py
   feature_requirements = {
       "calendar": PRO,
       "ai_pro_mode": PRO,
       "your_new_feature": PRO  # or ENTERPRISE
   }
   ```

2. Add access checks in your frontend components:
   ```tsx
   import { useAuth } from '../contexts/AuthContext';
   import { Tier, getTierFromSubscriptionStatus } from '../utils/tiers';
   import { canAccessFeature } from '../utils/accessControl';

   function YourComponent() {
     const { user } = useAuth();
     const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
     
     // paywall check for your_new_feature
     if (!canAccessFeature(userTier, 'your_new_feature')) {
       return <UpgradePrompt featureName="Your Feature" />;
     }
     
     return (
       <YourFeatureImplementation />
     );
   }
   ```

3. Add checks in your backend API routes:
   ```python
   from app.utils.tiers import get_tier_from_subscription_status
   from app.utils.access_control import can_access_feature

   @router.get("/your-feature")
   async def your_feature_endpoint(
       current_user: User = Depends(get_current_active_user)
   ):
       # Get user tier
       user_tier = get_tier_from_subscription_status(current_user.subscription_status)
       
       # paywall check for your_new_feature
       if not can_access_feature(user_tier, "your_new_feature"):
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail="This feature requires a Pro or Enterprise subscription."
           )
       
       # Your feature implementation
       return {"message": "Feature accessible"}
   ```

### AI Mode Selection Tooltip

The application includes an intelligent tooltip system that guides Pro and Enterprise users to discover the AI mode selection feature:

#### How it works:
- **Target Users**: Only shown to Pro and Enterprise tier users
- **Trigger**: Appears automatically when users visit an empty chat page
- **Frequency**: Shows maximum 3 times, with 24-hour intervals between appearances
- **Dismissal**: Can be permanently dismissed by clicking "Got it!" or the X button
- **Persistence**: Uses localStorage to remember user preferences across sessions

#### For Developers:
```javascript
// Reset tooltip for testing (in browser console)
import tooltipManager from './src/utils/tooltipManager';
tooltipManager.resetTooltip('ai_mode_selection');

// Reset all tooltips
tooltipManager.resetAllTooltips();

// Check tooltip stats
tooltipManager.getTooltipStats('ai_mode_selection');
```

#### Components:
- `AiModeTooltip.tsx` - The tooltip component with positioning and styling
- `tooltipManager.ts` - Manages tooltip display logic and persistence
- `AIChat.tsx` - Integrates tooltip with the chat interface

The tooltip appears as an informative popup with an arrow pointing to the AI mode selection button, providing contextual guidance without being intrusive.
