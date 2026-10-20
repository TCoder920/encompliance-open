/**
 * Description: Production-ready real-time synchronization service for team member accounts.
 * Purpose: Establishes SSE connections to backend and handles real-time data synchronization
 * when facility administrators make changes affecting team member accounts.
 * 
 * Educational Note: Server-Sent Events (SSE) provide a robust way to handle real-time
 * updates over HTTP. This implementation includes automatic reconnection, error handling,
 * and fallback polling to ensure reliable synchronization.
 * Reference: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
 */

import api from './api';

interface SyncEvent {
  type: string;
  data: Record<string, any>;
  timestamp: string;
  facility_id: number;
}

interface SyncData {
  type: string;
  data: Record<string, any>;
  timestamp: string;
  facility_id: number;
}

type SyncEventCallback = (event: SyncEvent) => void;

class RealtimeSyncService {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private isConnected = false;
  private callbacks = new Map<string, Set<SyncEventCallback>>();
  private pollingInterval: number | null = null;
  private lastEventTimestamp: string | null = null;
  private userId: number | null = null;
  private facilityId: number | null = null;
  private isTeamMember = false;

  /**
   * Description: Initializes real-time sync for team members.
   * Purpose: Establishes SSE connection and sets up event handling for data synchronization.
   */
  public initialize(userId: number, facilityId: number, userRole: string): void {
    if (userRole !== 'team_member') {
      console.log('Real-time sync only available for team members');
      return;
    }

    this.userId = userId;
    this.facilityId = facilityId;
    this.isTeamMember = true;

    console.log(`Initializing real-time sync for team member ${userId} in facility ${facilityId}`);
    
    // Start SSE connection
    this.connect();
    
    // Set up polling fallback
    this.startPollingFallback();
  }

  /**
   * Description: Establishes SSE connection to backend sync endpoint.
   * Purpose: Creates persistent connection for real-time event streaming.
   */
  private connect(): void {
    if (!this.userId || !this.facilityId || !this.isTeamMember) {
      console.error('Cannot connect: missing user/facility info or not a team member');
      return;
    }

    try {
      // Close existing connection
      this.disconnect();

      const token = localStorage.getItem('access_token');
      if (!token) {
        console.error('No access token available for SSE connection');
        this.startPollingFallback();
        return;
      }

      // Create SSE connection with authentication
      const baseURL = import.meta.env.VITE_API_BASE_URL ?? import.meta.env.VITE_API_URL ?? '';
      const url = `${baseURL}/api/v1/sync/events?user_id=${this.userId}&facility_id=${this.facilityId}&token=${encodeURIComponent(token)}`;
      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        console.log('SSE connection established');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000; // Reset delay
        
        // Stop polling fallback when SSE is working
        this.stopPollingFallback();
      };

      this.eventSource.onmessage = (event) => {
        try {
          const syncEvent: SyncEvent = JSON.parse(event.data);
          this.handleSyncEvent(syncEvent);
          this.lastEventTimestamp = syncEvent.timestamp;
        } catch (error) {
          console.error('Failed to parse SSE event:', error);
        }
      };

      this.eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        this.isConnected = false;
        
        // Close and retry connection
        this.disconnect();
        this.scheduleReconnect();
      };

    } catch (error) {
      console.error('Failed to establish SSE connection:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Description: Handles incoming sync events from SSE stream.
   * Purpose: Processes sync events and notifies registered callbacks.
   */
  private handleSyncEvent(event: SyncEvent): void {
    console.log('Received sync event:', event.type, event.data);

    // Handle different event types
    switch (event.type) {
      case 'connection':
        console.log('SSE connection confirmed');
        break;
      case 'heartbeat':
        console.log('SSE heartbeat received');
        break;
      case 'account_update':
        this.notifyCallbacks('account_update', event);
        break;
      case 'document_update':
        this.notifyCallbacks('document_update', event);
        break;
      case 'calendar_update':
        this.notifyCallbacks('calendar_update', event);
        break;
      case 'training_update':
        this.notifyCallbacks('training_update', event);
        break;
      default:
        console.log(`Unknown sync event type: ${event.type}`);
    }
  }

  /**
   * Description: Notifies registered callbacks for specific event types.
   * Purpose: Allows components to react to specific types of sync events.
   */
  private notifyCallbacks(eventType: string, event: SyncEvent): void {
    const callbacks = this.callbacks.get(eventType);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(event);
        } catch (error) {
          console.error(`Error in sync callback for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Description: Schedules reconnection attempt with exponential backoff.
   * Purpose: Implements robust reconnection strategy for resilient sync.
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached, falling back to polling');
      this.startPollingFallback();
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);
    
    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (!this.isConnected) {
        this.connect();
      }
    }, delay);
  }

  /**
   * Description: Starts polling fallback when SSE connection fails.
   * Purpose: Ensures data synchronization continues even when SSE is unavailable.
   */
  private startPollingFallback(): void {
    if (this.pollingInterval || !this.userId || !this.facilityId) {
      return;
    }

    console.log('Starting polling fallback for sync updates');
    
    this.pollingInterval = window.setInterval(async () => {
      try {
        await this.pollForUpdates();
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 10000); // Poll every 10 seconds
  }

  /**
   * Description: Stops polling fallback when SSE connection is restored.
   * Purpose: Prevents duplicate updates when SSE is working properly.
   */
  private stopPollingFallback(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
      console.log('Stopped polling fallback');
    }
  }

  /**
   * Description: Polls backend for missed sync updates.
   * Purpose: Catches up on events when SSE connection was down.
   */
  private async pollForUpdates(): Promise<void> {
    if (!this.userId || !this.facilityId) return;

    try {
      const since = this.lastEventTimestamp ? new Date(this.lastEventTimestamp).getTime() : undefined;
      const params = new URLSearchParams({
        user_id: this.userId.toString(),
        facility_id: this.facilityId.toString()
      });
      
      if (since) {
        params.append('since', since.toString());
      }

             const response = await api.get(`/api/v1/sync/updates?${params.toString()}`);
       const { updates } = response.data;

      if (updates && updates.length > 0) {
        console.log(`Polled ${updates.length} sync updates`);
        updates.forEach((update: any) => {
          this.handleSyncEvent({
            type: update.event_type,
            data: update.event_data,
            timestamp: update.created_at,
            facility_id: update.facility_id
          });
        });

        // Update last event timestamp
        const latestUpdate = updates[0];
        if (latestUpdate) {
          this.lastEventTimestamp = latestUpdate.created_at;
        }
      }
    } catch (error) {
      console.error('Failed to poll for updates:', error);
    }
  }

  /**
   * Description: Subscribes to specific sync event types.
   * Purpose: Allows components to register for relevant sync events.
   */
  public subscribe(eventType: string, callback: SyncEventCallback): () => void {
    if (!this.callbacks.has(eventType)) {
      this.callbacks.set(eventType, new Set());
    }
    
    this.callbacks.get(eventType)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.callbacks.get(eventType);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.callbacks.delete(eventType);
        }
      }
    };
  }

  /**
   * Description: Forces synchronization of specific data types.
   * Purpose: Allows manual sync when needed, using production endpoints.
   */
  public async forceSync(dataType: string): Promise<void> {
    if (!this.facilityId) {
      throw new Error('No facility ID available for sync');
    }

    try {
      let endpoint = '';
      switch (dataType) {
        case 'account':
          endpoint = `/api/v1/sync/account-overview?facility_id=${this.facilityId}`;
          break;
        case 'documents':
          endpoint = `/api/v1/sync/document-library?facility_id=${this.facilityId}`;
          break;
        case 'calendar':
          endpoint = `/api/v1/sync/calendar-events?facility_id=${this.facilityId}`;
          break;
        case 'training':
          endpoint = `/api/v1/sync/training-data?facility_id=${this.facilityId}`;
          break;
        default:
          throw new Error(`Unknown sync data type: ${dataType}`);
      }

             const response = await api.get(endpoint);
       const syncData: SyncData = response.data;
      
      // Trigger sync event with fetched data
      this.handleSyncEvent({
        type: syncData.type,
        data: syncData.data,
        timestamp: syncData.timestamp,
        facility_id: syncData.facility_id
      });

      console.log(`Force sync completed for ${dataType}`);
    } catch (error) {
      console.error(`Force sync failed for ${dataType}:`, error);
      throw error;
    }
  }

  /**
   * Description: Disconnects SSE connection and cleans up resources.
   * Purpose: Proper cleanup when sync is no longer needed.
   */
  public disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    
    this.stopPollingFallback();
    this.isConnected = false;
    console.log('Disconnected from real-time sync');
  }

  /**
   * Description: Gets current connection status.
   * Purpose: Allows components to check sync connectivity.
   */
  public getConnectionStatus(): { connected: boolean; reconnectAttempts: number } {
    return {
      connected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts
    };
  }

  /**
   * Description: Manually triggers reconnection attempt.
   * Purpose: Allows components to force reconnection when needed.
   */
  public reconnect(): void {
    console.log('Manual reconnection triggered');
    this.reconnectAttempts = 0; // Reset attempts for manual reconnection
    this.disconnect();
    this.connect();
  }

  /**
   * Description: Cleans up all resources and subscriptions.
   * Purpose: Complete cleanup when service is destroyed.
   */
  public destroy(): void {
    this.disconnect();
    this.callbacks.clear();
    this.userId = null;
    this.facilityId = null;
    this.isTeamMember = false;
    this.lastEventTimestamp = null;
  }
}

// Export singleton instance
export const realtimeSyncService = new RealtimeSyncService(); 