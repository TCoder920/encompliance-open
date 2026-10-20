/*
  Description: Display-only subscription page showing current subscription status and information
  Purpose: Provides users with subscription details and access to Stripe's Customer Portal
*/

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  CreditCard, 
  Users, 
  Calendar,
  ExternalLink
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import ErrorMessage from '../components/ErrorMessage';

// Subscription data interface
interface SubscriptionData {
  id: string;
  status: string;
  seat_count: number;
  total_amount: number;
  current_period_start: string;
  current_period_end: string;
  trial_end?: string;
  cancel_at_period_end: boolean;
}

const SubscriptionPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if user has pro features access (facility admin or team member)
    const hasProAccess = user?.subscription_status === 'pro' || 
                        user?.subscription_status === 'team_member' || 
                        user?.user_role === 'TEAM_MEMBER' ||
                        user?.user_role === 'FACILITY_ADMIN';
    
    if (!hasProAccess) {
      navigate('/facility');
      return;
    }
    fetchSubscriptionData();
  }, [user, navigate]);

  const fetchSubscriptionData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/payments/subscription-status');
      setSubscription(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch subscription data:', err);
      setError(err.response?.data?.detail || 'Failed to load subscription data');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenPaymentPortal = async () => {
    try {
      const response = await api.post('/payments/create-customer-portal', {}, {
        params: {
          return_url: window.location.href
        }
      });
      
      // Redirect to Stripe Customer Portal
      window.location.href = response.data.portal_url;
    } catch (error: any) {
      console.error('Error creating customer portal session:', error);
      setError(error.response?.data?.detail || 'Failed to open payment portal');
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (timestamp: number | string) => {
    const date = typeof timestamp === 'number' ? new Date(timestamp * 1000) : new Date(timestamp);
    return date.toLocaleDateString();
  };

  const calculateMonthlyCost = (seatCount: number) => {
    const baseCost = 50;
    const additionalSeats = Math.max(0, seatCount - 1);
    const additionalCost = additionalSeats * 20;
    return baseCost + additionalCost;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-navy-blue"></div>
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage message={error || 'No subscription found'} type="error" />
        <button
          onClick={() => navigate('/facility')}
          className="mt-4 bg-navy-blue text-white px-4 py-2 rounded-lg hover:bg-blue-800 transition-colors"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/facility')}
          className="flex items-center text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Facility Dashboard
        </button>
        
        <h1 className="text-3xl font-bold text-navy-blue dark:text-white mb-2">
          Subscription
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          View your current subscription details
        </p>
      </div>

      {error && (
        <div className="mb-6">
          <ErrorMessage message={error} type="error" onClose={() => setError(null)} />
        </div>
      )}

      {/* Subscription Details Card */}
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-navy-blue dark:text-white flex items-center">
            <CreditCard className="h-5 w-5 mr-2" />
            Subscription Details
          </h2>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Status */}
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Status</p>
            <p className={`text-lg font-semibold capitalize ${
              subscription.status === 'active' ? 'text-green-600' : 
              subscription.status === 'trialing' ? 'text-blue-600' : 
              subscription.status === 'past_due' ? 'text-orange-600' : 'text-red-600'
            }`}>
              {subscription.status === 'trialing' ? 'Trial Period' : 'Active'}
            </p>
          </div>

          {/* Monthly Cost */}
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Monthly Cost</p>
            <p className="text-2xl font-bold text-navy-blue dark:text-white">
              {formatCurrency(calculateMonthlyCost(subscription.seat_count))}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              $50 base + $20 per additional seat
            </p>
          </div>

          {/* Seats */}
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Seats</p>
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5 text-blue-500" />
              <p className="text-lg font-semibold text-navy-blue dark:text-white">
                {subscription.seat_count} users
              </p>
            </div>
          </div>

          {/* Trial End Date */}
          {subscription.trial_end && (
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Trial Ends</p>
              <div className="flex items-center space-x-2">
                <Calendar className="h-5 w-5 text-orange-500" />
                <p className="text-lg font-semibold text-orange-600">
                  {formatDate(subscription.trial_end)}
                </p>
              </div>
            </div>
          )}

          {/* Current Period */}
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Current Period</p>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {formatDate(subscription.current_period_start)} - {formatDate(subscription.current_period_end)}
            </p>
          </div>

          {/* Cancellation Notice */}
          {subscription.cancel_at_period_end && (
            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
              <p className="text-sm text-yellow-800">
                Subscription will be cancelled at the end of the current period.
              </p>
            </div>
          )}

          {/* Payment Portal Button */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleOpenPaymentPortal}
              className="w-full bg-navy-blue text-white px-6 py-3 rounded-lg hover:bg-blue-800 transition-colors flex items-center justify-center space-x-2"
            >
              <ExternalLink className="h-4 w-4" />
              <span>Open Payment Portal</span>
            </button>
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-2">
              Manage payments, billing, and subscription settings via Stripe
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPage; 