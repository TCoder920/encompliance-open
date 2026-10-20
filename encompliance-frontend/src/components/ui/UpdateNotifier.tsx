import React, { useState, useEffect } from 'react';
import { checkForUpdates, hardRefresh } from '../../utils/versionCheck';

interface UpdateNotifierProps {
  /** Check interval in milliseconds (default: 5 minutes) */
  checkInterval?: number;
  /** Show the component even when no updates are available */
  alwaysShow?: boolean;
  /** CSS class name for the container */
  className?: string;
}

/**
 * A component that periodically checks for application updates and notifies users.
 * Can be placed in a layout component to provide automatic update notifications.
 */
const UpdateNotifier: React.FC<UpdateNotifierProps> = ({
  checkInterval = 300000, // Default: 5 minutes
  alwaysShow = false,
  className = '',
}) => {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  
  // Function to check for updates
  const checkForAppUpdates = async () => {
    try {
      // We'll use the version check utility but only to detect changes,
      // not to automatically clear cache (by passing false)
      const isUpdated = checkForUpdates();
      
      if (isUpdated) {
        setUpdateAvailable(true);
      }
      
      setLastChecked(new Date());
    } catch (error) {
      console.error('Failed to check for updates:', error);
    }
  };
  
  // Set up periodic check
  useEffect(() => {
    // Check immediately on mount
    checkForAppUpdates();
    
    // Set up interval for checking
    const intervalId = setInterval(checkForAppUpdates, checkInterval);
    
    // Clean up on unmount
    return () => {
      clearInterval(intervalId);
    };
  }, [checkInterval]);
  
  // Handle update action
  const handleUpdate = () => {
    hardRefresh(); // This will clear cache and reload the page
  };
  
  if (!updateAvailable && !alwaysShow) {
    return null;
  }
  
  return (
    <div className={`fixed bottom-4 right-4 bg-blue-100 border border-blue-300 rounded p-3 shadow-lg z-50 max-w-xs ${className}`}>
      {updateAvailable ? (
        <>
          <p className="text-blue-800 font-medium mb-2">Application update available!</p>
          <p className="text-blue-600 text-sm mb-3">
            A new version of the application is available. Update now for the latest features and fixes.
          </p>
          <div className="flex justify-between">
            <button
              onClick={handleUpdate}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-1 rounded text-sm"
            >
              Update Now
            </button>
            <button
              onClick={() => setUpdateAvailable(false)}
              className="text-blue-500 hover:underline text-sm"
            >
              Dismiss
            </button>
          </div>
        </>
      ) : (
        <>
          <p className="text-blue-800 font-medium">Application is up to date</p>
          {lastChecked && (
            <p className="text-blue-600 text-xs mt-1">
              Last checked: {lastChecked.toLocaleTimeString()}
            </p>
          )}
        </>
      )}
    </div>
  );
};

export default UpdateNotifier; 