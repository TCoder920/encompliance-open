/**
 * Description: User subscription tier definitions for the EnCompliance application.
 * Purpose: Provides tier enumeration and utility functions to determine user's access level 
 * based on their subscription status. Used for paywall and feature access control.
 */

/**
 * User subscription tiers
 * Used to determine feature access based on subscription level
 */
export enum Tier {
  FREE = 0,
  PRO = 1,
  ENTERPRISE = 2
}

/**
 * Converts subscription_status string to Tier enum value
 */
export function getTierFromSubscriptionStatus(subscriptionStatus: string | undefined): Tier {
  if (!subscriptionStatus) return Tier.FREE;
  
  switch (subscriptionStatus.toLowerCase()) {
    case 'pro':
    case 'active':  // Treat 'active' as PRO tier
    case 'team_member':  // Team members get PRO tier access
      return Tier.PRO;
    case 'enterprise':
      return Tier.ENTERPRISE;
    case 'free':
    default:
      return Tier.FREE;
  }
} 