import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Save, 
  Calendar, 
  User, 
  BookOpen, 
  AlertTriangle,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import { trainingAssignmentService, trainingProgramService, staffMemberService } from '../services/trainingService';
import type { TrainingProgram, StaffMember } from '../services/trainingService';

interface AssignmentFormData {
  training_program_id: number | '';
  staff_member_id: number | '';
  due_date: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assignment_notes: string;
  training_url: string;
}

const CreateAssignmentPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [programs, setPrograms] = useState<TrainingProgram[]>([]);
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [formData, setFormData] = useState<AssignmentFormData>({
    training_program_id: '',
    staff_member_id: '',
    due_date: '',
    priority: 'medium',
    assignment_notes: '',
    training_url: ''
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoadingData(true);
      const [programsResponse, staffResponse] = await Promise.all([
        trainingProgramService.getAll({ is_active: true }),
        staffMemberService.getAll({ status: 'active' })
      ]);
      
      setPrograms(programsResponse.programs);
      setStaff(staffResponse.staff_members);
    } catch (error) {
      console.error('Error loading data:', error);
      setErrors({ 
        submit: 'Failed to load programs and staff. Please refresh the page.' 
      });
    } finally {
      setLoadingData(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'training_program_id' || name === 'staff_member_id' 
        ? (value === '' ? '' : parseInt(value)) 
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
    if (!formData.training_program_id) {
      newErrors.training_program_id = 'Training program is required';
    }
    if (!formData.staff_member_id) {
      newErrors.staff_member_id = 'Staff member is required';
    }
    if (!formData.due_date) {
      newErrors.due_date = 'Due date is required';
    } else {
      // Check if due date is in the future
      const dueDate = new Date(formData.due_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (dueDate < today) {
        newErrors.due_date = 'Due date must be today or in the future';
      }
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
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      await trainingAssignmentService.create({
        training_program_id: formData.training_program_id as number,
        staff_member_id: formData.staff_member_id as number,
        due_date: formData.due_date,
        priority: formData.priority,
        assignment_notes: formData.assignment_notes || undefined,
        training_url: formData.training_url || undefined
      });

      // Success - navigate back to assignments
      const selectedProgram = programs.find(p => p.id === formData.training_program_id);
      const selectedStaff = staff.find(s => s.id === formData.staff_member_id);
      
      navigate('/training/assignments', { 
        state: { 
          message: `Training assignment created successfully for ${selectedStaff?.first_name} ${selectedStaff?.last_name} - ${selectedProgram?.title}` 
        }
      });
    } catch (error) {
      console.error('Error creating assignment:', error);
      setErrors({ 
        submit: error instanceof Error ? error.message : 'Failed to create assignment. Please try again.' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/training/assignments');
  };

  if (loadingData) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="ml-4 text-gray-600 dark:text-gray-400">Loading programs and staff...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/training/assignments')}
          className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Training Assignments
        </button>
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
          Create Training Assignment
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Assign training programs to staff members with due dates and priorities
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
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <BookOpen className="h-5 w-5 mr-2" />
              Assignment Details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Training Program *
                </label>
                <select
                  name="training_program_id"
                  value={formData.training_program_id}
                  onChange={handleInputChange}
                  className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white ${
                    errors.training_program_id ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                >
                  <option value="">Select a training program</option>
                  {programs.map((program) => (
                    <option key={program.id} value={program.id}>
                      {program.title} {program.is_mandatory && '(Mandatory)'}
                    </option>
                  ))}
                </select>
                {errors.training_program_id && (
                  <p className="text-red-500 text-xs mt-1">{errors.training_program_id}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Staff Member *
                </label>
                <select
                  name="staff_member_id"
                  value={formData.staff_member_id}
                  onChange={handleInputChange}
                  className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white ${
                    errors.staff_member_id ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                >
                  <option value="">Select a staff member</option>
                  {staff.map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.first_name} {member.last_name} ({member.department || 'No Department'})
                    </option>
                  ))}
                </select>
                {errors.staff_member_id && (
                  <p className="text-red-500 text-xs mt-1">{errors.staff_member_id}</p>
                )}
              </div>

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
                    min={new Date().toISOString().split('T')[0]}
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
            </div>
          </div>

          {/* Assignment Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Assignment Notes (Optional)
            </label>
            <textarea
              name="assignment_notes"
              value={formData.assignment_notes}
              onChange={handleInputChange}
              rows={3}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Enter any additional notes or instructions for this assignment"
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
                  Creating...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Create Assignment
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateAssignmentPage; 