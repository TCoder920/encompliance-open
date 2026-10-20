/*
Description: Assignment Completion Modal for operational task assignments
Purpose: Handles task completion with photo requirements, notes, and status updates
Key functionalities: Photo upload validation, completion notes, status confirmation

Educational Note: Modal pattern with React Portal for overlay UI
Reference: React documentation on portals, form validation patterns
*/

import React, { useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, Clock, Camera, MessageSquare } from 'lucide-react';
import AssignmentImageUploader, { AssignmentImage } from './AssignmentImageUploader';
import { operationalTaskService, TaskAssignment } from '../services/operationalTaskService';

interface AssignmentCompletionModalProps {
  assignment: TaskAssignment;
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

const AssignmentCompletionModal: React.FC<AssignmentCompletionModalProps> = ({
  assignment,
  isOpen,
  onClose,
  onComplete
}) => {
  const [completionNotes, setCompletionNotes] = useState('');
  const [timeSpent, setTimeSpent] = useState(assignment.time_spent_minutes || 0);
  const [images, setImages] = useState<AssignmentImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existingImages, setExistingImages] = useState<AssignmentImage[]>([]);

  // Get photo requirements from task data
  const task = assignment.operational_task;
  const requiresBeforePhotos = task?.requires_before_photos || false;
  const requiresAfterPhotos = task?.requires_after_photos || false;
  const photoInstructions = task?.photo_instructions;

  useEffect(() => {
    if (isOpen && assignment.id) {
      loadExistingImages();
    }
  }, [isOpen, assignment.id]);

  const loadExistingImages = async () => {
    try {
      const response = await fetch(`/api/assignments/${assignment.id}/images`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'x-token': localStorage.getItem('token') || ''
        }
      });

      if (response.ok) {
        const imageData = await response.json();
        const formattedImages: AssignmentImage[] = imageData.map((img: any) => ({
          id: img.id,
          url: `/api/assignments/${assignment.id}/images/${img.id}`,
          type: img.image_type,
          label: img.label
        }));
        setExistingImages(formattedImages);
        setImages(formattedImages);
      }
    } catch (error) {
      console.error('Error loading existing images:', error);
    }
  };

  const validatePhotoRequirements = (): boolean => {
    const beforePhotos = images.filter(img => img.type === 'before' && !img.uploading && !img.error);
    const afterPhotos = images.filter(img => img.type === 'after' && !img.uploading && !img.error);

    const beforeMet = !requiresBeforePhotos || beforePhotos.length > 0;
    const afterMet = !requiresAfterPhotos || afterPhotos.length > 0;

    return beforeMet && afterMet;
  };

  const handleComplete = async () => {
    if (!validatePhotoRequirements()) {
      setError('Please upload required photos before completing the assignment.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await operationalTaskService.updateAssignment(assignment.id, {
        status: 'completed',
        completed_date: new Date().toISOString(),
        progress_percentage: 100,
        completion_notes: completionNotes || undefined,
        time_spent_minutes: timeSpent
      });

      onComplete();
      onClose();
    } catch (err) {
      setError('Failed to complete assignment. Please try again.');
      console.error('Assignment completion error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (minutes: number): string => {
    if (minutes < 60) {
      return `${minutes} minutes`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Complete Assignment
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {task?.title || `Assignment #${assignment.id}`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {error && (
            <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
                <p className="text-red-700 dark:text-red-300">{error}</p>
              </div>
            </div>
          )}

          {/* Assignment Info */}
          <div className="mb-6 bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Priority:</span>
                <span className="ml-2 font-medium capitalize">{assignment.priority}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Due Date:</span>
                <span className="ml-2 font-medium">
                  {new Date(assignment.due_date).toLocaleDateString()}
                </span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Progress:</span>
                <span className="ml-2 font-medium">{assignment.progress_percentage}%</span>
              </div>
            </div>
          </div>

          {/* Time Spent */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <Clock className="h-4 w-4 inline mr-1" />
              Time Spent (minutes)
            </label>
            <input
              type="number"
              min="0"
              value={timeSpent}
              onChange={(e) => setTimeSpent(parseInt(e.target.value) || 0)}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Enter time spent in minutes"
            />
            {timeSpent > 0 && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {formatDuration(timeSpent)}
              </p>
            )}
          </div>

          {/* Completion Notes */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <MessageSquare className="h-4 w-4 inline mr-1" />
              Completion Notes (optional)
            </label>
            <textarea
              value={completionNotes}
              onChange={(e) => setCompletionNotes(e.target.value)}
              rows={4}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Add any notes about the completed work, challenges encountered, or observations..."
            />
          </div>

          {/* Photo Upload Section */}
          {(requiresBeforePhotos || requiresAfterPhotos) && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Camera className="h-5 w-5 mr-2" />
                Photo Documentation
              </h3>
              
              <AssignmentImageUploader
                assignmentId={assignment.id}
                requiresBeforePhotos={requiresBeforePhotos}
                requiresAfterPhotos={requiresAfterPhotos}
                photoInstructions={photoInstructions}
                existingImages={existingImages}
                onImagesChange={setImages}
                onUploadComplete={() => {
                  // Refresh existing images after upload
                  loadExistingImages();
                }}
              />
            </div>
          )}

          {/* Special Instructions */}
          {task?.special_instructions && (
            <div className="mb-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h4 className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">
                Special Instructions
              </h4>
              <p className="text-sm text-blue-700 dark:text-blue-400">
                {task.special_instructions}
              </p>
            </div>
          )}

          {/* Required Equipment */}
          {task?.required_equipment && task.required_equipment.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Required Equipment Used:
              </h4>
              <div className="flex flex-wrap gap-2">
                {task.required_equipment.map((item: string, index: number) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center">
            {(requiresBeforePhotos || requiresAfterPhotos) ? (
              validatePhotoRequirements() ? (
                <div className="flex items-center text-green-600">
                  <CheckCircle className="h-4 w-4 mr-1" />
                  <span className="text-sm">Ready to complete</span>
                </div>
              ) : (
                <div className="flex items-center text-yellow-600">
                  <AlertCircle className="h-4 w-4 mr-1" />
                  <span className="text-sm">Photo requirements pending</span>
                </div>
              )
            ) : (
              <div className="flex items-center text-green-600">
                <CheckCircle className="h-4 w-4 mr-1" />
                <span className="text-sm">Ready to complete</span>
              </div>
            )}
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleComplete}
              disabled={loading || !validatePhotoRequirements()}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                  Completing...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Complete Assignment
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssignmentCompletionModal; 