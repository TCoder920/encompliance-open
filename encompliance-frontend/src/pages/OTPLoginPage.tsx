/*
  Description: OTP Login page combining request and verification steps.
  Purpose: Provides a complete flow for OTP-based authentication, supporting both email and SMS methods.
*/

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import OTPRequest from '../components/OTPRequest';
import OTPVerify from '../components/OTPVerify';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const OTPLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { refreshAuthState } = useAuth();
  const { theme } = useTheme();
  
  // Extract any initial recipient/method from URL query params
  const queryParams = new URLSearchParams(location.search);
  const initialRecipient = queryParams.get('recipient') || '';
  const initialMethod = (queryParams.get('method') as 'email' | 'sms') || 'email';
  const reason = queryParams.get('reason');
  const isForgotPasswordFlow = reason === 'forgot-password';
  
  const [showVerification, setShowVerification] = useState(false);
  const [recipient, setRecipient] = useState(initialRecipient);
  const [method, setMethod] = useState<'email' | 'sms'>(initialMethod);
  
  // Handle OTP request completion
  const handleOTPRequested = ({ recipient: requestedRecipient, method: requestedMethod }: { recipient: string; method: 'email' | 'sms' }) => {
    setRecipient(requestedRecipient);
    setMethod(requestedMethod);
    setShowVerification(true);
  };
  
  // Handle OTP verification success
  const handleVerified = async (token: string) => {
    // Explicitly refresh the auth state to update user context
    try {
      const success = await refreshAuthState();
      if (success) {
        navigate('/dashboard');
      } else {
        // Fallback: still navigate, but user context may not be set
        navigate('/dashboard');
        setTimeout(() => {
          if (window.location.pathname !== '/dashboard') {
            window.location.href = '/dashboard';
          }
        }, 500);
      }
    } catch (err) {
      // Fallback: still navigate, but user context may not be set
      navigate('/dashboard');
    }
  };
  
  // Handle going back to request OTP screen
  const handleCancel = () => {
    setShowVerification(false);
  };
  
  // Handle resend OTP request
  const handleResend = () => {
    setShowVerification(false);
    // Slight delay to show the request form again before auto-submitting
    setTimeout(() => {
      document.getElementById('otp-request-form')?.dispatchEvent(
        new Event('submit', { bubbles: true, cancelable: true })
      );
    }, 100);
  };
  
  const targetLabel = recipient || (method === 'sms' ? 'your phone' : 'your email');
  const subtitle = showVerification
    ? (isForgotPasswordFlow
        ? `Enter the confirmation code we sent to ${targetLabel} to finish resetting your password.`
        : `Enter the verification code sent to ${targetLabel}`)
    : (isForgotPasswordFlow
        ? 'We will send you a secure login code so you can get back into your account and update your password.'
        : 'Get a one-time verification code to login');

  return (
    <div className={`min-h-screen transition-colors duration-1000 ${theme === 'dark' ? 'bg-dark-bg text-white' : 'bg-gray-50 text-gray-900'}`}>
      <div className={`w-full max-w-md m-auto rounded-lg shadow-md p-8 ${theme === 'dark' ? 'bg-dark-surface' : 'bg-white'}`}>
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-navy-blue dark:text-white">
            {isForgotPasswordFlow ? 'Reset Your Password' : 'Login with Verification Code'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">{subtitle}</p>
        </div>
        
        {showVerification ? (
          <OTPVerify
            recipient={recipient}
            method={method}
            onVerified={handleVerified}
            onCancel={handleCancel}
            onResend={handleResend}
          />
        ) : (
          <OTPRequest
            defaultRecipient={recipient}
            defaultMethod={method}
            onOTPRequested={handleOTPRequested}
          />
        )}
        
        {isForgotPasswordFlow && (
          <p className="mt-6 text-sm text-gray-600 dark:text-gray-400 text-center">
            After signing in with the verification code, open Settings → Security to update your password.
          </p>
        )}
        
        <div className="mt-8 text-center">
          <p className="text-gray-600">
            Want to use a different login method?
          </p>
          <div className="mt-2">
            <button
              onClick={() => navigate('/login')}
              className="text-blue-500 hover:text-blue-700"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OTPLoginPage; 