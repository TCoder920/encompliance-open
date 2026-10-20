import axios from 'axios';

/*
  Description: API service for configuring and managing HTTP requests to the backend, including authentication and error handling.
  Purpose: Centralizes API configuration, token management, and error interception for robust and secure client-server communication.
*/

/**
 * Enhanced Error reporting for API issues
 */
export interface ApiErrorDetail {
  type: 'cors' | 'network' | 'server' | 'auth' | 'client' | 'unknown';
  status?: number;
  message: string;
  technicalDetails?: string;
  isRecoverable: boolean;
  retryRecommended: boolean;
}

// Get the base URL from environment or default to localhost:8000
const rawBaseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

// Ensure the base URL doesn't end with a slash, then append the API prefix
const baseURL = `${rawBaseURL.replace(/\/$/, '')}/api/v1`;

const api = axios.create({
  baseURL, // This now consistently includes /api/v1
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // Using Bearer token authentication instead of cookies
  timeout: 300000, // Increased timeout for long-running operations
});

// Add request interceptor to include auth token in all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      // Add token to both standard Authorization header and custom x-token header
      config.headers.Authorization = `Bearer ${token}`;
      config.headers['x-token'] = token;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => {
    // Special handling for document list response
    // Check relative URL now since baseURL includes /api/v1
    if (response.config.url === '/documents/list') { 
      // Check if the documents array exists
      if (!response.data?.documents) {
        // If not, try to normalize the response
        if (Array.isArray(response.data)) {
          response.data = { documents: response.data };
        } else if (response.data && typeof response.data === 'object') {
          response.data = { documents: [] };
        }
      }
      
      // Ensure documents is at least an empty array
      if (!response.data.documents) {
        response.data.documents = [];
      }
    }
    
    return response;
  },
  async (error) => {
    // Enhanced error details
    const errorDetail: ApiErrorDetail = {
      type: 'unknown',
      message: 'An unknown error occurred',
      isRecoverable: false,
      retryRecommended: false
    };
    
    // For CORS errors, provide a more helpful message
    if (error.message === 'Network Error') {
      console.error('Network error detected, this may be caused by CORS issues', error.config?.url);
      
      errorDetail.type = 'cors';
      errorDetail.message = 'API server connection failed - CORS configuration issue';
      errorDetail.technicalDetails = `Request to ${error.config?.url} failed due to CORS policy`;
      errorDetail.isRecoverable = false;
      errorDetail.retryRecommended = false;
      
      error.apiErrorDetail = errorDetail;
      
      // Add a helpful message for developers
      if (process.env.NODE_ENV === 'development') {
        console.error(`
          This is likely a CORS configuration issue on the backend.
          Make sure the server has proper CORS headers:
          - Access-Control-Allow-Origin: ${window.location.origin}
          - Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
          - Access-Control-Allow-Headers: Content-Type, Authorization
          
          Add this to your FastAPI app:
          
          from fastapi.middleware.cors import CORSMiddleware
          
          app.add_middleware(
              CORSMiddleware,
              allow_origins=["${window.location.origin}"],
              allow_credentials=True,
              allow_methods=["*"],
              allow_headers=["*"],
          )
        `);
      }
    }
    
    // Add error category and code for specific status codes
    if (error.response) {
      error.apiErrorDetail = {
        type: error.response.status >= 500 ? 'server' : 'client',
        status: error.response.status,
        message: error.response.data?.detail || `HTTP Error: ${error.response.status}`,
        technicalDetails: `Request to ${error.config?.url} failed with status ${error.response.status}`,
        isRecoverable: error.response.status < 500,
        retryRecommended: error.response.status >= 500 && error.response.status < 600
      };
      
      // Special handling for document-related errors
      if (error.config?.url?.startsWith('/documents/')) { 
        // Add a more user-friendly message
        error.userMessage = 'There was a problem with your document. Please try again.';
      }
    }
    
    // Handle 401 Unauthorized errors (expired token)
    if (error.response?.status === 401) {
      // Check if we're already trying to login or refresh token
      const isAuthEndpoint = error.config?.url?.includes('/auth/') || 
                         error.config?.url?.includes('/refresh-token');
      
      error.apiErrorDetail = {
        ...error.apiErrorDetail,
        type: 'auth',
        message: 'Authentication failed - please log in again',
        isRecoverable: true,
        retryRecommended: false
      };
      
      // Only try to refresh if we have a token and not on auth endpoints (to prevent loops)
      if (localStorage.getItem('token') && !isAuthEndpoint) {
        // Store the original request to retry it
        const originalRequest = error.config;
        
        // Prevent infinite loops
        if (!originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            // Try to refresh the token
            const refreshResponse = await axios.post(`${baseURL}/refresh-token`, {}, { 
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'x-token': localStorage.getItem('token') || '',
              },
              withCredentials: false
            });
            
            // If successful, update the token
            if (refreshResponse.status === 200 && refreshResponse.data.access_token) {
              const newToken = refreshResponse.data.access_token;
              localStorage.setItem('token', newToken);
              
              // Update the Authorization header on this and future requests
              api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
              api.defaults.headers.common['x-token'] = newToken;
              
              // Update the original request headers
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              originalRequest.headers['x-token'] = newToken;
              
              // Synchronize OpenAI resources after token refresh (in background)
              try {
                import('./authService').then(async (authServiceModule) => {
                  const { authService } = authServiceModule;
                  console.log('Token refreshed, synchronizing OpenAI resources...');
                  await authService.syncOpenAIResources();
                }).catch(syncErr => {
                  console.error('Failed to synchronize OpenAI resources after token refresh:', syncErr);
                });
              } catch (syncErr) {
                console.error('Failed to import authService for OpenAI sync after token refresh:', syncErr);
              }
              
              // Retry the original request with the new token
              return api(originalRequest);
            }
          } catch (refreshError) {
            // If refresh fails, clear the token to force re-login
            localStorage.removeItem('token');
            // If we're in a browser environment, redirect to login (with timeout to prevent loops)
            if (typeof window !== 'undefined') {
              setTimeout(() => {
                window.location.href = '/login';
              }, 100);
            }
          }
        }
      } else if (error.config?.url !== '/auth/signin' && !isAuthEndpoint) {
        // Not an auth endpoint and no token - redirect to login
        // If we're in a browser environment, redirect to login
        if (typeof window !== 'undefined') {
          setTimeout(() => {
            window.location.href = '/login'; 
          }, 100);
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// Create special versions of API methods for auth
export const authApi = {
  get: async (url: string) => {
    try {
      const token = localStorage.getItem('token');
      // Use the main api instance which has the correct baseURL
      const response = await api.get(url); 
      return response.data;
    } catch (error) {
      console.error(`Auth API GET error for ${url}:`, error);
      throw error;
    }
  },
  
  // Special method for getting user info that tries multiple approaches
  getUserInfo: async () => {
    const token = localStorage.getItem('token');
    
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    // Try endpoints relative to the api instance's baseURL
    try {
      const response = await api.get('/users/user-info');
      return response.data;
    } catch (error) {
      console.warn('Failed GET /users/user-info, trying /users/me', error);
    }
    
    // Fall back to /users/me
    try {
      const response = await api.get('/users/me');
      return response.data;
    } catch (error) {
      console.error('Failed GET /users/me as well.', error);
      throw new Error('Failed to get user info after multiple attempts');
    }
  }
};

export const sendContactMessage = async (data: { name: string; email: string; message: string }) => {
  return api.post('/contact', data);
};

export default api; 