# Frontend API Refactoring Verification Guide

## Overview

The frontend Customer Support Portal has been refactored to use a centralized API client (`customerSupportApi`) for all backend interactions. This ensures consistent authentication, base URL configuration, and error handling. Additionally, the WebSocket service has been updated for reliable real-time notifications.

## 1. Codebase Verification

### Centralized API Client

- **File:** `src/services/customerSupportApi.ts`
- **Verification:** ensuring it handles:
  - Base URL configuration (`VITE_SUPPORT_API_BASE_URL` or default `http://localhost:6050`).
  - Automatic injection of the `Authorization: Bearer <token>` header.
  - Consistent error interception.

### WebSocket Service

- **File:** `src/services/supportWebSocket.ts`
- **Verification:**
  - Correctly constructs `ws://` or `wss://` URLs based on the current window protocol and host.
  - Handles authentication by passing the token in the query string.
  - Automatically reconnects on disconnection.

### Components Refactored

The following components have been updated to use `customerSupportApi` and remove direct `axios` or `fetch` calls:

- `CustomerSupportLoginPage.tsx`
- `CustomerHistoryTimeline.tsx`
- `SupportUserManagement.tsx`
- `DataExplorer.tsx`
- `FileTreeVisualizer.tsx`
- `DbSchemaVisualizer.tsx`
- `ServiceStatusViewer.tsx`
- `AuditLogViewer.tsx`
- `SupportTicketDetail.tsx`
- `CustomerSupportPortal.tsx` (UserOverview component)

## 2. Manual Verification Options

### Option A: Browser Testing

1.  **Start the Support Portal:**
    Ensure your backend is running on port `6050`.
    Run the frontend:
    ```bash
    npm run dev:support
    # or
    npx vite --config vite.config.support.ts
    ```
2.  **Login:**
    - Navigate to the support portal URL (e.g., `http://localhost:5200/support` if proxied, or the vite dev server port).
    - Log in with valid support credentials.
    - **Verify:** Login succeeds, and you are redirected to the portal. Check the Network tab to confirm the `/auth/token` request goes to the correct URL.
3.  **Navigate & Test Features:**
    - **Tickets:** View the ticket list. Click on a ticket to view details. Verify comments load.
    - **Service Status:** Click "Service Status" (if available in UI mock). Verify status icons load.
    - **Analytics:** Switch to the Analytics view. Confirm charts/data load.
    - **Admin Tools:** If logged in as admin, check "User Management" and "Audit Logs".
4.  **Real-time Notifications:**
    - Open the portal in two different browser windows/tabs.
    - specificy different users if possible, or trigger an event (like updating a ticket status) in one window.
    - **Verify:** The other window receives a notification or updates automatically. Check the Network tab > WS to see the `notifications` websocket connection.

### Option B: Network Inspection

Open the browser's Developer Tools (F12) > **Network** tab.

- **XHR/Fetch:** Ensure request URLs are correct (e.g., `http://localhost:6050/api/v1/support/...` or relative `/api/v1/support/...` if proxied).
- **WS:** Filter by "WS" and check for the upgrade request to `/api/v1/support/ws/notifications`. Ensure the Status is `101 Switching Protocols`.

## 3. Troubleshooting

- **401 Unauthorized:** Ensure the token is being saved to `localStorage` key `customerSupportToken`.
- **WebSocket connection failed:** Check if the backend allows WebSocket connections from your origin (CORS) and that the URL protocol (`ws` vs `wss`) matches the environment (HTTP vs HTTPS).
- **ReferenceError (token is not defined):** We fixed this in `AuditLogViewer.tsx` and `CustomerSupportPortal.tsx`. If it recurs, check `useEffect` dependencies.
