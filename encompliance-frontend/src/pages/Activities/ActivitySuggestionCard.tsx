/*
Description: A card component for displaying activity suggestions with voting and admin controls.
Purpose: Shows activity suggestion details, vote counts, and provides voting/admin action buttons.
*/
import React, { useState } from 'react';
import { 
  ThumbsUp, 
  ThumbsDown, 
  Calendar, 
  Clock, 
  Users, 
  Star, 
  Edit, 
  Trash2, 
  Check, 
  X, 
  MessageSquare,
  User
} from 'lucide-react';
import { 
  ActivitySuggestion, 
  voteOnSuggestion, 
  removeVoteFromSuggestion,
  reviewActivitySuggestion,
  deleteActivitySuggestion
} from '../../services/activitySuggestionService';

interface ActivitySuggestionCardProps {
  suggestion: ActivitySuggestion;
  currentUserId?: number;
  isAdmin?: boolean;
  onUpdate: () => void;
  onEdit?: (suggestion: ActivitySuggestion) => void;
}

const ActivitySuggestionCard: React.FC<ActivitySuggestionCardProps> = ({
  suggestion,
  currentUserId,
  isAdmin = false,
  onUpdate,
  onEdit
}) => {
  const [isVoting, setIsVoting] = useState(false);
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [reviewStatus, setReviewStatus] = useState<'approved' | 'rejected'>('approved');
  const [adminResponse, setAdminResponse] = useState('');
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'rejected': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'implemented': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const handleVote = async (voteType: 'upvote' | 'downvote') => {
    if (isVoting || suggestion.status !== 'pending') return;
    
    setIsVoting(true);
    try {
      if (suggestion.user_vote === voteType) {
        // Remove vote if clicking the same vote type
        await removeVoteFromSuggestion(suggestion.id);
      } else {
        // Add or change vote
        await voteOnSuggestion(suggestion.id, voteType);
      }
      onUpdate();
    } catch (error) {
      console.error('Failed to vote:', error);
    } finally {
      setIsVoting(false);
    }
  };

  const handleReview = async () => {
    if (isSubmittingReview) return;
    
    setIsSubmittingReview(true);
    try {
      await reviewActivitySuggestion(suggestion.id, {
        status: reviewStatus,
        admin_response: adminResponse || undefined
      });
      setShowAdminPanel(false);
      setAdminResponse('');
      onUpdate();
    } catch (error) {
      console.error('Failed to review suggestion:', error);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this suggestion?')) {
      try {
        await deleteActivitySuggestion(suggestion.id);
        onUpdate();
      } catch (error) {
        console.error('Failed to delete suggestion:', error);
      }
    }
  };

  const canEdit = currentUserId === suggestion.suggested_by_user_id || isAdmin;
  const canVote = suggestion.status === 'pending' && currentUserId !== suggestion.suggested_by_user_id;
  const canReview = isAdmin;

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger if clicking on buttons or interactive elements
    if ((e.target as HTMLElement).closest('button, textarea, input')) {
      return;
    }
    
    if (isAdmin) {
      setShowAdminPanel(!showAdminPanel);
    }
  };

  return (
    <div 
      className={`bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700 transition-all duration-200 ${
        isAdmin ? 'cursor-pointer hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-600' : ''
      }`}
      onClick={handleCardClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {suggestion.title}
          </h3>
          <div className="flex items-center space-x-2 mt-1">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(suggestion.status)}`}>
              {suggestion.status.charAt(0).toUpperCase() + suggestion.status.slice(1)}
            </span>
            {suggestion.category && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {suggestion.category}
              </span>
            )}
          </div>
        </div>
        
        {/* Action buttons */}
        <div className="flex items-center space-x-2">
          {canEdit && onEdit && (
            <button
              onClick={() => onEdit(suggestion)}
              className="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              title="Edit suggestion"
            >
              <Edit className="h-4 w-4" />
            </button>
          )}
          {canEdit && (
            <button
              onClick={handleDelete}
              className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
              title="Delete suggestion"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Description */}
      {suggestion.description && (
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          {suggestion.description}
        </p>
      )}

      {/* Details */}
      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400 mb-4">
        {suggestion.suggested_date && (
          <span className="flex items-center">
            <Calendar className="h-4 w-4 mr-1" />
            {formatDate(suggestion.suggested_date)}
          </span>
        )}
        {suggestion.estimated_duration_minutes && (
          <span className="flex items-center">
            <Clock className="h-4 w-4 mr-1" />
            {suggestion.estimated_duration_minutes} min
          </span>
        )}
        <span className="flex items-center">
          <User className="h-4 w-4 mr-1" />
          Suggested by {suggestion.suggested_by_user?.full_name || 'Anonymous'}
        </span>
      </div>

      {/* Admin response */}
      {suggestion.admin_response && (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 mb-4">
          <div className="flex items-center mb-2">
            <MessageSquare className="h-4 w-4 mr-2 text-gray-500" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Admin Response
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {suggestion.admin_response}
          </p>
          {suggestion.reviewed_by_admin && (
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
              By {suggestion.reviewed_by_admin.full_name} on {formatDate(suggestion.reviewed_at)}
            </p>
          )}
        </div>
      )}

      {/* Voting section */}
      {suggestion.status === 'pending' && (
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => handleVote('upvote')}
              disabled={isVoting || !canVote}
              className={`flex items-center space-x-1 px-3 py-1 rounded-lg transition-colors ${
                suggestion.user_vote === 'upvote'
                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                  : 'text-gray-500 hover:bg-green-50 hover:text-green-600 dark:hover:bg-green-900 dark:hover:text-green-400'
              } ${!canVote ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <ThumbsUp className="h-4 w-4" />
              <span>{suggestion.upvote_count || 0}</span>
            </button>
            
            <button
              onClick={() => handleVote('downvote')}
              disabled={isVoting || !canVote}
              className={`flex items-center space-x-1 px-3 py-1 rounded-lg transition-colors ${
                suggestion.user_vote === 'downvote'
                  ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                  : 'text-gray-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900 dark:hover:text-red-400'
              } ${!canVote ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <ThumbsDown className="h-4 w-4" />
              <span>{suggestion.downvote_count || 0}</span>
            </button>
          </div>

          <div className="text-sm text-gray-500 dark:text-gray-400">
            {suggestion.total_votes || 0} total votes
          </div>
        </div>
      )}

      {/* Admin Panel */}
      {showAdminPanel && isAdmin && (
        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900 dark:text-white flex items-center">
              <Star className="h-4 w-4 mr-2 text-blue-600" />
              Admin Controls
            </h4>
            <button
              onClick={() => setShowAdminPanel(false)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            {onEdit && (
              <button
                onClick={() => onEdit(suggestion)}
                className="flex items-center justify-center space-x-2 px-3 py-2 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
              >
                <Edit className="h-4 w-4" />
                <span>Edit</span>
              </button>
            )}
            
            <button
              onClick={handleDelete}
              className="flex items-center justify-center space-x-2 px-3 py-2 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-200 dark:hover:bg-red-800 transition-colors"
            >
              <Trash2 className="h-4 w-4" />
              <span>Delete</span>
            </button>
          </div>

          {/* Review Section */}
          <div className="border-t border-blue-200 dark:border-blue-800 pt-4">
            <h5 className="font-medium text-gray-900 dark:text-white mb-3">Review Suggestion</h5>
            
            <div className="flex space-x-3 mb-3">
              <button
                onClick={() => setReviewStatus('approved')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  reviewStatus === 'approved'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 ring-2 ring-green-500'
                    : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-green-50 dark:hover:bg-green-900/30'
                }`}
              >
                <Check className="h-4 w-4" />
                <span>Approve</span>
              </button>
              
              <button
                onClick={() => setReviewStatus('rejected')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  reviewStatus === 'rejected'
                    ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300 ring-2 ring-red-500'
                    : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/30'
                }`}
              >
                <X className="h-4 w-4" />
                <span>Reject</span>
              </button>
            </div>

            <textarea
              value={adminResponse}
              onChange={(e) => setAdminResponse(e.target.value)}
              placeholder="Add your feedback or comments (optional)..."
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
            />

            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => {
                  setShowAdminPanel(false);
                  setAdminResponse('');
                }}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleReview}
                disabled={isSubmittingReview}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isSubmittingReview ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4" />
                    <span>Submit Review</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivitySuggestionCard; 