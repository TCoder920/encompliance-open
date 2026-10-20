/*
  Description: Notification service for handling notification operations on the frontend.
  Purpose: Provides methods for interacting with the notifications API endpoints.
*/
import api from './api'; // Import the shared api instance

// Define notification type enum
export enum NotificationType {
  NOTE = 'note',
  DOCUMENT = 'document',
  SYSTEM = 'system',
  SECURITY = 'security',
  SUBSCRIPTION = 'subscription'
}

// Define notification priority enum
export enum NotificationPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
}

// Define types
export interface Notification {
  id: number;
  title: string;
  message: string;
  type: NotificationType;
  priority: NotificationPriority;
  is_read: boolean;
  created_at: string;
  user_id: number;
  related_id?: number | null;
  related_type?: string | null;
  action_url?: string | null;
}

export interface NotificationUpdate {
  is_read?: boolean;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
}

export interface NotificationsFilter {
  skip?: number;
  limit?: number;
  unread_only?: boolean;
}

// Base path for notification endpoints, relative to the shared api instance's baseURL
const NOTIFICATIONS_BASE_PATH = '/notifications';

// Notification service class
export class NotificationService {
  private static instance: NotificationService;

  private constructor() {}

  // Singleton pattern
  public static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  // Get all notifications with filtering and pagination
  public async getNotifications(filters: NotificationsFilter = {}): Promise<NotificationListResponse> {
    const {
      skip = 0,
      limit = 20,
      unread_only = false,
    } = filters;

    // Construct query parameters
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    params.append('unread_only', unread_only.toString());
    
    const response = await api.get<NotificationListResponse>(`${NOTIFICATIONS_BASE_PATH}?${params.toString()}`);
    return response.data;
  }

  // Get unread notification count
  public async getUnreadCount(): Promise<number> {
    const response = await api.get<number>(`${NOTIFICATIONS_BASE_PATH}/unread-count`);
    return response.data;
  }

  // Get a specific notification by ID
  public async getNotification(id: number): Promise<Notification> {
    const response = await api.get<Notification>(`${NOTIFICATIONS_BASE_PATH}/${id}`);
    return response.data;
  }

  // Mark a notification as read
  public async markAsRead(id: number): Promise<Notification> {
    const response = await api.post<Notification>(`${NOTIFICATIONS_BASE_PATH}/${id}/mark-as-read`, {});
    return response.data;
  }

  // Mark all notifications as read
  public async markAllAsRead(): Promise<number> {
    const response = await api.post<number>(`${NOTIFICATIONS_BASE_PATH}/mark-all-as-read`, {});
    return response.data;
  }

  // Delete a notification
  public async deleteNotification(id: number): Promise<void> {
    await api.delete(`${NOTIFICATIONS_BASE_PATH}/${id}`);
  }

  // Delete all notifications
  public async deleteAllNotifications(): Promise<void> {
    await api.delete(NOTIFICATIONS_BASE_PATH);
  }
}

// Export a singleton instance
export const notificationService = NotificationService.getInstance(); 