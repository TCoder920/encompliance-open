/*
  Description: Payment service for handling subscription, checkout, and payment history operations via API.
  Purpose: Provides functions to manage user payments, subscriptions, and billing history for compliance platform monetization.
*/
import api from './api';

export interface CheckoutResponse {
  checkout_url: string;
  session_id: string;
}

export interface SubscriptionStatus {
  status: string;
  end_date?: string;
  has_active_subscription: boolean;
  subscription_id?: string;
  plan?: string;
  cancel_at_period_end?: boolean;
}

export interface PaymentHistoryItem {
  id: number;
  stripe_payment_id: string;
  amount: number;
  currency: string;
  status: string;
  payment_type: string;
  subscription_plan?: string;
  created_at: string;
}

export const paymentService = {
  async createSubscriptionCheckout(
    subscriptionType: 'monthly' | 'yearly',
    successUrl: string,
    cancelUrl: string
  ): Promise<CheckoutResponse> {
    const response = await api.post('/payments/create-checkout-session', {
      subscription_type: subscriptionType,
      success_url: successUrl,
      cancel_url: cancelUrl
    });
    return response.data;
  },
  
  async createOneTimeCheckout(
    amount: number, // in cents
    description: string,
    successUrl: string,
    cancelUrl: string
  ): Promise<CheckoutResponse> {
    const response = await api.post('/payments/create-one-time-checkout', {
      amount,
      description,
      success_url: successUrl,
      cancel_url: cancelUrl
    });
    return response.data;
  },
  
  async getSubscriptionStatus(): Promise<SubscriptionStatus> {
    const response = await api.get('/payments/subscription');
    return response.data;
  },
  
  async cancelSubscription(): Promise<{ success: boolean }> {
    const response = await api.post('/payments/cancel-subscription');
    return response.data;
  },
  
  async getPaymentHistory(): Promise<PaymentHistoryItem[]> {
    const response = await api.get('/payments/history');
    return response.data;
  }
}; 