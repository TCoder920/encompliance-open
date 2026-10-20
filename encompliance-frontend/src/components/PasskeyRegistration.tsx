/*
  Description: PasskeyRegistration component for managing WebAuthn passkey credentials.
  Purpose: Enables users to register and manage passkeys for passwordless authentication.
*/
import React, { useState, useEffect } from 'react';
import { webauthnService, Credential } from '../services/webauthnService';
import { Fingerprint, Key, Shield, Plus, Trash2, AlertCircle } from 'lucide-react';
import { logWebAuthnDiagnostics } from '../utils/webauthnUtils';

interface PasskeyRegistrationProps {
  onSuccess?: (message: string) => void;
  onError?: (error: string) => void;
}

/**
 * Converts technical error messages into user-friendly ones
 */
const getFriendlyErrorMessage = (errorMessage: string): string => {
  // Technical messages and their user-friendly equivalents
  if (errorMessage.includes('user_id must be bytes') || 
      errorMessage.includes('bytes-like object is required')) {
    return 'Your browser configuration is not properly set up for passkeys. Please try again or contact support.';
  }
  
  if (errorMessage.includes('No challenge found')) {
    return 'Your session has expired. Please refresh the page and try again.';
  }
  
  if (errorMessage.includes('already registered')) {
    return 'This passkey is already registered on your account.';
  }
  
  if (errorMessage.includes('not supported')) {
    return 'Passkeys are not supported in your browser. Please use a modern browser like Chrome, Edge, Safari, or Firefox.';
  }
  
  if (errorMessage.includes('Operation timed out') || errorMessage.includes('timeout')) {
    return 'The operation took too long to complete. Please try again.';
  }
  
  if (errorMessage.includes('operation') && errorMessage.includes('cancel')) {
    return 'You cancelled the passkey registration process.';
  }
  
  if (errorMessage.includes('Network Error')) {
    return 'Unable to connect to the server. Please check your internet connection and try again.';
  }
  
  // Default fallback message
  return 'Unable to register your passkey. Please try again or use a different device.';
};

const PasskeyRegistration: React.FC<PasskeyRegistrationProps> = ({ onSuccess, onError }) => {
  const [isRegistering, setIsRegistering] = useState(false);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState<boolean>(false);
  const [isPlatformSupported, setIsPlatformSupported] = useState<boolean>(false);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [credentialName, setCredentialName] = useState<string>('My passkey');

  // Check browser support for WebAuthn when component mounts
  useEffect(() => {
    fetchCredentials();
    // Run diagnostics to help troubleshoot WebAuthn issues
    logWebAuthnDiagnostics();
  }, []);

  const fetchCredentials = async () => {
    try {
      setLoading(true);
      const supported = webauthnService.isWebAuthnSupported();
      setIsSupported(supported);
      
      if (supported) {
        const platformSupported = await webauthnService.isPlatformAuthenticatorAvailable();
        setIsPlatformSupported(platformSupported);
        
        const existingCredentials = await webauthnService.getCredentials();
        setCredentials(existingCredentials || []);
      }
    } catch (err) {
      console.error('Failed to load credentials:', err);
    } finally {
      setLoading(false);
    }
  };

  const registerPasskey = async () => {
    try {
      setIsRegistering(true);
      
      // Log device and browser information for debugging
      console.log('Starting passkey registration process...');
      logWebAuthnDiagnostics();
      
      await webauthnService.registerPasskey(credentialName);
      
      // Refresh credentials list after successful registration
      await fetchCredentials();
      onSuccess?.('Passkey registered successfully');
    } catch (error: any) {
      console.error('Error in registerPasskey:', error);
      
      // Pass the error to the parent component
      if (onError) {
        onError(error.message || 'Failed to register passkey');
      }
    } finally {
      setIsRegistering(false);
    }
  };

  const handleDeleteCredential = async (id: number) => {
    if (!confirm('Are you sure you want to delete this passkey?')) {
      return;
    }
    
    setIsDeleting(id.toString());
    
    try {
      // Delete the credential
      await webauthnService.deleteCredential(id);
      
      // Update the UI
      onSuccess?.('Passkey deleted successfully');
      
      // Refresh the credential list
      await fetchCredentials();
    } catch (err: any) {
      // Get the technical error message
      const technicalMessage = err.response?.data?.detail || 
                               err.message || 
                               'Failed to delete passkey. Please try again.';
      
      // Set a user-friendly error message
      onError?.(technicalMessage);
      
      // Log the technical error for debugging
      console.error('Passkey deletion error (technical):', technicalMessage);
    } finally {
      setIsDeleting(null);
    }
  };

  // If WebAuthn is not supported, show message
  if (!isSupported) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
        <div className="flex items-center">
          <AlertCircle className="h-5 w-5 text-yellow-400 mr-2" />
          <p className="text-yellow-700">
            Your browser does not support passkeys (WebAuthn). Please use a modern browser like Chrome, Edge, Safari, or Firefox.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error and success messages */}
      {isDeleting && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-red-700">{isDeleting}</p>
          </div>
        </div>
      )}
      
      {/* Registration Form */}
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Register a New Passkey</h3>
        
        <div className="mb-4">
          <label htmlFor="credentialName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Passkey Name
          </label>
          <input
            type="text"
            id="credentialName"
            value={credentialName}
            onChange={(e) => setCredentialName(e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-navy-blue focus:border-navy-blue sm:text-sm p-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
            placeholder="My passkey"
            disabled={isRegistering}
          />
        </div>
        
        <div className="mt-6 space-y-4">
          {isPlatformSupported && (
            <button
              onClick={registerPasskey}
              disabled={isRegistering}
              className="flex items-center justify-center w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-navy-blue hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRegistering ? (
                <span>Registering...</span>
              ) : (
                <>
                  <Fingerprint className="h-5 w-5 mr-2" />
                  Register with Device Biometrics
                </>
              )}
            </button>
          )}
          
          <button
            onClick={registerPasskey}
            disabled={isRegistering}
            className="flex items-center justify-center w-full py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:hover:bg-gray-600"
          >
            {isRegistering ? (
              <span>Registering...</span>
            ) : (
              <>
                <Key className="h-5 w-5 mr-2" />
                Register Security Key or Mobile Device
              </>
            )}
          </button>
        </div>
      </div>
      
      {/* Credentials List */}
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Your Passkeys</h3>
        
        {credentials.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            You haven't registered any passkeys yet. Register a passkey to enable passwordless login.
          </p>
        ) : (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {credentials.map((credential) => (
              <li key={credential.id} className="py-3 flex justify-between items-center">
                <div className="flex items-center">
                  <Fingerprint className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{credential.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Added: {new Date(credential.created_at).toLocaleDateString()}
                      {credential.last_used_at && ` • Last used: ${new Date(credential.last_used_at).toLocaleDateString()}`}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteCredential(credential.id)}
                  disabled={isDeleting === credential.id.toString()}
                  className="text-red-600 hover:text-red-900 p-1 rounded-full hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed dark:hover:bg-red-900/20"
                  title="Delete passkey"
                >
                  <Trash2 className="h-5 w-5" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default PasskeyRegistration; 