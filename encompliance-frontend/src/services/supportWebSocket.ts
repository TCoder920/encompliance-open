/*
  Description: WebSocket service for real-time support ticket notifications.
  Purpose: Manages WebSocket connections to receive real-time updates about ticket changes.
*/

import { isJwtExpired } from '../utils/jwt';

export interface TicketEvent {
  type: string;
  data: any;
  timestamp: string;
}

type EventCallback = (event: TicketEvent) => void;

class SupportWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private eventCallbacks: Map<string, Set<EventCallback>> = new Map();
  private isConnecting = false;
  private shouldReconnect = true;
  private pingInterval: number | null = null;
  private authFailureHandler: (() => void) | null = null;

  connect(token: string): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    if (!token || isJwtExpired(token, 5_000)) {
      console.warn('Support WebSocket token missing or expired; skipping connection.');
      this.handleAuthFailure();
      return;
    }

    this.isConnecting = true;
    this.shouldReconnect = true;

    const supportApiBase = import.meta.env.VITE_SUPPORT_API_BASE_URL || 'http://localhost:6050';
    
    let wsUrl: string;
    if (supportApiBase.startsWith('/') || supportApiBase === '') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      // Use the proxy path directly, but we need to match how the backend expects it.
      // If we use /api, vite proxies it to backend.
      // If backend is at /, then /api -> /.
      // But typically backend is at /api/v1.
      // If we request /api/v1/..., proxy strips /api -> /v1/...
      // So we should construct wsUrl to point to root, and append /api if needed?
      // Actually, if we use just /api as base, and then append /v1/..., we get /api/v1/...
      // The previous code did /api and then appended /api/v1... which was wrong.
      wsUrl = `${protocol}//${host}`; 
    } else {
      wsUrl = supportApiBase.replace('http://', 'ws://').replace('https://', 'wss://');
    }

    const url = `${wsUrl}/api/v1/support/ws/notifications?token=${token}`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('WebSocket connected for support notifications');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.startPingInterval();
      };

      this.ws.onmessage = (event) => {
        try {
          const data: TicketEvent = JSON.parse(event.data);
          
          // Handle heartbeat/pong
          if (data.type === 'heartbeat' || data.type === 'pong') {
            return;
          }

          // Notify all callbacks for this event type
          const callbacks = this.eventCallbacks.get(data.type);
          if (callbacks) {
            callbacks.forEach(callback => callback(data));
          }

          // Also notify 'all' callbacks
          const allCallbacks = this.eventCallbacks.get('all');
          if (allCallbacks) {
            allCallbacks.forEach(callback => callback(data));
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
      };

      this.ws.onclose = (event: CloseEvent) => {
        console.log('WebSocket disconnected');
        this.isConnecting = false;
        this.stopPingInterval();

        if (event.code === 1008 || event.code === 4003) {
          console.warn('Support WebSocket closed due to authentication failure.');
          this.handleAuthFailure();
          return;
        }

        if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          setTimeout(() => this.connect(token), delay);
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      this.isConnecting = false;
    }
  }

  setAuthFailureHandler(handler: () => void) {
    this.authFailureHandler = handler;
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.eventCallbacks.clear();
  }

  subscribe(eventType: string, callback: EventCallback): () => void {
    if (!this.eventCallbacks.has(eventType)) {
      this.eventCallbacks.set(eventType, new Set());
    }
    this.eventCallbacks.get(eventType)!.add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.eventCallbacks.get(eventType);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.eventCallbacks.delete(eventType);
        }
      }
    };
  }

  private startPingInterval(): void {
    this.stopPingInterval();
    this.pingInterval = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Send ping every 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval !== null) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private handleAuthFailure(): void {
    this.shouldReconnect = false;
    this.reconnectAttempts = 0;
    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
      this.ws.close();
    }
    if (this.authFailureHandler) {
      this.authFailureHandler();
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  get isConnectingState(): boolean {
    return this.isConnecting;
  }
}

// Singleton instance
export const supportWebSocketService = new SupportWebSocketService();

