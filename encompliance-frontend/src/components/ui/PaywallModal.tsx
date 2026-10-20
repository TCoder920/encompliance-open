/**
 * Description: PaywallModal component for the EnCompliance application.
 * Purpose: Displays a modal to free tier users when they attempt to access premium features,
 * showing feature benefits and providing upgrade options to convert users to paid plans.
 */

import React from 'react';
import { X, Check, Crown, ArrowRight } from 'lucide-react';
import { Tier } from '../../utils/tiers';
import { FEATURE_BENEFITS, TIER_COMPARISON } from '../../utils/previewData';

interface PaywallModalProps {
  isOpen: boolean;
  onClose: () => void;
  featureKey: string;
  userTier: Tier;
}

const PaywallModal: React.FC<PaywallModalProps> = ({
  isOpen,
  onClose,
  featureKey,
  userTier
}) => {
  if (!isOpen) return null;

  const feature = FEATURE_BENEFITS[featureKey as keyof typeof FEATURE_BENEFITS];
  const currentTierInfo = TIER_COMPARISON[userTier];
  const requiredTierInfo = TIER_COMPARISON[feature?.requiredTier || Tier.PRO];

  const handleUpgrade = () => {
    // Navigate to subscription page for upgrade
    window.location.href = '/userSettings?tab=subscription';
  };

  const handleContactSales = () => {
    // Navigate to contact or open email
    window.location.href = 'mailto:sales@encompliance.io?subject=Enterprise%20Subscription%20Inquiry';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center">
            <Crown className="h-6 w-6 text-yellow-500 mr-2" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Upgrade Required
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {feature && (
            <>
              {/* Feature Info */}
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300 text-lg">
                  {feature.description}
                </p>
              </div>

              {/* Feature Benefits */}
              <div className="mb-8">
                <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  What you'll get:
                </h4>
                <div className="space-y-3">
                  {feature.benefits.map((benefit, index) => (
                    <div key={index} className="flex items-start">
                      <Check className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700 dark:text-gray-300">{benefit}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Plan Comparison */}
          <div className="mb-8">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Choose your plan:
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Current Plan */}
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="text-center mb-4">
                  <h5 className="font-bold text-gray-900 dark:text-white">
                    {currentTierInfo.name}
                  </h5>
                  <p className="text-gray-600 dark:text-gray-400">
                    {currentTierInfo.price}
                  </p>
                  <span className="inline-block bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs px-2 py-1 rounded mt-2">
                    Current Plan
                  </span>
                </div>
                <ul className="space-y-2 text-sm">
                  {currentTierInfo.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <Check className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-600 dark:text-gray-400">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Required Plan */}
              <div className="border-2 border-blue-500 rounded-lg p-4 relative">
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-blue-500 text-white text-xs px-3 py-1 rounded-full">
                    Recommended
                  </span>
                </div>
                <div className="text-center mb-4">
                  <h5 className="font-bold text-gray-900 dark:text-white">
                    {requiredTierInfo.name}
                  </h5>
                  <p className="text-gray-600 dark:text-gray-400">
                    {requiredTierInfo.price}
                  </p>
                </div>
                <ul className="space-y-2 text-sm mb-4">
                  {requiredTierInfo.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <Check className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-600 dark:text-gray-400">{feature}</span>
                    </li>
                  ))}
                </ul>
                {requiredTierInfo.name === 'Enterprise' ? (
                  <button
                    onClick={handleContactSales}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center"
                  >
                    Contact Sales
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </button>
                ) : (
                  <button
                    onClick={handleUpgrade}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center"
                  >
                    Upgrade Now
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Preview Notice */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 text-center">
            <p className="text-blue-800 dark:text-blue-300 text-sm">
              <strong>You're viewing a preview.</strong> Upgrade to unlock full functionality and start managing your compliance more effectively.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <button
            onClick={onClose}
            className="text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
          >
            Continue Preview
          </button>
          <div className="flex space-x-3">
            {requiredTierInfo.name === 'Enterprise' ? (
              <button
                onClick={handleContactSales}
                className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-6 rounded-lg transition-colors"
              >
                Contact Sales
              </button>
            ) : (
              <button
                onClick={handleUpgrade}
                className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-6 rounded-lg transition-colors"
              >
                Upgrade to {requiredTierInfo.name}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaywallModal; 