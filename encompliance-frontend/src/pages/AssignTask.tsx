/*
  Description: Task Assignment page for assigning staff members to operational tasks
  Purpose: Allows facility administrators to assign tasks to eligible staff members with due dates and priorities
*/

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Users, 
  Calendar, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  Plus,
  X,
  User
} from 'lucide-react';
import { operationalTaskService, OperationalTask, EligibleStaffMember, CreateAssignmentData } from '../services/operationalTaskService';
import ErrorMessage from '../components/ErrorMessage';

interface AssignmentFormData {
  staff_member_ids: number[];
  due_date: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assignment_notes: string;
}

const AssignTaskPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<OperationalTask | null>(null);
  const [eligibleStaff, setEligibleStaff] = useState<EligibleStaffMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<AssignmentFormData>({
    staff_member_ids: [],
    due_date: '',
    priority: 'medium',
    assignment_notes: ''
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (id) {
      loadTaskAndEligibleStaff();
    }
  }, [id]);

  const loadTaskAndEligibleStaff = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const taskId = parseInt(id!);
      
      // Load task details and eligible staff in parallel
      const [taskResponse, eligibleStaffResponse] = await Promise.all([
        operationalTaskService.getTask(taskId),
        operationalTaskService.getEligibleStaff(taskId)
      ]);
      
      setTask(taskResponse);
      setEligibleStaff(eligibleStaffResponse.eligible_staff);
      
      // Set default due date to tomorrow
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      setFormData(prev => ({
        ...prev,
        due_date: tomorrow.toISOString().split('T')[0]
      }));
      
    } catch (err) {
      setError('Failed to load task details and eligible staff');
      console.error('Error loading task assignment data:', err);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (formData.staff_member_ids.length === 0) {
      newErrors.staff_member_ids = 'Please select at least one staff member';
    }
    
    if (!formData.due_date) {
      newErrors.due_date = 'Due date is required';
    } else {
      const dueDate = new Date(formData.due_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (dueDate < today) {
        newErrors.due_date = 'Due date cannot be in the past';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm() || !task) {
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const assignmentData: CreateAssignmentData = {
        operational_task_id: task.id,
        staff_member_ids: formData.staff_member_ids,
        due_date: formData.due_date,
        priority: formData.priority,
        assignment_notes: formData.assignment_notes || undefined
      };

      await operationalTaskService.createAssignments(assignmentData);
      
      // Navigate back to task details
      navigate(`/tasks/${id}`);
    } catch (err) {
      setError('Failed to create task assignments. Please try again.');
      console.error('Assignment creation error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleStaffSelection = useCallback((staffId: number) => {
    setFormData(prev => ({
      ...prev,
      staff_member_ids: prev.staff_member_ids.includes(staffId)
        ? prev.staff_member_ids.filter(id => id !== staffId)
        : [...prev.staff_member_ids, staffId]
    }));
    
    // Clear error when user makes selection
    if (errors.staff_member_ids) {
      setErrors(prev => ({ ...prev, staff_member_ids: '' }));
    }
  }, [errors.staff_member_ids]);

  const handleInputChange = (field: keyof AssignmentFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading task assignment...</p>
        </div>
      </div>
    );
  }

  if (error && !task) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => navigate('/tasks')}
            className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tasks
          </button>
          <ErrorMessage message={error} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => navigate(`/tasks/${id}`)}
            className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Task Details
          </button>
          
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Assign Staff to Task
          </h1>
        </div>

        {/* Task Summary */}
        {task && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {task.title}
              </h2>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(task.priority)}`}>
                {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)} Priority
              </span>
            </div>
            
            {task.description && (
              <p className="text-gray-600 dark:text-gray-400 mb-4">{task.description}</p>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="flex items-center text-gray-500 dark:text-gray-400">
                <Calendar className="w-4 h-4 mr-2" />
                <span>Type: {task.task_type.replace('_', ' ')}</span>
              </div>
              
              {task.estimated_duration_minutes && (
                <div className="flex items-center text-gray-500 dark:text-gray-400">
                  <Clock className="w-4 h-4 mr-2" />
                  <span>Duration: {task.estimated_duration_minutes} minutes</span>
                </div>
              )}
              
              {task.category && (
                <div className="flex items-center text-gray-500 dark:text-gray-400">
                  <span>Category: {task.category}</span>
                </div>
              )}
            </div>
            
            {(task.min_age_required || task.max_age_allowed) && (
              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-center text-blue-800 dark:text-blue-200">
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  <span className="font-medium">Age Requirements:</span>
                </div>
                <p className="text-blue-700 dark:text-blue-300 text-sm mt-1">
                  {task.min_age_required && `Minimum age: ${task.min_age_required} years`}
                  {task.min_age_required && task.max_age_allowed && ' • '}
                  {task.max_age_allowed && `Maximum age: ${task.max_age_allowed} years`}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Assignment Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Staff Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Select Staff Members ({formData.staff_member_ids.length} selected)
              </h3>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                {eligibleStaff.length} eligible staff members
              </div>
            </div>
            
            {errors.staff_member_ids && (
              <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-red-800 dark:text-red-200 text-sm">{errors.staff_member_ids}</p>
              </div>
            )}
            
            {eligibleStaff.length === 0 ? (
              <div className="text-center py-8">
                <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  No eligible staff members found for this task
                </p>
                <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                  Staff members may not meet age requirements or may be inactive
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {eligibleStaff.map((staff) => (
                  <div
                    key={staff.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                      formData.staff_member_ids.includes(staff.id)
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                    onClick={() => handleStaffSelection(staff.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center">
                        <User className="w-5 h-5 text-gray-400 mr-2" />
                        <span className="font-medium text-gray-900 dark:text-white">
                          {staff.full_name}
                        </span>
                      </div>
                      {formData.staff_member_ids.includes(staff.id) && (
                        <CheckCircle className="w-5 h-5 text-blue-500" />
                      )}
                    </div>
                    
                    <div className="text-sm text-gray-500 dark:text-gray-400 space-y-1">
                      <p>{staff.email}</p>
                      <p>Role: {staff.role}</p>
                      {staff.department && <p>Department: {staff.department}</p>}
                      {staff.age && <p>Age: {staff.age} years</p>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Assignment Details */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Assignment Details
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Due Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Due Date *
                </label>
                <input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => handleInputChange('due_date', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                    errors.due_date ? 'border-red-500' : 'border-gray-300'
                  }`}
                  required
                />
                {errors.due_date && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.due_date}</p>
                )}
              </div>

              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Priority
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => handleInputChange('priority', e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>

            {/* Assignment Notes */}
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Assignment Notes (Optional)
              </label>
              <textarea
                value={formData.assignment_notes}
                onChange={(e) => handleInputChange('assignment_notes', e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Add any special instructions or notes for the assigned staff..."
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <ErrorMessage message={error} />
          )}

          {/* Form Actions */}
          <div className="flex items-center justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate(`/tasks/${id}`)}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || formData.staff_member_ids.length === 0}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {submitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating Assignments...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Assignments ({formData.staff_member_ids.length})
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AssignTaskPage; 