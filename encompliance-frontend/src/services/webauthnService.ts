/*
  Description: WebAuthn service for handling passkey registration and authentication.
  Purpose: Provides methods for registering and authenticating with passkeys using the WebAuthn API.
*/

import { startRegistration, startAuthentication } from '@simplewebauthn/browser';
import api from './api';
import { 
  detectBrowser,
  applyBrowserSpecificFixes,
  diagnoseWebAuthnError,
  logWebAuthnDiagnostics
} from '../utils/webauthnUtils';

export interface RegistrationOptionsResponse {
  options: any;
  user_id: number;
}

export interface AuthenticationOptionsResponse {
  options: any;
  user_id: number;
}

export interface Credential {
  id: number;
  name: string;
  created_at: string;
  last_used_at?: string;
  device_type?: string;
}

// Safari has a 1200 byte buffer size limit which can be exceeded when the allowList is too large
// This constant determines how many credentials we should include per batch in Safari
const MAX_SAFARI_CREDENTIALS_PER_BATCH = 5;

/**
 * Service for WebAuthn (passkey) operations
 */
export const webauthnService = {
  /**
   * Get WebAuthn registration options from the server
   * @param credentialName Name for the new credential
   * @param authenticatorAttachment Optional authenticator attachment type
   * @returns Registration options from the server
   */
  async getRegistrationOptions(
    credentialName: string = 'My passkey',
    authenticatorAttachment?: 'platform' | 'cross-platform',
  ): Promise<RegistrationOptionsResponse> {
    try {
      const response = await api.post('/webauthn/register/options', {
        credential_name: credentialName,
        authenticator_attachment: authenticatorAttachment,
      });
      return response.data;
    } catch (error) {
      console.error('Error getting registration options:', error);
      throw error;
    }
  },

  /**
   * Register a new passkey credential
   * @param credentialName Name for the new credential
   * @param authenticatorAttachment Optional authenticator attachment type
   * @returns The newly registered credential
   */
  async registerPasskey(
    credentialName: string = 'My passkey',
    authenticatorAttachment?: 'platform' | 'cross-platform'
  ): Promise<Credential> {
    // Clear any previous errors
    let optionsResponse;
    let registrationResponse;
    let verificationResponse;
    
    try {
      // Log diagnostic information
      console.log('Starting passkey registration process');
      logWebAuthnDiagnostics();
      
      // 1. Get options from the server
      console.log('Requesting registration options from server');
      optionsResponse = await this.getRegistrationOptions(credentialName, authenticatorAttachment);
      console.log('Received registration options from server', { options: optionsResponse.options });
      
      // Apply browser-specific fixes if needed
      // Note: we're not modifying the options directly but logging info
      const browserSettings = applyBrowserSpecificFixes();
      console.log('Browser-specific settings available:', browserSettings);
      
      // 2. Start the WebAuthn registration process in the browser
      console.log('Starting WebAuthn registration in browser');
      registrationResponse = await startRegistration(optionsResponse.options);
      console.log('Received registration response from browser', { registrationResponse });
      
      // 3. Send the response to the server for verification
      console.log('Sending verification request to server');
      verificationResponse = await api.post('/webauthn/register/verify', {
        credential: registrationResponse,
        credential_name: credentialName,
        device_type: authenticatorAttachment || 'platform'
      });
      console.log('Received verification response from server', { verificationResponse });
      
      return verificationResponse.data;
    } catch (error: any) {
      console.error('Error during passkey registration:', error);
      
      // Handle WebAuthn specific errors with user-friendly messages
      if (error.name === 'AbortError') {
        console.log('User aborted the passkey registration operation');
        throw new Error('You cancelled the passkey registration process.');
      }
      
      if (error.name === 'NotAllowedError') {
        console.log('Operation not allowed by the browser or authenticator');
        throw new Error('The passkey operation was not allowed. This could be due to security settings on your device.');
      }
      
      if (error.name === 'SecurityError') {
        console.log('Security error - possibly due to non-secure context or insecure connection');
        throw new Error('Security requirements not met. Ensure you are using HTTPS.');
      }
      
      if (error.name === 'NotSupportedError') {
        console.log('Browser or authenticator does not support this operation');
        throw new Error('Your browser or device does not support passkeys or this specific type of passkey.');
      }
      
      // Handle server-side errors based on status codes
      if (error.response) {
        console.log('Server returned an error response', {
          status: error.response.status,
          detail: error.response.data?.detail
        });
        
        // Check for specific server error cases
        if (error.response.status === 400) {
          if (error.response.data?.detail?.includes('already registered')) {
            throw new Error('This passkey is already registered with your account.');
          }
          
          if (error.response.data?.detail?.includes('Not supported')) {
            throw new Error('This type of passkey is not supported by the server.');
          }
        }
        
        // If we have a specific error message from the server, use it
        if (error.response.data?.detail) {
          throw new Error(error.response.data.detail);
        }
      }
      
      // Use our diagnostic utility for more detailed error analysis
      const errorMessage = diagnoseWebAuthnError(error);
      throw new Error(errorMessage);
    }
  },

  /**
   * Get WebAuthn authentication options from the server
   * @param username Optional username
   * @param email Optional email
   * @param userId Optional user ID
   * @returns Authentication options from the server
   */
  async getAuthenticationOptions(
    username?: string,
    email?: string,
    userId?: number,
  ): Promise<AuthenticationOptionsResponse> {
    try {
      // Verify that at least one identifier is provided
      if (!username && !email && !userId) {
        throw new Error("At least one of username, email, or user_id must be provided for passkey authentication");
      }
      
      // Log what we're sending to the server for debugging
      const requestBody: any = {};
      if (username) requestBody.username = username;
      if (email) requestBody.email = email;
      if (userId) requestBody.user_id = userId;
      
      console.log('Sending authentication options request:', JSON.stringify(requestBody));
      
      // Request authentication options from the server
      const response = await api.post('/webauthn/authenticate/options', requestBody);
      
      return response.data;
    } catch (error: any) {
      // Check for specific backend errors
      if (error.response) {
        console.error(`Authentication server error (${error.response.status}):`, JSON.stringify(error.response.data));
        
        if (error.response.status === 400) {
          if (error.response.data?.detail === "No user found") {
            throw new Error("No user found with these credentials. Please check your email or username.");
          } else if (error.response.data?.detail === "No credentials found for user") {
            throw new Error("Your account doesn't have any passkeys registered. Please sign in with your password and register a passkey in account settings.");
          } else if (error.response.data?.detail) {
            // For any other specific error message from the backend
            throw new Error(error.response.data.detail);
          }
        }
      }
      
      console.error('Error getting authentication options:', error);
      throw error;
    }
  },

  /**
   * Authenticate with a passkey
   * @param username Optional username
   * @param email Optional email
   * @param userId Optional user ID
   * @param signal Optional AbortSignal for cancellation
   * @returns Authentication response with token
   */
  async authenticateWithPasskey(
    username?: string,
    email?: string,
    userId?: number,
    signal?: AbortSignal
  ): Promise<any> {
    try {
      // 1. Get authentication options from the server
      const authOptionsResponse = await this.getAuthenticationOptions(username, email, userId);
      const authOptions = authOptionsResponse.options; // Extract the options object
      console.log('[FRONTEND_DEBUG] Authentication options received from server:', JSON.stringify(authOptions, null, 2)); // Log the options being passed
      
      // 2. Start the WebAuthn authentication process in the browser
      let authResponse;
      try {
        authResponse = await startAuthentication(authOptions);
        console.log('[FRONTEND_DEBUG] startAuthentication successful:', authResponse);
      } catch (startAuthError: any) {
        console.error('[FRONTEND_ERROR] Error calling startAuthentication:', startAuthError);
        console.error('[FRONTEND_ERROR] Options passed to startAuthentication:', JSON.stringify(authOptions, null, 2));
        // Re-throw the error to be handled by the outer catch block
        throw startAuthError;
      }
      
      // 3. Verify the authentication
      const verificationResponse = await api.post('/webauthn/authenticate/verify', {
        credential: authResponse,
        user_id: authOptionsResponse.user_id,
      });
      
      return verificationResponse.data;
    } catch (error: any) {
      // Handle WebAuthn specific errors with user-friendly messages
      if (error.name === 'AbortError' || 
          (error.message && error.message.includes('abort'))) {
        throw new Error('You cancelled the authentication process.');
      }
      
      if (error.name === 'NotAllowedError') {
        throw new Error('The passkey operation was not allowed. This could be due to security settings on your device.');
      }
      
      if (error.name === 'SecurityError') {
        throw new Error('A security error occurred. Please ensure you are using a secure (HTTPS) connection.');
      }
      
      if (error.name === 'NotSupportedError') {
        throw new Error('Your browser or device does not support passkeys or this specific type of passkey.');
      }
      
      // Check for timeout errors
      if (error.name === 'TimeoutError' || 
          (error.message && error.message.includes('timeout'))) {
        throw new Error('The authentication took too long to complete. Please try again.');
      }
      
      // Handle axios errors from the backend
      if (error.response) {
        console.error(`Authentication server error (${error.response.status}): ${error.response.data?.detail || 'Unknown server error'}`);
        
        if (error.response.status === 400) {
          if (error.response.data?.detail === "No user found") {
            throw new Error("No account found with these credentials. Please check your email or username.");
          } else if (error.response.data?.detail === "No credentials found for user") {
            throw new Error("You don't have any passkeys registered. Please sign in with your password.");
          } else if (error.response.data?.detail === "Unknown credential") {
            throw new Error("This passkey isn't registered to your account. Please try a different device or sign in with your password.");
          } else if (error.response.data?.detail === "No challenge found") {
            throw new Error("Your session has expired. Please refresh the page and try again.");
          } else if (error.response.data?.detail) {
            // For any other specific error message from the backend, make it user friendly
            throw new Error("Unable to verify your passkey. Please try another device or use your password.");
          }
        }
      }

      // Network errors
      if (error.message && error.message.includes('Network Error')) {
        throw new Error('Unable to connect to the server. Please check your internet connection and try again.');
      }
      
      // Provide a more helpful error message for any other errors
      console.error('Error during passkey authentication:', error);
      throw new Error('Unable to sign in with your passkey. Please try again or use your password.');
    }
  },

  /**
   * Get a list of registered credentials for the current user
   * @returns List of credentials
   */
  async getCredentials(): Promise<Credential[]> {
    try {
      const response = await api.get('/webauthn/credentials');
      return response.data;
    } catch (error: any) {
      console.error('Error getting credentials:', error);
      
      // Handle network errors
      if (error.message && error.message.includes('Network Error')) {
        console.error('Network error when fetching credentials');
        // Return empty array instead of throwing - makes the UI more resilient
        return [];
      }
      
      // For other errors, also return empty array to avoid breaking the UI
      return [];
    }
  },

  /**
   * Delete a credential
   * @param credentialId ID of the credential to delete
   * @returns Success message
   */
  async deleteCredential(credentialId: number): Promise<any> {
    try {
      const response = await api.delete(`/webauthn/credentials/${credentialId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error deleting credential:', error);
      
      // Handle specific backend errors
      if (error.response) {
        if (error.response.status === 404) {
          throw new Error('This passkey no longer exists or has already been deleted.');
        } else if (error.response.status === 403) {
          throw new Error('You do not have permission to delete this passkey.');
        } else if (error.response.data?.detail) {
          console.error('Server error details:', error.response.data.detail);
        }
      }
      
      // Network errors
      if (error.message && error.message.includes('Network Error')) {
        throw new Error('Unable to connect to the server. Please check your internet connection and try again.');
      }
      
      // Generic error message for users
      throw new Error('Unable to delete the passkey. Please try again later.');
    }
  },
  
  /**
   * Check if WebAuthn is available in the current browser
   * @returns Boolean indicating WebAuthn support
   */
  isWebAuthnSupported(): boolean {
    return (
      window.PublicKeyCredential !== undefined && 
      typeof window.PublicKeyCredential === 'function'
    );
  },
  
  /**
   * Check if platform authenticator (e.g., TouchID, Windows Hello) is available
   * @returns Promise resolving to boolean indicating platform authenticator support
   */
  async isPlatformAuthenticatorAvailable(): Promise<boolean> {
    if (!this.isWebAuthnSupported()) {
      return false;
    }
    
    try {
      // This is a standard WebAuthn check for platform authenticators
      return await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
    } catch (error) {
      console.error('Error checking platform authenticator:', error);
      return false;
    }
  }
}; 