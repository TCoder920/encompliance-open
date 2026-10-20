/*
  Description: AiModeSelection component. Allows users to select between different AI assistant modes for tailored compliance support.
  Purpose: Provides a user interface for switching AI behavior and capabilities based on user needs.
  Enhanced with freemium preview functionality.
*/
import React, { useState, useEffect, useRef, forwardRef } from 'react';
import { Settings, Check, X, Save, BrainCircuit, Cpu, Cloud } from 'lucide-react';
import { useModel } from '../contexts/ModelContext';
import { useAuth } from '../contexts/AuthContext';
import { Tier, getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature } from '../utils/accessControl';
import FeaturePreview from './ui/FeaturePreview';

const aiModelSelector = forwardRef<HTMLButtonElement>((props, ref) => {
  const { selectedModel, setSelectedModel } = useModel();
  const { user } = useAuth();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(selectedModel);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUseProMode = canUseFeature(userTier, 'ai_pro_mode');

  // Close modal when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        handleCancel();
      }
    };

    if (isModalOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isModalOpen]);

  // Close modal on escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        handleCancel();
      }
    };

    if (isModalOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isModalOpen]);

  const handleSave = async () => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (activeTab === 'pro' && !canUseProMode) return;

    setSaveStatus('saving');
    setErrorMessage(null);

    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setSelectedModel(activeTab);
      setSaveStatus('success');
      
      // Close modal after successful save
      setTimeout(() => {
        setIsModalOpen(false);
        setSaveStatus('idle');
      }, 1000);
    } catch (error) {
      setSaveStatus('error');
      setErrorMessage('Failed to save AI mode selection. Please try again.');
    }
  };

  const handleCancel = () => {
    setActiveTab(selectedModel);
    setIsModalOpen(false);
    setSaveStatus('idle');
    setErrorMessage(null);
  };

  const handleProModeClick = () => {
    if (!canUseProMode) {
      // This will trigger the paywall modal through FeaturePreview
      return;
    }
    setActiveTab('pro');
  };

  // Get display name for current mode
  const getActiveModelDisplayName = () => {
    if (selectedModel === 'basic') {
      return "Basic Mode AI Assistant";
    } else if (selectedModel === 'pro') {
      return "Pro Mode AI Assistant";
    } else {
      return 'Basic Mode AI Assistant'; 
    }
  };

  // Get icon for current mode - removed icons, using text only
  const ModelIcon = null;

  // Main content for the modal
  const modalContent = (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div ref={modalRef} className="bg-white dark:bg-dark-surface rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            AI Assistant Mode
          </h2>
          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            Choose your AI assistant mode for the best compliance support experience.
          </p>

          {/* Mode Selection */}
          <div className="space-y-4">
            {/* Basic Mode */}
            <button
              onClick={() => setActiveTab('basic')}
              className={`w-full p-4 rounded-md border-2 flex items-center justify-between ${
                activeTab === 'basic' 
                  ? 'border-navy-blue bg-blue-50 dark:bg-blue-900/20 text-navy-blue dark:text-blue-300' 
                  : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              <div className="text-left">
                <div className="font-medium text-lg">
                  Basic Mode AI Assistant
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Standard AI responses for compliance questions
                </div>
              </div>
              {activeTab === 'basic' && (
                <div className="bg-navy-blue text-white dark:bg-blue-600 p-1 rounded-full">
                  <Check size={16} />
                </div>
              )}
            </button>

            {/* Pro Mode */}
            <FeaturePreview
              featureKey="ai_pro_mode"
              showPreviewBadge={false}
            >
              <button
                onClick={handleProModeClick}
                className={`w-full p-4 rounded-md border-2 flex items-center justify-between ${
                  activeTab === 'pro' 
                    ? 'border-navy-blue bg-blue-50 dark:bg-blue-900/20 text-navy-blue dark:text-blue-300' 
                    : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
                } ${!canUseProMode ? 'relative' : ''}`}
                disabled={!canUseProMode}
              >
                <div className="text-left">
                  <div className="font-medium text-lg">
                    Pro Mode AI Assistant
                    {!canUseProMode && (
                      <span className="ml-2 text-xs text-yellow-400 whitespace-nowrap">
                        Subscription Required
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {canUseProMode ? 'Enhanced responses with internet search' : 'Enhanced AI with real-time information'}
                  </div>
                </div>
                {activeTab === 'pro' && canUseProMode && (
                  <div className="bg-navy-blue text-white dark:bg-blue-600 p-1 rounded-full">
                    <Check size={16} />
                  </div>
                )}
              </button>
            </FeaturePreview>
          </div>

          {/* Error message */}
          {errorMessage && (
            <div className="mt-4 p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-800 text-red-800 dark:text-red-300 rounded-md text-sm">
              {errorMessage}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={handleCancel}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
              disabled={saveStatus === 'saving'}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saveStatus === 'saving' || (activeTab === 'pro' && !canUseProMode)}
              className="bg-navy-blue text-white dark:bg-blue-700 px-4 py-2 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {saveStatus === 'saving' ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Saving...
                </>
              ) : saveStatus === 'success' ? (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Saved!
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* AI Mode Button - Shows current mode with text only */}
      <button
        ref={ref}
        onClick={() => setIsModalOpen(true)}
        className="flex items-center space-x-2 p-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
        title="Change AI Mode"
      >
        <span>{getActiveModelDisplayName()}</span>
      </button>

      {/* Modal */}
      {isModalOpen && modalContent}
    </>
  );
});

aiModelSelector.displayName = 'AiModeSelection';

export default aiModelSelector; 