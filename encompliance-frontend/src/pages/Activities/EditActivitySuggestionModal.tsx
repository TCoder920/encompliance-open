/*
Description: A modal component for editing activity suggestions.
Purpose: Allows users to edit their own activity suggestions or admins to edit any suggestion.
*/
import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { ActivitySuggestion, updateActivitySuggestion, ActivitySuggestionUpdate } from '../../services/activitySuggestionService';
import DateTimePicker from '../../components/ui/DateTimePicker';

interface EditActivitySuggestionModalProps {
  suggestion: ActivitySuggestion;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

const EditActivitySuggestionModal: React.FC<EditActivitySuggestionModalProps> = ({
  suggestion,
  isOpen,
  onClose,
  onUpdate
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [suggestedDate, setSuggestedDate] = useState('');
  const [estimatedDuration, setEstimatedDuration] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState('');

  // Initialize form with suggestion data
  useEffect(() => {
    if (suggestion) {
      setTitle(suggestion.title);
      setDescription(suggestion.description || '');
      setCategory(suggestion.category || '');
      setSuggestedDate(suggestion.suggested_date || '');
      setEstimatedDuration(suggestion.estimated_duration_minutes?.toString() || '');
    }
  }, [suggestion]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    setIsSubmitting(true);

    try {
      const updateData: ActivitySuggestionUpdate = {
        title,
        description: description || undefined,
        category: category || undefined,
        suggested_date: suggestedDate || undefined,
        estimated_duration_minutes: estimatedDuration ? parseInt(estimatedDuration) : undefined,
      };

      await updateActivitySuggestion(suggestion.id, updateData);
      setMessage('Suggestion updated successfully!');
      setTimeout(() => {
        onUpdate();
        onClose();
      }, 1000);
    } catch (error) {
      console.error('Failed to update suggestion:', error);
      setMessage('Failed to update suggestion. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setMessage('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Edit Activity Suggestion
          </h2>
          <button
            onClick={handleClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {message && (
            <div
              className={`text-center p-3 rounded-lg font-medium 
                ${message.toLowerCase().includes('success')
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'}`}
            >
              {message}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Activity Title *
            </label>
            <input
              type="text"
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What would you like to call this activity?"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Description
            </label>
            <textarea
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the activity, what it involves, and why it would be beneficial..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Category
            </label>
            <select
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">Select a category</option>
              <option value="wellness">Wellness & Health</option>
              <option value="training">Training & Education</option>
              <option value="social">Social & Team Building</option>
              <option value="recreational">Recreational</option>
              <option value="community">Community Service</option>
              <option value="professional">Professional Development</option>
              <option value="other">Other</option>
            </select>
          </div>

          <DateTimePicker
            label="Suggested Date & Time"
            value={suggestedDate}
            onChange={setSuggestedDate}
            placeholder="When would be ideal for this activity?"
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Estimated Duration (minutes)
            </label>
            <input
              type="number"
              min="15"
              max="480"
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={estimatedDuration}
              onChange={(e) => setEstimatedDuration(e.target.value)}
              placeholder="How long should this activity last?"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Updating...' : 'Update Suggestion'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditActivitySuggestionModal; 