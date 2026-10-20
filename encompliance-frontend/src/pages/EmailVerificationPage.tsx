/*
  Description: Email verification page for confirming user accounts.
  Purpose: Allows users to verify their email by entering an OTP after signup.
  
  Educational Note: Updated to support both session-based and legacy user-based
  verification flows for backward compatibility during transition.
*/

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/authService';
import ErrorMessage from '../components/ErrorMessage';
import { Shield, Mail } from 'lucide-react';
import api from '../services/api';

const EmailVerificationPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, signup, refreshAuthState } = useAuth();
  
  // Parse state passed from signup - now supports both session and user-based flows
  const state = location.state as { 
    userId?: number; 
    email?: string; 
    sessionToken?: string;
    isSessionBased?: boolean;
    selectedTier?: string;
  } || {};
  const { userId, email, sessionToken, isSessionBased = false, selectedTier } = state;
  
  const [otpCode, setOtpCode] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState(60); // 60 seconds countdown for resend
  const [canResend, setCanResend] = useState(false);

  // Helper function to handle pro user Stripe redirect
  const handleProUserStripeRedirect = async () => {
    try {
      console.log('Creating Stripe checkout session for pro user');
      setError(null); // Clear any previous errors
      
      const response = await api.post('/payments/upgrade-to-pro', {
        facility_name: `${email || 'User'}'s Facility`,
        success_url: `${window.location.origin}/dashboard?upgrade=success`,
        cancel_url: `${window.location.origin}/dashboard?upgrade=cancelled`,
        trial_days: 7
      });
      
      console.log('Stripe checkout session created, redirecting to:', response.data.checkout_url);
      
      // Show user feedback before redirect
      setError('Redirecting to payment portal...');
      
      // Small delay to show the message, then redirect
      setTimeout(() => {
      window.location.href = response.data.checkout_url;
      }, 1000);
      
    } catch (error: any) {
      console.error('Error creating Stripe checkout session:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to start payment process. Please try again.';
      setError(`Payment setup failed: ${errorMessage}`);
      // Don't redirect to dashboard on error - let user see the error and try again
    }
  };

  // If user is already authenticated, redirect to appropriate page based on tier
  useEffect(() => {
    if (isAuthenticated) {
      console.log('User is already authenticated, redirecting based on tier:', selectedTier);
      if (selectedTier === 'pro') {
        console.log('Redirecting pro user to Stripe checkout');
        handleProUserStripeRedirect();
      } else {
        console.log('Redirecting to dashboard');
        navigate('/dashboard');
      }
    }
  }, [isAuthenticated, navigate, selectedTier]);

  // If no userId or sessionToken was provided, redirect to login
  useEffect(() => {
    if (!userId && !sessionToken) {
      navigate('/login');
    }
  }, [userId, sessionToken, navigate]);

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
    
    if ((!userId && !sessionToken) || (isSessionBased && !sessionToken) || (!isSessionBased && !userId)) {
      setError('Verification information is missing. Please try signing up again.');
      return;
    }
    
    if (otpCode.length !== 6) {
      setError('Please enter a 6-digit verification code');
      return;
    }
    
    setIsSubmitting(true);
    setError(null);
    
    try {
      if (isSessionBased && sessionToken) {
        // Session-based verification
        console.log('Verifying session-based signup email');
        const response = await api.post('/verify-session-signup-email', {
          session_token: sessionToken,
          otp_code: otpCode
        });
        
        console.log('Session verification response:', response.data);
        
        // Session verification returns a token directly
        if (response.data?.access_token) {
          console.log('Token received from session verification, storing token');
          authService.setToken(response.data.access_token);
          
          // Update auth state and navigate to appropriate location
          await refreshAuthState();
          
          // If this is an invitation signup, redirect to the original invitation page
          const urlParams = new URLSearchParams(location.search);
          const redirectUrl = urlParams.get('redirect');
          
          if (redirectUrl) {
            navigate(redirectUrl);
          } else if (selectedTier === 'pro') {
            // Pro users need to complete payment via Stripe
            handleProUserStripeRedirect();
          } else {
            navigate('/dashboard');
          }
        } else {
          setError('Verification successful but no authentication token received. Please try logging in.');
        }
      } else if (userId) {
        // Legacy user-based verification
        console.log('Verifying legacy user-based signup email');
        const response = await authService.verifySignupEmail(userId, otpCode);
        
        console.log('Email verification response:', response);
        
        // Now explicitly update the auth context to ensure state is properly set
        if (response && response.access_token) {
          console.log('Token received, refreshing auth state');
          
          // Refresh auth state to get user data
          const authSuccess = await refreshAuthState();
          
          if (authSuccess) {
            console.log('Auth state refreshed successfully, navigating to appropriate page');
            if (selectedTier === 'pro') {
              // Pro users need to complete payment via Stripe
              handleProUserStripeRedirect();
            } else {
              navigate('/dashboard');
            }
          } else {
            console.warn('Auth state refresh failed, but token exists. Attempting direct navigation.');
            // Still try to navigate - the token might be valid
            if (selectedTier === 'pro') {
              handleProUserStripeRedirect();
            } else {
              navigate('/dashboard');
            }
          }
        } else {
          console.warn('No token received from verification response');
          setError('Verification completed but authentication failed. Please try logging in.');
        }
      }
    } catch (error: any) {
      console.error('Email verification error:', error);
      const errorMessage = error.response?.data?.detail || 'Verification failed. Please check your code and try again.';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendOtp = async () => {
    if ((!userId && !sessionToken) || (isSessionBased && !sessionToken) || (!isSessionBased && !userId)) {
      setError('Verification information is missing. Please try signing up again.');
      return;
    }
    
    setCanResend(false);
    setTimeLeft(60);
    setError(null);
    
    try {
      if (isSessionBased && sessionToken) {
        // Session-based resend
        await api.post('/resend-session-signup-email', {
          session_token: sessionToken
        });
      } else if (userId) {
        // Legacy user-based resend
        await authService.resendSignupOtp(userId);
      }
      // Show success message or toast
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to resend verification code. Please try again later.';
      setError(errorMessage);
      setCanResend(true); // Allow immediate retry
    }
  };

  return (
    <div className="container mx-auto px-4 py-12 max-w-md">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-lg p-8">
        <div className="text-center mb-6">
          <Mail className="h-12 w-12 text-navy-blue dark:text-blue-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-navy-blue dark:text-white">Verify Your Email</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            We've sent a verification code to your email. Please enter it below to complete your registration.
          </p>
          {email && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Code sent to: {email}
            </p>
          )}
        </div>
        
        {error && (
          <div className="mb-4">
            <ErrorMessage 
              message={error}
              type="error"
              onClose={() => setError(null)}
            />
            {selectedTier === 'pro' && error.includes('Payment setup failed') && (
              <div className="mt-3 text-center">
                <button
                  onClick={handleProUserStripeRedirect}
                  className="bg-navy-blue text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 transition-colors"
                >
                  Try Payment Setup Again
                </button>
              </div>
            )}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="mt-6">
          <div className="mb-6">
            <label htmlFor="otp-code" className="block text-gray-700 dark:text-gray-300 text-sm font-medium mb-2">
              Verification Code
            </label>
            <input
              type="text"
              id="otp-code"
              value={otpCode}
              onChange={handleOtpChange}
              placeholder="Enter 6-digit code"
              className="w-full p-3 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm text-center text-xl tracking-widest focus:ring-navy-blue focus:border-navy-blue dark:bg-gray-800 dark:text-white"
              inputMode="numeric"
              autoFocus
              disabled={isSubmitting}
            />
            <p className="text-sm text-gray-500 mt-1">
              Enter the 6-digit code sent to your email
            </p>
          </div>
          
          <button
            type="submit"
            className={`w-full bg-navy-blue text-white py-2 px-4 rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-navy-blue ${
              isSubmitting ? 'opacity-70 cursor-not-allowed' : ''
            }`}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Verifying...' : 'Verify Email'}
          </button>
          
          <div className="mt-4 flex justify-between items-center">
            <button
              type="button"
              className="text-sm text-navy-blue dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
              onClick={() => navigate('/login')}
            >
              Back to Login
            </button>
            
            <button
              type="button"
              className={`text-sm text-navy-blue dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 ${
                !canResend ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              onClick={handleResendOtp}
              disabled={!canResend || isSubmitting}
            >
              {canResend ? 'Resend Code' : `Resend in ${timeLeft}s`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EmailVerificationPage; 