/*
  Description: Signup page component. Handles user registration and onboarding for the compliance platform.
  Purpose: Enables new users to create accounts and configure initial settings.
  
  Educational Note: Uses session-based signup flow to defer user creation
  until email verification, following data minimization principles.
*/
import React, { useState, useEffect } from 'react';
import { MapPin, User, Building, Mail, Phone, Lock, Eye, EyeOff, CheckCircle, XCircle, Shield, Users } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/authService';
import ErrorMessage from '../components/ErrorMessage';
import api from '../services/api';
import { useNavigate, useLocation } from 'react-router-dom';

// Password validation uses a predefined set of safe symbols

const SignupPage: React.FC = () => {
  const { signup, error: authError, clearError, isAuthenticated } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  
  // Parse URL parameters for invitation handling
  const urlParams = new URLSearchParams(location.search);
  const invitationCode = urlParams.get('invitation');
  const invitationEmail = urlParams.get('email');
  const facilityName = urlParams.get('facility');
  const isInvitation = !!invitationCode;
  
  const [step, setStep] = useState(1);
  const [userId, setUserId] = useState<number | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [selectedState, setSelectedState] = useState('');
  const [userRole, setUserRole] = useState<'facility_admin' | 'regular_user' | ''>('');
  const [selectedTier, setSelectedTier] = useState<'free' | 'pro' | ''>('');
  const [facilityTypes, setFacilityTypes] = useState<string[]>([]);
  const [selectedFacilityTypes, setSelectedFacilityTypes] = useState<string[]>([]);
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    fullName: '',
    operationName: facilityName || '', // Pre-fill with facility name if invitation
    email: invitationEmail || '', // Pre-fill with email if invitation
    password: '',
    phoneNumber: ''
  });
  
  // State for password validation criteria
  const [passwordValidation, setPasswordValidation] = useState({
    minLength: false,
    hasNumber: false,
    hasSymbol: false,
    hasUppercase: false,
    hasLowercase: false,
  });

  // State for phone number validation
  const [isPhoneValid, setIsPhoneValid] = useState(false);

  // Facility data for facility administrators (users with pro subscription)
  const [facilityData, setFacilityData] = useState({
    facilityName: '',
    facilityAddress: '',
    facilityCity: '',
    facilityState: '',
    facilityZip: '',
    facilityPhone: '',
    facilityEmail: ''
  });

  // Clear errors when component unmounts
  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);
  
  // Fetch facility types when state is selected
  useEffect(() => {
    if (step === 3 && selectedState) {
      fetchFacilityTypes();
    }
  }, [step, selectedState]);
  
  const states = [
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 
    'Delaware', 'District of Columbia', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 
    'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 
    'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 
    'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 
    'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Puerto Rico', 'Rhode Island', 'South Carolina', 
    'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 
    'West Virginia', 'Wisconsin', 'Wyoming'
  ];
  
  // Validate password in real-time
  const validatePassword = (password: string) => {
    setPasswordValidation({
      minLength: password.length >= 8,
      hasNumber: /\d/.test(password),
      hasSymbol: /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password),
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
    });
  };

  // Validate phone number in real-time
  const validatePhoneNumber = (phoneNumber: string) => {
    // Remove all non-digit characters for validation
    const digitsOnly = phoneNumber.replace(/[^\d]/g, '');
    
    // Check if it's a valid US phone number (10 digits)
    const isValid = digitsOnly.length === 10;
    setIsPhoneValid(isValid);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Validate password in real-time
    if (name === 'password') {
      validatePassword(value);
    }

    // Validate phone number in real-time
    if (name === 'phoneNumber') {
      validatePhoneNumber(value);
    }

    // Clear errors when user starts typing
    if (localError) setLocalError(null);
    if (authError) clearError();
  };
  
  const fetchFacilityTypes = async () => {
    setIsLoading(true);
    try {
      const response = await api.get(`/facility-types?state=${selectedState}`);
      if (response.data && Array.isArray(response.data)) {
        // The API returns an array of strings directly, not objects with .name property
        setFacilityTypes(response.data);
      } else {
        console.error('Unexpected facility types response format:', response.data);
        setFacilityTypes([]);
      }
    } catch (error) {
      console.error('Error fetching facility types:', error);
      setLocalError('Failed to fetch facility types. Please try again.');
      setFacilityTypes([]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleNextStep = async () => {
    if (step === 1) {
      // Validate step 1 fields
      if (!isFormValid()) {
        setLocalError('Please fill all required fields and meet password/phone requirements.');
        return;
      }
      
      setIsSubmitting(true);
      try {
        // Use session-based signup (default behavior)
        const response = await api.post('/session-signup/step1', {
          email: formData.email,
          password: formData.password,
          full_name: formData.fullName,
          operation_name: formData.operationName,
          phone_number: formData.phoneNumber.replace(/[^\d]/g, '')
        });
        
        // Store the session token for subsequent steps
        setSessionToken(response.data.session_token);
        
        // Clear any errors and proceed to next step
        setLocalError(null);
        if (authError) clearError();
        
        // For invitations, skip role selection and set as team member
        if (isInvitation) {
          setUserRole('regular_user'); // This will be converted to team_member in backend
          setSelectedTier('free'); // Team members get pro access through facility
          // Skip directly to email verification
          try {
            await api.post('/session-signup/step1point5', {
              session_token: response.data.session_token,
              user_role: 'regular_user' // Backend will convert to team_member for invitations
            });
            
            await api.post('/session-signup/step1point75', {
              session_token: response.data.session_token,
              selected_tier: 'free' // Individual subscription stays free
            });
            
            // Complete signup with invitation code
            const completeResponse = await api.post('/session-signup/step3-invitation', {
              session_token: response.data.session_token,
              invitation_code: invitationCode
            });
            
            console.log('Step3-invitation request data:', {
              session_token: response.data.session_token,
              invitation_code: invitationCode,
              invitationCodeType: typeof invitationCode,
              invitationCodeLength: invitationCode?.length
            });
            
            if (completeResponse.data.status === 'session_signup_pending_email_verification') {
              navigate('/verify-email', { 
                state: { 
                  sessionToken: completeResponse.data.session_token,
                  email: completeResponse.data.email,
                  isSessionBased: true,
                  invitationCode: invitationCode
                } 
              });
              return;
            }
          } catch (error: any) {
            const errorMessage = error.response?.data?.detail || 'An error occurred during invitation signup.';
            setLocalError(errorMessage);
          }
        } else {
          setStep(2); // Go to tier selection
        }
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || 'An error occurred during signup.';
        setLocalError(errorMessage);
      } finally {
        setIsSubmitting(false);
      }
    } else if (step === 2) {
      // Tier selection step - infer role from tier
      if (!selectedTier) {
        setLocalError('Please select a subscription tier to continue.');
        return;
      }
      
      // All users are regular users - tier only affects subscription level
      const userRole = 'regular_user';
      setUserRole(userRole);
      
      setIsSubmitting(true);
      try {
        // Send role selection - all users are regular users
        await api.post('/session-signup/step1point5', {
          session_token: sessionToken,
          user_role: userRole
        });
        
        await api.post('/session-signup/step1point75', {
          session_token: sessionToken,
          selected_tier: selectedTier
        });
        
        setLocalError(null);
        if (authError) clearError();
        
        // All users go to state selection next
        setStep(3);
      } catch (error: any) {
        if (error.response?.status === 404) {
          setLocalError('Session expired or invalid. Please start over.');
          setTimeout(() => setStep(1), 2000);
        } else {
          const errorMessage = error.response?.data?.detail || 'An error occurred during tier selection.';
          setLocalError(errorMessage);
        }
      } finally {
        setIsSubmitting(false);
      }
    } else if (step === 3) {
      // Combined state and facility type selection step (for ALL users)
      if (!selectedState) {
        setLocalError('Please select a state to continue');
        return;
      }
      
      if (selectedFacilityTypes.length === 0) {
        setLocalError('Please select at least one facility type');
        return;
      }
      
      setIsSubmitting(true);
      try {
        // First save the state
        await api.post('/session-signup/step2', {
          session_token: sessionToken,
          state: selectedState
        });
        
        // Then complete signup with facility types
        const response = await api.post('/session-signup/step3', {
          session_token: sessionToken,
          selected_facility_types: selectedFacilityTypes
        });
        
        // Check for pending email verification
        if (response.data.status === 'session_signup_pending_email_verification') {
          navigate('/verify-email', { 
            state: { 
              sessionToken: response.data.session_token,
              email: response.data.email,
              isSessionBased: true,
              selectedTier: selectedTier // Pass tier info for post-auth routing
            } 
          });
          return;
        }
        
      } catch (error: any) {
        if (error.response?.status === 404) {
          setLocalError('Session expired or invalid. Please start over.');
          setTimeout(() => setStep(1), 2000);
        } else {
          const errorMessage = error.response?.data?.detail || 'An error occurred during signup completion.';
          setLocalError(errorMessage);
        }
      } finally {
        setIsSubmitting(false);
      }
    }
  };
  
  const handleFacilityTypeToggle = (facilityType: string) => {
    setSelectedFacilityTypes(prev => {
      if (prev.includes(facilityType)) {
        return prev.filter(type => type !== facilityType);
      } else {
        return [...prev, facilityType];
      }
    });
  };
  
  // Add an effect to watch for authentication state changes
  useEffect(() => {
    // If authentication state changes to true and we're on step 3 (final step), navigate to dashboard
    if (isAuthenticated && step === 3 && navigate) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, step, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (userRole === 'facility_admin') {
      // Validate facility data
      if (!facilityData.facilityName.trim()) {
        setLocalError('Please enter a facility name');
        return;
      }
      
      setIsSubmitting(true);
      try {
        const response = await api.post('/session-signup/step3-facility-admin', {
          session_token: sessionToken,
          facility_name: facilityData.facilityName,
          facility_address: facilityData.facilityAddress,
          facility_city: facilityData.facilityCity,
          facility_state: facilityData.facilityState,
          facility_zip: facilityData.facilityZip,
          facility_phone: facilityData.facilityPhone,
          facility_email: facilityData.facilityEmail,
          trial_days: 7
        });
        
        // Navigate to email verification
        if (response.data.status === 'session_signup_pending_email_verification') {
          navigate('/verify-email', { 
            state: { 
              sessionToken: response.data.session_token,
              email: response.data.email,
              isSessionBased: true,
              userType: 'facility_admin'
            } 
          });
          return;
        }
        
      } catch (error: any) {
        if (error.response?.status === 404) {
          setLocalError('Session expired or invalid. Please start over.');
          setTimeout(() => setStep(1), 2000);
        } else {
          const errorMessage = error.response?.data?.detail || 'An error occurred during facility creation.';
          setLocalError(errorMessage);
        }
      } finally {
        setIsSubmitting(false);
      }
    } else {
      // Regular user flow - validate facility type selection
      if (selectedFacilityTypes.length === 0) {
        setLocalError('Please select at least one facility type');
        return;
      }
      
      setIsSubmitting(true);
      try {
        // Session-based signup step 3
        const response = await api.post('/session-signup/step3', {
          session_token: sessionToken,
          selected_facility_types: selectedFacilityTypes
        });
        
        // Check for pending email verification
        if (response.data.status === 'session_signup_pending_email_verification') {
          // Navigate to the email verification page with session token
          navigate('/verify-email', { 
            state: { 
              sessionToken: response.data.session_token,
              email: response.data.email,
              isSessionBased: true,
              selectedTier: selectedTier // Pass tier info for post-auth routing
            } 
          });
          return;
        }
        
      } catch (error: any) {
        if (error.response?.status === 404) {
          setLocalError('Session expired or invalid. Please start over.');
          setTimeout(() => setStep(1), 2000);
        } else {
          const errorMessage = error.response?.data?.detail || 'An error occurred during signup completion.';
          setLocalError(errorMessage);
        }
      } finally {
        setIsSubmitting(false);
      }
    }
  };
  
  // Check if all form fields are valid AND password/phone requirements are met
  const isFormValid = () => {
    const basicFieldsValid = 
      formData.fullName.trim() !== '' &&
      formData.operationName.trim() !== '' &&
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim()) && // Basic email format check
      formData.password.trim() !== '' && 
      formData.phoneNumber.trim() !== '';

    // Do not block form submission based on password requirements
    return basicFieldsValid && isPhoneValid;
  };
  
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };
  
  // Helper component for password requirements
  const PasswordRequirement: React.FC<{met: boolean; text: string}> = ({ met, text }) => (
    <div className={`flex items-center text-xs ${met ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
      {met ? <CheckCircle className="h-3 w-3 mr-1" /> : <XCircle className="h-3 w-3 mr-1" />}
      {text}
    </div>
  );

  // Render team member invitation signup flow
  if (isInvitation) {
    return (
      <div className="container mx-auto px-4 py-12 max-w-md">
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-lg p-8">
          {/* Team Member Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/20 rounded-full mb-4">
              <Users className="h-8 w-8 text-green-600 dark:text-green-400" />
            </div>
            <h1 className="text-2xl font-bold text-navy-blue dark:text-white mb-2">Join {facilityName}</h1>
            <p className="text-gray-600 dark:text-gray-400">
              You've been invited to join as a team member
            </p>
          </div>
          
          {/* Display errors */}
          {localError && (
            <ErrorMessage 
              message={localError}
              type="error"
              onClose={() => setLocalError(null)}
            />
          )}
          
          {authError && !localError && (
            <ErrorMessage 
              message={authError}
              type="error"
              onClose={clearError}
            />
          )}
          
          <div className="space-y-4">
            {/* Full Name */}
            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="fullName"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleInputChange}
                  className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-navy-blue focus:border-navy-blue border p-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                  placeholder="John Doe"
                  required
                />
              </div>
            </div>
            
            {/* Email (pre-filled and disabled) */}
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
                  className="pl-10 block w-full rounded-md bg-gray-100 dark:bg-gray-900 border-gray-300 shadow-sm border p-2 text-gray-600 dark:text-gray-400 cursor-not-allowed"
                  disabled
                />
              </div>
            </div>
            
            {/* Phone Number */}
            <div>
              <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone Number</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Phone className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="tel"
                  id="phoneNumber"
                  name="phoneNumber"
                  value={formData.phoneNumber}
                  onChange={handleInputChange}
                  className={`pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-navy-blue focus:border-navy-blue border p-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white ${
                    formData.phoneNumber && !isPhoneValid ? 'border-red-500' : ''
                  }`}
                  placeholder="(555) 123-4567"
                  required
                />
              </div>
              {formData.phoneNumber && !isPhoneValid && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">Please enter a valid 10-digit phone number</p>
              )}
            </div>
            
            {/* Password */}
            <form>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Create Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="pl-10 pr-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-navy-blue focus:border-navy-blue border p-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                  placeholder="Enter your password"
                  required
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={togglePasswordVisibility}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              
              {formData.password && (
                <div className="mt-2 space-y-1">
                  <PasswordRequirement met={passwordValidation.minLength} text="At least 8 characters" />
                  <PasswordRequirement met={passwordValidation.hasNumber} text="Contains a number" />
                  <PasswordRequirement met={passwordValidation.hasSymbol} text="Contains a symbol" />
                  <PasswordRequirement met={passwordValidation.hasUppercase} text="Contains uppercase letter" />
                  <PasswordRequirement met={passwordValidation.hasLowercase} text="Contains lowercase letter" />
                </div>
              )}
            </form>
            
            {/* Hidden fields for invitation flow */}
            <input type="hidden" name="operationName" value={formData.operationName} />
          </div>
          
          <button
            onClick={handleNextStep}
            disabled={!isFormValid() || isSubmitting}
            className={`w-full mt-6 py-3 px-4 rounded-lg font-medium transition duration-200 ${
              isFormValid() && !isSubmitting
                ? 'bg-green-600 text-white hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400'
            }`}
          >
            {isSubmitting ? 'Creating Your Account...' : 'Join Team'}
          </button>
          
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <Shield className="inline-block h-4 w-4 mr-1" />
              You'll get access to all Pro features as a team member
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Regular signup flow (non-invitation)
  return (
    <div className="container mx-auto px-4 py-12 max-w-2xl">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-navy-blue dark:text-white mb-6 text-center font-times">Create Your Account</h1>
        
        {/* Step indicator */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center">
            <div className={`rounded-full h-8 w-8 flex items-center justify-center ${step >= 1 ? 'bg-navy-blue text-white' : 'bg-gray-300 text-gray-600'}`}>1</div>
            <div className={`h-1 w-8 ${step >= 2 ? 'bg-navy-blue' : 'bg-gray-300'}`}></div>
            <div className={`rounded-full h-8 w-8 flex items-center justify-center ${step >= 2 ? 'bg-navy-blue text-white' : 'bg-gray-300 text-gray-600'}`}>2</div>
            <div className={`h-1 w-8 ${step >= 3 ? 'bg-navy-blue' : 'bg-gray-300'}`}></div>
            <div className={`rounded-full h-8 w-8 flex items-center justify-center ${step >= 3 ? 'bg-navy-blue text-white' : 'bg-gray-300 text-gray-600'}`}>3</div>
          </div>
        </div>
        
        {/* Display localError if it exists (covers both validation and API errors) */}
        {localError && (
          <ErrorMessage 
            message={localError}
            type="error"
            onClose={() => setLocalError(null)} // Allow dismissing local errors
          />
        )}
        
        {/* Display authError from context if it exists (usually from checkAuth on load) */}
        {authError && !localError && ( // Avoid showing duplicate errors if localError is set
          <ErrorMessage 
            message={authError}
            type="error"
            onClose={clearError} // Allow dismissing context errors
          />
        )}
        
        {step === 1 ? (
          <>
            <div className="space-y-4 mb-6">
              {/* Full Name */}
              <div>
                <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    id="fullName"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleInputChange}
                    className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-navy-blue focus:border-navy-blue border p-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                    placeholder="John Doe"
                    required // Add HTML5 required attribute
                  />
                </div>
              </div>
              
              {/* Operation Name */}
              <div>
                <label htmlFor="operationName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Operation Name</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Building className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    id="operationName"
                    name="operationName"
                    value={formData.operationName}
                    onChange={handleInputChange}
                    className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-navy-blue focus:border-navy-blue border p-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                    placeholder="ABC Daycare"
                    required
                  />
                </div>
              </div>
              
              {/* Email */}
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
                  />
                </div>
              </div>
              
              {/* Phone Number */}
              <div>
                <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone Number</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Phone className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="tel"
                    id="phoneNumber"
                    name="phoneNumber"
                    value={formData.phoneNumber}
                    onChange={handleInputChange}
                    className={`pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-navy-blue focus:border-navy-blue border p-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white ${
                      formData.phoneNumber && !isPhoneValid ? 'border-red-500' : ''
                    }`}
                    placeholder="(555) 123-4567"
                    required
                  />
                </div>
                {formData.phoneNumber && !isPhoneValid && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">Please enter a valid 10-digit phone number</p>
                )}
              </div>
              
              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="pl-10 pr-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-navy-blue focus:border-navy-blue border p-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                    placeholder="Enter your password"
                    required
                  />
                  <button
                    type="button"
                    onClick={togglePasswordVisibility}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5 text-gray-400" />
                    ) : (
                      <Eye className="h-5 w-5 text-gray-400" />
                    )}
                  </button>
                </div>
                
                {formData.password && (
                  <div className="mt-2 space-y-1">
                    <PasswordRequirement met={passwordValidation.minLength} text="At least 8 characters" />
                    <PasswordRequirement met={passwordValidation.hasNumber} text="Contains a number" />
                    <PasswordRequirement met={passwordValidation.hasSymbol} text="Contains a symbol" />
                    <PasswordRequirement met={passwordValidation.hasUppercase} text="Contains uppercase letter" />
                    <PasswordRequirement met={passwordValidation.hasLowercase} text="Contains lowercase letter" />
                  </div>
                )}
              </div>
            </div>
            
            <button
              onClick={handleNextStep}
              disabled={!isFormValid() || isSubmitting}
              className={`w-full py-2 px-4 rounded ${
                isFormValid() && !isSubmitting
                  ? 'bg-navy-blue text-white hover:bg-blue-800 dark:bg-blue-700 dark:hover:bg-blue-800'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400'
              } transition duration-200`}
            >
              {isSubmitting ? 'Creating Account...' : 'Next'}
            </button>
          </>
        ) : step === 2 ? (
          <>
            <h2 className="text-xl font-semibold text-navy-blue dark:text-white mb-4 text-center">Choose Your Plan</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6 text-center">
              Select the subscription tier that best fits your needs.
            </p>
            
            <div className="space-y-4 mb-6">
              {/* Free Tier Option */}
              <div 
                onClick={() => setSelectedTier('free')}
                className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                  selectedTier === 'free' 
                    ? 'border-navy-blue bg-blue-50 dark:bg-blue-900/20' 
                    : 'border-gray-300 hover:border-gray-400 dark:border-gray-700'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className={`w-4 h-4 rounded-full border-2 mt-1 ${
                    selectedTier === 'free' 
                      ? 'border-navy-blue bg-navy-blue' 
                      : 'border-gray-300'
                  }`}>
                    {selectedTier === 'free' && (
                      <div className="w-2 h-2 bg-white rounded-full m-0.5"></div>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-navy-blue dark:text-white">Free</h3>
                        <p className="text-2xl font-bold text-navy-blue dark:text-white">$0</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">per month</p>
                      </div>
                    </div>
                    <ul className="text-sm text-gray-600 dark:text-gray-400 mt-3 space-y-1">
                      <li>✓ Basic compliance tools</li>
                      <li>✓ AI assistant with limited queries</li>
                      <li>✓ Document uploads</li>
                      <li>✓ Personal compliance tracking</li>
                    </ul>
                  </div>
                </div>
              </div>
              
              {/* Pro Tier Option */}
              <div 
                onClick={() => setSelectedTier('pro')}
                className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                  selectedTier === 'pro' 
                    ? 'border-navy-blue bg-blue-50 dark:bg-blue-900/20' 
                    : 'border-gray-300 hover:border-gray-400 dark:border-gray-700'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className={`w-4 h-4 rounded-full border-2 mt-1 ${
                    selectedTier === 'pro' 
                      ? 'border-navy-blue bg-navy-blue' 
                      : 'border-gray-300'
                  }`}>
                    {selectedTier === 'pro' && (
                      <div className="w-2 h-2 bg-white rounded-full m-0.5"></div>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-navy-blue dark:text-white">Pro</h3>
                        <p className="text-2xl font-bold text-navy-blue dark:text-white">$50</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">base + $15/additional user</p>
                      </div>
                      <div className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                        Facility Administrator
                      </div>
                    </div>
                    <ul className="text-sm text-gray-600 dark:text-gray-400 mt-3 space-y-1">
                      <li>✓ All Free features</li>
                      <li>✓ Unlimited AI queries</li>
                      <li>✓ Compliance calendar</li>
                      <li>✓ Advanced notes system</li>
                      <li>✓ Training & certification management</li>
                      <li>✓ Team member management</li>
                      <li>✓ Facility-wide reporting</li>
                      <li>✓ User invitations</li>
                      <li>✓ Priority support</li>
                    </ul>
                    <div className="mt-2 text-xs text-green-600 dark:text-green-400">
                      Includes 7-day free trial + facility administrator privileges
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={() => setStep(1)}
                className="w-1/2 py-2 px-4 rounded border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition duration-200"
              >
                Back
              </button>
              <button
                onClick={handleNextStep}
                disabled={!selectedTier || isSubmitting}
                className={`w-1/2 py-2 px-4 rounded ${
                  selectedTier && !isSubmitting
                    ? 'bg-navy-blue text-white hover:bg-blue-800 dark:bg-blue-700 dark:hover:bg-blue-800'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400'
                } transition duration-200`}
              >
                {isSubmitting ? 'Processing...' : 'Continue'}
              </button>
            </div>
          </>
        ) : step === 3 ? (
          // Combined state and facility type selection for ALL users
          <>
            <h2 className="text-xl font-semibold text-navy-blue dark:text-white mb-4 text-center">Select Your State & Facility Types</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6 text-center">
              Choose your state and the types of facilities that apply to your operation.
            </p>
            
            {/* State Selection */}
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3">State</h3>
              <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                {states.map((state) => (
                  <button
                    key={state}
                    onClick={() => setSelectedState(state)}
                    className={`p-2 text-left rounded border transition duration-200 ${
                      selectedState === state 
                        ? 'bg-navy-blue text-white border-navy-blue'
                        : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center">
                      <MapPin className="h-4 w-4 mr-2" />
                      {state}
                    </div>
                  </button>
                ))}
              </div>
            </div>
            
            {/* Facility Types Selection */}
            {selectedState && (
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3">Facility Types</h3>
                {isLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-navy-blue mx-auto"></div>
                    <p className="mt-4 text-gray-600 dark:text-gray-400">Loading facility types...</p>
                  </div>
                ) : facilityTypes.length > 0 ? (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {facilityTypes.map((facilityType) => (
                      <label
                        key={facilityType}
                        className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer border-gray-300 dark:border-gray-700"
                      >
                        <input
                          type="checkbox"
                          checked={selectedFacilityTypes.includes(facilityType)}
                          onChange={() => handleFacilityTypeToggle(facilityType)}
                          className="h-4 w-4 text-navy-blue focus:ring-navy-blue border-gray-300 rounded"
                        />
                        <span className="text-gray-700 dark:text-gray-300">{facilityType}</span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600 dark:text-gray-400 text-center py-4">No facility types available for {selectedState}.</p>
                )}
              </div>
            )}
            
            <div className="flex space-x-4">
              <button
                onClick={() => setStep(2)}
                className="w-1/2 py-2 px-4 rounded border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition duration-200"
              >
                Back
              </button>
              <button
                onClick={handleNextStep}
                disabled={!selectedState || selectedFacilityTypes.length === 0 || isSubmitting}
                className={`w-1/2 py-2 px-4 rounded ${
                  selectedState && selectedFacilityTypes.length > 0 && !isSubmitting
                    ? 'bg-navy-blue text-white hover:bg-blue-800 dark:bg-blue-700 dark:hover:bg-blue-800'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400'
                } transition duration-200`}
              >
                {isSubmitting ? 'Creating Account...' : 'Complete Signup'}
              </button>
            </div>
          </>
                ) : null}
      </div>
    </div>
  );
};

export default SignupPage;