import api from './api';
import { webauthnService } from './webauthnService';
import { otpService } from './otpService';

/*
  Description: Authentication service for managing user authentication state and API calls.
  Purpose: Handles login, signup, logout, token management, and OpenAI resource synchronization for secure user access.
*/

/**
 * User signup data interface
 */
export interface SignupData {
  email: string;
  password: string;
  full_name: string;
  operation_name: string;
  facility_type?: string;
  state?: string;
  phone_number?: string;
  subscription_status?: string;
}

/**
 * User signup step 3 data interface (different from full SignupData)
 */
export interface SignupStep3Data {
  user_id: number | null;
  selected_facility_types: string[];
}

/**
 * Login credentials interface
 */
export interface LoginData {
  email: string;
  password: string;
}

/**
 * Authentication response interface with flexibility for different backend formats
 */
export interface AuthResponse {
  access_token?: string;
  token_type?: string;
  status?: string;
  user_id?: number;
  [key: string]: any; // For flexibility
}

/**
 * Authentication service for managing user authentication state and API calls
 */
export const authService = {
  /**
   * Store authentication token in localStorage
   * @param token JWT token string
   */
  setToken(token: string): void {
    localStorage.setItem('token', token);
  },

  /**
   * Retrieve authentication token from localStorage
   * @returns JWT token string or null if not found
   */
  getToken(): string | null {
    return localStorage.getItem('token');
  },

  /**
   * Remove authentication token from localStorage
   */
  removeToken(): void {
    localStorage.removeItem('token');
  },

  /**
   * Check if user is currently authenticated
   * @returns boolean indicating authentication status
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
  },

  /**
   * Log the user out by calling the backend logout endpoint and clearing local storage
   * @returns Promise resolving to logout response
   */
  async logout(): Promise<any> {
    try {
      // Only call the backend if we have a token
      if (this.isAuthenticated()) {
        // Call logout endpoint to trigger OpenAI resource cleanup
        await api.post('/logout');
        console.log('Backend logout successful');
      }
      // Always remove the token, even if the backend call fails
      this.removeToken();
      return { success: true };
    } catch (error) {
      console.error('Backend logout failed:', error);
      // Still remove the token even if the API call fails
      this.removeToken();
      throw error;
    }
  },

  /**
   * Synchronize OpenAI resources for the current user
   * This ensures that the OpenAI assistant, files, and vector store are up-to-date
   * @returns Promise resolving to synchronization response
   */
  async syncOpenAIResources(): Promise<any> {
    try {
      if (!this.isAuthenticated()) {
        // No logging - just return failed status
        return { success: false, message: 'User not authenticated' };
      }
      
      // No logging before request
      const response = await api.post('/sync-openai-resources');
      // No logging after request
      return response.data;
    } catch (error) {
      // No error logging - just return failed status
      return { 
        success: false, 
        message: 'Failed to synchronize OpenAI resources',
        error: error instanceof Error ? error.message : String(error)
      };
    }
  },

  /**
   * Authenticate user with email and password
   * Uses the /email-login endpoint which accepts JSON data directly
   * @param data Login credentials (email and password)
   * @returns Promise resolving to authentication response with token
   * @throws Error if authentication fails
   */
  async login(data: LoginData): Promise<AuthResponse> {
    try {
      // Use the email-login endpoint which accepts JSON data directly
      console.log('Attempting login with email-login endpoint');
      const response = await api.post('/email-login', data);
      console.log('Login successful');
      return response.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  },

  /**
   * Register a new user account - final step
   * @param data Signup step 3 data with user_id and selected_facility_types
   * @returns Promise resolving to authentication response
   * @throws Error if signup fails
   */
  async signup(data: SignupStep3Data): Promise<AuthResponse> {
    try {
      console.log('Attempting signup');
      const response = await api.post('/signup/step3', data);
      console.log('Signup successful');
      return response.data;
    } catch (error) {
      console.error('Signup failed:', error);
      throw error;
    }
  },
  
  /**
   * Check if WebAuthn/passkey is supported in the current browser
   * @returns boolean indicating WebAuthn support
   */
  isWebAuthnSupported(): boolean {
    return webauthnService.isWebAuthnSupported();
  },
  
  /**
   * Check if platform authenticator (TouchID, Windows Hello, etc.) is available
   * @returns Promise resolving to boolean indicating platform authenticator support
   */
  async isPlatformAuthenticatorAvailable(): Promise<boolean> {
    return webauthnService.isPlatformAuthenticatorAvailable();
  },
  
  /**
   * Authenticate with a passkey (WebAuthn)
   * @param email User email for identification
   * @returns Promise resolving to authentication response with token
   */
  async loginWithPasskey(email: string): Promise<AuthResponse> {
    try {
      console.log(`Attempting passkey login for email: ${email}`);
      const response = await webauthnService.authenticateWithPasskey(undefined, email);
      
      // If the response has an access token, store it
      if (response.access_token) {
        this.setToken(response.access_token);
        console.log('Passkey login successful');
      }
      
      return response;
    } catch (error: any) {
      // Extract the most useful error message possible
      let errorMessage: string;
      
      if (error.message?.includes("No user found")) {
        errorMessage = `No user account found with email "${email}". Please check your email or create an account.`;
      } else if (error.message?.includes("doesn't have any passkeys registered")) {
        errorMessage = error.message; // This is already a well-formatted message from webauthnService
      } else if (error.message?.includes("No credentials found") || error.response?.data?.detail === "No credentials found for user") {
        errorMessage = `No passkeys found for your account. Please sign in with your password first, then go to Account Settings → Passkeys to register a passkey for passwordless login.`;
      } else if (error.response?.data?.detail) {
        errorMessage = `Authentication failed: ${error.response.data.detail}`;
      } else if (error.message) {
        errorMessage = error.message;
      } else {
        errorMessage = 'Passkey authentication failed for an unknown reason';
      }
      
      console.error('Passkey login failed:', errorMessage);
      
      // Create an enhanced error with a better message
      const enhancedError = new Error(errorMessage);
      // Preserve the original error properties
      enhancedError.stack = error.stack;
      throw enhancedError;
    }
  },

  /**
   * Request an OTP for email or SMS verification
   * @param recipient Email address or phone number
   * @param method OTP delivery method ('email' or 'sms')
   * @returns Promise resolving to OTP request response
   */
  async requestOTP(recipient: string, method: 'email' | 'sms'): Promise<any> {
    return otpService.requestOTP({ recipient, method });
  },

  /**
   * Verify an OTP and authenticate the user
   * @param recipient Email address or phone number
   * @param otpCode 6-digit OTP code
   * @param method OTP delivery method ('email' or 'sms')
   * @returns Promise resolving to OTP verification response with token
   */
  async verifyOTP(recipient: string, otpCode: string, method: 'email' | 'sms'): Promise<any> {
    try {
      const response = await otpService.verifyOTP({
        recipient,
        otp_code: otpCode,
        method
      });
      
      // If verification successful and token provided, store it
      if (response.verified && response.token) {
        this.setToken(response.token);
      }
      
      return response;
    } catch (error) {
      console.error('OTP verification failed:', error);
      throw error;
    }
  },

  /**
   * Verify signup email using OTP
   * @param userId User ID from signup response
   * @param otpCode Verification code from email
   * @returns Promise resolving to authentication response with token
   */
  async verifySignupEmail(userId: number, otpCode: string): Promise<AuthResponse> {
    try {
      console.log(`Verifying signup email for user: ${userId}`);
      const response = await api.post('/verify-signup-email', {
        user_id: userId,
        otp_code: otpCode
      });
      
      console.log('Verification API response:', response.data);
      
      // If response contains a token, store it
      if (response.data?.access_token) {
        console.log('Token received from email verification, storing token');
        this.setToken(response.data.access_token);
        console.log('Email verification successful, token stored');
        
        // Update localStorage timestamp for future reference
        localStorage.setItem('auth_timestamp', Date.now().toString());
      } else {
        console.warn('Email verification response did not contain a token:', response.data);
      }
      
      return response.data;
    } catch (error) {
      console.error('Email verification failed:', error);
      throw error;
    }
  },
  
  /**
   * Resend signup verification OTP
   * @param userId User ID
   * @returns Promise resolving to response data
   */
  async resendSignupOtp(userId: number): Promise<any> {
    try {
      console.log(`Requesting new signup OTP for user: ${userId}`);
      // Use the actual endpoint
      const response = await api.post('/resend-signup-email', { user_id: userId });
      return response.data;
    } catch (error) {
      console.error('Failed to resend verification code:', error);
      throw error;
    }
  },
  
  /**
   * Verify login email using OTP (for inactive accounts)
   * @param userId User ID from login response
   * @param otpCode Verification code from email
   * @returns Promise resolving to authentication response with token
   */
  async verifyLoginEmail(userId: number, otpCode: string): Promise<AuthResponse> {
    try {
      console.log(`Verifying login email for user: ${userId}`);
      const response = await api.post('/verify-login-email', {
        user_id: userId,
        otp_code: otpCode
      });
      
      // If response contains a token, store it
      if (response.data?.access_token) {
        this.setToken(response.data.access_token);
        console.log('Login verification successful');
      }
      
      return response.data;
    } catch (error) {
      console.error('Login verification failed:', error);
      throw error;
    }
  }
}; 