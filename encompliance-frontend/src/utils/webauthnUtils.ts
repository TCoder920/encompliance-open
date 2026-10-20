/*
  Description: WebAuthn utilities for browser detection and error handling
  Purpose: Provides helper functions for WebAuthn operations, browser compatibility checks, and error diagnosis
*/

type Browser = 'chrome' | 'firefox' | 'safari' | 'edge' | 'opera' | 'other';

/**
 * Detect the user's browser
 */
export const detectBrowser = (): Browser => {
  const userAgent = navigator.userAgent.toLowerCase();
  
  if (userAgent.indexOf('chrome') > -1 && userAgent.indexOf('edg') === -1) {
    return 'chrome';
  } else if (userAgent.indexOf('firefox') > -1) {
    return 'firefox';
  } else if (userAgent.indexOf('safari') > -1 && userAgent.indexOf('chrome') === -1) {
    return 'safari';
  } else if (userAgent.indexOf('edg') > -1) {
    return 'edge';
  } else if (userAgent.indexOf('opera') > -1 || userAgent.indexOf('opr') > -1) {
    return 'opera';
  } else {
    return 'other';
  }
};

/**
 * Apply browser-specific fixes for WebAuthn
 */
export const applyBrowserSpecificFixes = () => {
  const browser = detectBrowser();
  
  // Log browser detection for debugging
  console.log(`WebAuthn: Detected browser: ${browser}`);
  
  // Return browser-specific settings
  switch (browser) {
    case 'safari':
      return {
        useConditionalUI: true,
        batchCredentials: true
      };
    case 'chrome':
      return {
        useConditionalUI: true,
        batchCredentials: false
      };
    default:
      return {
        useConditionalUI: false,
        batchCredentials: false
      };
  }
};

/**
 * Diagnose WebAuthn errors and provide more helpful error messages
 */
export const diagnoseWebAuthnError = (error: any): string => {
  console.error('WebAuthn error details:', error);
  
  // Check for AbortError (user cancellation)
  if (error.name === 'AbortError' || 
      (error.message && error.message.includes('abort'))) {
    return 'The operation was cancelled by the user or timed out.';
  }
  
  // Check for NotAllowedError (permission denied)
  if (error.name === 'NotAllowedError' || 
      (error.message && error.message.includes('not allowed'))) {
    return 'The operation was not allowed, possibly due to security settings or requirements.';
  }
  
  // Check for SecurityError
  if (error.name === 'SecurityError' || 
      (error.message && error.message.includes('security'))) {
    return 'A security error occurred. This might be due to an insecure context or cross-origin issues.';
  }
  
  // Check for NotSupportedError
  if (error.name === 'NotSupportedError' || 
      (error.message && error.message.includes('not supported'))) {
    return 'The operation is not supported by your browser or device.';
  }
  
  // Check for InvalidStateError (already registered)
  if (error.name === 'InvalidStateError' || 
      (error.message && error.message.includes('already registered'))) {
    return 'This credential appears to be already registered.';
  }
  
  // Check for response errors from backend
  if (error.response) {
    // Extract the detail message if available
    const detail = error.response.data?.detail;
    if (detail) {
      // If the backend provides a detailed error message, use it
      return `Server error: ${detail}`;
    }
    
    // Otherwise, return a generic message based on status code
    switch (error.response.status) {
      case 400:
        return 'The request was invalid. The credential may already be registered or the data format was incorrect.';
      case 401:
        return 'Authentication required. Please sign in again.';
      case 403:
        return 'You do not have permission to perform this operation.';
      case 404:
        return 'The requested resource was not found.';
      case 500:
        return 'A server error occurred. Please try again later or contact support.';
      default:
        return `Server error (${error.response.status}).`;
    }
  }
  
  // Add debug info for RP_ID issues
  if (error.message && (
      error.message.includes('RP ID') || 
      error.message.includes('rp'))) {
    return 'There might be a configuration issue with the domain. Please contact support.';
  }
  
  // Add debug info for iOS/MacOS issues
  if (detectBrowser() === 'safari' && error.message) {
    if (error.message.includes('keychain') || error.message.includes('iCloud')) {
      return 'There was an issue with your iCloud Keychain. Check that you are signed in to your Apple account.';
    }
  }

  // Default fallback message
  return error.message || 'An unknown error occurred with the WebAuthn operation.';
};

/**
 * Check if the browser is running on a mobile device
 */
export const isMobileDevice = (): boolean => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

/**
 * Log WebAuthn diagnostic information
 */
export const logWebAuthnDiagnostics = (): void => {
  const browser = detectBrowser();
  const isMobile = isMobileDevice();
  const isSecureContext = window.isSecureContext;
  const hasNavigatorCredentials = !!navigator.credentials;
  const hasPublicKeyCredential = !!window.PublicKeyCredential;
  const isUserVerifyingPlatformAuthenticatorAvailable = 
    window.PublicKeyCredential?.isUserVerifyingPlatformAuthenticatorAvailable?.() || Promise.resolve(false);
  
  // Log diagnostic information
  console.log('WebAuthn Diagnostics:', {
    browser,
    isMobile,
    isSecureContext,
    hasNavigatorCredentials,
    hasPublicKeyCredential,
    userVerifyingPlatformAuthenticatorAvailable: isUserVerifyingPlatformAuthenticatorAvailable
  });
  
  // Check for secure context
  if (!isSecureContext) {
    console.error('WebAuthn requires a secure context (HTTPS).');
  }
  
  // Check for basic WebAuthn support
  if (!hasNavigatorCredentials || !hasPublicKeyCredential) {
    console.error('Browser does not support WebAuthn.');
  }
}; 