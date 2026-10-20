/**
 * Version checker and cache management utility
 * 
 * This module provides functionality to:
 * 1. Check for application updates by comparing versions
 * 2. Clear browser caches when updates are detected
 * 3. Preserve important user state between updates
 */

// List of localStorage keys that should be preserved between updates
const PRESERVED_KEYS = [
  'token',                  // User authentication token
  'customerSupportToken',   // Support portal authentication token
  'user_settings',          // User preferences
  'theme_preference',       // Theme settings
];

// Version storage key
const VERSION_STORAGE_KEY = 'app_version';

/**
 * Check if the application has been updated and clear caches if needed
 * @returns {boolean} True if an update was detected and caches were cleared
 */
export function checkForUpdates(): boolean {
  const currentVersion = import.meta.env.VITE_APP_VERSION || '1.0.0';
  const storedVersion = localStorage.getItem(VERSION_STORAGE_KEY);
  
  // If versions match, no update needed
  if (storedVersion === currentVersion) {
    return false;
  }
  
  // Log the update
  console.log(`Application updated from ${storedVersion || 'unknown'} to ${currentVersion}`);
  
  // Store preservable values
  const preservedValues = PRESERVED_KEYS.reduce((acc, key) => {
    const value = localStorage.getItem(key);
    if (value) acc[key] = value;
    return acc;
  }, {} as Record<string, string>);
  
  // Clear all localStorage
  localStorage.clear();
  
  // Restore preserved values
  Object.entries(preservedValues).forEach(([key, value]) => {
    localStorage.setItem(key, value);
  });
  
  // Update stored version
  localStorage.setItem(VERSION_STORAGE_KEY, currentVersion);
  
  // Try to clear browser cache if Cache API is available
  if (typeof caches !== 'undefined') {
    try {
      caches.keys().then(cacheNames => {
        cacheNames.forEach(cacheName => {
          caches.delete(cacheName);
        });
      });
    } catch (e) {
      console.error('Failed to clear browser cache:', e);
    }
  }
  
  return true;
}

/**
 * Force cache clearing regardless of version
 * @param {boolean} preserveUserData If true, user data from PRESERVED_KEYS will be kept
 * @param {boolean} hardReload If true, will reload the page after clearing cache
 */
export function forceCacheClear(preserveUserData = true, hardReload = false): void {
  if (preserveUserData) {
    // Store preservable values
    const preservedValues = PRESERVED_KEYS.reduce((acc, key) => {
      const value = localStorage.getItem(key);
      if (value) acc[key] = value;
      return acc;
    }, {} as Record<string, string>);
    
    // Clear all localStorage
    localStorage.clear();
    
    // Restore preserved values
    Object.entries(preservedValues).forEach(([key, value]) => {
      localStorage.setItem(key, value);
    });
  } else {
    // Clear everything
    localStorage.clear();
  }
  
  // Update stored version
  const currentVersion = import.meta.env.VITE_APP_VERSION || '1.0.0';
  localStorage.setItem(VERSION_STORAGE_KEY, currentVersion);
  
  // Try to clear browser cache if Cache API is available
  if (typeof caches !== 'undefined') {
    try {
      caches.keys().then(cacheNames => {
        cacheNames.forEach(cacheName => {
          caches.delete(cacheName);
        });
        
        console.log('Browser cache cleared');
        
        // Hard reload if requested
        if (hardReload && typeof window !== 'undefined') {
          window.location.reload();
        }
      });
    } catch (e) {
      console.error('Failed to clear browser cache:', e);
      // Still reload if requested, even if cache clearing failed
      if (hardReload && typeof window !== 'undefined') {
        window.location.reload();
      }
    }
  } else if (hardReload && typeof window !== 'undefined') {
    // If Cache API is not available but reload is requested
    window.location.reload();
  }
  
  console.log('Application cache forcefully cleared');
}

/**
 * Perform a hard refresh of the application
 * Clear all caches and reload the page from the server
 */
export function hardRefresh(): void {
  forceCacheClear(true, true);
}

/**
 * Add a key to the list of preserved keys
 * @param {string} key The localStorage key to preserve between updates
 */
export function addPreservedKey(key: string): void {
  if (!PRESERVED_KEYS.includes(key)) {
    PRESERVED_KEYS.push(key);
  }
} 