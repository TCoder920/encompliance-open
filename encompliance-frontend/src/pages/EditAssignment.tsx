import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  ArrowLeft, 
  Save, 
  Calendar, 
  AlertTriangle,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import { trainingAssignmentService } from '../services/trainingService';
import type { TrainingAssignment } from '../services/trainingService';

interface EditAssignmentFormData {
  due_date: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'assigned' | 'in_progress' | 'completed' | 'overdue' | 'cancelled';
  progress_percentage: number;
  assignment_notes: string;
  completion_notes: string;
  training_url: string;
}

const EditAssignmentPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [assignment, setAssignment] = useState<TrainingAssignment | null>(null);
  const [formData, setFormData] = useState<EditAssignmentFormData>({
    due_date: '',
    priority: 'medium',
    status: 'assigned',
    progress_percentage: 0,
    assignment_notes: '',
    completion_notes: '',
    training_url: ''
  });

  useEffect(() => {
    if (id) {
      loadAssignment(parseInt(id));
    }
  }, [id]);

  const loadAssignment = async (assignmentId: number) => {
    try {
      setLoadingData(true);
      const data = await trainingAssignmentService.getById(assignmentId);
      setAssignment(data);
      
      // Populate form with existing data
      setFormData({
        due_date: data.due_date.split('T')[0], // Convert to YYYY-MM-DD format
        priority: data.priority,
        status: data.status,
        progress_percentage: data.progress_percentage,
        assignment_notes: data.assignment_notes || '',
        completion_notes: data.completion_notes || '',
        training_url: data.training_url || ''
      });
    } catch (error) {
      console.error('Error loading assignment:', error);
      setErrors({ 
        submit: 'Failed to load assignment. Please try again.' 
      });
    } finally {
      setLoadingData(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'progress_percentage' ? parseInt(value) || 0 : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Required fields
    if (!formData.due_date) {
      newErrors.due_date = 'Due date is required';
    }

    // Progress percentage validation
    if (formData.progress_percentage < 0 || formData.progress_percentage > 100) {
      newErrors.progress_percentage = 'Progress must be between 0 and 100';
    }

    // Optional URL validation - only validate if not empty
    if (formData.training_url && formData.training_url.trim()) {
      const urlPattern = /^(https?:\/\/|\/)/i;
      if (!urlPattern.test(formData.training_url.trim())) {
        newErrors.training_url = 'Please enter a valid URL (starting with http://, https://, or /)';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm() || !assignment) {
      return;
    }

    setLoading(true);
    try {
      await trainingAssignmentService.update(assignment.id, {
        due_date: formData.due_date,
        priority: formData.priority,
        status: formData.status,
        progress_percentage: formData.progress_percentage,
        assignment_notes: formData.assignment_notes || undefined,
        completion_notes: formData.completion_notes || undefined,
        training_url: formData.training_url || undefined
      });

      // Success - navigate back to assignment details
      navigate(`/training/assignments/${assignment.id}`, { 
        state: { 
          message: `Assignment #${assignment.id} has been updated successfully.` 
        }
      });
    } catch (error) {
      console.error('Error updating assignment:', error);
      setErrors({ 
        submit: error instanceof Error ? error.message : 'Failed to update assignment. Please try again.' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (assignment) {
      navigate(`/training/assignments/${assignment.id}`);
    } else {
      navigate('/training/assignments');
    }
  };

  if (loadingData) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="ml-4 text-gray-600 dark:text-gray-400">Loading assignment...</p>
        </div>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <AlertCircle className="h-12 w-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">Assignment Not Found</h3>
          <p className="text-red-700 dark:text-red-300 mb-4">The assignment you're trying to edit could not be found.</p>
          <button
            onClick={() => navigate('/training/assignments')}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Back to Assignments
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(`/training/assignments/${assignment.id}`)}
          className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Assignment Details
        </button>
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
          Edit Assignment #{assignment.id}
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Update assignment details, progress, and status
        </p>
      </div>

      {/* Form */}
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Error Alert */}
          {errors.submit && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mr-3" />
                <p className="text-sm text-red-700 dark:text-red-300">{errors.submit}</p>
              </div>
            </div>
          )}

          {/* Assignment Details */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Assignment Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Due Date *
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <input
                    type="date"
                    name="due_date"
                    value={formData.due_date}
                    onChange={handleInputChange}
                    className={`w-full border rounded-lg pl-10 pr-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white ${
                      errors.due_date ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                    }`}
                  />
                </div>
                {errors.due_date && (
                  <p className="text-red-500 text-xs mt-1">{errors.due_date}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Priority *
                </label>
                <div className="relative">
                  <AlertTriangle className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <select
                    name="priority"
                    value={formData.priority}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg pl-10 pr-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Status *
                </label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="assigned">Assigned</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="overdue">Overdue</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Progress Percentage *
                </label>
                <input
                  type="number"
                  name="progress_percentage"
                  value={formData.progress_percentage}
                  onChange={handleInputChange}
                  min="0"
                  max="100"
                  className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white ${
                    errors.progress_percentage ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                  placeholder="0-100"
                />
                {errors.progress_percentage && (
                  <p className="text-red-500 text-xs mt-1">{errors.progress_percentage}</p>
                )}
              </div>
            </div>
          </div>

          {/* Assignment Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Assignment Notes
            </label>
            <textarea
              name="assignment_notes"
              value={formData.assignment_notes}
              onChange={handleInputChange}
              rows={3}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Enter any assignment notes or instructions"
            />
          </div>

          {/* Completion Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Completion Notes
            </label>
            <textarea
              name="completion_notes"
              value={formData.completion_notes}
              onChange={handleInputChange}
              rows={3}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Enter any completion notes or feedback"
            />
          </div>

          {/* Training URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Training URL (Optional)
            </label>
            <div className="relative">
              <ExternalLink className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <input
                type="text"
                name="training_url"
                value={formData.training_url}
                onChange={handleInputChange}
                className={`w-full border rounded-lg pl-10 pr-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white ${
                  errors.training_url ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                }`}
                placeholder="https://example.com/training-content or /internal/route"
              />
            </div>
            {errors.training_url && (
              <p className="text-red-500 text-xs mt-1">{errors.training_url}</p>
            )}
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Specify a custom URL where the training content is located. If not provided, the system will use the training program's materials.
            </p>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={handleCancel}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Updating...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Update Assignment
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditAssignmentPage; 