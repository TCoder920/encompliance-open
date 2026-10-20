/**
 * Description: Informative popup tooltip for AI mode selection.
 * Purpose: Guides Pro and Enterprise users to discover the AI mode selection feature.
 * Shows only a few times for new users, then permanently dismissed.
 */

import React, { useState, useEffect, useRef } from 'react';
import { X, MousePointer } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Tier, getTierFromSubscriptionStatus } from '../../utils/tiers';

interface AiModeTooltipProps {
  isVisible: boolean;
  onDismiss: () => void;
  targetRef: React.RefObject<HTMLElement>;
}

const AiModeTooltip: React.FC<AiModeTooltipProps> = ({ isVisible, onDismiss, targetRef }) => {
  const { user } = useAuth();
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const tooltipRef = useRef<HTMLDivElement>(null);

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const shouldShow = userTier === Tier.PRO || userTier === Tier.ENTERPRISE;

  // Calculate position relative to target element
  useEffect(() => {
    if (isVisible && targetRef.current && tooltipRef.current) {
      const targetRect = targetRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      
      // Position below the target element
      const top = targetRect.bottom + 10;
      const left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
      
      // Ensure tooltip stays within viewport
      const adjustedLeft = Math.max(10, Math.min(left, window.innerWidth - tooltipRect.width - 10));
      const adjustedTop = Math.max(10, top);
      
      setPosition({ top: adjustedTop, left: adjustedLeft });
    }
  }, [isVisible, targetRef]);

  if (!isVisible || !shouldShow) {
    return null;
  }

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-20 z-40" onClick={onDismiss} />
      
      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className="fixed z-50 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-4 max-w-sm"
        style={{ top: position.top, left: position.left }}
      >
        {/* Close button */}
        <button
          onClick={onDismiss}
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
        
        {/* Content */}
        <div className="pr-6">
          <div className="flex items-center mb-2">
            <MousePointer className="h-5 w-5 text-blue-500 mr-2" />
            <h3 className="font-semibold text-gray-900 dark:text-white">
              AI Mode Selection
            </h3>
          </div>
          
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
            Click here to switch between Basic and Pro AI assistant modes. Pro mode offers enhanced capabilities and more detailed responses.
          </p>
          
          <div className="flex justify-end">
            <button
              onClick={onDismiss}
              className="text-xs bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded transition-colors"
            >
              Got it!
            </button>
          </div>
        </div>
        
        {/* Arrow pointing to target */}
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2">
          <div className="w-0 h-0 border-l-8 border-r-8 border-b-8 border-l-transparent border-r-transparent border-b-white dark:border-b-gray-800"></div>
          <div className="w-0 h-0 border-l-8 border-r-8 border-b-8 border-l-transparent border-r-transparent border-b-gray-200 dark:border-b-gray-700 mt-px"></div>
        </div>
      </div>
    </>
  );
};

export default AiModeTooltip; 