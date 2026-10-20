/*
  Description: Create Task page for facility administrators to create new operational tasks and chores.
  Purpose: Provides a comprehensive form for creating tasks with age-based assignment and recurring scheduling.
*/

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Save, 
  ArrowLeft, 
  Calendar, 
  Users, 
  User,
  Clock, 
  MapPin,
  AlertCircle,
  Plus,
  X,
  Camera,
  CheckCircle
} from 'lucide-react';
import { operationalTaskService, CreateTaskData, OperationalTask, EligibleStaffMember } from '../services/operationalTaskService';
import ErrorMessage from '../components/ErrorMessage';
import TaskPhotoUploader, { TaskPhoto } from '../components/TaskPhotoUploader';
import { taskReferenceImageService } from '../services/taskReferenceImageService';

interface FormData {
  title: string;
  description: string;
  category: string;
  task_type: 'one_time' | 'recurring';
  recurrence_pattern: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  recurrence_interval: number;
  min_age_required: string;
  max_age_allowed: string;
  estimated_duration_minutes: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  requires_supervision: boolean;
  special_instructions: string;
  location: string;
  required_equipment: string[];
  start_date: string;
  end_date: string;
  // Photo instructions for staff
  photo_instructions: string;
  // Photo requirements are optional
  requires_before_photos: boolean;
  requires_after_photos: boolean;
  // Assignment data (optional)
  assign_to_staff: boolean;
  selected_staff_ids: number[];
  assignment_due_date: string;
  assignment_priority: 'low' | 'medium' | 'high' | 'urgent';
  assignment_notes: string;
}

const CreateTaskPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newEquipment, setNewEquipment] = useState('');
  const [preTaskImages, setPreTaskImages] = useState<TaskPhoto[]>([]);
  const [staffMembers, setStaffMembers] = useState<EligibleStaffMember[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);

  const [formData, setFormData] = useState<FormData>({
    title: '',
    description: '',
    category: '',
    task_type: 'one_time',
    recurrence_pattern: 'weekly',
    recurrence_interval: 1,
    min_age_required: '',
    max_age_allowed: '',
    estimated_duration_minutes: '',
    priority: 'medium',
    requires_supervision: false,
    special_instructions: '',
    location: '',
    required_equipment: [],
    start_date: '',
    end_date: '',
    // Photo instructions for staff
    photo_instructions: '',
    // Photo requirements are optional
    requires_before_photos: false,
    requires_after_photos: false,
    // Assignment data (optional)
    assign_to_staff: false,
    selected_staff_ids: [],
    assignment_due_date: '',
    assignment_priority: 'medium',
    assignment_notes: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    // Set default start date to today
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    setFormData(prev => ({ ...prev, start_date: todayStr, assignment_due_date: todayStr }));
    
    // Load staff members for assignment
    loadStaffMembers();
  }, []);

  const loadStaffMembers = async () => {
    try {
      setLoadingStaff(true);
      const response = await fetch('/api/v1/facilities/staff-members', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'x-token': localStorage.getItem('token') || ''
        }
      });
      
      if (response.ok) {
        const staff = await response.json();
        setStaffMembers(staff);
      } else {
        console.error('Failed to load staff members:', response.statusText);
      }
    } catch (error) {
      console.error('Failed to load staff members:', error);
    } finally {
      setLoadingStaff(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }

    if (formData.task_type === 'recurring' && formData.end_date && formData.start_date) {
      if (new Date(formData.end_date) <= new Date(formData.start_date)) {
        newErrors.end_date = 'End date must be after start date';
      }
    }

    if (formData.min_age_required && formData.max_age_allowed) {
      const minAge = parseInt(formData.min_age_required);
      const maxAge = parseInt(formData.max_age_allowed);
      if (minAge >= maxAge) {
        newErrors.max_age_allowed = 'Maximum age must be greater than minimum age';
      }
    }

    if (formData.min_age_required) {
      const minAge = parseInt(formData.min_age_required);
      if (minAge < 14 || minAge > 100) {
        newErrors.min_age_required = 'Minimum age must be between 14 and 100';
      }
    }

    if (formData.max_age_allowed) {
      const maxAge = parseInt(formData.max_age_allowed);
      if (maxAge < 14 || maxAge > 100) {
        newErrors.max_age_allowed = 'Maximum age must be between 14 and 100';
      }
    }

    if (formData.estimated_duration_minutes) {
      const duration = parseInt(formData.estimated_duration_minutes);
      if (duration < 1 || duration > 1440) {
        newErrors.estimated_duration_minutes = 'Duration must be between 1 and 1440 minutes';
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

    try {
      setLoading(true);
      setError(null);

      const taskData: CreateTaskData = {
        title: formData.title,
        description: formData.description || undefined,
        category: formData.category || undefined,
        task_type: formData.task_type,
        recurrence_pattern: formData.task_type === 'recurring' ? formData.recurrence_pattern : undefined,
        recurrence_interval: formData.task_type === 'recurring' ? formData.recurrence_interval : undefined,
        min_age_required: formData.min_age_required ? parseInt(formData.min_age_required) : undefined,
        max_age_allowed: formData.max_age_allowed ? parseInt(formData.max_age_allowed) : undefined,
        estimated_duration_minutes: formData.estimated_duration_minutes ? parseInt(formData.estimated_duration_minutes) : undefined,
        priority: formData.priority,
        requires_supervision: formData.requires_supervision,
        special_instructions: formData.special_instructions || undefined,
        location: formData.location || undefined,
        required_equipment: formData.required_equipment.length > 0 ? formData.required_equipment : undefined,
        start_date: formData.start_date,
        end_date: formData.task_type === 'recurring' && formData.end_date ? formData.end_date : undefined,
        // Photo requirements are optional
        requires_before_photos: formData.requires_before_photos || false,
        requires_after_photos: formData.requires_after_photos || false,
        photo_instructions: formData.photo_instructions || undefined
      };

      const createdTask = await operationalTaskService.createTask(taskData);

      // Upload reference photos if any were selected
      if (preTaskImages.length > 0) {
        try {
          await taskReferenceImageService.uploadImages(
            createdTask.id,
            preTaskImages.map((p) => p.file),
            preTaskImages.map((p) => p.label)
          );
        } catch (uploadErr) {
          console.error('Reference photo upload failed:', uploadErr);
          // Continue navigation even if photo upload fails, but you could add a toast/alert here
        }
      }

      // Create assignments if staff members were selected
      if (formData.assign_to_staff && formData.selected_staff_ids.length > 0) {
        try {
          await operationalTaskService.createAssignments({
            operational_task_id: createdTask.id,
            staff_member_ids: formData.selected_staff_ids,
            due_date: formData.assignment_due_date,
            priority: formData.assignment_priority,
            assignment_notes: formData.assignment_notes || undefined
          });
        } catch (assignErr) {
          console.error('Assignment creation failed:', assignErr);
          // Continue navigation even if assignment creation fails
        }
      }

      navigate('/tasks');
    } catch (err) {
      setError('Failed to create task. Please try again.');
      console.error('Create task error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof FormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const addEquipment = () => {
    if (newEquipment.trim() && !formData.required_equipment.includes(newEquipment.trim())) {
      setFormData(prev => ({
        ...prev,
        required_equipment: [...prev.required_equipment, newEquipment.trim()]
      }));
      setNewEquipment('');
    }
  };

  const removeEquipment = (index: number) => {
    setFormData(prev => ({
      ...prev,
      required_equipment: prev.required_equipment.filter((_, i) => i !== index)
    }));
  };

  const handleBack = () => {
    navigate('/tasks');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center space-x-4 mb-8">
        <button
          onClick={handleBack}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-navy-blue dark:text-white">Create New Task</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Create a new operational task or chore with age-based assignment criteria
          </p>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Basic Information */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Basic Information</h2>
              
              {/* Title */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  className={`w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                    errors.title ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                  placeholder="Enter task title"
                />
                {errors.title && <p className="text-red-500 text-sm mt-1">{errors.title}</p>}
              </div>

              {/* Description */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  rows={3}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Enter task description"
                />
              </div>

              {/* Category */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Category
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">Select category</option>
                  <option value="cleaning">Cleaning</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="safety">Safety</option>
                  <option value="administrative">Administrative</option>
                </select>
              </div>

              {/* Priority */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Priority
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => handleInputChange('priority', e.target.value)}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              {/* Location */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <MapPin className="h-4 w-4 inline mr-1" />
                  Location
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => handleInputChange('location', e.target.value)}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Where should this task be performed?"
                />
              </div>

              {/* Duration */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Clock className="h-4 w-4 inline mr-1" />
                  Estimated Duration (minutes)
                </label>
                <input
                  type="number"
                  min="1"
                  max="1440"
                  value={formData.estimated_duration_minutes}
                  onChange={(e) => handleInputChange('estimated_duration_minutes', e.target.value)}
                  className={`w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                    errors.estimated_duration_minutes ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                  placeholder="How long should this task take?"
                />
                {errors.estimated_duration_minutes && (
                  <p className="text-red-500 text-sm mt-1">{errors.estimated_duration_minutes}</p>
                )}
              </div>

              {/* Requires Supervision */}
              <div className="mb-4">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={formData.requires_supervision}
                      onChange={(e) => handleInputChange('requires_supervision', e.target.checked)}
                      className="sr-only" // Tailwind class to hide the checkbox visually but keep it accessible
                    />
                    <div className="block bg-gray-600 w-14 h-8 rounded-full"></div>
                    <div className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition ${formData.requires_supervision ? 'transform translate-x-full bg-green-400' : ''}`}></div>
                  </div>
                  <div className="ml-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                    Requires Supervision
                  </div>
                </label>
              </div>

              {/* Special Instructions */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Special Instructions
                </label>
                <textarea
                  value={formData.special_instructions}
                  onChange={(e) => handleInputChange('special_instructions', e.target.value)}
                  rows={3}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Any special instructions or safety notes"
                />
              </div>
            </div>

            {/* Required Equipment */}
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Required Equipment</h2>
              
              <div className="flex space-x-2 mb-4">
                <input
                  type="text"
                  value={newEquipment}
                  onChange={(e) => setNewEquipment(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addEquipment())}
                  className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Add required equipment"
                />
                <button
                  type="button"
                  onClick={addEquipment}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-2">
                {formData.required_equipment.map((equipment, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded-lg px-3 py-2">
                    <span className="text-gray-900 dark:text-white">{equipment}</span>
                    <button
                      type="button"
                      onClick={() => removeEquipment(index)}
                      className="text-red-500 hover:text-red-700 transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Pre-Task Photo Documentation */}
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                <Camera className="h-5 w-5 inline mr-2" />
                Pre-Task Photo Documentation
              </h2>

              {/* Photo Instructions */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Photo Instructions for Staff
                </label>
                <textarea
                  value={formData.photo_instructions}
                  onChange={(e) => handleInputChange('photo_instructions', e.target.value)}
                  rows={4}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  placeholder="e.g., 'Take photos from multiple angles', 'Include close-ups of cleaned surfaces', 'Show before and after states', etc."
                />
              </div>

              {/* Photo Uploader */}
              <TaskPhotoUploader
                photos={preTaskImages}
                onPhotosChange={setPreTaskImages}
                title="Reference Photos"
                description="Upload photos showing the expected final result. Staff will automatically take 'before' and 'after' photos when completing this task."
              />
            </div>
          </div>

          {/* Right Column - Scheduling & Assignment */}
          <div className="space-y-6">
            {/* Task Type & Scheduling */}
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                <Calendar className="h-5 w-5 inline mr-2" />
                Scheduling
              </h2>

              {/* Task Type */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Task Type
                </label>
                <select
                  value={formData.task_type}
                  onChange={(e) => handleInputChange('task_type', e.target.value as 'one_time' | 'recurring')}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="one_time">One-time Task</option>
                  <option value="recurring">Recurring Task</option>
                </select>
              </div>

              {/* Recurring Task Options */}
              {formData.task_type === 'recurring' && (
                <>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Recurrence Pattern
                    </label>
                    <select
                      value={formData.recurrence_pattern}
                      onChange={(e) => handleInputChange('recurrence_pattern', e.target.value)}
                      className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="quarterly">Quarterly</option>
                    </select>
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Repeat Every
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        min="1"
                        max="365"
                        value={formData.recurrence_interval}
                        onChange={(e) => handleInputChange('recurrence_interval', parseInt(e.target.value) || 1)}
                        className="w-20 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                      <span className="text-gray-600 dark:text-gray-400">
                        {formData.recurrence_pattern === 'daily' && 'day(s)'}
                        {formData.recurrence_pattern === 'weekly' && 'week(s)'}
                        {formData.recurrence_pattern === 'monthly' && 'month(s)'}
                        {formData.recurrence_pattern === 'quarterly' && 'quarter(s)'}
                      </span>
                    </div>
                  </div>
                </>
              )}

              {/* Start Date */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Start Date *
                </label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => handleInputChange('start_date', e.target.value)}
                  className={`w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                    errors.start_date ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  }`}
                />
                {errors.start_date && <p className="text-red-500 text-sm mt-1">{errors.start_date}</p>}
              </div>

              {/* End Date (for recurring tasks) */}
              {formData.task_type === 'recurring' && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    End Date (optional)
                  </label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => handleInputChange('end_date', e.target.value)}
                    className={`w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                      errors.end_date ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                    }`}
                  />
                  {errors.end_date && <p className="text-red-500 text-sm mt-1">{errors.end_date}</p>}
                </div>
              )}
            </div>

            {/* Age-Based Assignment */}
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                <Users className="h-5 w-5 inline mr-2" />
                Age-Based Assignment
              </h2>

              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4">
                <div className="flex items-start space-x-2">
                  <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-300">Age Restrictions</h3>
                    <p className="text-sm text-yellow-700 dark:text-yellow-400 mt-1">
                      Set age restrictions to ensure compliance with child labor laws and facility safety requirements.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Minimum Age
                  </label>
                  <input
                    type="number"
                    min="14"
                    max="100"
                    value={formData.min_age_required}
                    onChange={(e) => handleInputChange('min_age_required', e.target.value)}
                    className={`w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                      errors.min_age_required ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                    }`}
                    placeholder="14"
                  />
                  {errors.min_age_required && (
                    <p className="text-red-500 text-sm mt-1">{errors.min_age_required}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Maximum Age
                  </label>
                  <input
                    type="number"
                    min="14"
                    max="100"
                    value={formData.max_age_allowed}
                    onChange={(e) => handleInputChange('max_age_allowed', e.target.value)}
                    className={`w-full border rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                      errors.max_age_allowed ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                    }`}
                    placeholder="65"
                  />
                  {errors.max_age_allowed && (
                    <p className="text-red-500 text-sm mt-1">{errors.max_age_allowed}</p>
                  )}
                </div>
              </div>

              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                Leave blank for no age restrictions. Only staff members within the specified age range will be eligible for assignment.
              </p>
            </div>

            {/* Task Assignment (Optional) */}
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                <Users className="h-5 w-5 inline mr-2" />
                Assign to Staff (Optional)
              </h2>

              {/* Assign to Staff Toggle */}
              <div className="mb-4">
                <div className="flex items-center space-x-4">
                  <button
                    type="button"
                    onClick={() => handleInputChange('assign_to_staff', !formData.assign_to_staff)}
                    className={`px-4 py-2 rounded-lg border transition-colors ${
                      formData.assign_to_staff
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                    }`}
                  >
                    {formData.assign_to_staff ? 'Enabled' : 'Disabled'}
                  </button>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Assign this task to staff members immediately
                  </span>
                </div>
              </div>

              {formData.assign_to_staff && (
                <div className="space-y-4">
                  {/* Staff Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Select Staff Members ({formData.selected_staff_ids.length} selected)
                    </label>
                    {loadingStaff ? (
                      <div className="text-sm text-gray-500">Loading staff...</div>
                    ) : (
                      <div className="max-h-60 overflow-y-auto">
                        {staffMembers.length === 0 ? (
                          <div className="text-center py-8">
                            <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                            <p className="text-gray-500 dark:text-gray-400">No staff members available</p>
                          </div>
                        ) : (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {staffMembers.map((staff) => (
                              <div
                                key={staff.id}
                                className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                                  formData.selected_staff_ids.includes(staff.id)
                                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                                }`}
                                onClick={() => {
                                  const newSelected = formData.selected_staff_ids.includes(staff.id)
                                    ? formData.selected_staff_ids.filter(id => id !== staff.id)
                                    : [...formData.selected_staff_ids, staff.id];
                                  handleInputChange('selected_staff_ids', newSelected);
                                }}
                              >
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center">
                                    <User className="w-4 h-4 text-gray-400 mr-2" />
                                    <span className="font-medium text-gray-900 dark:text-white">
                                      {staff.full_name}
                                    </span>
                                  </div>
                                  {formData.selected_staff_ids.includes(staff.id) && (
                                    <CheckCircle className="w-4 h-4 text-blue-500" />
                                  )}
                                </div>
                                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                  {staff.role}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Assignment Due Date */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Assignment Due Date
                    </label>
                    <input
                      type="date"
                      value={formData.assignment_due_date}
                      onChange={(e) => handleInputChange('assignment_due_date', e.target.value)}
                      className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>

                  {/* Assignment Priority */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Assignment Priority
                    </label>
                    <select
                      value={formData.assignment_priority}
                      onChange={(e) => handleInputChange('assignment_priority', e.target.value)}
                      className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>

                  {/* Assignment Notes */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Assignment Notes (Optional)
                    </label>
                    <textarea
                      value={formData.assignment_notes}
                      onChange={(e) => handleInputChange('assignment_notes', e.target.value)}
                      rows={3}
                      className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="Add any specific notes for the assigned staff members..."
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={handleBack}
            className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center space-x-2"
          >
            <Save className="h-5 w-5" />
            <span>{loading ? 'Creating...' : 'Create Task'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateTaskPage; 