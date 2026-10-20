import React, { useState } from 'react';
import { forceCacheClear } from '../../utils/versionCheck';

interface CacheClearButtonProps {
  /** CSS class name for styling */
  className?: string;
  /** Button label. Defaults to "Clear Cache" */
  label?: string;
  /** Whether to show a notification after clearing. Default: true */
  showNotification?: boolean;
  /** Whether to preserve user data (authentication, settings) */
  preserveUserData?: boolean;
}

/**
 * Button component that allows users to manually clear the application cache.
 * Useful for developers and for troubleshooting in production when users experience stale UI issues.
 */
const CacheClearButton: React.FC<CacheClearButtonProps> = ({
  className = '',
  label = 'Clear Cache',
  showNotification = true,
  preserveUserData = true
}) => {
  const [showSuccess, setShowSuccess] = useState(false);
  
  const handleClearCache = () => {
    forceCacheClear(preserveUserData);
    
    if (showNotification) {
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    }
  };
  
  return (
    <div className="relative">
      <button
        onClick={handleClearCache}
        className={`px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 text-sm ${className}`}
        aria-label="Clear application cache"
      >
        {label}
      </button>
      
      {showSuccess && (
        <div className="absolute top-full mt-2 p-2 bg-green-100 border border-green-300 rounded text-sm text-green-700">
          Cache cleared successfully
        </div>
      )}
    </div>
  );
};

export default CacheClearButton; 