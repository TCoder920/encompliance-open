/*
  Description: Component for verifying an OTP code.
  Purpose: Allows users to enter and submit a one-time password for verification.
*/

import React, { useState, useEffect } from 'react';
import { authService } from '../services/authService';

interface OTPVerifyProps {
  recipient: string;
  method: 'email' | 'sms';
  onVerified: (token: string) => void;
  onCancel: () => void;
  onResend: () => void;
  className?: string;
}

const OTPVerify: React.FC<OTPVerifyProps> = ({
  recipient,
  method,
  onVerified,
  onCancel,
  onResend,
  className = ''
}) => {
  const [otpCode, setOtpCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState(60); // 60 seconds countdown for resend
  const [canResend, setCanResend] = useState(false);

  // Handle countdown for resend button
  useEffect(() => {
    if (timeLeft <= 0) {
      setCanResend(true);
      return;
    }

    const timer = setTimeout(() => {
      setTimeLeft(timeLeft - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [timeLeft]);

  const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Only allow digits and limit to 6 characters
    const value = e.target.value.replace(/\D/g, '').substring(0, 6);
    setOtpCode(value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Reset error
    setError(null);
    
    // Validate OTP code
    if (otpCode.length !== 6) {
      setError('Please enter a 6-digit verification code');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await authService.verifyOTP(recipient, otpCode, method);
      
      if (response.verified && response.token) {
        // Notify parent that OTP verification was successful
        onVerified(response.token);
      } else {
        setError(response.message || 'Verification failed. Please try again.');
      }
    } catch (err) {
      setError('Verification failed. Please try again.');
      console.error('OTP verification error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = () => {
    setCanResend(false);
    setTimeLeft(60);
    onResend();
  };

  return (
    <div className={`otpverify-container ${className}`}>
      <h2 className="text-xl font-semibold mb-4">Enter Verification Code</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <p className="text-gray-600 mb-4">
        {recipient
          ? <>We've sent a verification code to {recipient} via {method}. Please enter the code below.</>
          : <>We've sent a verification code via {method}. Please enter the code below.</>}
      </p>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2">
            6-Digit Verification Code
          </label>
          <input
            type="text"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 text-center text-xl tracking-widest leading-tight focus:outline-none focus:shadow-outline"
            value={otpCode}
            onChange={handleOtpChange}
            disabled={isLoading}
            autoFocus
            placeholder="------"
            inputMode="numeric"
          />
        </div>
        
        <div className="flex flex-col space-y-2">
          <button
            type="submit"
            className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline ${
              isLoading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            disabled={isLoading}
          >
            {isLoading ? 'Verifying...' : 'Verify Code'}
          </button>
          
          <div className="flex justify-between">
            <button
              type="button"
              className="text-blue-500 hover:text-blue-700 text-sm font-medium"
              onClick={onCancel}
              disabled={isLoading}
            >
              Back
            </button>
            
            <button
              type="button"
              className={`text-blue-500 hover:text-blue-700 text-sm font-medium ${
                !canResend ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              onClick={handleResend}
              disabled={!canResend || isLoading}
            >
              {canResend ? 'Resend Code' : `Resend in ${timeLeft}s`}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default OTPVerify; 