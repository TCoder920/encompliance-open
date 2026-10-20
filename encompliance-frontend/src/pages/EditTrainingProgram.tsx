import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  ArrowLeft, 
  Save, 
  BookOpen, 
  Clock, 
  Award,
  AlertTriangle,
  AlertCircle
} from 'lucide-react';
import { trainingProgramService } from '../services/trainingService';
import type { TrainingProgram } from '../services/trainingService';

interface EditProgramFormData {
  title: string;
  description: string;
  category: string;
  delivery_method: 'online' | 'in_person' | 'hybrid';
  estimated_duration_minutes: number;
  is_mandatory: boolean;
  requires_certification: boolean;
  certification_valid_months: number;
  prerequisites: string;
  is_active: boolean;
}

const EditTrainingProgramPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [program, setProgram] = useState<TrainingProgram | null>(null);
  const [formData, setFormData] = useState<EditProgramFormData>({
    title: '',
    description: '',
    category: '',
    delivery_method: 'online',
    estimated_duration_minutes: 0,
    is_mandatory: false,
    requires_certification: false,
    certification_valid_months: 12,
    prerequisites: '',
    is_active: true
  });

  useEffect(() => {
    if (id) {
      loadProgram(parseInt(id));
    }
  }, [id]);

  const loadProgram = async (programId: number) => {
    try {
      setLoadingData(true);
      const data = await trainingProgramService.getById(programId);
      setProgram(data);
      
      // Populate form with existing data
      setFormData({
        title: data.title,
        description: data.description || '',
        category: data.category || '',
        delivery_method: data.delivery_method,
        estimated_duration_minutes: data.estimated_duration_minutes || 0,
        is_mandatory: data.is_mandatory,
        requires_certification: data.requires_certification,
        certification_valid_months: data.certification_valid_months || 12,
        prerequisites: data.prerequisites || '',
        is_active: data.is_active
      });
    } catch (error) {
      console.error('Error loading program:', error);
      setErrors({ 
        submit: 'Failed to load program. Please try again.' 
      });
    } finally {
      setLoadingData(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' 
        ? (e.target as HTMLInputElement).checked
        : type === 'number' 
          ? parseInt(value) || 0
          : value
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
    if (!formData.title.trim()) {
      newErrors.title = 'Program title is required';
    }
    
    if (!formData.delivery_method) {
      newErrors.delivery_method = 'Delivery method is required';
    }

    // Duration validation
    if (formData.estimated_duration_minutes <= 0) {
      newErrors.estimated_duration_minutes = 'Duration must be greater than 0';
    }

    // Certification validation
    if (formData.requires_certification && formData.certification_valid_months <= 0) {
      newErrors.certification_valid_months = 'Certification validity must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm() || !program) {
      return;
    }

    setLoading(true);
    try {
      await trainingProgramService.update(program.id, {
        title: formData.title,
        description: formData.description || undefined,
        category: formData.category || undefined,
        delivery_method: formData.delivery_method,
        estimated_duration_minutes: formData.estimated_duration_minutes,
        is_mandatory: formData.is_mandatory,
        requires_certification: formData.requires_certification,
        certification_valid_months: formData.requires_certification ? formData.certification_valid_months : undefined,
        prerequisites: formData.prerequisites || undefined,
        is_active: formData.is_active
      });

      // Success - navigate back to program details
      navigate(`/training/programs/${program.id}`, { 
        state: { 
          message: `Training program "${formData.title}" has been updated successfully.` 
        }
      });
    } catch (error) {
      console.error('Error updating program:', error);
      setErrors({ 
        submit: error instanceof Error ? error.message : 'Failed to update program. Please try again.' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (program) {
      navigate(`/training/programs/${program.id}`);
    } else {
      navigate('/training/programs');
    }
  };

  if (loadingData) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="ml-4 text-gray-600 dark:text-gray-400">Loading program...</p>
        </div>
      </div>
    );
  }

  if (!program) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <AlertCircle className="h-12 w-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">Program Not Found</h3>
          <p className="text-red-700 dark:text-red-300 mb-4">The training program you're trying to edit could not be found.</p>
          <button
            onClick={() => navigate('/training/programs')}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Back to Programs
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
          onClick={() => navigate(`/training/programs/${program.id}`)}
          className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Program Details
        </button>
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
          Edit Training Program
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Update program details and settings
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

          {/* Basic Information */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <BookOpen className="h-5 w-5 mr-2" />
              Basic Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Program Title *
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white ${
                    errors.title ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                  placeholder="Enter program title"
                />
                {errors.title && (
                  <p className="text-red-500 text-xs mt-1">{errors.title}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Category
                </label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">Select a category</option>
                  <option value="Safety">Safety</option>
                  <option value="Compliance">Compliance</option>
                  <option value="Technical">Technical</option>
                  <option value="Administrative">Administrative</option>
                  <option value="Leadership">Leadership</option>
                  <option value="Customer Service">Customer Service</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Delivery Method *
                </label>
                <select
                  name="delivery_method"
                  value={formData.delivery_method}
                  onChange={handleInputChange}
                  className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white ${
                    errors.delivery_method ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                >
                  <option value="online">Online</option>
                  <option value="in_person">In-Person</option>
                  <option value="hybrid">Hybrid</option>
                </select>
                {errors.delivery_method && (
                  <p className="text-red-500 text-xs mt-1">{errors.delivery_method}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Estimated Duration (minutes) *
                </label>
                <div className="relative">
                  <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <input
                    type="number"
                    name="estimated_duration_minutes"
                    value={formData.estimated_duration_minutes}
                    onChange={handleInputChange}
                    min="1"
                    className={`w-full border rounded-lg pl-10 pr-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white ${
                      errors.estimated_duration_minutes ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                    }`}
                    placeholder="60"
                  />
                </div>
                {errors.estimated_duration_minutes && (
                  <p className="text-red-500 text-xs mt-1">{errors.estimated_duration_minutes}</p>
                )}
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows={4}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Describe the training program objectives and content"
            />
          </div>

          {/* Prerequisites */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Prerequisites
            </label>
            <textarea
              name="prerequisites"
              value={formData.prerequisites}
              onChange={handleInputChange}
              rows={3}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="List any prerequisites or requirements for this training"
            />
          </div>

          {/* Settings */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Program Settings
            </h3>
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="is_mandatory"
                  checked={formData.is_mandatory}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  This is a mandatory training program
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="requires_certification"
                  checked={formData.requires_certification}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  This program requires certification
                </label>
              </div>

              {formData.requires_certification && (
                <div className="ml-6">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Certification Valid For (months) *
                  </label>
                  <div className="relative max-w-xs">
                    <Award className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <input
                      type="number"
                      name="certification_valid_months"
                      value={formData.certification_valid_months}
                      onChange={handleInputChange}
                      min="1"
                      className={`w-full border rounded-lg pl-10 pr-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white ${
                        errors.certification_valid_months ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                      }`}
                      placeholder="12"
                    />
                  </div>
                  {errors.certification_valid_months && (
                    <p className="text-red-500 text-xs mt-1">{errors.certification_valid_months}</p>
                  )}
                </div>
              )}

              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Program is active and available for assignment
                </label>
              </div>
            </div>
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
                  Update Program
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditTrainingProgramPage; 