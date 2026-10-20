/*
  Description: Unit tests for the PasskeyRegistration component
  Purpose: Verifies that the passkey registration component works correctly
*/
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PasskeyRegistration from '../PasskeyRegistration';
import { webauthnService } from '../../services/webauthnService';

// Mock the webauthnService
jest.mock('../../services/webauthnService', () => ({
  webauthnService: {
    isWebAuthnSupported: jest.fn(),
    isPlatformAuthenticatorAvailable: jest.fn(),
    getCredentials: jest.fn(),
    registerPasskey: jest.fn(),
    deleteCredential: jest.fn(),
  },
}));

describe('PasskeyRegistration Component', () => {
  // Mock credentials for testing
  const mockCredentials = [
    {
      id: 1,
      name: 'Test Passkey 1',
      created_at: '2023-01-01T00:00:00',
      last_used_at: '2023-01-02T00:00:00',
      device_type: 'platform'
    },
    {
      id: 2,
      name: 'Test Passkey 2',
      created_at: '2023-01-03T00:00:00',
      device_type: 'cross-platform'
    }
  ];
  
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    
    // Default mock implementations
    (webauthnService.isWebAuthnSupported as jest.Mock).mockReturnValue(true);
    (webauthnService.isPlatformAuthenticatorAvailable as jest.Mock).mockResolvedValue(true);
    (webauthnService.getCredentials as jest.Mock).mockResolvedValue(mockCredentials);
    (webauthnService.registerPasskey as jest.Mock).mockResolvedValue({
      id: 3,
      name: 'New Passkey',
      created_at: '2023-01-04T00:00:00',
      device_type: 'platform'
    });
    (webauthnService.deleteCredential as jest.Mock).mockResolvedValue({ message: 'Credential deleted successfully' });
    
    // Mock confirm dialog
    global.confirm = jest.fn(() => true);
  });
  
  afterEach(() => {
    // Clean up
    jest.resetAllMocks();
  });
  
  test('renders unsupported message when WebAuthn is not supported', async () => {
    (webauthnService.isWebAuthnSupported as jest.Mock).mockReturnValue(false);
    
    render(<PasskeyRegistration />);
    
    // Check for unsupported message
    expect(screen.getByText(/Your browser does not support passkeys/i)).toBeInTheDocument();
  });
  
  test('renders registration form and credential list when WebAuthn is supported', async () => {
    render(<PasskeyRegistration />);
    
    // Wait for credentials to load
    await waitFor(() => {
      // Check for registration form
      expect(screen.getByText(/Register a New Passkey/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Passkey Name/i)).toBeInTheDocument();
      
      // Check for credentials section
      expect(screen.getByText(/Your Passkeys/i)).toBeInTheDocument();
      expect(screen.getByText(/Test Passkey 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Test Passkey 2/i)).toBeInTheDocument();
    });
  });
  
  test('shows platform button when platform authenticator is available', async () => {
    render(<PasskeyRegistration />);
    
    // Wait for component to check platform authenticator availability
    await waitFor(() => {
      expect(screen.getByText(/Register with Device Biometrics/i)).toBeInTheDocument();
    });
  });
  
  test('handles passkey registration successfully', async () => {
    const onSuccessMock = jest.fn();
    render(<PasskeyRegistration onSuccess={onSuccessMock} />);
    
    // Set credential name
    const nameInput = screen.getByLabelText(/Passkey Name/i);
    fireEvent.change(nameInput, { target: { value: 'New Passkey' } });
    
    // Click register button
    const registerButton = await screen.findByText(/Register with Device Biometrics/i);
    fireEvent.click(registerButton);
    
    // Wait for registration to complete
    await waitFor(() => {
      // Check if registerPasskey was called
      expect(webauthnService.registerPasskey).toHaveBeenCalledWith('New Passkey', 'platform');
      
      // Check if success callback was called
      expect(onSuccessMock).toHaveBeenCalled();
      
      // Check for success message
      expect(screen.getByText(/Passkey.*registered successfully/i)).toBeInTheDocument();
      
      // Check if getCredentials was called to refresh the list
      expect(webauthnService.getCredentials).toHaveBeenCalledTimes(2); // Once on init, once after registration
    });
  });
  
  test('handles passkey registration error', async () => {
    // Mock registration to fail
    (webauthnService.registerPasskey as jest.Mock).mockRejectedValue({
      message: 'Registration failed',
      response: { data: { detail: 'User verification failed' } }
    });
    
    const onErrorMock = jest.fn();
    render(<PasskeyRegistration onError={onErrorMock} />);
    
    // Click register button
    const registerButton = await screen.findByText(/Register with Device Biometrics/i);
    fireEvent.click(registerButton);
    
    // Wait for registration to fail
    await waitFor(() => {
      // Check if onError callback was called
      expect(onErrorMock).toHaveBeenCalled();
      
      // Check for error message
      expect(screen.getByText(/User verification failed/i)).toBeInTheDocument();
    });
  });
  
  test('handles credential deletion', async () => {
    render(<PasskeyRegistration />);
    
    // Wait for credentials to load
    await waitFor(() => {
      expect(screen.getByText(/Test Passkey 1/i)).toBeInTheDocument();
    });
    
    // Find and click delete button (using title attribute)
    const deleteButtons = screen.getAllByTitle('Delete passkey');
    fireEvent.click(deleteButtons[0]); // Delete first credential
    
    // Wait for deletion to complete
    await waitFor(() => {
      // Check if deleteCredential was called with correct ID
      expect(webauthnService.deleteCredential).toHaveBeenCalledWith(1);
      
      // Check for success message
      expect(screen.getByText(/Passkey deleted successfully/i)).toBeInTheDocument();
      
      // Check if getCredentials was called to refresh the list
      expect(webauthnService.getCredentials).toHaveBeenCalledTimes(2); // Once on init, once after deletion
    });
  });
  
  test('shows empty state when no credentials', async () => {
    // Mock empty credentials list
    (webauthnService.getCredentials as jest.Mock).mockResolvedValue([]);
    
    render(<PasskeyRegistration />);
    
    // Wait for credentials check
    await waitFor(() => {
      // Check for empty state message
      expect(screen.getByText(/You haven't registered any passkeys yet/i)).toBeInTheDocument();
    });
  });
}); 