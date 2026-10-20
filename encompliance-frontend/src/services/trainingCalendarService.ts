/*
Description: Frontend service for training calendar operations
Purpose: Handle training-specific calendar API calls and data management
Key functionalities: CRUD operations for training calendar events, external sync

Educational Note: Service pattern for API communication using axios
Reference: Axios documentation for HTTP client usage
*/

import api from './api';

// Training calendar event interface
export interface TrainingCalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  description?: string;
  location?: string;
  allDay: boolean;
  eventType: 'training_assignment' | 'certification_renewal' | 'training_deadline';
  trainingProgramId?: number;
  trainingAssignmentId?: number;
  trainingCompletionId?: number;
  facilityId?: number;
  createdByAdmin: boolean;
  isEditableByUser: boolean;
}

// Training calendar settings interface
export interface TrainingCalendarSettings {
  autoCreateEvents: boolean;
  reminderDays: number[];
  certificationReminderDays: number;
  syncToExternalCalendar: boolean;
  eventVisibility: 'private' | 'shared';
}

// Simple debounce mechanism to prevent rapid API calls
const debounceTimers: { [key: string]: NodeJS.Timeout } = {};
const lastCallTimes: { [key: string]: number } = {};
const MIN_CALL_INTERVAL = 1000; // Minimum 1 second between calls

function shouldAllowCall(key: string): boolean {
  const now = Date.now();
  const lastCall = lastCallTimes[key] || 0;
  
  if (now - lastCall < MIN_CALL_INTERVAL) {
    console.warn(`Blocking rapid API call for ${key}. Last call was ${now - lastCall}ms ago.`);
    return false;
  }
  
  lastCallTimes[key] = now;
  return true;
}

// Training calendar service
export const trainingCalendarService = {
  // Get training calendar events
  getTrainingEvents: async (params?: {
    start?: string;
    end?: string;
    eventType?: string;
    trainingProgramId?: number;
    staffMemberId?: number;
  }): Promise<TrainingCalendarEvent[]> => {
    // Check if we should allow this call
    if (!shouldAllowCall('getTrainingEvents')) {
      console.log('Returning empty events array due to rapid call prevention');
      return [];
    }
    
    try {
    const response = await api.get('/calendar/events', { 
      params: { 
        ...params, 
        includeTraining: true 
      } 
    });
    
    // Filter to only training events
    return response.data.filter((event: any) => 
      ['training_assignment', 'certification_renewal', 'training_deadline'].includes(event.eventType)
    );
    } catch (error: any) {
      console.warn('Training calendar events endpoint not available:', error.message);
      // Return empty array if endpoint doesn't exist or fails
      return [];
    }
  },

  // Create training calendar event
  createTrainingEvent: async (eventData: {
    title: string;
    start: string;
    end: string;
    description?: string;
    eventType: string;
    trainingProgramId?: number;
    trainingAssignmentId?: number;
    allDay?: boolean;
  }): Promise<TrainingCalendarEvent> => {
    const response = await api.post('/calendar/events', eventData);
    return response.data;
  },

  // Update training calendar event
  updateTrainingEvent: async (eventId: string, eventData: {
    title?: string;
    start?: string;
    end?: string;
    description?: string;
    allDay?: boolean;
  }): Promise<TrainingCalendarEvent> => {
    const response = await api.put(`/calendar/events/${eventId}`, eventData);
    return response.data;
  },

  // Delete training calendar event
  deleteTrainingEvent: async (eventId: string): Promise<void> => {
    await api.delete(`/calendar/events/${eventId}`);
  },

  // Get training calendar settings
  getTrainingCalendarSettings: async (): Promise<TrainingCalendarSettings> => {
    // Check if we should allow this call
    if (!shouldAllowCall('getTrainingCalendarSettings')) {
      console.log('Returning cached default settings due to rapid call prevention');
      return {
        autoCreateEvents: true,
        reminderDays: [7, 3, 1],
        certificationReminderDays: 30,
        syncToExternalCalendar: false,
        eventVisibility: 'private'
      };
    }
    
    try {
      const response = await api.get('/calendar/settings/training');
      return response.data;
    } catch (error: any) {
      console.warn('Training calendar settings endpoint not available:', error.message);
      // Return default settings if endpoint doesn't exist or fails
      return {
        autoCreateEvents: true,
        reminderDays: [7, 3, 1],
        certificationReminderDays: 30,
        syncToExternalCalendar: false,
        eventVisibility: 'private'
      };
    }
  },

  // Update training calendar settings
  updateTrainingCalendarSettings: async (settings: Partial<TrainingCalendarSettings>): Promise<TrainingCalendarSettings> => {
    try {
    const response = await api.put('/calendar/settings/training', settings);
    return response.data;
    } catch (error: any) {
      console.warn('Training calendar settings update endpoint not available:', error.message);
      // Return merged settings with defaults if endpoint doesn't exist
      return {
        autoCreateEvents: true,
        reminderDays: [7, 3, 1],
        certificationReminderDays: 30,
        syncToExternalCalendar: false,
        eventVisibility: 'private',
        ...settings
      };
    }
  },

  // Get training assignment calendar events
  getAssignmentCalendarEvents: async (assignmentIds: number[]): Promise<TrainingCalendarEvent[]> => {
    const response = await api.post('/calendar/training/assignments', { assignmentIds });
    return response.data;
  },

  // Create calendar events for training assignment
  createAssignmentCalendarEvent: async (assignmentId: number): Promise<TrainingCalendarEvent> => {
    const response = await api.post(`/calendar/training/assignments/${assignmentId}/event`);
    return response.data;
  },

  // Get certification renewal events
  getCertificationRenewalEvents: async (staffMemberId?: number): Promise<TrainingCalendarEvent[]> => {
    const params = staffMemberId ? { staffMemberId } : {};
    const response = await api.get('/calendar/training/certifications', { params });
    return response.data;
  },

  // Create certification renewal reminder
  createCertificationRenewalEvent: async (completionId: number): Promise<TrainingCalendarEvent> => {
    const response = await api.post(`/calendar/training/certifications/${completionId}/renewal`);
    return response.data;
  },

  // Sync training events to external calendar
  syncTrainingEventsToExternal: async (provider: 'google' | 'apple', eventIds: string[]): Promise<{
    synced: number;
    failed: number;
    errors: string[];
  }> => {
    const response = await api.post('/calendar/sync/training', {
      provider,
      eventIds
    });
    return response.data;
  },

  // Get training calendar statistics
  getTrainingCalendarStats: async (): Promise<{
    totalEvents: number;
    upcomingAssignments: number;
    overdueTasks: number;
    certificationRenewals: number;
  }> => {
    // Check if we should allow this call
    if (!shouldAllowCall('getTrainingCalendarStats')) {
      console.log('Returning cached default stats due to rapid call prevention');
      return {
        totalEvents: 0,
        upcomingAssignments: 0,
        overdueTasks: 0,
        certificationRenewals: 0
      };
    }
    
    try {
    const response = await api.get('/calendar/training/stats');
    return response.data;
    } catch (error: any) {
      console.warn('Training calendar stats endpoint not available:', error.message);
      // Return default stats if endpoint doesn't exist or fails
      return {
        totalEvents: 0,
        upcomingAssignments: 0,
        overdueTasks: 0,
        certificationRenewals: 0
      };
    }
  },

  // Bulk create training deadline reminders
  createBulkDeadlineReminders: async (assignmentIds: number[], reminderDays: number[]): Promise<TrainingCalendarEvent[]> => {
    const response = await api.post('/calendar/training/reminders/bulk', {
      assignmentIds,
      reminderDays
    });
    return response.data;
  }
}; 