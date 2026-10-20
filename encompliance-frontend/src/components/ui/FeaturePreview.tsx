/**
 * Description: FeaturePreview wrapper component for the EnCompliance application.
 * Purpose: Higher-order component that wraps premium features to provide preview functionality
 * for free tier users while maintaining full access for paid users. Handles paywall modal display.
 */

import React, { useState, ReactNode } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Tier, getTierFromSubscriptionStatus } from '../../utils/tiers';
import { canUseFeature, isPremiumFeature } from '../../utils/accessControl';
import PaywallModal from './PaywallModal';

interface FeaturePreviewProps {
  featureKey: string;
  children: ReactNode;
  previewContent?: ReactNode;
  showPreviewBadge?: boolean;
  onInteractionBlocked?: () => void;
}

interface FeaturePreviewWrapperProps {
  featureKey: string;
  isPreviewMode: boolean;
  onPaywallTrigger: () => void;
  children: ReactNode;
}

/**
 * Wrapper component that intercepts interactions for preview mode
 */
const FeaturePreviewWrapper: React.FC<FeaturePreviewWrapperProps> = ({
  featureKey,
  isPreviewMode,
  onPaywallTrigger,
  children
}) => {
  if (!isPreviewMode) {
    return <>{children}</>;
  }

  // In preview mode, intercept clicks and show paywall
  const handleInteraction = (e: React.MouseEvent) => {
    // Allow certain interactions like scrolling, viewing
    const target = e.target as HTMLElement;
    const allowedElements = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
    
    // Block interactive elements
    if (target.tagName.toLowerCase() === 'button' || 
        target.tagName.toLowerCase() === 'input' ||
        target.tagName.toLowerCase() === 'textarea' ||
        target.tagName.toLowerCase() === 'select' ||
        target.closest('button') ||
        target.closest('[role="button"]') ||
        target.closest('.fc-event') || // FullCalendar events
        target.closest('.fc-daygrid-day') || // Calendar day cells
        target.closest('.fc-timegrid-slot')) { // Calendar time slots
      
      e.preventDefault();
      e.stopPropagation();
      onPaywallTrigger();
      return;
    }
  };

  return (
    <div 
      className="relative"
      onClick={handleInteraction}
      onMouseDown={handleInteraction}
    >
      {children}
    </div>
  );
};

/**
 * Main FeaturePreview component
 */
const FeaturePreview: React.FC<FeaturePreviewProps> = ({
  featureKey,
  children,
  previewContent,
  showPreviewBadge = true,
  onInteractionBlocked
}) => {
  const { user } = useAuth();
  const [showPaywall, setShowPaywall] = useState(false);
  
  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUse = canUseFeature(userTier, featureKey);
  const isPremium = isPremiumFeature(featureKey);
  const isPreviewMode = isPremium && !canUse;

  const handlePaywallTrigger = () => {
    setShowPaywall(true);
    onInteractionBlocked?.();
  };

  const handleClosePaywall = () => {
    setShowPaywall(false);
  };

  return (
    <div className="relative">
      {/* Prominent Preview Banner */}
      {isPreviewMode && showPreviewBadge && (
        <>
          {/* Background overlay */}
          <div className="absolute inset-0 z-10 bg-black/20 backdrop-blur-[1px]" />
          
          {/* Banner container */}
          <div className="absolute inset-0 z-20 flex items-center justify-center pointer-events-none">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-2xl shadow-2xl border-2 border-white/20 backdrop-blur-sm max-w-md mx-4 text-center pointer-events-auto">
              <div className="flex items-center justify-center mb-3">
                <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center mr-3">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 2L13 7h5l-4 3.5L16 16l-6-4.5L4 16l2-5.5L2 7h5l3-5z" clipRule="evenodd"/>
                  </svg>
                </div>
                <h3 className="text-xl font-bold">Preview Mode</h3>
              </div>
              <p className="text-sm opacity-90 mb-4">
                You're viewing a preview of this premium feature. 
                Upgrade to unlock full functionality and interactive features.
              </p>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handlePaywallTrigger();
                }}
                className="bg-white text-blue-600 px-6 py-2 rounded-lg font-semibold hover:bg-blue-50 transition-colors shadow-lg"
              >
                Upgrade Now
              </button>
            </div>
          </div>
        </>
      )}

      {/* Feature Content */}
      <FeaturePreviewWrapper
        featureKey={featureKey}
        isPreviewMode={isPreviewMode}
        onPaywallTrigger={handlePaywallTrigger}
      >
        {isPreviewMode && previewContent ? previewContent : children}
      </FeaturePreviewWrapper>

      {/* Paywall Modal */}
      <PaywallModal
        isOpen={showPaywall}
        onClose={handleClosePaywall}
        featureKey={featureKey}
        userTier={userTier}
      />
    </div>
  );
};

export default FeaturePreview; 