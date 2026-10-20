/**
 * Description: Feature requirements mapping for the EnCompliance application.
 * Purpose: Defines which subscription tier is required for each premium feature.
 * Used in conjunction with accessControl.ts to enforce paywall restrictions.
 */

import { Tier } from './tiers';

/**
 * Defines the minimum tier required for each feature in the application
 * Used for paywall and feature access control
 */
export const featureRequirements: Record<string, Tier> = {
  calendar: Tier.PRO,
  ai_pro_mode: Tier.PRO,
  notes: Tier.PRO,
  data_export: Tier.PRO,
  training_certification: Tier.PRO,
  analytics: Tier.PRO,
  facility_management: Tier.PRO,
  task_management: Tier.PRO,
  scheduling: Tier.PRO,
  team_communication: Tier.PRO,
  data_import: Tier.PRO,
  enterprise_console: Tier.PRO,
  usage_billing: Tier.PRO
}; 