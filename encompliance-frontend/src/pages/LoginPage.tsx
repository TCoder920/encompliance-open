/**
 * LoginPage Component
 * 
 * This component provides authentication functionality for the application, including:
 * - Email/password login
 * - Passkey (WebAuthn) authentication when supported by the browser
 * - OTP-based login via email or SMS
 * - Form validation and error handling
 * - Visual feedback during authentication processes
 * 
 * The component detects browser support for WebAuthn and platform authenticators
 * to conditionally render passkey authentication options when available.
 */

import React, { useState, useEffect } from 'react';
import { Mail, Lock, Eye, EyeOff, Fingerprint, AlertCircle, Key, MessageSquare, Shield, HelpCircle, Info, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import ErrorMessage from '../components/ErrorMessage';
import { useNavigate, Link } from 'react-router-dom';

const LoginPage: React.FC = () => {
  const { login, loginWithPasskey, error: authError, clearError, isWebAuthnSupported, isPlatformAuthenticatorAvailable } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [webAuthnSupported, setWebAuthnSupported] = useState(false);
  const [platformAuthSupported, setPlatformAuthSupported] = useState(false);
  const [showPasskeyTooltip, setShowPasskeyTooltip] = useState(false);
  const [showPasskeyHelpModal, setShowPasskeyHelpModal] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const navigate = useNavigate();
  
  // Check WebAuthn support when component mounts
  useEffect(() => {
    const checkWebAuthnSupport = async () => {
      const supported = isWebAuthnSupported();
      setWebAuthnSupported(supported);
      
      if (supported) {
        const platformSupported = await isPlatformAuthenticatorAvailable();
        setPlatformAuthSupported(platformSupported);
      }
    };
    
    checkWebAuthnSupport();
    
    // Clear errors when component unmounts
    return () => {
      clearError();
    };
  }, [clearError, isWebAuthnSupported, isPlatformAuthenticatorAvailable]);
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Clear errors when user starts typing
    if (localError) setLocalError(null);
    if (authError) clearError();
  };
  
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    try {
      setIsSubmitting(true);
      setLocalError(null);
      
      await login(formData.email, formData.password);
      
      // Redirect to dashboard on successful login
      // Check for authError again *after* login attempt
      if (!authError) {
        navigate('/dashboard');
      } else {
        setLocalError('Invalid email or password. Please try again.');
      }
    } catch (err) {
      setLocalError('Invalid email or password. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handlePasskeyLogin = async (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    // Check for valid email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email.trim() || !emailRegex.test(formData.email.trim())) {
      setLocalError('Please enter a valid email address to use passkey login.');
      return;
    }
    
    try {
      setIsSubmitting(true);
      setLocalError(null);
      
      await loginWithPasskey(formData.email);
      
      // Redirect to dashboard on successful login
      if (!authError) {
        navigate('/dashboard');
      }
    } catch (err: any) {
      // Display the error message directly - it's already been formatted nicely by upstream services
      setLocalError(err.message || 'Passkey authentication failed. Please try again or use your password.');
      
      // Show the help modal if the error is about not having passkeys registered
      if (err.message?.includes("No passkeys found") || 
          err.message?.includes("register a passkey") || 
          err.message?.includes("doesn't have any passkeys")) {
        setShowPasskeyHelpModal(true);
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const isFormValid = () => {
    return formData.email.trim() !== '' && formData.password.trim() !== '';
  };
  
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const redirectToOtpLogin = (reason?: string) => {
    const query = new URLSearchParams();
    if (formData.email.trim() !== '') {
      query.set('recipient', formData.email.trim());
    }
    query.set('method', 'email');
    if (reason) {
      query.set('reason', reason);
    }
    const queryString = query.toString();
    navigate(`/login/otp${queryString ? `?${queryString}` : ''}`);
  };

  const handleOTPLogin = () => {
    redirectToOtpLogin();
  };

  const handleForgotPassword = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    redirectToOtpLogin('forgot-password');
  };
  
  return (
    <div className="container mx-auto px-4 py-12 max-w-md">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-navy-blue dark:text-white mb-6 text-center font-times">Login to Your Account</h1>
        
        {localError && (
          <ErrorMessage 
            message={localError}
            type="error"
            onClose={() => setLocalError(null)}
          />
        )}
        
        {authError && (
          <ErrorMessage 
            message={authError}
            type="error"
            onClose={clearError}
          />
        )}
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email Address</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-navy-blue focus:border-navy-blue border p-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                placeholder="john@example.com"
                required
                autoComplete="email"
              />
            </div>
          </div>
          
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="pl-10 pr-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-navy-blue focus:border-navy-blue border p-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={togglePasswordVisibility}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
          </div>
          
          <div className="flex justify-between text-sm">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 text-navy-blue focus:ring-navy-blue border-gray-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-gray-700 dark:text-gray-300">
                Remember me
              </label>
            </div>
            <button
              type="button"
              onClick={handleForgotPassword}
              className="font-medium text-navy-blue hover:text-navy-blue/80 dark:text-sky-400 dark:hover:text-sky-300"
            >
              Forgot password?
            </button>
          </div>
          
          <div>
            <button
              type="submit"
              disabled={!isFormValid() || isSubmitting}
              className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-navy-blue dark:bg-slate-800 hover:bg-navy-blue/90 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-navy-blue dark:focus:ring-slate-700 ${
                (!isFormValid() || isSubmitting) ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {isSubmitting ? 'Logging in...' : 'Sign in'}
            </button>
          </div>
          
          {webAuthnSupported && (
            <div className="relative">
              <button
                type="button"
                onClick={handlePasskeyLogin}
                disabled={isSubmitting}
                className={`w-full flex justify-center items-center gap-2 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-white bg-white dark:bg-slate-700 hover:bg-gray-50 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-navy-blue dark:focus:ring-slate-500 ${
                  isSubmitting ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <Fingerprint className="h-5 w-5" />
                {platformAuthSupported ? 'Sign in with Passkey' : 'Sign in with Security Key'}
                <span 
                  className="inline-flex ml-1 cursor-help"
                  onMouseEnter={() => setShowPasskeyTooltip(true)}
                  onMouseLeave={() => setShowPasskeyTooltip(false)}
                  onFocus={() => setShowPasskeyTooltip(true)}
                  onBlur={() => setShowPasskeyTooltip(false)}
                  aria-describedby="passkey-tooltip"
                >
                  <Info className="h-4 w-4 text-gray-400" />
                </span>
              </button>
              
              {showPasskeyTooltip && (
                <div 
                  id="passkey-tooltip" 
                  role="tooltip" 
                  className="absolute z-10 mt-2 p-3 bg-gray-800 text-white text-xs rounded shadow-lg w-64 animate-fadeIn right-0"
                >
                  <div className="flex items-start gap-2">
                    <Info className="h-4 w-4 flex-shrink-0 mt-0.5 text-blue-300" />
                    <div>
                      <p className="font-semibold">First-time passkey user?</p>
                      <p className="mt-1">You need to register a passkey before using this option:</p>
                      <ol className="list-decimal ml-4 mt-1">
                        <li>Sign in with password first</li>
                        <li>Go to Account Settings</li>
                        <li>Find the Passkeys section</li>
                        <li>Register your device</li>
                      </ol>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <div>
            <button
              type="button"
              onClick={handleOTPLogin}
              disabled={isSubmitting}
              className={`w-full flex justify-center items-center gap-2 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-white bg-white dark:bg-slate-700 hover:bg-gray-50 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-navy-blue dark:focus:ring-slate-500 ${
                isSubmitting ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <Shield className="h-5 w-5" />
              Sign in with OTP
            </button>
          </div>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Don't have an account?{' '}
            <Link to="/signup" className="font-medium text-navy-blue hover:text-navy-blue/80 dark:text-sky-400 dark:hover:text-sky-300">
              Sign up
            </Link>
          </p>
        </div>
        
        {/* Passkey Help Modal */}
        {showPasskeyHelpModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                  <Fingerprint className="h-5 w-5 mr-2 text-navy-blue dark:text-blue-400" />
                  Setting Up Passkey Authentication
                </h3>
                <button 
                  onClick={() => setShowPasskeyHelpModal(false)}
                  className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              
              <div className="mb-6">
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                  Passkeys are a secure, passwordless way to sign in. You need to set up a passkey before you can use this feature.
                </p>
                
                <div className="space-y-4">
                  <div className="flex items-start">
                    <div className="bg-navy-blue text-white rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">1</div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Sign in with your password</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Use your email and password to sign in first</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="bg-navy-blue text-white rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">2</div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Go to Account Settings</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Find your account or profile settings in the app</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="bg-navy-blue text-white rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">3</div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Find the Passkeys section</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Look for "Passkeys" or "Security" in your settings</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="bg-navy-blue text-white rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">4</div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Register your device</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Follow the prompts to register a new passkey</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowPasskeyHelpModal(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-600"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    setShowPasskeyHelpModal(false);
                    document.getElementById('password')?.focus();
                  }}
                  className="px-4 py-2 bg-navy-blue text-white rounded-md hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700"
                >
                  Sign In with Password
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginPage; 