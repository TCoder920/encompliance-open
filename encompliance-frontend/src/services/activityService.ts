/*
Description: Frontend service for activity calendar operations.
Purpose: Provides functions to interact with the activity-related API endpoints, such as fetching activities and signing up.
*/
import api from './api';

export interface Activity {
  id: string;
  title: string;
  description?: string;
  start: string;
  end: string;
  location?: string;
  allDay: boolean;
  activityCategory?: string;
  requiresSignup: boolean;
  maxParticipants?: number;
  currentParticipants: number;
  signupDeadline?: string;
  activityStatus: string;
  facilityId: number;
  createdByAdmin: boolean;
}

export interface ActivitySignupData {
  calendar_event_id: string;
  notes?: string;
}

/**
 * Fetches all activities for the user's facility.
 * @returns A promise that resolves to an array of activities.
 */
export const getActivities = async (): Promise<Activity[]> => {
  const response = await api.get('/activities/');
  return response.data;
};

/**
 * Submits a signup request for a specific activity.
 * @param signupData - The data required for the signup, including the event ID and optional notes.
 * @returns A promise that resolves to the created signup data.
 */
export const signupForActivity = async (signupData: ActivitySignupData): Promise<any> => {
  const response = await api.post('/activity-signups/', signupData);
  return response.data;
}; 