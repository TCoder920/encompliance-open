/*
  Description: Facility administrator overview component
  Purpose: Provides comprehensive facility management interface for Pro users
  
  Educational Note: Pro users manage exactly ONE facility. Enterprise users 
  (future feature) will manage multiple facilities. This component provides
  real-time analytics, user management, and operations oversight for a single facility.
*/

import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserPlus, 
  Calendar, 
  TrendingUp, 
  CreditCard, 
  Settings,
  Mail,
  Clock,
  CheckCircle,
  AlertTriangle,
  Building,
  BarChart3
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import ErrorMessage from '../components/ErrorMessage';
// import LoadingSpinner from '../components/LoadingSpinner';

interface FacilityInfo {
  id: number;
  facility_name: string;
  facility_address?: string;
  facility_city?: string;
  facility_state?: string;
  facility_zip?: string;
  facility_phone?: string;
  facility_email?: string;
  current_user_count: number;
  max_users: number;
  is_active: boolean;
}

interface SubscriptionInfo {
  id: number;
  status: string;
  seat_count: number;
  total_amount: number;
  current_period_end: string;
  trial_end?: string;
  cancel_at_period_end: boolean;
}

interface FacilityUser {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
  role_description?: string;
}

interface Invitation {
  id: number;
  invitation_code: string;
  email?: string;
  status: string;
  expires_at: string;
  personal_message?: string;
  days_until_expiry: number;
}

interface TrainingStats {
  total_assignments: number;
  completed_assignments: number;
  completion_rate: number;
  overdue_assignments: number;
}

interface UpcomingEvent {
  id: number;
  title: string;
  start_date: string;
  end_date?: string;
  description?: string;
}

interface DashboardData {
  facility: FacilityInfo;
  subscription?: SubscriptionInfo;
  users: FacilityUser[];
  active_invitations: Invitation[];
  training_completion_stats: TrainingStats;
  upcoming_events: UpcomingEvent[];
}

const FacilityDashboard: React.FC = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteMessage, setInviteMessage] = useState('');
  const [inviteLoading, setInviteLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [editingRoleId, setEditingRoleId] = useState<number | null>(null);
  const [editingRoleDescription, setEditingRoleDescription] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const [showSeatReductionModal, setShowSeatReductionModal] = useState(false);
  const [seatsToRemove, setSeatsToRemove] = useState(1);
  const [showAddSeatsModal, setShowAddSeatsModal] = useState(false);
  const [seatsToAdd, setSeatsToAdd] = useState(1);

  useEffect(() => {
    fetchDashboardData();
  }, [refreshKey]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // Add cache-busting parameter to ensure fresh data
      const response = await api.get(`/facilities/overview?t=${Date.now()}`);
      setDashboardData(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch overview data:', err);
      setError(err.response?.data?.detail || 'Failed to load overview data');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteUser = async () => {
    if (!inviteEmail.trim()) return;
    
    setInviteLoading(true);
    setError(null);
    
    try {
      // Check if we have available seats for invitation
      const currentUsers = dashboardData?.facility.current_user_count || 0;
      const currentSeats = dashboardData?.subscription?.seat_count || 1;
      
      if (currentUsers >= currentSeats) {
        // No available seats - show clear error message
        setError(`Cannot send invitation. You have ${currentUsers} users but only ${currentSeats} seats. Please add additional seats first using the "Add Additional Seats" button in the subscription section, then try inviting again.`);
        setInviteLoading(false);
        return;
      }

      // Seats are available - send invitation directly
      await sendInvitation();
    } catch (error) {
      console.error('Error in handleInviteUser:', error);
      setError('Failed to send invitation. Please try again.');
      setInviteLoading(false);
    }
  };

  const sendInvitation = async () => {
    try {
      const response = await api.post('/facilities/invitations', {
        email: inviteEmail,
        personal_message: inviteMessage || undefined,
        expires_in_days: 7
      });
      
      setSuccessMessage('Invitation sent successfully! The team member will be added to your facility when they accept the invitation.');
      setShowInviteModal(false);
      setInviteEmail('');
      setInviteMessage('');
      
      // Refresh dashboard data
      setRefreshKey(prev => prev + 1);
    } catch (error: any) {
      console.error('Error sending invitation:', error);
      setError(error.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setInviteLoading(false);
    }
  };

  const handleResendInvitation = async (invitationId: number) => {
    try {
      await api.post(`/facilities/invitations/${invitationId}/resend`);
      setError(null);
      setSuccessMessage('Invitation email resent successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
      
      // Refresh data
      setRefreshKey(prev => prev + 1);
    } catch (err: any) {
      console.error('Failed to resend invitation:', err);
      setError(err.response?.data?.detail || 'Failed to resend invitation');
    }
  };

  const handleCancelInvitation = async (invitationId: number) => {
    if (!confirm('Are you sure you want to cancel this invitation? The invitation link will be immediately voided and cannot be used.')) {
      return;
    }

    try {
      await api.delete(`/facilities/invitations/${invitationId}`);
      setError(null);
      setSuccessMessage('Invitation cancelled successfully. The invitation link has been voided and can no longer be used.');
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
      
      // Refresh dashboard to remove cancelled invitation
      setRefreshKey(prev => prev + 1);
    } catch (err: any) {
      console.error('Failed to cancel invitation:', err);
      setError(err.response?.data?.detail || 'Failed to cancel invitation');
    }
  };

  const handleRemoveUser = async (userId: number) => {
    if (!confirm('Are you sure you want to remove this user from your facility? This will reduce your monthly cost by $20.')) {
      return;
    }

    try {
      await api.delete(`/facilities/users/${userId}`);
      setError(null);
      setSuccessMessage('User removed successfully. Your subscription will be updated to reflect the $20 monthly savings.');
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
      
      // Refresh dashboard to show updated user list and billing
      setRefreshKey(prev => prev + 1);
    } catch (err: any) {
      console.error('Failed to remove user:', err);
      setError(err.response?.data?.detail || 'Failed to remove user');
    }
  };

  const handleEditRole = (userId: number, currentRole: string) => {
    setEditingRoleId(userId);
    setEditingRoleDescription(currentRole || 'Team Member');
  };

  const handleSaveRole = async (userId: number) => {
    if (!editingRoleDescription.trim()) {
      setError('Role description cannot be empty');
      return;
    }

    try {
      await api.put(`/facilities/users/${userId}/role`, {
        role_description: editingRoleDescription.trim()
      });
      
      setEditingRoleId(null);
      setEditingRoleDescription('');
      setSuccessMessage('Role updated successfully');
      
      // Add a small delay to ensure backend processing is complete
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Refresh dashboard data
      setRefreshKey(prev => prev + 1);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      console.error('Failed to update role:', err);
      setError(err.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleCancelEdit = () => {
    setEditingRoleId(null);
    setEditingRoleDescription('');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const handleManageSubscription = async () => {
    try {
      const response = await api.post('/payments/create-customer-portal', {}, {
        params: {
          return_url: window.location.href // Return to current page
        }
      });
      
      // Redirect to Stripe Customer Portal
      window.location.href = response.data.portal_url;
    } catch (error: any) {
      console.error('Error creating customer portal session:', error);
      setError(error.response?.data?.detail || 'Failed to open billing portal');
    }
  };

  const handleAddAdditionalSeats = () => {
    // Check subscription status before allowing seat additions
    const subscriptionStatus = dashboardData?.subscription?.status;
    
    if (subscriptionStatus === 'canceled' || subscriptionStatus === 'cancelled') {
      setError('⚠️ Your subscription has been canceled. Please resubscribe to your Pro plan before adding additional seats. You can resubscribe by upgrading your account in the settings.');
      return;
    }
    
    if (!subscriptionStatus || subscriptionStatus === 'inactive') {
      setError('⚠️ No active subscription found. Please subscribe to a Pro plan to add additional seats.');
      return;
    }
    
    // Open modal to add additional seats
    setShowAddSeatsModal(true);
    setError(null);
    setSuccessMessage(null);
  };

  const handleReduceSeats = () => {
    setShowSeatReductionModal(true);
  };

  const handleConfirmAddSeats = async () => {
    try {
      setInviteLoading(true);
      
      // Create checkout session for adding seats
      const baseUrl = window.location.origin + window.location.pathname;
      const response = await api.post('/payments/create-checkout-session', {
        type: 'seat_upgrade',
        additional_seats: seatsToAdd,
        success_url: `${baseUrl}?seat_upgrade_success=true&session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${baseUrl}?seat_upgrade_cancelled=true`
      });
      
      // Redirect to Stripe checkout
      window.location.href = response.data.checkout_url;
    } catch (error: any) {
      console.error('Error creating checkout session for adding seats:', error);
      setError(error.response?.data?.detail || 'Failed to create payment session');
      setInviteLoading(false);
    }
  };

  // Handle seat upgrade success/cancellation
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const seatUpgradeSuccess = urlParams.get('seat_upgrade_success');
    const seatUpgradeCancelled = urlParams.get('seat_upgrade_cancelled');
    const sessionId = urlParams.get('session_id');
    
    console.log('Checking URL parameters:', {
      seatUpgradeSuccess,
      seatUpgradeCancelled,
      sessionId,
      fullURL: window.location.href
    });
    
    if (seatUpgradeSuccess === 'true' && sessionId) {
      console.log('Starting payment verification process...');
      
      const verifyPayment = async () => {
        try {
          console.log('Verifying seat upgrade payment:', sessionId);
          const verifyResponse = await api.post(`/payments/verify-payment?session_id=${sessionId}`);
          
          if (verifyResponse.data.success) {
            setSuccessMessage('🎉 Additional seats added successfully! Your subscription has been updated.');
            setShowAddSeatsModal(false);
            setSeatsToAdd(1);
            
            // Refresh dashboard data
            setRefreshKey(prev => prev + 1);
            
            // Clean up URL
            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
          } else {
            console.error('Payment verification failed:', verifyResponse.data);
            setError(verifyResponse.data.message || 'Payment verification failed');
          }
        } catch (error: any) {
          console.error('Error verifying seat upgrade payment:', error);
          
          // Check for specific subscription canceled error
          if (error.response?.data?.error_code === 'subscription_canceled') {
            setError('⚠️ Your subscription has been canceled. Please resubscribe to your Pro plan before adding additional seats. You can resubscribe by upgrading your account in the settings.');
          } else if (error.response?.data?.error_code === 'session_for_canceled_subscription') {
            setError('⚠️ This payment session is for a canceled subscription. You have since resubscribed with a new subscription. Please try adding seats again from your current dashboard.');
            
            // Clear the URL parameters since this session is no longer valid
            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
            
            // Refresh dashboard to show current subscription
            setRefreshKey(prev => prev + 1);
          } else {
            setError(error.response?.data?.message || 'Failed to verify payment. Please contact support.');
          }
        }
      };
      
      verifyPayment();
      
      // Clean up URL parameters after a short delay to ensure processing completes
      setTimeout(() => {
        window.history.replaceState({}, '', window.location.pathname);
      }, 1000);
    } else if (seatUpgradeCancelled === 'true') {
      setError('Seat upgrade was cancelled. No changes were made to your subscription.');
      
      // Clean up URL parameters
      setTimeout(() => {
        window.history.replaceState({}, '', window.location.pathname);
      }, 1000);
    }
  }, []);

  const handleConfirmSeatReduction = async () => {
    try {
      setInviteLoading(true);
      const response = await api.post('/payments/reduce-seats-direct', {}, {
        params: {
          seats_to_remove: seatsToRemove
        }
      });
      
      if (response.data.success) {
        setSuccessMessage(
          `Successfully removed ${seatsToRemove} seat${seatsToRemove > 1 ? 's' : ''}! ` +
          `You'll save $${response.data.monthly_savings.toFixed(2)} per month. ` +
          `Your new monthly cost is $${response.data.new_monthly_cost.toFixed(2)}.`
        );
        setShowSeatReductionModal(false);
        setSeatsToRemove(1);
        
        // Refresh dashboard data to show updated subscription
        setRefreshKey(prev => prev + 1);
      }
    } catch (error: any) {
      console.error('Error reducing seats:', error);
      setError(error.response?.data?.detail || 'Failed to reduce seats');
    } finally {
      setInviteLoading(false);
    }
  };



  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        {/* <LoadingSpinner size="large" /> */}
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage message={error || 'Failed to load facility overview'} type="error" />
      </div>
    );
  }

  const { facility, subscription, users, active_invitations, training_completion_stats, upcoming_events } = dashboardData;

  // Determine if user has access to Pro features
  const hasProAccess = (user?.subscription_status === 'pro' || user?.subscription_status === 'team_member' || user?.user_role === 'TEAM_MEMBER') && facility?.is_active;
  const isDowngraded = user?.subscription_status === 'free' && user?.user_role !== 'TEAM_MEMBER' && facility && !facility.is_active;

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-navy-blue dark:text-white mb-2">
              Facility Overview
            </h1>
            {isDowngraded && (
              <div className="bg-orange-50 border border-orange-200 text-orange-800 px-3 py-2 rounded-lg text-sm mt-2">
                <strong>Free Tier:</strong> Some features are limited. <button className="underline text-orange-900 hover:text-orange-700" onClick={() => window.location.href = '/userSettings?tab=subscription'}>Upgrade to Pro</button> to restore full functionality.
              </div>
            )}
          </div>
          <div className="flex space-x-3">
            {hasProAccess && (
              <button
                onClick={() => setShowInviteModal(true)}
                className="flex items-center space-x-2 bg-navy-blue text-white px-4 py-2 rounded-lg hover:bg-blue-800 transition-colors"
              >
                <UserPlus className="h-4 w-4" />
                <span>Invite User</span>
              </button>
            )}
            {!hasProAccess && (
              <button
                onClick={() => window.location.href = '/userSettings?tab=subscription'}
                className="flex items-center space-x-2 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors"
              >
                <UserPlus className="h-4 w-4" />
                <span>Upgrade to Invite Users</span>
            </button>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6">
          <ErrorMessage message={error} type="error" onClose={() => setError(null)} />
        </div>
      )}

      {successMessage && (
        <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded flex justify-between items-center">
          <span>{successMessage}</span>
          <button 
            onClick={() => setSuccessMessage(null)}
            className="text-green-500 hover:text-green-700"
          >
            ×
          </button>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Training Completion</p>
              <p className="text-2xl font-bold text-navy-blue dark:text-white">
                {training_completion_stats.completion_rate}%
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-dark-surface rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Invitations</p>
              <p className="text-2xl font-bold text-navy-blue dark:text-white">
                {active_invitations.length}
              </p>
            </div>
            <Mail className="h-8 w-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-dark-surface rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Overdue Training</p>
              <p className="text-2xl font-bold text-red-600">
                {training_completion_stats.overdue_assignments}
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Users List */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-navy-blue dark:text-white">Team Members</h2>
                {!hasProAccess && (
                  <span className="text-sm text-orange-600 bg-orange-50 px-2 py-1 rounded">Pro Feature</span>
                )}
              </div>
            </div>
            <div className="p-6">
              {!hasProAccess ? (
                <div className="text-center py-8">
                  <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-400 mb-4">Team management is available with Pro subscription</p>
                  <button
                    onClick={() => window.location.href = '/userSettings?tab=subscription'}
                    className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors"
                  >
                    Upgrade to Pro
                  </button>
                </div>
              ) : users.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-400">No team members yet. Invite users to get started!</p>
                </div>
              ) : (
                <div className="space-y-4" key={refreshKey}>
                  {users.map((user) => (
                    <div key={user.id} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="w-10 h-10 bg-navy-blue text-white rounded-full flex items-center justify-center">
                          {user.full_name?.charAt(0) || user.email.charAt(0)}
                        </div>
                        <div>
                          <p className="font-medium text-navy-blue dark:text-white">{user.full_name}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{user.email}</p>
                          <div className="flex items-center gap-2">
                            {editingRoleId === user.id ? (
                              <div className="flex items-center space-x-2">
                                <input
                                  type="text"
                                  value={editingRoleDescription}
                                  onChange={(e) => setEditingRoleDescription(e.target.value)}
                                  className="text-xs px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-navy-blue"
                                  placeholder="Role description"
                                  maxLength={100}
                                />
                                <button
                                  onClick={() => handleSaveRole(user.id)}
                                  className="text-green-600 hover:text-green-800 text-xs"
                                >
                                  Save
                                </button>
                                <button
                                  onClick={handleCancelEdit}
                                  className="text-gray-600 hover:text-gray-800 text-xs"
                                >
                                  Cancel
                                </button>
                              </div>
                            ) : (
                              <div className="flex items-center space-x-2">
                                <span className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2 py-1 rounded-full">
                                  {user.role_description || 'Team Member'}
                                </span>
                                <button
                                  onClick={() => handleEditRole(user.id, user.role_description || '')}
                                  className="text-blue-600 hover:text-blue-800 text-xs"
                                >
                                  Edit Role
                                </button>
                              </div>
                            )}
                          </div>
                          <p className="text-xs text-gray-500">
                            {user.last_login ? `Last login: ${formatDate(user.last_login)}` : 'Never logged in'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          user.is_active 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                        }`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <button
                          onClick={() => handleRemoveUser(user.id)}
                          className="text-red-600 hover:text-red-800 text-sm px-3 py-1 rounded hover:bg-red-50 dark:hover:bg-red-900"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-8">
          {/* Subscription Info */}
          {subscription && hasProAccess && (
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-navy-blue dark:text-white flex items-center">
                  <CreditCard className="h-5 w-5 mr-2" />
                  Subscription
                </h3>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
                  <p className={`font-medium ${subscription.status === 'trialing' ? 'text-blue-600' : 'text-green-600'}`}>
                    {subscription.status === 'trialing' ? 'Trial Period' : 'Active'}
                  </p>
                  {subscription.status === 'past_due' && (
                    <p className="text-xs text-orange-600 mt-1">
                      Payment failed - please update your payment method
                    </p>
                  )}
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Monthly Cost</p>
                  <p className="font-medium text-navy-blue dark:text-white">
                    {formatCurrency(subscription.total_amount)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    $50 base + $20 per additional member
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Seats</p>
                  <p className="font-medium text-navy-blue dark:text-white">
                    {subscription.seat_count} users
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {subscription.trial_end ? 'Trial Ends' : 'Next Billing'}
                  </p>
                  <p className="font-medium text-navy-blue dark:text-white">
                    {formatDate(subscription.trial_end || subscription.current_period_end)}
                  </p>
                </div>
                {subscription.cancel_at_period_end && (
                  <div className="bg-yellow-50 border border-yellow-200 p-3 rounded">
                    <p className="text-sm text-yellow-800">
                      Subscription will be cancelled at the end of the current period.
                    </p>
                  </div>
                )}
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                  <button
                    onClick={() => window.location.href = '/subscription'}
                    className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors text-sm font-medium"
                  >
                    View Details
                  </button>
                  <button
                    onClick={handleManageSubscription}
                    className="w-full bg-navy-blue text-white px-4 py-2 rounded-lg hover:bg-blue-800 transition-colors text-sm font-medium"
                  >
                    Manage Subscription
                  </button>
                  <button
                    onClick={handleAddAdditionalSeats}
                    className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                    title="Add additional seats to your subscription - then invite users to fill them"
                  >
                    Add Additional Seats
                  </button>
                  <button
                    onClick={handleReduceSeats}
                    className="w-full bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
                  >
                    Reduce Seats
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Free Tier Info */}
          {!hasProAccess && (
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-navy-blue dark:text-white flex items-center">
                  <CreditCard className="h-5 w-5 mr-2" />
                  Subscription
                </h3>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Current Plan</p>
                  <p className="font-medium text-orange-600">Free</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Monthly Cost</p>
                  <p className="font-medium text-navy-blue dark:text-white">$0.00</p>
                </div>
                <div className="bg-blue-50 border border-blue-200 p-3 rounded">
                  <h4 className="font-medium text-blue-900 mb-2">Upgrade to Pro</h4>
                  <ul className="text-sm text-blue-800 space-y-1 mb-3">
                    <li>• Team member management</li>
                    <li>• Advanced compliance tools</li>
                    <li>• Priority support</li>
                    <li>• 7-day free trial</li>
                  </ul>
                  <button
                    onClick={() => window.location.href = '/userSettings?tab=subscription'}
                    className="w-full bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700 transition-colors"
                  >
                    Start Free Trial
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Active Invitations */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-navy-blue dark:text-white flex items-center">
                <Mail className="h-5 w-5 mr-2" />
                Pending Invitations
              </h3>
            </div>
            <div className="p-6">
              {active_invitations.length === 0 ? (
                <p className="text-gray-600 dark:text-gray-400 text-sm">No pending invitations</p>
              ) : (
                <div className="space-y-3">
                  {active_invitations.map((invitation) => (
                    <div key={invitation.id} className="p-3 border border-gray-200 dark:border-gray-700 rounded">
                      <div className="flex justify-between items-start gap-3">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm text-navy-blue dark:text-white break-words">
                            {invitation.email || 'General invitation'}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            Expires in {invitation.days_until_expiry} days
                          </p>
                          {invitation.personal_message && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 italic break-words">
                              "{invitation.personal_message}"
                            </p>
                          )}
                        </div>
                        <div className="flex space-x-2 flex-shrink-0">
                          {invitation.email && (
                            <button
                              onClick={() => handleResendInvitation(invitation.id)}
                              className="px-2 py-1 text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 rounded transition-colors"
                              title="Resend invitation email"
                            >
                              Resend
                            </button>
                          )}
                          <button
                            onClick={() => handleCancelInvitation(invitation.id)}
                            className="px-2 py-1 text-xs bg-red-100 text-red-700 hover:bg-red-200 rounded transition-colors"
                            title="Cancel invitation"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Upcoming Events */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-navy-blue dark:text-white flex items-center">
                <Calendar className="h-5 w-5 mr-2" />
                Upcoming Events
              </h3>
            </div>
            <div className="p-6">
              {upcoming_events.length === 0 ? (
                <p className="text-gray-600 dark:text-gray-400 text-sm">No upcoming events</p>
              ) : (
                <div className="space-y-3">
                  {upcoming_events.map((event) => (
                    <div key={event.id} className="p-3 border border-gray-200 dark:border-gray-700 rounded">
                      <p className="font-medium text-sm text-navy-blue dark:text-white">{event.title}</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {formatDate(event.start_date)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Invite User Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-dark-surface rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-semibold text-navy-blue dark:text-white mb-4">
              Invite Team Member
            </h2>
            
            {/* Capacity Information */}
            <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                <strong>Seat Capacity:</strong> {dashboardData?.facility.current_user_count || 0} of {dashboardData?.subscription?.seat_count || 1} seats used
              </p>
              {(dashboardData?.facility.current_user_count || 0) >= (dashboardData?.subscription?.seat_count || 1) && (
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  ⚠️ No available seats. Please add additional seats first.
                </p>
              )}
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-navy-blue dark:bg-gray-800 dark:text-white"
                  placeholder="colleague@example.com"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Note: Invited user must use an email that has not been registered before
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Personal Message (Optional)
                </label>
                <textarea
                  value={inviteMessage}
                  onChange={(e) => setInviteMessage(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-navy-blue dark:bg-gray-800 dark:text-white"
                  placeholder="Welcome to our team! Looking forward to working with you."
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowInviteModal(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                disabled={inviteLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleInviteUser}
                disabled={inviteLoading || !inviteEmail.trim()}
                className="px-4 py-2 bg-navy-blue text-white rounded-md hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {inviteLoading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>}
                <span>{inviteLoading ? 'Sending...' : 'Send Invitation'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Seat Reduction Modal */}
      {showSeatReductionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-dark-surface rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-semibold text-navy-blue dark:text-white mb-4">
              Reduce Seats
            </h2>
            
                         <div className="space-y-4">
               <div>
                 <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                   Seats to Remove
                 </label>
                 <input
                   type="number"
                   min="1"
                   max={Math.max(1, (subscription?.seat_count || 1) - (users.length + 1))}
                   value={seatsToRemove}
                   onChange={(e) => setSeatsToRemove(Number(e.target.value))}
                   className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-navy-blue dark:bg-gray-800 dark:text-white"
                   placeholder="1"
                 />
                 <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                   Current seats: {subscription?.seat_count || 0} | Current users: {users.length + 1} (including admin) | 
                   Maximum removable: {Math.max(0, (subscription?.seat_count || 1) - (users.length + 1))}
                 </p>
               </div>
               
               {seatsToRemove > 0 && subscription && (
                 <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                   <p className="text-sm text-green-800 dark:text-green-200">
                     Monthly savings: ${(seatsToRemove * 20).toFixed(2)}
                   </p>
                   <p className="text-sm text-green-600 dark:text-green-300">
                     New seat count: {subscription.seat_count - seatsToRemove}
                   </p>
                 </div>
               )}
             </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowSeatReductionModal(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                disabled={inviteLoading}
              >
                Cancel
              </button>
                             <button
                 onClick={handleConfirmSeatReduction}
                 disabled={inviteLoading || seatsToRemove <= 0 || seatsToRemove > Math.max(0, (subscription?.seat_count || 1) - (users.length + 1))}
                 className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
               >
                 {inviteLoading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>}
                 <span>{inviteLoading ? 'Processing...' : 'Remove Seats'}</span>
               </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Seats Modal */}
      {showAddSeatsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-dark-surface rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-semibold text-navy-blue dark:text-white mb-4">
              Purchase Additional Seats
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Additional Seats to Purchase
                </label>
                <input
                  type="number"
                  min="1"
                  value={seatsToAdd}
                  onChange={(e) => setSeatsToAdd(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-navy-blue dark:bg-gray-800 dark:text-white"
                  placeholder="1"
                />
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Current seats: {subscription?.seat_count || 0} | $20 per additional seat per month
                </p>
              </div>
              
              {seatsToAdd > 0 && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    Additional monthly cost: ${(seatsToAdd * 20).toFixed(2)}
                  </p>
                  <p className="text-sm text-blue-600 dark:text-blue-300">
                    New seat count: {(subscription?.seat_count || 0) + seatsToAdd}
                  </p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    After payment, you'll be able to invite {seatsToAdd} additional team member{seatsToAdd > 1 ? 's' : ''}
                  </p>
                </div>
              )}
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddSeatsModal(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                disabled={inviteLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmAddSeats}
                disabled={inviteLoading || seatsToAdd <= 0}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {inviteLoading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>}
                <span>{inviteLoading ? 'Processing...' : 'Purchase Seats'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FacilityDashboard; 