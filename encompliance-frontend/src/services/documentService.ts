/*
  Description: Document service for managing document upload, download, listing, and related API interactions.
  Purpose: Provides functions for handling user documents, including caching, refreshing, and secure access for compliance workflows.
*/
import api from './api';
import axios from 'axios';

// In Vite, environment variables are accessed via import.meta.env
// See: https://vitejs.dev/guide/env-and-mode.html
const backendUrl = (import.meta.env.VITE_BACKEND_URL as string) || 'http://localhost:8000';

// Add rate limiting utility
let lastDocumentApiCallTime: { [key: string]: number } = {};
let documentCallErrorCount: { [key: string]: number } = {};
// Increase timeout to 5 seconds (from 2.5) and only activate after errors
const MIN_DOC_API_CALL_INTERVAL = 5000; 

export interface Document {
  id: number;
  filename: string;
  filepath: string;
  file_type: string;
  file_size: number;
  custom_label?: string;
  uploaded_at: string;
  uploaded_by: number;
  is_deleted: boolean;
  deleted_at: string | null;
  deleted_by: number | null;
  expiration_date?: string;
  document_type?: string;
  issuing_authority?: string;
  renewal_required?: boolean;
  is_expired?: boolean;
  days_until_expiry?: number;
  needs_expiration_reminder?: boolean;
}

export interface DocumentListResponse {
  documents: Document[];
}

export interface DocumentExpirationData {
  expirationDate?: string;
  documentType?: string;
  issuingAuthority?: string;
  renewalRequired?: boolean;
}

class DocumentService {
  async uploadDocument(
    file: File, 
    customLabel?: string, 
    expirationData?: DocumentExpirationData
  ): Promise<Document> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (customLabel && customLabel.trim()) {
        formData.append('custom_label', customLabel.trim());
      }
      
      // Add expiration tracking data if provided
      if (expirationData) {
        if (expirationData.expirationDate) {
          formData.append('expiration_date', expirationData.expirationDate);
        }
        if (expirationData.documentType) {
          formData.append('document_type', expirationData.documentType);
        }
        if (expirationData.issuingAuthority) {
          formData.append('issuing_authority', expirationData.issuingAuthority);
        }
        if (expirationData.renewalRequired !== undefined) {
          formData.append('renewal_required', expirationData.renewalRequired.toString());
        }
      }
      
      const response = await api.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.data) {
        throw new Error('Document upload response missing data');
      } else if (!response.data.id) {
        throw new Error('Document upload response missing ID');
      }

      // Clear document cache to ensure fresh data on next fetch
      localStorage.removeItem('cachedDocuments');
      
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async listDocuments(): Promise<Document[]> {
    try {
      let attempts = 0;
      const maxAttempts = 2;
      
      // Clear cached documents to ensure fresh data
      localStorage.removeItem('cachedDocuments');
      
      while (attempts < maxAttempts) {
        try {
          attempts++;
          const response = await api.get<DocumentListResponse>('/documents/list');
          
          if (response.data && Array.isArray(response.data.documents)) {
            // Cache documents locally (could use localStorage or state management)
            localStorage.setItem('cachedDocuments', JSON.stringify(response.data.documents));
            
            return response.data.documents;
          } else {
            if (attempts < maxAttempts) {
              await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
            }
          }
        } catch (error) {
          if (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
          } else {
            throw error; // Rethrow on last attempt
          }
        }
      }
      
      // Try to return cached documents if any
      const cachedDocuments = localStorage.getItem('cachedDocuments');
      if (cachedDocuments) {
        return JSON.parse(cachedDocuments);
      }
      
      return []; // Return empty array after all attempts fail
    } catch (err) {
      return []; // Return empty array on error
    }
  }

  async downloadDocument(documentId: string): Promise<string> {
    const response = await api.get<Document>(`/documents/download/${documentId}`);
    return response.data.filepath;
  }

  async deleteDocument(documentId: number): Promise<Document> {
    const response = await api.delete<Document>(`/documents/delete/${documentId}`);
    return response.data;
  }

  async updateDocumentLabel(documentId: number, customLabel?: string): Promise<Document> {
    try {
      console.log(`[DEBUG] DocumentService: Updating label for document ${documentId} with label: "${customLabel}"`);
      console.log(`[DEBUG] DocumentService: API base URL: ${api.defaults.baseURL}`);
      console.log(`[DEBUG] DocumentService: Full URL will be: ${api.defaults.baseURL}/documents/${documentId}/label`);
      
      const response = await api.put(`/documents/${documentId}/label`, {
        custom_label: customLabel && customLabel.trim() ? customLabel.trim() : null
      });

      console.log(`[DEBUG] DocumentService: Label update successful for document ${documentId}`);
      
      // Clear document cache to ensure fresh data on next fetch
      localStorage.removeItem('cachedDocuments');
      
      return response.data;
    } catch (err: any) {
      console.error(`[DEBUG] DocumentService: Error updating label for document ${documentId}:`, err);
      console.error(`[DEBUG] DocumentService: Error response:`, err.response);
      console.error(`[DEBUG] DocumentService: Error config:`, err.config);
      throw err;
    }
  }

  // Add the new refresh function here
  async refreshVectorStore(): Promise<{ message: string; details?: any; success: boolean; errors?: string[] }> {
    try {
      const response = await api.post('/documents/refresh');

      // Check for success and return appropriate structure
      if (response.data && response.data.message) {
        return { 
          success: true, 
          message: response.data.message, 
          details: response.data.details 
        };
      } else {
        // Handle cases where the response might not have the expected structure
        // but is still technically a 2xx success from the backend call
        console.warn("[DEBUG] DocumentService: Refresh response structure unexpected but request succeeded:", response.data);
        return { 
          success: true, // Assume success if HTTP status was OK
          message: "Refresh initiated successfully, but response format was unexpected.",
          details: response.data // Include whatever data was returned
        };
      }
    } catch (err: any) {
      console.error("[DEBUG] DocumentService: Error calling /documents/refresh:", err);
      let errorMessage = 'Failed to trigger document library refresh.';
      let errorsList: string[] = [];

      // Extract error message from AxiosError or standard Error
      if (axios.isAxiosError(err) && err.response?.data) {
          if (err.response.data.detail?.message) {
            errorMessage = err.response.data.detail.message;
          } else if (typeof err.response.data.detail === 'string') {
            errorMessage = err.response.data.detail;
          }
          if (err.response.data.detail?.errors) {
            errorsList = err.response.data.detail.errors;
          } else if (Array.isArray(err.response.data.errors)) {
             errorsList = err.response.data.errors;
          } else {
             errorsList = [errorMessage]; // Fallback to main message
          }
      } else if (err instanceof Error) {
          errorMessage = err.message;
          errorsList = [err.message];
      }
      
      // Return a standardized error structure
      return {
        success: false,
        message: errorMessage,
        errors: errorsList
      };
    }
  }

  // Utility function to get the authenticated URL for a document
  getAuthenticatedDocumentUrl(documentId: string): string {
    const token = localStorage.getItem('token');
    return `${backendUrl}/document/${documentId}?token=${token}`;
  }

  // Utility function to get the embeddable URL for a document (for iframe embedding)
  getEmbeddableDocumentUrl(documentId: string): string {
    const token = localStorage.getItem('token');
    // Point directly to the correct endpoint for viewing documents
    return `${backendUrl}/api/v1/view/${documentId}?token=${token}`;
  }

  // Open document in a new tab
  openDocumentInNewTab(documentId: string): void {
    const token = localStorage.getItem('token');
    // Use the direct document API endpoint that returns only the document without UI
    const url = `${backendUrl}/api/v1/documents/download/${documentId}?token=${token}`;
    window.open(url, '_blank');
  }

  /**
   * Forcefully refresh the document list cache
   * This can be called when we need to ensure we have the latest documents
   * @param force - If true, bypass any potential internal caching mechanisms (if implemented)
   */
  async refreshDocumentCache(force: boolean = false): Promise<Document[]> {
    const endpoint = 'documents/list';
    const currentTime = Date.now();
    
    try {
      // Only apply rate limiting if we've seen errors for this endpoint
      // and we're not forcing a refresh
      if (!force && documentCallErrorCount[endpoint] && 
          lastDocumentApiCallTime[endpoint] && 
          currentTime - lastDocumentApiCallTime[endpoint] < MIN_DOC_API_CALL_INTERVAL) {
        // Avoid console spam by not logging every time
        if (documentCallErrorCount[endpoint] % 5 === 0) {
          console.warn(`Rate limiting document API call after previous errors`);
        }
        
        // Try to use cached documents from localStorage if available
        const cachedDocs = localStorage.getItem('cachedDocuments');
        if (cachedDocs) {
          try {
            const parsedDocs = JSON.parse(cachedDocs);
            if (Array.isArray(parsedDocs) && parsedDocs.length > 0) {
              return parsedDocs;
            }
          } catch (e) {
            // Silent catch - no console spam
          }
        }
        
        // Return empty array if no cache
        return [];
      }
      
      // Update the last call time
      lastDocumentApiCallTime[endpoint] = currentTime;
      
      // Only clear cache on forced refresh
      if (force) {
        localStorage.removeItem('cachedDocuments');
      }
      
      // Make a direct API call
      const response = await api.get<DocumentListResponse>('/documents/list');
      
      // Reset error count on success
      documentCallErrorCount[endpoint] = 0;
      
      if (response.data && Array.isArray(response.data.documents)) {
        const documents = response.data.documents;
        // Store in localStorage for backup
        localStorage.setItem('cachedDocuments', JSON.stringify(documents));
        
        return documents;
      } else {
        // If response format is unexpected, log error and return empty array
        return [];
      }
    } catch (err: any) {
      // Increment error count for this endpoint
      documentCallErrorCount[endpoint] = (documentCallErrorCount[endpoint] || 0) + 1;
      
      // Log error only occasionally to avoid console spam
      if (documentCallErrorCount[endpoint] <= 3 || documentCallErrorCount[endpoint] % 10 === 0) {
        console.error(`Error refreshing document cache (attempt #${documentCallErrorCount[endpoint]})`, err.code || err.message || 'Unknown error');
      }
      
      // Special handling for resource exhaustion errors
      if (err.message?.includes('ERR_INSUFFICIENT_RESOURCES') || 
          err.code === 'ERR_NETWORK' || 
          err.code === 'ECONNABORTED') {
        
        // Force a longer cooldown for this endpoint
        lastDocumentApiCallTime[endpoint] = currentTime + 15000; // Add 15 seconds
        
        // Try to use cached documents as fallback
        const cachedDocs = localStorage.getItem('cachedDocuments');
        if (cachedDocs) {
          try {
            const parsedDocs = JSON.parse(cachedDocs);
            if (Array.isArray(parsedDocs)) {
              return parsedDocs;
            }
          } catch (e) {
            // Silent catch
          }
        }
      }
      
      return [];
    }
  }

  // Get document details by ID
  async getDocumentDetails(documentId: string): Promise<Document | null> {
    // Implementation of getDocumentDetails method
    return null;
  }
}

export default new DocumentService(); 