/*
Description: Frontend service for activity suggestion operations.
Purpose: Provides functions to submit and retrieve user-created activity suggestions to/from the backend.
*/
import api from './api';

export interface ActivitySuggestionData {
  title: string;
  description?: string;
  category?: string;
  location?: string;
  suggested_date?: string;
  estimated_duration_minutes?: number;
}

export interface ActivitySuggestionUpdate {
  title?: string;
  description?: string;
  category?: string;
  suggested_date?: string;
  estimated_duration_minutes?: number;
}

export interface ActivitySuggestionReview {
  status: 'pending' | 'approved' | 'rejected' | 'implemented';
  admin_response?: string;
}

export interface ActivitySuggestionVote {
  id: number;
  suggestion_id: number;
  user_id: number;
  vote_type: string;
  created_at: string;
  user?: {
    full_name: string;
  };
}

export interface UserSummary {
  id: number;
  full_name: string;
  email: string;
}

export interface ActivitySuggestion {
  id: number;
  title: string;
  description?: string;
  category?: string;
  location?: string;
  suggested_date?: string;
  estimated_duration_minutes?: number;
  status: string;
  admin_response?: string;
  reviewed_by_admin_id?: number;
  reviewed_at?: string;
  created_at: string;
  updated_at: string;
  facility_id: number;
  suggested_by_user_id: number;
  suggested_by_user?: UserSummary;
  reviewed_by_admin?: UserSummary;
  votes?: ActivitySuggestionVote[];
  upvote_count?: number;
  downvote_count?: number;
  total_votes?: number;
  user_vote?: string;
}

/**
 * Submits a new activity suggestion.
 * @param suggestionData - The data for the new suggestion.
 * @returns A promise that resolves to the created suggestion data.
 */
export const submitActivitySuggestion = async (suggestionData: ActivitySuggestionData): Promise<ActivitySuggestion> => {
  const response = await api.post('/activity-suggestions/', suggestionData);
  return response.data;
};

/**
 * Updates an existing activity suggestion.
 * @param suggestionId - The ID of the suggestion to update.
 * @param updateData - The data to update.
 * @returns A promise that resolves to the updated suggestion data.
 */
export const updateActivitySuggestion = async (suggestionId: number, updateData: ActivitySuggestionUpdate): Promise<ActivitySuggestion> => {
  const response = await api.put(`/activity-suggestions/${suggestionId}`, updateData);
  return response.data;
};

/**
 * Deletes an activity suggestion.
 * @param suggestionId - The ID of the suggestion to delete.
 * @returns A promise that resolves when the suggestion is deleted.
 */
export const deleteActivitySuggestion = async (suggestionId: number): Promise<void> => {
  await api.delete(`/activity-suggestions/${suggestionId}`);
};

/**
 * Reviews (approves/rejects) an activity suggestion (admin only).
 * @param suggestionId - The ID of the suggestion to review.
 * @param reviewData - The review data including status and optional response.
 * @returns A promise that resolves to the updated suggestion data.
 */
export const reviewActivitySuggestion = async (suggestionId: number, reviewData: ActivitySuggestionReview): Promise<ActivitySuggestion> => {
  const response = await api.post(`/activity-suggestions/${suggestionId}/review`, reviewData);
  return response.data;
};

/**
 * Votes on an activity suggestion.
 * @param suggestionId - The ID of the suggestion to vote on.
 * @param voteType - The type of vote ('upvote' or 'downvote').
 * @returns A promise that resolves to the vote data.
 */
export const voteOnSuggestion = async (suggestionId: number, voteType: 'upvote' | 'downvote'): Promise<ActivitySuggestionVote> => {
  const response = await api.post(`/activity-suggestions/${suggestionId}/vote`, { vote_type: voteType });
  return response.data;
};

/**
 * Removes a vote from an activity suggestion.
 * @param suggestionId - The ID of the suggestion to remove vote from.
 * @returns A promise that resolves when the vote is removed.
 */
export const removeVoteFromSuggestion = async (suggestionId: number): Promise<void> => {
  await api.delete(`/activity-suggestions/${suggestionId}/vote`);
};

/**
 * Fetches all activity suggestions for the current user's facility.
 * Note: This endpoint requires facility admin privileges.
 * @returns A promise that resolves to an array of activity suggestions.
 */
export const getFacilitySuggestions = async (): Promise<ActivitySuggestion[]> => {
  const response = await api.get('/activity-suggestions/');
  return response.data;
};

/**
 * Fetches all activity suggestions (development endpoint).
 * @returns A promise that resolves to an array of activity suggestions.
 */
export const getAllSuggestions = async (): Promise<ActivitySuggestion[]> => {
  const response = await api.get('/activity-suggestions/all');
  return response.data;
};

/**
 * Fetches all activity suggestions submitted by the current user.
 * @returns A promise that resolves to an array of activity suggestions.
 */
export const getMySuggestions = async (): Promise<ActivitySuggestion[]> => {
  const response = await api.get('/activity-suggestions/my-suggestions');
  return response.data;
}; 