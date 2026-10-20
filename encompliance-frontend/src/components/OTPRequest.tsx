/*
  Description: Component for requesting an OTP via email or SMS.
  Purpose: Allows users to initiate the OTP verification process by requesting a one-time code.
*/

import React, { useState } from 'react';
import { authService } from '../services/authService';

interface OTPRequestProps {
  defaultRecipient?: string;
  defaultMethod?: 'email' | 'sms';
  onOTPRequested: (details: { recipient: string; method: 'email' | 'sms' }) => void;
  className?: string;
}

const OTPRequest: React.FC<OTPRequestProps> = ({
  defaultRecipient = '',
  defaultMethod = 'email',
  onOTPRequested,
  className = ''
}) => {
  const [recipient, setRecipient] = useState(defaultRecipient);
  const [method, setMethod] = useState<'email' | 'sms'>(defaultMethod);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleRecipientChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setRecipient(e.target.value);
  };

  const handleMethodChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setMethod(e.target.value as 'email' | 'sms');
  };

  const validateRecipient = () => {
    if (!recipient) {
      setError('Recipient is required');
      return false;
    }
    
    if (method === 'email') {
      // Basic email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(recipient)) {
        setError('Please enter a valid email address');
        return false;
      }
    } else if (method === 'sms') {
      // Basic phone number validation
      const phoneRegex = /^\+?[1-9]\d{1,14}$/;
      if (!phoneRegex.test(recipient)) {
        setError('Please enter a valid phone number');
        return false;
      }
    }
    
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Reset states
    setError(null);
    setSuccess(null);
    
    if (!validateRecipient()) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await authService.requestOTP(recipient, method);
      
      if (response.success) {
        setSuccess(`Verification code sent to your ${method}. Valid for ${Math.floor((response.expires_in || 600) / 60)} minutes.`);
        onOTPRequested({ recipient, method }); // Notify parent that OTP was requested successfully
      } else {
        setError(response.message || 'Failed to send verification code');
      }
    } catch (err) {
      setError('Failed to send verification code. Please try again later.');
      console.error('OTP request error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`otprequest-container ${className}`}>
      <h2 className="text-xl font-semibold mb-4">Verification Code</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}
      
      <form id="otp-request-form" onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2">
            Verification Method
          </label>
          <select
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            value={method}
            onChange={handleMethodChange}
            disabled={isLoading}
          >
            <option value="email">Email</option>
            <option value="sms">SMS</option>
          </select>
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2">
            {method === 'email' ? 'Email Address' : 'Phone Number'}
          </label>
          <input
            type={method === 'email' ? 'email' : 'tel'}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder={method === 'email' ? 'your@email.com' : '+1234567890'}
            value={recipient}
            onChange={handleRecipientChange}
            disabled={isLoading}
          />
          <p className="text-gray-600 text-xs mt-1">
            {method === 'email' 
              ? 'We\'ll send a verification code to this email address' 
              : 'We\'ll send a verification code to this phone number'}
          </p>
        </div>
        
        <div className="flex items-center justify-between">
          <button
            type="submit"
            className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline ${
              isLoading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            disabled={isLoading}
          >
            {isLoading ? 'Sending...' : 'Send Verification Code'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default OTPRequest; 