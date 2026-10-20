/*
  Description: Tests for the WebAuthn service
  Purpose: Verifies that the WebAuthn service functions correctly for registration and authentication
*/
import { webauthnService } from '../webauthnService';
import * as browser from '@simplewebauthn/browser';
import api from '../api';

// Mock the SimpleWebAuthn browser package
jest.mock('@simplewebauthn/browser', () => ({
  startRegistration: jest.fn(),
  startAuthentication: jest.fn(),
}));

// Mock the API service
jest.mock('../api', () => ({
  post: jest.fn(),
  get: jest.fn(),
  delete: jest.fn(),
}));

describe('WebAuthn Service', () => {
  // Mock data
  const mockOptions = {
    challenge: 'test_challenge',
    rp: { id: 'localhost', name: 'EnCompliance' },
  };
  
  const mockCredentialResponse = {
    id: 'test-credential-id',
    rawId: 'test-raw-id',
    response: {},
    type: 'public-key',
    clientExtensionResults: {},
  };
  
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Set up default mock implementations
    (api.post as jest.Mock).mockImplementation((url, data) => {
      if (url === '/webauthn/register/options') {
        return Promise.resolve({ data: { options: mockOptions, user_id: 1 } });
      } else if (url === '/webauthn/register/verify') {
        return Promise.resolve({ 
          data: { 
            id: 1, 
            name: 'Test Passkey', 
            created_at: '2023-01-01T00:00:00',
            device_type: 'platform',
            message: 'Registration successful'
          } 
        });
      } else if (url === '/webauthn/authenticate/options') {
        return Promise.resolve({ data: { options: mockOptions, user_id: 1 } });
      } else if (url === '/webauthn/authenticate/verify') {
        return Promise.resolve({ 
          data: { 
            access_token: 'test_token', 
            token_type: 'bearer',
            user_id: 1,
            username: 'testuser'
          } 
        });
      }
      return Promise.reject(new Error('Unexpected URL'));
    });
    
    (api.get as jest.Mock).mockResolvedValue({
      data: [
        { id: 1, name: 'Test Passkey 1', created_at: '2023-01-01T00:00:00' },
        { id: 2, name: 'Test Passkey 2', created_at: '2023-01-02T00:00:00' },
      ]
    });
    
    (api.delete as jest.Mock).mockResolvedValue({
      data: { message: 'Credential deleted successfully' }
    });
    
    // Mock browser API functions
    (browser.startRegistration as jest.Mock).mockResolvedValue(mockCredentialResponse);
    (browser.startAuthentication as jest.Mock).mockResolvedValue(mockCredentialResponse);
    
    // Mock global PublicKeyCredential
    global.PublicKeyCredential = function () {} as any;
    global.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable = jest.fn().mockResolvedValue(true);
  });
  
  afterEach(() => {
    jest.resetAllMocks();
  });
  
  describe('getRegistrationOptions', () => {
    it('should fetch registration options from the server', async () => {
      const result = await webauthnService.getRegistrationOptions('My Passkey', 'platform');
      
      expect(api.post).toHaveBeenCalledWith('/webauthn/register/options', {
        credential_name: 'My Passkey',
        authenticator_attachment: 'platform',
      });
      
      expect(result).toEqual({ options: mockOptions, user_id: 1 });
    });
    
    it('should handle errors when fetching registration options', async () => {
      (api.post as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
      
      await expect(webauthnService.getRegistrationOptions()).rejects.toThrow('Network error');
    });
  });
  
  describe('registerPasskey', () => {
    it('should complete the full registration flow', async () => {
      const result = await webauthnService.registerPasskey('My Passkey', 'platform');
      
      // Should have called getRegistrationOptions
      expect(api.post).toHaveBeenCalledWith('/webauthn/register/options', {
        credential_name: 'My Passkey',
        authenticator_attachment: 'platform',
      });
      
      // Should have called startRegistration with options
      expect(browser.startRegistration).toHaveBeenCalledWith(mockOptions);
      
      // Should have called verify with response
      expect(api.post).toHaveBeenCalledWith('/webauthn/register/verify', {
        credential: mockCredentialResponse,
        credential_name: 'My Passkey',
        device_type: 'platform',
      });
      
      // Should return server response
      expect(result).toEqual({
        id: 1,
        name: 'Test Passkey',
        created_at: '2023-01-01T00:00:00',
        device_type: 'platform',
        message: 'Registration successful'
      });
    });
    
    it('should handle browser errors during registration', async () => {
      (browser.startRegistration as jest.Mock).mockRejectedValueOnce(new Error('User cancelled'));
      
      await expect(webauthnService.registerPasskey()).rejects.toThrow('User cancelled');
    });
  });
  
  describe('getAuthenticationOptions', () => {
    it('should fetch authentication options with email', async () => {
      const result = await webauthnService.getAuthenticationOptions(undefined, 'test@example.com');
      
      expect(api.post).toHaveBeenCalledWith('/webauthn/authenticate/options', {
        email: 'test@example.com'
      });
      
      expect(result).toEqual({ options: mockOptions, user_id: 1 });
    });
    
    it('should fetch authentication options with username', async () => {
      const result = await webauthnService.getAuthenticationOptions('testuser');
      
      expect(api.post).toHaveBeenCalledWith('/webauthn/authenticate/options', {
        username: 'testuser'
      });
    });
  });
  
  describe('authenticateWithPasskey', () => {
    it('should complete the full authentication flow', async () => {
      const result = await webauthnService.authenticateWithPasskey(undefined, 'test@example.com');
      
      // Should have called getAuthenticationOptions
      expect(api.post).toHaveBeenCalledWith('/webauthn/authenticate/options', {
        email: 'test@example.com'
      });
      
      // Should have called startAuthentication with options
      expect(browser.startAuthentication).toHaveBeenCalledWith(mockOptions);
      
      // Should have called verify with response
      expect(api.post).toHaveBeenCalledWith('/webauthn/authenticate/verify', {
        credential: mockCredentialResponse,
        user_id: 1
      });
      
      // Should return server response with token
      expect(result).toEqual({
        access_token: 'test_token',
        token_type: 'bearer',
        user_id: 1,
        username: 'testuser'
      });
    });
    
    it('should handle browser errors during authentication', async () => {
      (browser.startAuthentication as jest.Mock).mockRejectedValueOnce(new Error('User cancelled'));
      
      await expect(webauthnService.authenticateWithPasskey('testuser')).rejects.toThrow('User cancelled');
    });
  });
  
  describe('getCredentials', () => {
    it('should fetch credentials from the server', async () => {
      const result = await webauthnService.getCredentials();
      
      expect(api.get).toHaveBeenCalledWith('/webauthn/credentials');
      
      expect(result).toEqual([
        { id: 1, name: 'Test Passkey 1', created_at: '2023-01-01T00:00:00' },
        { id: 2, name: 'Test Passkey 2', created_at: '2023-01-02T00:00:00' },
      ]);
    });
  });
  
  describe('deleteCredential', () => {
    it('should delete a credential', async () => {
      const result = await webauthnService.deleteCredential(1);
      
      expect(api.delete).toHaveBeenCalledWith('/webauthn/credentials/1');
      
      expect(result).toEqual({ message: 'Credential deleted successfully' });
    });
  });
  
  describe('browser support checks', () => {
    it('should check if WebAuthn is supported', () => {
      // Test when supported
      expect(webauthnService.isWebAuthnSupported()).toBe(true);
      
      // Test when not supported
      delete (global as any).PublicKeyCredential;
      expect(webauthnService.isWebAuthnSupported()).toBe(false);
    });
    
    it('should check if platform authenticator is available', async () => {
      // Restore PublicKeyCredential if previous test deleted it
      if (!(global as any).PublicKeyCredential) {
        global.PublicKeyCredential = function () {} as any;
        global.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable = jest.fn().mockResolvedValue(true);
      }
      
      const result = await webauthnService.isPlatformAuthenticatorAvailable();
      
      expect(global.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable).toHaveBeenCalled();
      expect(result).toBe(true);
    });
    
    it('should return false for platform authenticator check when WebAuthn not supported', async () => {
      delete (global as any).PublicKeyCredential;
      
      const result = await webauthnService.isPlatformAuthenticatorAvailable();
      
      expect(result).toBe(false);
    });
  });
}); 