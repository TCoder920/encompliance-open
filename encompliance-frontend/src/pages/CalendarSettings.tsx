/**
 * Description: Calendar settings page for the EnCompliance application.
 * Purpose: Provides interface for users to connect, manage, and sync external calendars
 * (Google Calendar and Apple Calendar). Implements OAuth flows and connection management.
 * Educational Note: Demonstrates secure external service integration with proper error handling.
 */

import React, { useState, useEffect } from 'react';
import { Calendar, Settings, RotateCw, Trash2, Plus, AlertCircle, CheckCircle, Info } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { getTierFromSubscriptionStatus } from '../utils/tiers';
import { canAccessFeature } from '../utils/accessControl';
import AppleCalendarGuide from '../components/AppleCalendarGuide';

interface CalendarConnection {
  id: number;
  provider: string;
  calendar_id: string;
  calendar_name: string;
  is_active: boolean;
  sync_enabled: boolean;
  token_expires_at: string | null;
  created_at: string;
}

interface SyncStatus {
  connection_id: number;
  provider: string;
  calendar_name: string;
  sync_enabled: boolean;
  synced_events_count: number;
  last_sync: string | null;
}

const CalendarSettings: React.FC = () => {
  const { user } = useAuth();
  const [connections, setConnections] = useState<CalendarConnection[]>([]);
  const [syncStatus, setSyncStatus] = useState<SyncStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showAppleModal, setShowAppleModal] = useState(false);
  const [showAppleGuide, setShowAppleGuide] = useState(false);
  const [appleCredentials, setAppleCredentials] = useState({
    username: '',
    password: '',
    server_url: ''
  });
  const [syncingConnections, setSyncingConnections] = useState<Set<number>>(new Set());

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);

  useEffect(() => {
    if (canAccessFeature(userTier, 'calendar')) {
      fetchConnections();
      fetchSyncStatus();
    } else {
      setIsLoading(false);
    }
  }, [userTier]);

  const fetchConnections = async () => {
    try {
      const response = await api.get('/calendar/integration/connections');
      setConnections(response.data);
      setError(null);
    } catch (err: any) {
      setError('Failed to load calendar connections');
      console.error('Error fetching connections:', err);
    }
  };

  const fetchSyncStatus = async () => {
    try {
      const response = await api.get('/calendar/integration/sync/status');
      setSyncStatus(response.data.connections);
      setError(null);
    } catch (err: any) {
      setError('Failed to load sync status');
      console.error('Error fetching sync status:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleConnect = async () => {
    try {
      setError(null);
      const response = await api.get('/calendar/integration/google/auth');
      
      // Open Google OAuth in popup window
      const popup = window.open(
        response.data.authorization_url,
        'google-oauth',
        'width=500,height=600,scrollbars=yes,resizable=yes'
      );

      // Listen for OAuth completion
      const checkClosed = setInterval(() => {
        if (popup?.closed) {
          clearInterval(checkClosed);
          // Refresh connections after OAuth completion
          setTimeout(() => {
            fetchConnections();
            fetchSyncStatus();
          }, 1000);
        }
      }, 1000);

    } catch (err: any) {
      setError('Failed to initiate Google Calendar connection');
      console.error('Error connecting to Google Calendar:', err);
    }
  };

  const handleAppleConnect = async () => {
    try {
      setError(null);
      const response = await api.post('/calendar/integration/apple/connect', appleCredentials);
      
      if (response.data.success) {
        setSuccess('Successfully connected to Apple Calendar');
        setShowAppleModal(false);
        setAppleCredentials({ username: '', password: '', server_url: '' });
        fetchConnections();
        fetchSyncStatus();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to connect to Apple Calendar');
      console.error('Error connecting to Apple Calendar:', err);
    }
  };

  const handleDisconnect = async (connectionId: number) => {
    try {
      setError(null);
      await api.delete(`/calendar/integration/connections/${connectionId}`);
      setSuccess('Calendar disconnected successfully');
      fetchConnections();
      fetchSyncStatus();
    } catch (err: any) {
      setError('Failed to disconnect calendar');
      console.error('Error disconnecting calendar:', err);
    }
  };

  const handleSync = async (connectionId: number, provider: string) => {
    try {
      setError(null);
      setSyncingConnections(prev => new Set(prev).add(connectionId));
      
      const response = await api.post(`/calendar/integration/sync/${provider}?connection_id=${connectionId}`);
      
      if (response.data.success) {
        setSuccess(`Sync completed: ${response.data.imported_count} imported, ${response.data.exported_count} exported`);
        fetchSyncStatus();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to sync calendar');
      console.error('Error syncing calendar:', err);
    } finally {
      setSyncingConnections(prev => {
        const newSet = new Set(prev);
        newSet.delete(connectionId);
        return newSet;
      });
    }
  };

  const handleImport = async (connectionId: number, provider: string) => {
    try {
      setError(null);
      setSyncingConnections(prev => new Set(prev).add(connectionId));
      
      const response = await api.post(`/calendar/integration/import/${provider}?connection_id=${connectionId}`);
      
      if (response.data.success) {
        setSuccess(`Successfully imported ${response.data.imported_count} events`);
        fetchSyncStatus();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import events');
      console.error('Error importing events:', err);
    } finally {
      setSyncingConnections(prev => {
        const newSet = new Set(prev);
        newSet.delete(connectionId);
        return newSet;
      });
    }
  };

  // Check if user can access calendar feature
  if (!canAccessFeature(userTier, 'calendar')) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-gray-50 dark:bg-gray-800 rounded-lg shadow">
        <Calendar className="w-16 h-16 text-gray-400 mb-4" />
        <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">Calendar Integration</h2>
        <p className="text-gray-600 dark:text-gray-300 mb-6 text-center">
          Calendar integration is available for Pro and Enterprise subscribers.
          Connect your Google and Apple calendars to sync events seamlessly.
        </p>
        <button 
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          onClick={() => window.location.href = '/userSettings?tab=subscription'}
        >
          Upgrade Now
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Calendar Settings</h1>
        <p className="text-gray-600 dark:text-gray-300">
          Connect and manage your external calendar integrations
        </p>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center">
          <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center">
          <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
          <span className="text-green-700 dark:text-green-300">{success}</span>
        </div>
      )}

      {/* Connect New Calendar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <Plus className="w-5 h-5 mr-2" />
          Connect Calendar
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={handleGoogleConnect}
            className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 transition-colors"
          >
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center mx-auto mb-2">
                <Calendar className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-medium text-gray-900 dark:text-white">Google Calendar</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">Connect via OAuth</p>
            </div>
          </button>

          <button
            onClick={() => setShowAppleModal(true)}
            className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 transition-colors relative"
          >
            <div className="text-center">
              <div className="w-12 h-12 bg-gray-800 rounded-lg flex items-center justify-center mx-auto mb-2">
                <Calendar className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-medium text-gray-900 dark:text-white">Apple Calendar</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">Connect via CalDAV</p>
            </div>
            <div
              onClick={(e) => {
                e.stopPropagation();
                setShowAppleGuide(true);
              }}
              className="absolute top-2 right-2 w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors cursor-pointer"
              title="Setup Guide"
            >
              <Info className="w-4 h-4" />
            </div>
          </button>
        </div>
      </div>

      {/* Connected Calendars */}
      {isLoading ? (
        <div className="flex justify-center items-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
              <Settings className="w-5 h-5 mr-2" />
              Connected Calendars
            </h2>
          </div>

          {connections.length === 0 ? (
            <div className="p-6 text-center text-gray-500 dark:text-gray-400">
              No calendars connected yet. Connect your first calendar above.
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {connections.map((connection) => {
                const status = syncStatus.find(s => s.connection_id === connection.id);
                const isSyncing = syncingConnections.has(connection.id);
                
                return (
                  <div key={connection.id} className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center mr-4 ${
                          connection.provider === 'google' ? 'bg-blue-500' : 'bg-gray-800'
                        }`}>
                          <Calendar className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h3 className="font-medium text-gray-900 dark:text-white">
                            {connection.calendar_name}
                          </h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                            {connection.provider} Calendar
                          </p>
                          {status && (
                            <p className="text-xs text-gray-400 dark:text-gray-500">
                              {status.synced_events_count} events synced
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleImport(connection.id, connection.provider)}
                          disabled={isSyncing}
                          className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isSyncing ? 'Importing...' : 'Import'}
                        </button>
                        
                        <button
                          onClick={() => handleSync(connection.id, connection.provider)}
                          disabled={isSyncing}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                        >
                          <RotateCw className={`w-4 h-4 mr-1 ${isSyncing ? 'animate-spin' : ''}`} />
                          {isSyncing ? 'Syncing...' : 'Sync'}
                        </button>
                        
                        <button
                          onClick={() => handleDisconnect(connection.id)}
                          className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 flex items-center"
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Disconnect
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Apple Calendar Modal */}
      {showAppleModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
              Connect Apple Calendar
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Apple ID / Username
                </label>
                <input
                  type="text"
                  value={appleCredentials.username}
                  onChange={(e) => setAppleCredentials({...appleCredentials, username: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  placeholder="developer@example.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  App-Specific Password
                </label>
                <input
                  type="password"
                  value={appleCredentials.password}
                  onChange={(e) => setAppleCredentials({...appleCredentials, password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  placeholder="xxxx-xxxx-xxxx-xxxx"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  CalDAV Server (Optional)
                </label>
                <input
                  type="text"
                  value={appleCredentials.server_url}
                  onChange={(e) => setAppleCredentials({...appleCredentials, server_url: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  placeholder="https://caldav.icloud.com (default)"
                />
              </div>
              
              <div className="text-xs text-gray-500 dark:text-gray-400">
                <p>You'll need to generate an app-specific password in your Apple ID settings.</p>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-2">
              <button
                onClick={() => setShowAppleModal(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleAppleConnect}
                disabled={!appleCredentials.username || !appleCredentials.password}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Connect
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Apple Calendar Setup Guide */}
      <AppleCalendarGuide 
        isOpen={showAppleGuide} 
        onClose={() => setShowAppleGuide(false)} 
      />
    </div>
  );
};

export default CalendarSettings; 