/**
 * Description: Notification settings service for the frontend.
 * Purpose: Handles notification preferences and settings management.
 * Educational Note: Provides interface for user notification preference management.
 */

import api from './api';

export interface NotificationSettings {
  id?: number;
  user_id?: number;
  
  // In-app notification settings
  in_app_calendar_enabled: boolean;
  in_app_calendar_reminders_enabled: boolean;
  in_app_note_notifications_enabled: boolean;
  in_app_message_notifications_enabled: boolean;
  in_app_regulatory_updates_enabled: boolean;
  in_app_system_notifications_enabled: boolean;
  
  // Email notification settings
  email_calendar_enabled: boolean;
  email_calendar_reminders_enabled: boolean;
  email_note_notifications_enabled: boolean;
  email_message_notifications_enabled: boolean;
  email_regulatory_updates_enabled: boolean;
  email_system_notifications_enabled: boolean;
  
  // Push notification settings
  push_enabled: boolean;
  push_calendar_enabled: boolean;
  push_calendar_reminders_enabled: boolean;
  push_note_notifications_enabled: boolean;
  push_message_notifications_enabled: boolean;
  push_regulatory_updates_enabled: boolean;
  push_system_notifications_enabled: boolean;
  
  // Calendar-specific settings
  calendar_reminder_offset_minutes: number;
  
  // Email digest settings
  email_digest_frequency: string;
  
  created_at?: string;
  updated_at?: string;
}

export interface NotificationSettingsUpdate {
  // In-app notification settings
  in_app_calendar_enabled?: boolean;
  in_app_calendar_reminders_enabled?: boolean;
  in_app_note_notifications_enabled?: boolean;
  in_app_message_notifications_enabled?: boolean;
  in_app_regulatory_updates_enabled?: boolean;
  in_app_system_notifications_enabled?: boolean;
  
  // Email notification settings
  email_calendar_enabled?: boolean;
  email_calendar_reminders_enabled?: boolean;
  email_note_notifications_enabled?: boolean;
  email_message_notifications_enabled?: boolean;
  email_regulatory_updates_enabled?: boolean;
  email_system_notifications_enabled?: boolean;
  
  // Push notification settings
  push_enabled?: boolean;
  push_calendar_enabled?: boolean;
  push_calendar_reminders_enabled?: boolean;
  push_note_notifications_enabled?: boolean;
  push_message_notifications_enabled?: boolean;
  push_regulatory_updates_enabled?: boolean;
  push_system_notifications_enabled?: boolean;
  
  // Calendar-specific settings
  calendar_reminder_offset_minutes?: number;
  
  // Email digest settings
  email_digest_frequency?: string;
}

class NotificationSettingsService {
  /**
   * Get user notification settings
   */
  async getSettings(): Promise<NotificationSettings> {
    try {
      const response = await api.get('/notifications/settings');
      return response.data;
    } catch (error) {
      console.error('Error fetching notification settings:', error);
      throw error;
    }
  }

  /**
   * Update user notification settings
   */
  async updateSettings(settings: NotificationSettingsUpdate): Promise<NotificationSettings> {
    try {
      const response = await api.put('/notifications/settings', settings);
      return response.data;
    } catch (error) {
      console.error('Error updating notification settings:', error);
      throw error;
    }
  }

  /**
   * Get default notification settings
   */
  getDefaultSettings(): NotificationSettings {
    return {
      // In-app notification settings
      in_app_calendar_enabled: true,
      in_app_calendar_reminders_enabled: true,
      in_app_note_notifications_enabled: true,
      in_app_message_notifications_enabled: true,
      in_app_regulatory_updates_enabled: true,
      in_app_system_notifications_enabled: true,
      
      // Email notification settings
      email_calendar_enabled: false,
      email_calendar_reminders_enabled: true,
      email_note_notifications_enabled: false,
      email_message_notifications_enabled: true,
      email_regulatory_updates_enabled: true,
      email_system_notifications_enabled: true,
      
      // Push notification settings
      push_enabled: false,
      push_calendar_enabled: true,
      push_calendar_reminders_enabled: true,
      push_note_notifications_enabled: false,
      push_message_notifications_enabled: true,
      push_regulatory_updates_enabled: true,
      push_system_notifications_enabled: true,
      
      // Calendar-specific settings
      calendar_reminder_offset_minutes: 15,
      
      // Email digest settings
      email_digest_frequency: 'daily'
    };
  }

  /**
   * Enable push notifications
   */
  async enablePushNotifications(): Promise<NotificationSettings> {
    return this.updateSettings({ push_enabled: true });
  }

  /**
   * Disable push notifications
   */
  async disablePushNotifications(): Promise<NotificationSettings> {
    return this.updateSettings({ push_enabled: false });
  }

  /**
   * Update calendar reminder offset
   */
  async updateCalendarReminderOffset(minutes: number): Promise<NotificationSettings> {
    return this.updateSettings({ calendar_reminder_offset_minutes: minutes });
  }

  /**
   * Update email digest frequency
   */
  async updateEmailDigestFrequency(frequency: string): Promise<NotificationSettings> {
    return this.updateSettings({ email_digest_frequency: frequency });
  }

  /**
   * Enable all notifications for a specific type
   */
  async enableNotificationType(type: 'calendar' | 'notes' | 'messages' | 'regulatory' | 'system'): Promise<NotificationSettings> {
    const updates: NotificationSettingsUpdate = {};
    
    switch (type) {
      case 'calendar':
        updates.in_app_calendar_enabled = true;
        updates.email_calendar_enabled = true;
        updates.push_calendar_enabled = true;
        break;
      case 'notes':
        updates.in_app_note_notifications_enabled = true;
        updates.email_note_notifications_enabled = true;
        updates.push_note_notifications_enabled = true;
        break;
      case 'messages':
        updates.in_app_message_notifications_enabled = true;
        updates.email_message_notifications_enabled = true;
        updates.push_message_notifications_enabled = true;
        break;
      case 'regulatory':
        updates.in_app_regulatory_updates_enabled = true;
        updates.email_regulatory_updates_enabled = true;
        updates.push_regulatory_updates_enabled = true;
        break;
      case 'system':
        updates.in_app_system_notifications_enabled = true;
        updates.email_system_notifications_enabled = true;
        updates.push_system_notifications_enabled = true;
        break;
    }
    
    return this.updateSettings(updates);
  }

  /**
   * Disable all notifications for a specific type
   */
  async disableNotificationType(type: 'calendar' | 'notes' | 'messages' | 'regulatory' | 'system'): Promise<NotificationSettings> {
    const updates: NotificationSettingsUpdate = {};
    
    switch (type) {
      case 'calendar':
        updates.in_app_calendar_enabled = false;
        updates.email_calendar_enabled = false;
        updates.push_calendar_enabled = false;
        break;
      case 'notes':
        updates.in_app_note_notifications_enabled = false;
        updates.email_note_notifications_enabled = false;
        updates.push_note_notifications_enabled = false;
        break;
      case 'messages':
        updates.in_app_message_notifications_enabled = false;
        updates.email_message_notifications_enabled = false;
        updates.push_message_notifications_enabled = false;
        break;
      case 'regulatory':
        updates.in_app_regulatory_updates_enabled = false;
        updates.email_regulatory_updates_enabled = false;
        updates.push_regulatory_updates_enabled = false;
        break;
      case 'system':
        updates.in_app_system_notifications_enabled = false;
        updates.email_system_notifications_enabled = false;
        updates.push_system_notifications_enabled = false;
        break;
    }
    
    return this.updateSettings(updates);
  }
}

export const notificationSettingsService = new NotificationSettingsService(); 