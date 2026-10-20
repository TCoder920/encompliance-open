/**
 * Description: Access control utility for the EnCompliance application.
 * Purpose: Provides functions to determine if a user can access specific premium features
 * based on their subscription tier. Implements the core paywall logic by comparing
 * user tier against feature requirements. Enhanced with freemium preview functionality.
 */

import { Tier } from './tiers';
import { featureRequirements } from './featureRequirements';

/**
 * Checks if a user with the given tier can access a specific feature
 * @param userTier - The tier of the current user
 * @param featureKey - The key of the feature to check access for
 * @returns boolean indicating whether the user can access the feature
 */
export function canAccessFeature(userTier: Tier, featureKey: string): boolean {
  // If the feature doesn't exist in requirements, assume it's available to all
  if (!(featureKey in featureRequirements)) return true;
  
  // Check if user tier meets or exceeds the required tier for the feature
  return userTier >= featureRequirements[featureKey];
}

/**
 * Checks if a user can preview a feature (always true for freemium model)
 * @param userTier - The tier of the current user
 * @param featureKey - The key of the feature to check preview access for
 * @returns boolean indicating whether the user can preview the feature
 */
export function canPreviewFeature(userTier: Tier, featureKey: string): boolean {
  // All users can preview all features in freemium model
  return true;
}

/**
 * Checks if a user can actually use/interact with a feature (same as canAccessFeature)
 * @param userTier - The tier of the current user
 * @param featureKey - The key of the feature to check usage access for
 * @returns boolean indicating whether the user can use the feature
 */
export function canUseFeature(userTier: Tier, featureKey: string): boolean {
  return canAccessFeature(userTier, featureKey);
}

/**
 * Enhanced access control that considers both tier and user role for specific features
 * @param userTier - The tier of the current user
 * @param featureKey - The key of the feature to check access for
 * @param userRole - The role of the current user (optional)
 * @param subscriptionStatus - The subscription status of the current user (optional)
 * @returns boolean indicating whether the user can use the feature
 */
export function canUseFeatureWithRole(
  userTier: Tier, 
  featureKey: string, 
  userRole?: string, 
  subscriptionStatus?: string
): boolean {
  // Special case for data_export: only facility administrators can access it
  if (featureKey === 'data_export') {
    return userRole === 'facility_admin';
  }
  
  // For all other features, use normal tier-based access control
  return canAccessFeature(userTier, featureKey);
}

/**
 * Gets the required tier for a specific feature
 * @param featureKey - The key of the feature
 * @returns the minimum tier required for the feature
 */
export function getRequiredTier(featureKey: string): Tier {
  return featureRequirements[featureKey] || Tier.FREE;
}

/**
 * Checks if a feature is premium (requires paid subscription)
 * @param featureKey - The key of the feature to check
 * @returns boolean indicating whether the feature is premium
 */
export function isPremiumFeature(featureKey: string): boolean {
  return featureKey in featureRequirements && featureRequirements[featureKey] > Tier.FREE;
} 