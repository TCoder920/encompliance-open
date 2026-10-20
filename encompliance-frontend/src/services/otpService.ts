/*
  Description: OTP service for handling one-time password functionality.
  Purpose: Manages requesting, verifying, and handling OTPs for email and SMS verification.
*/

import api from './api';

/**
 * OTP Request data interface
 */
export interface OTPRequestData {
  recipient: string;
  method: 'email' | 'sms';
}

/**
 * OTP Verification data interface
 */
export interface OTPVerifyData {
  recipient: string;
  otp_code: string;
  method: 'email' | 'sms';
}

/**
 * OTP Response interface
 */
export interface OTPResponse {
  success: boolean;
  message: string;
  expires_in?: number;
}

/**
 * OTP Verification Response interface
 */
export interface OTPVerifyResponse {
  success: boolean;
  message: string;
  verified: boolean;
  token?: string;
}

/**
 * Service for handling OTP operations
 */
export const otpService = {
  /**
   * Request an OTP to be sent via email or SMS
   * @param data OTP request data (recipient and method)
   * @returns Promise resolving to OTP response
   */
  async requestOTP(data: OTPRequestData): Promise<OTPResponse> {
    try {
      console.log(`Requesting ${data.method} OTP for ${data.recipient}`);
      const response = await api.post('/request-otp', data);
      console.log('OTP request successful');
      return response.data;
    } catch (error) {
      console.error('OTP request failed:', error);
      throw error;
    }
  },

  /**
   * Verify an OTP code
   * @param data OTP verification data (recipient, code, and method)
   * @returns Promise resolving to verification response
   */
  async verifyOTP(data: OTPVerifyData): Promise<OTPVerifyResponse> {
    try {
      console.log(`Verifying ${data.method} OTP for ${data.recipient}`);
      const response = await api.post('/verify-otp', data);
      console.log('OTP verification result:', response.data.verified);
      return response.data;
    } catch (error) {
      console.error('OTP verification failed:', error);
      throw error;
    }
  }
}; 