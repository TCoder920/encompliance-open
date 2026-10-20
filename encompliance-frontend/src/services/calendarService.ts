/*
Description: Frontend service for calendar operations.
Purpose: Provides functions to interact with calendar-related API endpoints.
*/
import api from './api';

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  description?: string;
  location?: string;
  allDay: boolean;
}

export interface CalendarEventUpdate {
  title?: string;
  start?: string;
  end?: string;
  description?: string;
  location?: string;
  allDay?: boolean;
}

/**
 * Updates an existing calendar event.
 * @param eventId - The ID of the event to update.
 * @param updateData - The data to update.
 * @returns A promise that resolves to the updated event data.
 */
export const updateCalendarEvent = async (eventId: string, updateData: CalendarEventUpdate): Promise<CalendarEvent> => {
  const response = await api.put(`/calendar/events/${eventId}`, updateData);
  return response.data;
};

/**
 * Deletes a calendar event.
 * @param eventId - The ID of the event to delete.
 * @returns A promise that resolves when the event is deleted.
 */
export const deleteCalendarEvent = async (eventId: string): Promise<void> => {
  await api.delete(`/calendar/events/${eventId}`);
};

/**
 * Creates a new calendar event.
 * @param eventData - The event data to create.
 * @returns A promise that resolves to the created event data.
 */
export const createCalendarEvent = async (eventData: Omit<CalendarEvent, 'id'>): Promise<CalendarEvent> => {
  const response = await api.post('/calendar/events', eventData);
  return response.data;
}; 