/*
  Description: User service for managing user profile data, updates, and account operations via API.
  Purpose: Provides functions for fetching, updating, deleting, and caching user data to support authentication and profile management.
*/
import api from './api';
import axios from 'axios';

// Define quick access link type
export interface QuickAccessLink {
  label: string;
  path: string;
  icon?: string;
}

// Define generic user data types since we don't have the specific imports
export interface UserData {
  id?: number;
  username?: string;
  email?: string;
  full_name?: string;
  facility_type?: string;
  facility_types?: string[];
  facility_name?: string;
  operation_name?: string;
  state?: string;
  phone_number?: string;
  is_active?: boolean;
  email_verified?: boolean;
  subscription_status?: string; // "free" or "pro" - Pro users get all facility features
  user_role?: string; // "FREE_USER", "FACILITY_ADMIN", or "TEAM_MEMBER"
  assistant_id?: string;
  vector_store_id?: string;
  created_at?: string;
  updated_at?: string;
  quick_access_links?: QuickAccessLink[];
  // Facility management fields - Pro users get facility access
  facility_id?: number;
  administered_facility?: {
    id: number;
    facility_name: string;
    is_active: boolean;
  };
  [key: string]: any; // Allow for additional fields
}

export type UserUpdateData = Partial<UserData>;

// Custom error types
export type UserServiceError = {
  code: string;
  message: string;
  originalError?: any;
  technicalDetails?: string;
};

// Add private property for cached user data
interface UserServiceType {
  cachedUserData: UserData | null;
  getCurrentUser(forceRefresh?: boolean): Promise<UserData>;
  updateCurrentUser(data: UserUpdateData): Promise<UserData>;
  deleteAccount(): Promise<{ success: boolean }>;
  clearCache(): void;
  refreshUserData(): Promise<UserData>;
  formatError(error: any, code: string, defaultMessage: string): UserServiceError;
  getQuickAccessLinks(): Promise<QuickAccessLink[]>;
  updateQuickAccessLinks(links: QuickAccessLink[]): Promise<QuickAccessLink[]>;
}

export const userService: UserServiceType = {
  cachedUserData: null,
  
  async getCurrentUser(forceRefresh: boolean = false): Promise<UserData> {
    try {
      // Use cached user data if available and not forcing refresh
      if (this.cachedUserData && !forceRefresh) {
        return this.cachedUserData;
      }
      
      return await this.refreshUserData();
    } catch (error) {
      console.error('Error fetching current user:', error);
      
      // Add detailed error info for troubleshooting
      if (axios.isAxiosError(error)) {
        console.error(`API Error Details - Status: ${error.response?.status}, URL: ${error.config?.url}`);
        
        if (error.response?.status === 0 || error.code === 'ERR_NETWORK') {
          console.error('CORS or Network Error detected. Backend server may be down or misconfigured.');
        }
      }
      
      throw this.formatError(error, 'USER_FETCH_ERROR', 'Failed to fetch user data');
    }
  },
  
  async updateCurrentUser(data: UserUpdateData): Promise<UserData> {
    try {
      const response = await api.put('/users/me', data);
      
      // Update cache with the new data
      if (response.data) {
        this.cachedUserData = response.data;
      }
      
      // Return the updated data directly from the response
      return response.data;
    } catch (error) {
      console.error('Error updating user:', error);
      throw this.formatError(error, 'USER_UPDATE_ERROR', 'Failed to update user profile');
    }
  },
  
  async deleteAccount(): Promise<{ success: boolean }> {
    try {
      const response = await api.delete('/users/me');
      // Clear cache on account deletion
      this.clearCache();
      return response.data;
    } catch (error) {
      throw this.formatError(error, 'ACCOUNT_DELETE_ERROR', 'Failed to delete account');
    }
  },
  
  // Add method to clear the cache
  clearCache(): void {
    this.cachedUserData = null;
  },
  
  // Add method to refresh user data directly from the API
  async refreshUserData(): Promise<UserData> {
    try {
      console.log("Refreshing user data from API");
      const response = await api.get('/users/me');
      
      console.log("User data API response received:", response.status);
      
      if (response.data) {
        // Cache the user data for future use
        console.log("User data refreshed successfully");
        this.cachedUserData = response.data;
        return response.data;
      } else {
        console.warn("API response missing user data:", response);
        throw new Error('User data not found in response');
      }
    } catch (error) {
      console.error('Error refreshing user data:', error);
      
      // Add detailed troubleshooting for common authentication issues
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        console.error("Authentication error (401) during user data refresh. Token may be invalid or expired.");
        // Clear cached data on auth errors
        this.clearCache();
      }
      
      throw this.formatError(error, 'USER_REFRESH_ERROR', 'Failed to refresh user data');
    }
  },
  
  // Get user's quick access links
  async getQuickAccessLinks(): Promise<QuickAccessLink[]> {
    try {
      // Try to get from cache first
      if (this.cachedUserData?.quick_access_links) {
        return this.cachedUserData.quick_access_links;
      }
      
      // Fetch from API if not in cache
      const response = await api.get('/users/me/quick-access-links');
      
      // Update cache
      if (this.cachedUserData) {
        this.cachedUserData.quick_access_links = response.data;
      }
      
      return response.data;
    } catch (error) {
      console.error('Error fetching quick access links:', error);
      throw this.formatError(error, 'QUICK_ACCESS_FETCH_ERROR', 'Failed to fetch quick access links');
    }
  },
  
  // Update user's quick access links
  async updateQuickAccessLinks(links: QuickAccessLink[]): Promise<QuickAccessLink[]> {
    try {
      const response = await api.put('/users/me/quick-access-links', links);
      
      // Update cache
      if (this.cachedUserData) {
        this.cachedUserData.quick_access_links = response.data;
      }
      
      return response.data;
    } catch (error) {
      console.error('Error updating quick access links:', error);
      throw this.formatError(error, 'QUICK_ACCESS_UPDATE_ERROR', 'Failed to update quick access links');
    }
  },
  
  // Helper function to format errors consistently
  formatError(error: any, code: string, defaultMessage: string): UserServiceError {
    let message = defaultMessage;
    let technicalDetails = '';
    
    if (axios.isAxiosError(error)) {
      // Build detailed technical info for logging
      technicalDetails = `URL: ${error.config?.url || 'unknown'}, ` +
                        `Method: ${error.config?.method?.toUpperCase() || 'unknown'}, ` +
                        `Status: ${error.response?.status || 'none'}, ` +
                        `Message: ${error.message}`;
                        
      if (error.code === 'ERR_NETWORK') {
        message = 'Network error: Unable to connect to the server. This may be a CORS issue or the server is down.';
      } else if (error.response) {
        // Server responded with an error status
        switch (error.response.status) {
          case 401:
            message = 'Authentication error: Your session has expired. Please log in again.';
            code = 'AUTH_ERROR';
            break;
          case 403:
            message = 'Permission denied: You do not have access to this resource.';
            code = 'PERMISSION_ERROR';
            break;
          case 404:
            message = 'Resource not found: The requested data does not exist.';
            code = 'NOT_FOUND_ERROR';
            break;
          case 500:
            message = 'Server error: The server encountered an internal error. Our team has been notified.';
            code = 'SERVER_ERROR';
            break;
          default:
            message = error.response.data?.detail || 
                     `Error ${error.response.status}: ${defaultMessage}`;
        }
      }
    } else if (error instanceof Error) {
      message = error.message;
      technicalDetails = error.stack || '';
    }
    
    // Log detailed error to console for troubleshooting
    console.error(`API Error (${code}): ${message}\nTechnical Details: ${technicalDetails}`);
    
    return {
      code,
      message,
      originalError: error,
      technicalDetails
    };
  }
}; 