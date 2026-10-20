/*
  Description: User settings page component. Allows users to view and update their profile, preferences, and account settings.
  Purpose: Provides a user interface for managing personal information and application preferences.
*/
import React, { useState, useEffect } from 'react';
import { User, Mail, Phone, Lock, Save, AlertCircle, Trash2, Building, CreditCard, Star, Award, MapPin, RefreshCw, Shield, Bell } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import ErrorMessage from '../components/ErrorMessage';
import api from '../services/api';
import { userService } from '../services/userService';
import { authService } from '../services/authService';
import { useNavigate, useSearchParams } from 'react-router-dom';
import PasskeyRegistration from '../components/PasskeyRegistration';
import { notificationSettingsService, NotificationSettings, NotificationSettingsUpdate } from '../services/notificationSettingsService';
import { pushNotificationService } from '../services/pushNotificationService';

const UserSettingsPage: React.FC = () => {
  const { user, error: authError, clearError, logout, updateUserContext, isWebAuthnSupported, refreshAuthState } = useAuth();
  const [localError, setLocalError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isPhoneValid, setIsPhoneValid] = useState(false);
  const [facilityTypes, setFacilityTypes] = useState<string[]>([]);
  const [selectedFacilityTypes, setSelectedFacilityTypes] = useState<string[]>([]);
  const [isLoadingFacilityTypes, setIsLoadingFacilityTypes] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'subscription' | 'notifications' | 'advanced'>('profile');
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phoneNumber: '',
    operationName: '',
    subscription: 'free',
    state: ''
  });
  const [notificationSettingsData, setNotificationSettingsData] = useState<NotificationSettings | null>(null);
  const [isPushSubscribed, setIsPushSubscribed] = useState(false);
  const [isPushLoading, setIsPushLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // Expanded states list with availability
  const states = [
    { name: 'Alabama', available: true },
    { name: 'Alaska', available: true },
    { name: 'Arizona', available: true },
    { name: 'Arkansas', available: true },
    { name: 'California', available: true },
    { name: 'Colorado', available: true },
    { name: 'Connecticut', available: true },
    { name: 'Delaware', available: true },
    { name: 'District of Columbia', available: true },
    { name: 'Florida', available: true },
    { name: 'Georgia', available: true },
    { name: 'Hawaii', available: true },
    { name: 'Idaho', available: true },
    { name: 'Illinois', available: true },
    { name: 'Indiana', available: true },
    { name: 'Iowa', available: true },
    { name: 'Kansas', available: true },
    { name: 'Kentucky', available: true },
    { name: 'Louisiana', available: true },
    { name: 'Maine', available: true },
    { name: 'Maryland', available: true },
    { name: 'Massachusetts', available: true },
    { name: 'Michigan', available: true },
    { name: 'Minnesota', available: true },
    { name: 'Mississippi', available: true },
    { name: 'Missouri', available: true },
    { name: 'Montana', available: true },
    { name: 'Nebraska', available: true },
    { name: 'Nevada', available: true },
    { name: 'New Hampshire', available: true },
    { name: 'New Jersey', available: true },
    { name: 'New Mexico', available: true },
    { name: 'New York', available: true },
    { name: 'North Carolina', available: true },
    { name: 'North Dakota', available: true },
    { name: 'Ohio', available: true },
    { name: 'Oklahoma', available: true },
    { name: 'Oregon', available: true },
    { name: 'Pennsylvania', available: true },
    { name: 'Rhode Island', available: true },
    { name: 'South Carolina', available: true },
    { name: 'South Dakota', available: true },
    { name: 'Tennessee', available: true },
    { name: 'Texas', available: true },
    { name: 'Utah', available: true },
    { name: 'Vermont', available: true },
    { name: 'Virginia', available: true },
    { name: 'Washington', available: true },
    { name: 'West Virginia', available: true },
    { name: 'Wisconsin', available: true },
    { name: 'Wyoming', available: true },
    { name: 'Guam', available: true },
    { name: 'Northern Mariana Islands', available: true },
    { name: 'Puerto Rico', available: true },
    { name: 'Virgin Islands', available: true },
  ].sort((a, b) => a.name.localeCompare(b.name)); // Sort alphabetically
  
  // Load user data when component mounts
  useEffect(() => {
    const initPage = async () => {
      if (user) { // Ensure user context is loaded
        setFormData({
          fullName: user.full_name || '',
          email: user.email || '',
          phoneNumber: user.phone_number || '',
          operationName: user.operation_name || '',
          subscription: user.subscription_status || 'free',
          state: user.state || '' // Load user state
        });
        // Initialize selected facility types from user data (comma-separated string)
        if (user.facility_type) {
          setSelectedFacilityTypes(user.facility_type.split(',').map((type: string) => type.trim()));
        } else {
          setSelectedFacilityTypes([]);
        }
        // Validate phone number on load
        validatePhoneNumber(user.phone_number || '');

        // Fetch notification settings ONLY if user is available
        try {
          console.log("UserSettingsPage: User context available, fetching notification settings...");
          const settings = await notificationSettingsService.getSettings();
          setNotificationSettingsData(settings);
          console.log("UserSettingsPage: Notification settings fetched:", settings);
        } catch (err) {
          console.error("UserSettingsPage: Error fetching notification settings:", err);
          setLocalError("Failed to load notification settings.");
        }

        // Check current push subscription status
        if (pushNotificationService.isSupported()) {
          const subscribed = await pushNotificationService.isSubscribed();
          setIsPushSubscribed(subscribed);
        }
      } else {
        console.log("UserSettingsPage: User context not yet available.");
        // Optionally, set loading state or handle case where user is not logged in
      }
    };

    // Handle upgrade success/cancellation messages first
    const urlParams = new URLSearchParams(window.location.search);
    const upgradeStatus = urlParams.get('upgrade');
    
    const handleUpgradeMessages = async () => {
      if (upgradeStatus === 'success') {
        // Check if we have a session_id to verify
        const sessionId = urlParams.get('session_id');
        
        if (sessionId) {
          try {
            console.log('Verifying checkout session:', sessionId);
            const verifyResponse = await api.post(`/payments/verify-payment?session_id=${sessionId}`);
            
            if (verifyResponse.data.success) {
              setSuccessMessage('🎉 Welcome to Pro! Your subscription has been activated and your facility is ready.');
              console.log('Checkout session verified successfully:', verifyResponse.data);
              
              // Add a small delay to ensure backend has committed changes
              setTimeout(async () => {
                try {
                  const refreshed = await refreshAuthState();
                  if (refreshed) {
                    console.log('User data refreshed after verification success');
                  }
                } catch (error) {
                  console.error('Failed to refresh user data after verification:', error);
                }
              }, 1000);
            } else {
              console.error('Checkout session verification failed:', verifyResponse.data);
              // Check if this is a "already upgraded" case
              if (verifyResponse.data.action === 'user_already_upgraded_to_pro') {
                setSuccessMessage('🎉 Welcome to Pro! Your subscription is already active.');
                
                // Still refresh user data
                setTimeout(async () => {
                  try {
                    await refreshAuthState();
                  } catch (error) {
                    console.error('Failed to refresh user data:', error);
                  }
                }, 500);
              } else {
                setLocalError(`Payment verification failed: ${verifyResponse.data.message || 'Unknown error'}. Please contact support if your payment was processed.`);
              }
            }
          } catch (error: any) {
            console.error('Error verifying checkout session:', error);
            if (error.response?.data?.detail) {
              setLocalError(`Payment verification failed: ${error.response.data.detail}. Please contact support if your payment was processed.`);
            } else {
              setLocalError('Payment verification failed. Please contact support if your payment was processed.');
            }
          }
        } else {
          // Fallback for old URLs without session_id
          setSuccessMessage('🎉 Welcome to Pro! Your subscription has been activated and your facility is ready.');
          
          // Still try to refresh user data
          setTimeout(async () => {
            try {
              await refreshAuthState();
            } catch (error) {
              console.error('Failed to refresh user data:', error);
            }
          }, 500);
        }
        
        // Clear the URL parameters
        window.history.replaceState({}, '', window.location.pathname + '?tab=subscription');
      } else if (upgradeStatus === 'cancelled') {
        setLocalError('Upgrade was cancelled. You can try again anytime.');
        // Clear the URL parameter
        window.history.replaceState({}, '', window.location.pathname + '?tab=subscription');
      }
    };
    
    // Run both functions
    initPage();
    handleUpgradeMessages();
    
    return () => {
      if (authError) clearError();
    };
  }, [user, authError, clearError, refreshAuthState]);
  
  // Fetch facility types when state changes
  useEffect(() => {
    if (formData.state) {
      setSelectedFacilityTypes([]); // Reset selections when state changes
      fetchFacilityTypes();
    } else {
      // Clear types if state is deselected
      setFacilityTypes([]);
      setSelectedFacilityTypes([]);
    }
  }, [formData.state]);
  
  // Handle URL parameters to set active tab
  useEffect(() => {
    const tabParam = searchParams.get('tab');
    const allowedTabs = user?.user_role === 'team_member' 
      ? ['profile', 'security', 'notifications'] 
      : ['profile', 'security', 'subscription', 'notifications', 'advanced'];
    
    if (tabParam && allowedTabs.includes(tabParam)) {
      setActiveTab(tabParam as 'profile' | 'security' | 'subscription' | 'notifications' | 'advanced');
    } else if (user?.user_role === 'team_member' && (tabParam === 'subscription' || tabParam === 'advanced')) {
      // Redirect team members away from restricted tabs
      setActiveTab('profile');
    }
  }, [searchParams, user?.user_role]);
  
  const fetchFacilityTypes = async () => {
    if (!formData.state) return; // Don't fetch if no state is selected

    setIsLoadingFacilityTypes(true);
    setFacilityTypes([]); // Clear previous types
    setLocalError(null);
    try {
      const response = await api.get(`/facility-types?state=${formData.state}`);
      if (response.data && Array.isArray(response.data)) {
        setFacilityTypes(response.data);
      } else {
        console.error('Unexpected facility types response format:', response.data);
        setFacilityTypes([]);
      }
    } catch (error) {
      console.error('Error fetching facility types:', error);
      setLocalError('Failed to fetch facility types for the selected state. Please try again.');
      setFacilityTypes([]);
    } finally {
      setIsLoadingFacilityTypes(false);
    }
  };
  
  // Phone number validation function (same as in SignupPage)
  const validatePhoneNumber = (phone: string) => {
    const digitsOnly = phone.replace(/[^\d]/g, ''); // Remove non-digit characters
    setIsPhoneValid(digitsOnly.length === 10);
  };
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Validate phone number in real-time
    if (name === 'phoneNumber') {
      validatePhoneNumber(value);
    }
    
    // Clear messages when user starts typing
    if (localError) setLocalError(null);
    if (successMessage) setSuccessMessage(null);
    if (authError) clearError();
  };
  
  const handleFacilityTypeToggle = (facilityType: string) => {
    setSelectedFacilityTypes(prev => {
      if (prev.includes(facilityType)) {
        return prev.filter((type: string) => type !== facilityType);
      } else {
        return [...prev, facilityType];
      }
    });
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate the form before submitting
    if (!formData.fullName.trim()) {
      setLocalError('Full name is required.');
      return;
    }
    
    // Only validate facility fields for non-team members
    if (user?.user_role !== 'team_member') {
    if (!formData.operationName.trim()) {
      setLocalError('Operation name is required.');
      return;
    }
    
      if (!formData.state) {
        setLocalError('Please select your state.');
      return;
      }
    }
    
    if (!isPhoneValid) {
      setLocalError('Please enter a valid 10-digit phone number.');
      return;
    }
    
    try {
      setIsLoading(true);
      setLocalError(null);
      setSuccessMessage(null);
      
      // Prepare update data - only include facility fields for non-team members
      const updateData: any = {
        full_name: formData.fullName,
        phone_number: formData.phoneNumber.replace(/[^\d]/g, ''), 
        subscription_status: formData.subscription,
      };
      
      // Only include facility management fields for non-team members
      if (user?.user_role !== 'team_member') {
        updateData.operation_name = formData.operationName;
        updateData.facility_type = selectedFacilityTypes.join(', ');
        updateData.state = formData.state;
      }
      
      // Call API to update user
      const updatedUser = await userService.updateCurrentUser(updateData);
      
      // Update the AuthContext directly with the returned user data
      updateUserContext(updatedUser);
      
      setSuccessMessage('Your profile has been updated successfully.');
      // Navigate back to dashboard after successful update
      navigate('/dashboard');
    } catch (err) {
      console.error('Error updating profile:', err);
      setLocalError('Failed to update profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSubscriptionChange = async (plan: string) => {
    try {
      setIsLoading(true);
      setLocalError(null);
      
      if (plan === 'pro' && formData.subscription === 'free') {
        // Redirect to Pro upgrade flow
        handleUpgradeToPro();
        return;
      }
      
      if (plan === 'free' && formData.subscription === 'pro') {
        // Handle downgrade through Stripe Customer Portal
        handleManageSubscription();
        return;
      }
      
      // For other changes, use the old method
      const updateData = { subscription_status: plan };
      
      // Call API to update user
      const updatedUser = await userService.updateCurrentUser(updateData);
      
      // Update local form data first for responsiveness
      setFormData(prev => ({ ...prev, subscription: plan }));
      
      // Update the AuthContext directly with the returned user data
      updateUserContext(updatedUser);
      
      setSuccessMessage(`Your subscription has been updated to ${plan.charAt(0).toUpperCase() + plan.slice(1)}.`);
    } catch (err) {
      console.error('Error updating subscription:', err);
      setLocalError('Failed to update subscription. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpgradeToPro = async () => {
    try {
      setIsLoading(true);
      setLocalError(null);
      
      // Create upgrade checkout session
      const response = await api.post('/payments/upgrade-to-pro', {
        facility_name: `${user?.full_name || user?.email}'s Facility`,
        success_url: `${window.location.origin}/userSettings?tab=subscription&upgrade=success`,
        cancel_url: `${window.location.origin}/userSettings?tab=subscription&upgrade=cancelled`,
                  trial_days: 7
      });
      
      // Redirect to Stripe Checkout
      window.location.href = response.data.checkout_url;
      
    } catch (err: any) {
      console.error('Error creating upgrade checkout:', err);
      setLocalError(err.response?.data?.detail || 'Failed to start upgrade process. Please try again.');
      setIsLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    try {
      setIsLoading(true);
      setLocalError(null);
      
      // Open Stripe Customer Portal for subscription management
      const response = await api.post('/payments/create-customer-portal', {}, {
        params: {
          return_url: `${window.location.origin}/userSettings?tab=subscription`
        }
      });
      
      // Redirect to Stripe Customer Portal
      window.location.href = response.data.portal_url;
      
    } catch (err: any) {
      console.error('Error opening customer portal:', err);
      setLocalError(err.response?.data?.detail || 'Failed to open billing portal. Please try again.');
      setIsLoading(false);
    }
  };
  
  const handleDeleteAccount = async () => {
    if (!showDeleteConfirm) {
      setShowDeleteConfirm(true);
      return;
    }
    
    try {
      setIsDeleting(true);
      await userService.deleteAccount();
      logout();
      navigate('/login');
    } catch (error) {
      console.error('Error deleting account:', error);
      setLocalError('Failed to delete account. Please try again later.');
      setShowDeleteConfirm(false);
    } finally {
      setIsDeleting(false);
    }
  };
  
  const cancelDelete = () => {
    setShowDeleteConfirm(false);
  };
  
  const handleSyncResources = async () => {
    try {
      setIsSyncing(true);
      setSyncStatus('idle');
      setSyncMessage(null);
      
      const result = await authService.syncOpenAIResources();
      
      if (result.success) {
        setSyncStatus('success');
        setSyncMessage(`Resources synchronized successfully. Added ${result.files_added || 0} files, removed ${result.files_removed || 0} files.`);
      } else {
        setSyncStatus('error');
        setSyncMessage(result.message || 'Failed to synchronize resources. Please try again later.');
      }
    } catch (error) {
      console.error('Error synchronizing resources:', error);
      setSyncStatus('error');
      setSyncMessage('Failed to synchronize resources. Please try again later.');
    } finally {
      setIsSyncing(false);
    }
  };
  
  const handleNotificationSettingsChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    if (!notificationSettingsData) return;

    const { name, value, type, checked } = e.target as HTMLInputElement;
    const val = type === 'checkbox' ? checked : (type === 'number' ? parseInt(value, 10) : value);

    setNotificationSettingsData({
      ...notificationSettingsData,
      [name]: val,
    });
  };

  const handleSaveNotificationSettings = async () => {
    if (!notificationSettingsData) return;
    setLocalError(null);
    setSuccessMessage(null);
    setIsLoading(true);
    try {
      // Prepare the data for update. NotificationSettingsUpdate expects optional fields.
      // We only send the fields that are part of NotificationSettingsUpdate.
      const updatePayload: NotificationSettingsUpdate = {};
      for (const key in notificationSettingsData) {
        if (Object.prototype.hasOwnProperty.call(notificationSettingsData, key) && 
            key !== 'id' && key !== 'user_id' && key !== 'created_at' && key !== 'updated_at') {
          // Type assertion to allow indexing
          (updatePayload as any)[key] = (notificationSettingsData as any)[key];
        }
      }

      const updatedSettings = await notificationSettingsService.updateSettings(updatePayload);
      setNotificationSettingsData(updatedSettings); // The response from updateSettings should be the full NotificationSettings object
      setSuccessMessage('Notification settings saved successfully.');
    } catch (err) {
      console.error('Error saving notification settings:', err);
      setLocalError('Failed to save notification settings.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTogglePushSubscription = async () => {
    setLocalError(null);
    setIsPushLoading(true);
    try {
      if (isPushSubscribed) {
        await pushNotificationService.unsubscribe();
        setIsPushSubscribed(false);
        setSuccessMessage("Unsubscribed from push notifications on this browser.");
        if (notificationSettingsData) {
          const updatedGlobalSettings = await notificationSettingsService.updateSettings({ push_enabled: false });
          setNotificationSettingsData(updatedGlobalSettings);
        }
      } else {
        await pushNotificationService.subscribe();
        setIsPushSubscribed(true);
        setSuccessMessage("Subscribed to push notifications on this browser.");
        if (notificationSettingsData) {
          const updatedGlobalSettings = await notificationSettingsService.updateSettings({ push_enabled: true });
          setNotificationSettingsData(updatedGlobalSettings);
        }
      }
    } catch (err) {
      console.error("Error toggling push subscription:", err);
      setLocalError("Failed to update push notification subscription. Please ensure notifications are allowed for this site in your browser settings.");
    } finally {
      setIsPushLoading(false);
    }
  };
  
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-navy-blue dark:text-white font-times">User Settings</h1>
        {user && (user.subscription_status === 'pro' || user.subscription_status === 'team_member' || user.user_role === 'TEAM_MEMBER') && (
          <div className="text-right">
            <span className="text-sm text-gray-600 dark:text-gray-400">Role:</span>
            <div className={`inline-block ml-2 px-3 py-1 rounded-full text-xs font-medium ${
              user.subscription_status === 'pro' 
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            }`}>
              {user.subscription_status === 'pro' 
                ? 'Facility Administrator'
                : user.role_description || 'Team Member'}
            </div>
          </div>
        )}
      </div>
      
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
      
      {successMessage && (
        <div className="bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 text-green-700 dark:text-green-200 px-4 py-3 rounded mb-6 flex items-start">
          <div className="flex-shrink-0 mr-2">
            <AlertCircle className="h-5 w-5 text-green-500 dark:text-green-400" />
          </div>
          <div className="flex-grow">
            <p>{successMessage}</p>
          </div>
          <button 
            onClick={() => setSuccessMessage(null)}
            className="flex-shrink-0 ml-2 text-green-500 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300"
          >
            &times;
          </button>
        </div>
      )}
      
      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="-mb-px flex space-x-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab('profile')}
            className={`py-2 px-1 font-medium text-sm inline-flex items-center border-b-2 ${
              activeTab === 'profile'
                ? 'border-navy-blue dark:border-blue-400 text-navy-blue dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-navy-blue dark:hover:text-blue-300 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <User className="h-4 w-4 mr-2" />
            Profile
          </button>
          
          <button
            onClick={() => setActiveTab('security')}
            className={`py-2 px-1 font-medium text-sm inline-flex items-center border-b-2 ${
              activeTab === 'security'
                ? 'border-navy-blue dark:border-blue-400 text-navy-blue dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-navy-blue dark:hover:text-blue-300 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <Shield className="h-4 w-4 mr-2" />
            Security
          </button>
          
          {/* Subscription Tab - Hidden for team members */}
          {user?.user_role !== 'team_member' && (
          <button
            onClick={() => setActiveTab('subscription')}
            className={`py-2 px-1 font-medium text-sm inline-flex items-center border-b-2 ${
              activeTab === 'subscription'
                ? 'border-navy-blue dark:border-blue-400 text-navy-blue dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-navy-blue dark:hover:text-blue-300 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <CreditCard className="h-4 w-4 mr-2" />
            Subscription
          </button>
          )}
          
          <button
            onClick={() => setActiveTab('notifications')}
            className={`py-2 px-1 font-medium text-sm inline-flex items-center border-b-2 ${
              activeTab === 'notifications'
                ? 'border-navy-blue dark:border-blue-400 text-navy-blue dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-navy-blue dark:hover:text-blue-300 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <Bell className="h-4 w-4 mr-2" />
            Notifications
          </button>
          
          {/* Advanced Tab - Hidden for team members */}
          {user?.user_role !== 'team_member' && (
          <button
            onClick={() => setActiveTab('advanced')}
            className={`py-2 px-1 font-medium text-sm inline-flex items-center border-b-2 ${
              activeTab === 'advanced'
                ? 'border-navy-blue dark:border-blue-400 text-navy-blue dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-navy-blue dark:hover:text-blue-300 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Advanced
          </button>
          )}
        </nav>
      </div>
      
      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4">Profile Information</h2>
          <form onSubmit={handleSubmit}>
            <div className="space-y-6">
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
                    className="pl-10 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:ring-navy-blue focus:border-navy-blue dark:focus:ring-blue-500 dark:focus:border-blue-500 border p-2 dark:bg-gray-700 dark:text-white"
                    placeholder="John Doe"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email Address</label>
                <div className="relative flex items-center">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    disabled
                    className="pl-10 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800 shadow-sm border p-2 cursor-not-allowed dark:text-gray-400"
                    placeholder="john@example.com"
                  />
                </div>
              </div>
              
              {/* Operation Name - Hidden for team members */}
              {user?.user_role !== 'team_member' && (
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
                    className="pl-10 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:ring-navy-blue focus:border-navy-blue dark:focus:ring-blue-500 dark:focus:border-blue-500 border p-2 dark:bg-gray-700 dark:text-white"
                    placeholder="Sunshine Daycare"
                  />
                </div>
              </div>
              )}
              
              <div>
                <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone Number (10 digits)</label>
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
                    className={`pl-10 block w-full rounded-md shadow-sm focus:ring-navy-blue focus:border-navy-blue dark:focus:ring-blue-500 dark:focus:border-blue-500 border p-2 dark:bg-gray-700 dark:text-white ${isPhoneValid ? 'border-gray-300 dark:border-gray-600' : 'border-red-500 dark:border-red-600'}`}
                    placeholder="(123) 456-7890"
                    maxLength={14}
                    title="Please enter a 10-digit phone number"
                    required
                  />
                </div>
                {!isPhoneValid && formData.phoneNumber && (
                  <p className="mt-1 text-xs text-red-600 dark:text-red-400">Phone number must be 10 digits.</p>
                )}
              </div>
              
              {/* State Selection - Hidden for team members */}
              {user?.user_role !== 'team_member' && (
              <div>
                <label htmlFor="state" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">State/Territory</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <MapPin className="h-5 w-5 text-gray-400" />
                  </div>
                  <select
                    id="state"
                    name="state"
                    value={formData.state}
                    onChange={handleInputChange}
                    className="pl-10 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:ring-navy-blue focus:border-navy-blue dark:focus:ring-blue-500 dark:focus:border-blue-500 border p-2 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="" disabled>Select your state or territory</option>
                    {states.map(state => (
                      <option 
                        key={state.name} 
                        value={state.name} 
                        disabled={!state.available}
                      >
                        {state.name}{!state.available ? ' (Coming Soon)' : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Select the state/territory where your facility operates.</p>
              </div>
              )}
              
              {/* Facility Type Selection - Hidden for team members */}
              {user?.user_role !== 'team_member' && formData.state && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Facility Type(s)</label>
                  {isLoadingFacilityTypes ? (
                    <div className="flex justify-center items-center h-20">
                      <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-navy-blue dark:border-blue-500"></div>
                    </div>
                  ) : facilityTypes.length > 0 ? (
                    <div className="space-y-2 max-h-60 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-md p-3">
                      {facilityTypes.map((facilityType: string) => (
                        <label 
                          key={facilityType}
                          className={`flex items-center p-2 rounded cursor-pointer transition-colors ${
                            selectedFacilityTypes.includes(facilityType)
                              ? 'bg-blue-50 border border-navy-blue dark:bg-blue-900 dark:border-blue-500'
                              : 'bg-white border border-gray-300 hover:border-navy-blue dark:bg-gray-800 dark:border-gray-700 dark:hover:border-blue-500'
                          }`}
                        >
                          <input
                            type="checkbox"
                            className="h-4 w-4 text-navy-blue focus:ring-navy-blue border-gray-300 rounded"
                            checked={selectedFacilityTypes.includes(facilityType)}
                            onChange={() => handleFacilityTypeToggle(facilityType)}
                          />
                          <span className="ml-2 text-sm text-gray-800 dark:text-white">{facilityType}</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center p-4 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No specific facility types found for {formData.state}. 
                        {/* You can still save your settings. */}
                      </p>
                    </div>
                  )}
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Select all types that apply to your operation. This determines relevant documents.</p>
                </div>
              )}
              
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => navigate('/changePassword')}
                  className="inline-flex items-center text-navy-blue dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                >
                  <Lock className="h-4 w-4 mr-1" />
                  Change Password
                </button>
              </div>
              
              <div className="pt-4">
                <button
                  type="submit"
                  disabled={isLoading || !isPhoneValid}
                  className={`w-full flex justify-center items-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-navy-blue dark:bg-blue-700 hover:bg-blue-800 dark:hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-navy-blue dark:focus:ring-blue-500 ${
                    (isLoading || !isPhoneValid) ? 'opacity-70 cursor-not-allowed' : ''
                  }`}
                >
                  {isLoading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Save Changes
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}
      
      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4">Password</h2>
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Change your password or set up additional security options.
              </p>
              <button
                type="button"
                onClick={() => navigate('/changePassword')}
                className="inline-flex items-center text-navy-blue dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
              >
                <Lock className="h-4 w-4 mr-1" />
                Change Password
              </button>
            </div>
          </div>
          
          {/* OTP Settings Section */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4">One-Time Password Settings</h2>
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Configure one-time password (OTP) verification settings for enhanced security.
              </p>
              
              <div className="flex flex-col space-y-4">
                <div className="flex items-center">
                  <Shield className="h-5 w-5 mr-2 text-navy-blue dark:text-blue-400" />
                  <span className="text-gray-800 dark:text-gray-200">OTP Authentication</span>
                </div>
                
                <div className="ml-7 space-y-4">
                  <div className="flex items-center">
                    <input
                      type="radio"
                      id="otp-optional"
                      name="otpPreference"
                      value="optional"
                      checked={true} // Currently always optional
                      className="h-4 w-4 text-navy-blue focus:ring-navy-blue border-gray-300 rounded"
                    />
                    <label htmlFor="otp-optional" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                      Optional (can use OTP when needed)
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="radio"
                      id="otp-required"
                      name="otpPreference"
                      value="required"
                      checked={false} // Future feature
                      disabled={true}
                      className="h-4 w-4 text-gray-400 focus:ring-navy-blue border-gray-300 rounded cursor-not-allowed"
                    />
                    <label htmlFor="otp-required" className="ml-2 block text-sm text-gray-400 dark:text-gray-500">
                      Required (coming soon) <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded ml-1">Coming Soon</span>
                    </label>
                  </div>
                </div>
                
                <div className="flex items-center mt-4">
                  <Mail className="h-5 w-5 mr-2 text-navy-blue dark:text-blue-400" />
                  <span className="text-gray-800 dark:text-gray-200">
                    Email verification: {user?.email_verified ? (
                      <span className="text-green-600 dark:text-green-400 text-sm">Verified</span>
                    ) : (
                      <span className="text-yellow-600 dark:text-yellow-400 text-sm">Not verified</span>
                    )}
                  </span>
                </div>
                
                {!user?.email_verified && (
                  <button
                    type="button"
                    onClick={() => navigate(`/login/otp?recipient=${encodeURIComponent(user?.email || '')}&method=email`)}
                    className="ml-7 inline-flex items-center text-sm px-3 py-1 bg-navy-blue text-white rounded hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
                  >
                    Verify Email
                  </button>
                )}
                
                <div className="flex items-center mt-2">
                  <Phone className="h-5 w-5 mr-2 text-navy-blue dark:text-blue-400" />
                  <span className="text-gray-800 dark:text-gray-200">
                    Phone verification: {user?.phone_verified ? (
                      <span className="text-green-600 dark:text-green-400 text-sm">Verified</span>
                    ) : (
                      <span className="text-yellow-600 dark:text-yellow-400 text-sm">Not verified</span>
                    )}
                  </span>
                </div>
                
                {!user?.phone_verified && user?.phone_number && (
                  <button
                    type="button"
                    onClick={() => navigate(`/login/otp?recipient=${encodeURIComponent(user?.phone_number || '')}&method=sms`)}
                    className="ml-7 inline-flex items-center text-sm px-3 py-1 bg-navy-blue text-white rounded hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
                  >
                    Verify Phone
                  </button>
                )}
              </div>
            </div>
          </div>
          
          {/* Passkey Registration Section */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4">Passkeys (Passwordless Login)</h2>
            <PasskeyRegistration 
              onSuccess={() => setSuccessMessage("Passkey operation completed successfully.")}
              onError={(error) => setLocalError(error)}
            />
          </div>
        </div>
      )}
      
      {/* Subscription Tab - Hidden for team members */}
      {activeTab === 'subscription' && user?.user_role !== 'team_member' && (
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4">Subscription Management</h2>
          <div className="space-y-6">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Manage your subscription plan.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Free Plan */}
                <div className={`border rounded-lg p-4 ${formData.subscription === 'free' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400' : 'border-gray-200 dark:border-gray-700'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-bold">Free</h3>
                    {formData.subscription === 'free' && (
                      <span className="bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100 text-xs px-2 py-1 rounded">Current</span>
                    )}
                  </div>
                  <div className="text-gray-700 dark:text-gray-300 text-sm mb-3">
                    <ul className="space-y-1">
                      <li>✓ Basic compliance tools</li>
                      <li>✓ Standard document uploads</li>
                      <li>✓ Basic AI assistance</li>
                    </ul>
                  </div>
                  {formData.subscription === 'free' ? (
                    <button
                      disabled={true}
                      className="w-full bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400 cursor-not-allowed py-2 px-4 rounded text-sm"
                    >
                      Current Plan
                    </button>
                  ) : (
                    <button
                      onClick={() => handleSubscriptionChange('free')}
                      disabled={isLoading}
                      className="w-full bg-orange-600 text-white py-2 px-4 rounded text-sm hover:bg-orange-700 transition-colors"
                    >
                      Manage Subscription
                    </button>
                  )}
                </div>
                
                {/* Pro Plan */}
                <div className={`border rounded-lg p-4 ${formData.subscription === 'pro' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400' : 'border-gray-200 dark:border-gray-700'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-bold">Pro</h3>
                    {formData.subscription === 'pro' && (
                      <span className="bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100 text-xs px-2 py-1 rounded">Current</span>
                    )}
                  </div>
                  <div className="text-gray-700 dark:text-gray-300 text-sm mb-3">
                    <ul className="space-y-1">
                      <li>✓ All Free features</li>
                      <li>✓ Advanced compliance tools</li>
                      <li>✓ Priority AI assistance</li>
                      <li>✓ Enhanced document analysis</li>
                    </ul>
                  </div>
                  {formData.subscription === 'pro' ? (
                    <div className="space-y-2">
                      <button
                        disabled={true}
                        className="w-full bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400 cursor-not-allowed py-2 px-4 rounded text-sm"
                      >
                        Current Plan
                      </button>
                      <button
                        onClick={handleManageSubscription}
                        disabled={isLoading}
                        className="w-full bg-blue-600 text-white py-2 px-4 rounded text-sm hover:bg-blue-700 transition-colors"
                      >
                        Manage Subscription
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleSubscriptionChange('pro')}
                      disabled={isLoading}
                      className="w-full bg-navy-blue text-white dark:bg-blue-700 hover:bg-blue-700 dark:hover:bg-blue-600 py-2 px-4 rounded text-sm"
                    >
                      Upgrade to Pro
                    </button>
                  )}
                </div>

                {/* Enterprise Plan */}
                <div className={`border rounded-lg p-4 ${formData.subscription === 'enterprise' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400' : 'border-gray-200 dark:border-gray-700'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-bold">Enterprise</h3>
                    {formData.subscription === 'enterprise' && (
                      <span className="bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100 text-xs px-2 py-1 rounded">Current</span>
                    )}
                  </div>
                  <div className="text-gray-700 dark:text-gray-300 text-sm mb-3">
                    <ul className="space-y-1">
                      <li>✓ All Pro features</li>
                      <li>✓ Dedicated account manager</li>
                      <li>✓ Custom integrations</li>
                      <li>✓ Priority support SLAs</li>
                      <li>✓ Volume discounts</li>
                    </ul>
                  </div>
                  <button
                    // onClick={() => handleSubscriptionChange('enterprise')} // Or link to contact page/modal
                    disabled={true} // Enterprise plans typically require sales contact
                    className={`w-full py-2 px-4 rounded text-sm ${
                      formData.subscription === 'enterprise'
                        ? 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400 cursor-not-allowed'
                        : 'bg-gray-400 text-white dark:bg-gray-600 cursor-not-allowed' // Style as disabled/informational
                    }`}
                  >
                    Contact Sales
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Notification Settings Tab */}
      {activeTab === 'notifications' && notificationSettingsData && (
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-6">Notification Preferences</h2>
          
          {/* Push Notification Master Control */}
          {pushNotificationService.isSupported() && (
            <div className="mb-6 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
              <h3 className="text-lg font-semibold text-navy-blue dark:text-white mb-2">Browser Push Notifications</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                Receive instant alerts directly in your browser.
              </p>
              <button
                onClick={handleTogglePushSubscription}
                disabled={isPushLoading}
                className={`w-full sm:w-auto flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                  isPushSubscribed 
                    ? 'bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-600' 
                    : 'bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-600'
                } ${isPushLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
              >
                {isPushLoading ? (
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : null}
                {isPushSubscribed ? 'Disable Push Notifications on this Browser' : 'Enable Push Notifications on this Browser'}
              </button>
              {!pushNotificationService.isSupported() && <p className="text-xs text-red-500 mt-1">Push notifications are not supported by your browser.</p>}
               <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Note: This enables/disables push notifications for this browser only.
                Use the settings below to control which types of push notifications you receive if enabled.
              </p>
            </div>
          )}

          <form onSubmit={(e) => { e.preventDefault(); handleSaveNotificationSettings(); }}>
            <div className="space-y-8">

              {/* In-App Notification Settings */}
              <fieldset>
                <legend className="text-lg font-semibold text-navy-blue dark:text-white mb-3">In-App Notifications</legend>
                <div className="space-y-3">
                  {(Object.keys(notificationSettingsData) as Array<keyof NotificationSettings>)
                    .filter(key => key.startsWith('in_app_'))
                    .map(key => (
                      <div key={key} className="flex items-center">
                        <input
                          id={key.toString()}
                          name={key.toString()}
                          type="checkbox"
                          checked={notificationSettingsData[key] as boolean}
                          onChange={handleNotificationSettingsChange}
                          className="h-4 w-4 text-navy-blue focus:ring-navy-blue border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:checked:bg-blue-500"
                        />
                        <label htmlFor={key.toString()} className="ml-3 block text-sm font-medium text-gray-700 dark:text-gray-300">
                          {key.replace('in_app_', '').replace(/_/g, ' ').replace(' enabled', '').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                        </label>
                      </div>
                  ))}
                </div>
              </fieldset>

              {/* Email Notification Settings */}
              <fieldset>
                <legend className="text-lg font-semibold text-navy-blue dark:text-white mb-3">Email Notifications</legend>
                <div className="space-y-3">
                  {(Object.keys(notificationSettingsData) as Array<keyof NotificationSettings>)
                    .filter(key => key.startsWith('email_') && !key.endsWith('_frequency'))
                    .map(key => (
                      <div key={key} className="flex items-center">
                        <input
                          id={key.toString()}
                          name={key.toString()}
                          type="checkbox"
                          checked={notificationSettingsData[key] as boolean}
                          onChange={handleNotificationSettingsChange}
                          className="h-4 w-4 text-navy-blue focus:ring-navy-blue border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:checked:bg-blue-500"
                        />
                        <label htmlFor={key.toString()} className="ml-3 block text-sm font-medium text-gray-700 dark:text-gray-300">
                           {key.replace('email_', '').replace(/_/g, ' ').replace(' enabled', '').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                        </label>
                      </div>
                  ))}
                   <div className="pt-2">
                      <label htmlFor="email_digest_frequency" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Email Digest Frequency</label>
                      <select
                        id="email_digest_frequency"
                        name="email_digest_frequency"
                        value={notificationSettingsData.email_digest_frequency}
                        onChange={handleNotificationSettingsChange}
                        className="mt-1 block w-full sm:w-1/2 rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:ring-navy-blue focus:border-navy-blue dark:focus:ring-blue-500 dark:focus:border-blue-500 border p-2 dark:bg-gray-700 dark:text-white"
                      >
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="never">Never</option>
                      </select>
                    </div>
                </div>
              </fieldset>
              
              {/* Push Notification Settings (Conditional on browser support and subscription) */}
               <fieldset>
                <legend className="text-lg font-semibold text-navy-blue dark:text-white mb-3">Push Notification Types</legend>
                <div className="space-y-3">
                   <div className="flex items-center">
                        <input
                          id="push_enabled"
                          name="push_enabled"
                          type="checkbox"
                          checked={notificationSettingsData.push_enabled as boolean}
                          onChange={handleNotificationSettingsChange}
                          className="h-4 w-4 text-navy-blue focus:ring-navy-blue border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:checked:bg-blue-500"
                        />
                        <label htmlFor="push_enabled" className="ml-3 block text-sm font-medium text-gray-700 dark:text-gray-300">
                          Enable All Push Notifications (Global Preference)
                        </label>
                      </div>
                  {(Object.keys(notificationSettingsData) as Array<keyof NotificationSettings>)
                    .filter(key => key.startsWith('push_') && key !== 'push_enabled')
                    .map(key => (
                      <div key={key} className="flex items-center pl-6">
                        <input
                          id={key.toString()}
                          name={key.toString()}
                          type="checkbox"
                          checked={notificationSettingsData[key] as boolean}
                          disabled={!notificationSettingsData.push_enabled} // Disable if global push is off
                          onChange={handleNotificationSettingsChange}
                          className={`h-4 w-4 text-navy-blue focus:ring-navy-blue border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:checked:bg-blue-500 ${!notificationSettingsData.push_enabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                        />
                        <label htmlFor={key.toString()} className={`ml-3 block text-sm font-medium text-gray-700 dark:text-gray-300 ${!notificationSettingsData.push_enabled ? 'opacity-50' : ''}`}>
                           {key.replace('push_', '').replace(/_/g, ' ').replace(' enabled', '').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                        </label>
                      </div>
                  ))}
                </div>
              </fieldset>

              {/* Calendar Specific Settings */}
              <fieldset>
                <legend className="text-lg font-semibold text-navy-blue dark:text-white mb-3">Calendar Settings</legend>
                <div>
                  <label htmlFor="calendar_reminder_offset_minutes" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Reminder Before Event (minutes)</label>
                  <input
                    type="number"
                    id="calendar_reminder_offset_minutes"
                    name="calendar_reminder_offset_minutes"
                    value={notificationSettingsData.calendar_reminder_offset_minutes}
                    onChange={handleNotificationSettingsChange}
                    min="0"
                    max="1440" // 24 hours
                    className="mt-1 block w-full sm:w-1/4 rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:ring-navy-blue focus:border-navy-blue dark:focus:ring-blue-500 dark:focus:border-blue-500 border p-2 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </fieldset>
              
              <div className="pt-4">
                <button
                  type="submit"
                  disabled={isLoading}
                  className={`w-full sm:w-auto flex justify-center items-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-navy-blue dark:bg-blue-700 hover:bg-blue-800 dark:hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-navy-blue dark:focus:ring-blue-500 ${
                    isLoading ? 'opacity-70 cursor-not-allowed' : ''
                  }`}
                >
                  {isLoading && !isPushLoading ? ( // Ensure only one loader shows if both happen
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Saving Settings...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Save Notification Settings
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}
      
      {/* Advanced Tab - Hidden for team members */}
      {activeTab === 'advanced' && user?.user_role !== 'team_member' && (
        <div className="space-y-6">
          {/* Resource Synchronization */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4">Resource Synchronization</h2>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Manually synchronize your resources with the latest updates.
            </p>
            
            <button
              type="button"
              onClick={handleSyncResources}
              disabled={isSyncing}
              className={`mt-4 flex items-center justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-navy-blue dark:bg-blue-700 hover:bg-blue-800 dark:hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-navy-blue dark:focus:ring-blue-500 ${
                isSyncing ? 'opacity-70 cursor-not-allowed' : ''
              }`}
            >
              {isSyncing ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Synchronizing...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Synchronize Resources
                </>
              )}
            </button>
          </div>
          
          {/* Danger Zone Section */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-red-600 dark:text-red-400 mb-4">Danger Zone</h2>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Once you delete your account, all of your data will be permanently removed.
              This action cannot be undone.
            </p>
            
            {!showDeleteConfirm ? (
              <button
                type="button"
                onClick={handleDeleteAccount}
                className="mt-4 flex items-center justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Account
              </button>
            ) : (
              <div className="mt-4 p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md">
                <p className="text-sm text-red-700 dark:text-red-300 font-medium">
                  Are you sure you want to delete your account? This will remove all your data and cannot be undone.
                </p>
                <div className="mt-3 flex space-x-3">
                  <button
                    type="button"
                    onClick={handleDeleteAccount}
                    disabled={isDeleting}
                    className={`flex items-center justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 ${
                      isDeleting ? 'opacity-70 cursor-not-allowed' : ''
                    }`}
                  >
                    {isDeleting ? 'Deleting...' : 'Yes, Delete My Account'}
                  </button>
                  <button
                    type="button"
                    onClick={cancelDelete}
                    disabled={isDeleting}
                    className="flex items-center justify-center py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-navy-blue dark:focus:ring-blue-500"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {syncStatus === 'success' && syncMessage && (
        <div className="bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 text-green-700 dark:text-green-200 px-4 py-3 rounded mb-6 flex items-start">
          <div className="flex-shrink-0 mr-2">
            <AlertCircle className="h-5 w-5 text-green-500 dark:text-green-400" />
          </div>
          <div className="flex-grow">
            <p>{syncMessage}</p>
          </div>
          <button 
            onClick={() => setSyncStatus('idle')}
            className="flex-shrink-0 ml-2 text-green-500 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300"
          >
            &times;
          </button>
        </div>
      )}
      
      {syncStatus === 'error' && syncMessage && (
        <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded mb-6 flex items-start">
          <div className="flex-shrink-0 mr-2">
            <AlertCircle className="h-5 w-5 text-red-500 dark:text-red-400" />
          </div>
          <div className="flex-grow">
            <p>{syncMessage}</p>
          </div>
          <button 
            onClick={() => setSyncStatus('idle')}
            className="flex-shrink-0 ml-2 text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
          >
            &times;
          </button>
        </div>
      )}
    </div>
  );
};

export default UserSettingsPage; 