/*
  Description: AuthContext provides authentication state and user context for the application.
  Purpose: Manages user login, signup, session, and error handling for secure access control.
*/
import React, { createContext, useState, useEffect, useContext } from 'react';
import { authService, AuthResponse } from '../services/authService';
import { userService, UserData } from '../services/userService';
import { noteService } from '../services/noteService';
import { notificationService } from '../services/notificationService';
import { realtimeSyncService } from '../services/realtimeSync';
import axios from 'axios';

// Extended response type to handle flexible token responses
interface ExtendedAuthResponse extends AuthResponse {
  token?: string;
  [key: string]: any; // Allow any string key for flexible token field detection
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: UserData | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  loginWithPasskey: (email: string) => Promise<void>;
  signup: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  updateUserContext: (newUserData: UserData) => void;
  refreshAuthState: () => Promise<boolean>;
  isWebAuthnSupported: () => boolean;
  isPlatformAuthenticatorAvailable: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Cache for platform authenticator availability check
  const [platformAuthenticatorAvailable, setPlatformAuthenticatorAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      const token = authService.getToken();
      if (token) {
        noteService.updateToken(token);
        setIsAuthenticated(true);
        try {
          const userData = await userService.getCurrentUser();
          setUser(userData);
          
          // Silently synchronize OpenAI resources when session is restored
          try {
            // No logging needed
            await authService.syncOpenAIResources();
          } catch (syncErr) {
            // Silently continue if sync fails - don't block user experience
          }
        } catch (err) {
          handleError(err, 'Unable to load user profile. Please try logging in again.');
          authService.removeToken();
          setIsAuthenticated(false);
        }
      }
      setLoading(false);
    };

    checkAuth();
    
    // Check WebAuthn support
    if (authService.isWebAuthnSupported()) {
      // Preload platform authenticator availability
      authService.isPlatformAuthenticatorAvailable()
        .then(available => setPlatformAuthenticatorAvailable(available))
        .catch(() => setPlatformAuthenticatorAvailable(false));
    }
  }, []);

  // Subscribe to account updates for team members
  useEffect(() => {
    if (user?.user_role === 'team_member') {
      const unsubscribe = realtimeSyncService.subscribe('account_update', async (event) => {
        console.log('AuthContext received account update, refreshing user data');
        // Refresh user data from server to get updated state/facility type
        try {
          const updatedUserData = await userService.refreshUserData();
          if (updatedUserData) {
            setUser(updatedUserData);
          }
        } catch (error) {
          console.error('Failed to refresh user data after sync:', error);
        }
      });

      return () => {
        unsubscribe();
      };
    }
  }, [user?.user_role]);

  const handleError = (err: unknown, defaultMessage: string) => {
    if (axios.isAxiosError(err)) {
      // Handle Axios errors
      if (err.response) {
        // Server responded with an error status
        if (err.response.status === 401) {
          setError('Your session has expired. Please login again.');
        } else if (err.response.status === 404) {
          setError('The requested resource was not found. Our team has been notified.');
        } else if (err.response.data && err.response.data.detail) {
          setError(err.response.data.detail);
        } else {
          setError(`Error ${err.response.status}: ${defaultMessage}`);
        }
      } else if (err.request) {
        // Request was made but no response received
        setError('Unable to connect to the server. Please check your internet connection and try again.');
      } else {
        setError(defaultMessage);
      }
    } else if (err instanceof Error) {
      setError(err.message);
    } else {
      setError(defaultMessage);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await authService.login({ email, password });
      
      if (response && response.access_token) {
        authService.setToken(response.access_token);
        noteService.updateToken(response.access_token);
        
        // Don't set authenticated immediately - wait for user data first
        
        // Get user data
        try {
          const userData = await userService.getCurrentUser();
          
          // Only set authenticated status after successful user data retrieval
          setUser(userData);
          setIsAuthenticated(true);
          
          // Silently synchronize OpenAI resources after successful login
          try {
            // No logging needed
            await authService.syncOpenAIResources();
          } catch (syncErr) {
            // Silently continue if sync fails - don't block user experience
          }
        } catch (userErr) {
          authService.removeToken(); // Remove potentially invalid token
          setIsAuthenticated(false);
          setUser(null);
          throw new Error('Failed to verify authentication. Please try again.');
        }
      } else {
        setError('Login failed. Please check your credentials and try again.');
        setIsAuthenticated(false);
      }
    } catch (err) {
      handleError(err, 'Login failed. Please check your credentials and try again.');
      setIsAuthenticated(false);
      authService.removeToken(); // Ensure any partial tokens are removed
    } finally {
      setLoading(false);
    }
  };
  
  const loginWithPasskey = async (email: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await authService.loginWithPasskey(email);
      
      if (response && response.access_token) {
        // Token is already stored by authService.loginWithPasskey
        noteService.updateToken(response.access_token);
        
        // Get user data
        try {
          const userData = await userService.getCurrentUser();
          
          // Only set authenticated status after successful user data retrieval
          setUser(userData);
          setIsAuthenticated(true);
          
          // Silently synchronize OpenAI resources after successful login
          try {
            await authService.syncOpenAIResources();
          } catch (syncErr) {
            // Silently continue if sync fails - don't block user experience
          }
        } catch (userErr) {
          authService.removeToken(); // Remove potentially invalid token
          setIsAuthenticated(false);
          setUser(null);
          throw new Error('Failed to verify authentication. Please try again.');
        }
      } else {
        setError('Passkey login failed. Please try again or use your password.');
        setIsAuthenticated(false);
      }
    } catch (err: any) {
      // Check for specific error messages we want to propagate
      if (err.message?.includes("No user found") || 
          err.message?.includes("Authentication was canceled") ||
          err.message?.includes("user verification failed")) {
        // Simply propagate these specific error messages
        setError(err.message);
      } else {
        // For other errors, use our general error handler
        handleError(err, 'Passkey authentication failed. Please try again or use your password.');
      }
      setIsAuthenticated(false);
      authService.removeToken();
    } finally {
      setLoading(false);
    }
  };

  const signup = async (data: any) => {
    try {
      setError(null);
      setLoading(true); // Start loading
      
      // Attempt signup
      const response = await authService.signup(data) as ExtendedAuthResponse;
      
      // Check if response contains token directly or nested
      let token = null;
      if (response?.access_token) {
        token = response.access_token;
      } else if (response?.token) { 
        token = response.token;
      } else if (typeof response === 'object') {
        // Search through response object for token-like fields
        for (const key in response) {
          if (typeof response[key] === 'string' && 
              (key.includes('token') || key.includes('access'))) {
            token = response[key];
            break;
          }
        }
      }
      
      // If we found a token, proceed with authentication
      if (token) {
        authService.setToken(token);
        noteService.updateToken(token);
        
        // Always force refresh user profile after signup
        try {
          const userData = await userService.refreshUserData();
          if (!userData || !userData.facility_name || !userData.facility_types) {
            // Silently handle missing fields
          }
          setUser(userData);
          setIsAuthenticated(true);
          setError(null);
          
          // Silently synchronize OpenAI resources after successful signup
          try {
            // No logging needed
            await authService.syncOpenAIResources();
          } catch (syncErr) {
            // Silently continue if sync fails - don't block user experience
          }
        } catch (profileErr) {
          authService.removeToken();
          setIsAuthenticated(false);
          setUser(null);
          // Don't log error
          setError('Signup complete, but failed to load profile. Please try logging in.');
        }
      } else {
        // This case should ideally not happen if signup API succeeded and returned a token.
        // If it does, treat as signup failure.
        // Don't log error
        setIsAuthenticated(false);
        setUser(null);
        setError('Signup failed: No authentication token received.');
      }
    } catch (err) {
      // Handle signup-specific errors
      handleError(err, 'Signup failed. Please check your details and try again.');
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Error during logout:', error);
      // Continue with logout process even if the API call fails
    }
    userService.clearCache(); // Clear user data cache
    noteService.updateToken('');
    setIsAuthenticated(false);
    setUser(null);
    setError(null);
  };

  // Add function to update user state directly
  const updateUserContext = (newUserData: UserData) => {
    setUser(newUserData);
  };
  
  // WebAuthn support check
  const isWebAuthnSupported = () => {
    return authService.isWebAuthnSupported();
  };
  
  // Platform authenticator availability check with caching
  const isPlatformAuthenticatorAvailable = async () => {
    if (platformAuthenticatorAvailable !== null) {
      return platformAuthenticatorAvailable;
    }
    
    try {
      const available = await authService.isPlatformAuthenticatorAvailable();
      setPlatformAuthenticatorAvailable(available);
      return available;
    } catch (error) {
      setPlatformAuthenticatorAvailable(false);
      return false;
    }
  };

  // Add function to manually refresh auth state
  const refreshAuthState = async (): Promise<boolean> => {
    console.log("Manually refreshing authentication state...");
    
    if (!authService.isAuthenticated()) {
      console.log("No token found, not authenticated");
      setIsAuthenticated(false);
      setUser(null);
      return false;
    }
    
    try {
      console.log("Token found, fetching user data...");
      const userData = await userService.refreshUserData();
      
      if (userData) {
        console.log("User data refreshed successfully");
        setUser(userData);
        setIsAuthenticated(true);
        return true;
      } else {
        console.log("User data refresh failed");
        setIsAuthenticated(false);
        setUser(null);
        return false;
      }
    } catch (error) {
      console.error("Error refreshing auth state:", error);
      setIsAuthenticated(false);
      setUser(null);
      return false;
    }
  };

  return (
    <AuthContext.Provider value={{
      isAuthenticated, 
      user, 
      loading, 
      error,
      login,
      loginWithPasskey,
      signup, 
      logout,
      clearError,
      updateUserContext,
      refreshAuthState,
      isWebAuthnSupported,
      isPlatformAuthenticatorAvailable
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 