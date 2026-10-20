/*
  Description: Create Training Program page for adding new training programs.
  Purpose: Allows facility administrators to create new training programs with all necessary details.
  
  Note: Facility administrators are users with a pro subscription who manage facility operations.
*/

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Save, 
  X, 
  BookOpen, 
  Clock, 
  Award, 
  AlertTriangle,
  Plus,
  Trash2
} from 'lucide-react';
import { trainingProgramService } from '../services/trainingService';
import ErrorMessage from '../components/ErrorMessage';

const CreateTrainingProgramPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    is_mandatory: false,
    requires_certification: false,
    certification_valid_months: 12,
    estimated_duration_minutes: 0,
    delivery_method: 'online',
    prerequisites: [] as number[],
    reminder_schedule_days: [30, 14, 7, 1],
    auto_assign_new_staff: false,
    facility_type_ids: [] as number[]
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({
        ...prev,
        [name]: checked
      }));
    } else if (name === 'estimated_duration_minutes') {
      setFormData(prev => ({
        ...prev,
        [name]: parseInt(value) || 0
      }));
    } else if (name === 'certification_valid_months') {
      setFormData(prev => ({
        ...prev,
        [name]: parseInt(value) || 12
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleReminderDaysChange = (index: number, value: string) => {
    const newDays = [...formData.reminder_schedule_days];
    newDays[index] = parseInt(value) || 0;
    setFormData(prev => ({
      ...prev,
      reminder_schedule_days: newDays
    }));
  };

  const addReminderDay = () => {
    setFormData(prev => ({
      ...prev,
      reminder_schedule_days: [...prev.reminder_schedule_days, 1]
    }));
  };

  const removeReminderDay = (index: number) => {
    setFormData(prev => ({
      ...prev,
      reminder_schedule_days: prev.reminder_schedule_days.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const submitData = {
        ...formData,
        estimated_duration_minutes: formData.estimated_duration_minutes || undefined
      };
      
      await trainingProgramService.create(submitData);
      navigate('/training/programs');
    } catch (err) {
      console.error('Create program error:', err);
      setError('Failed to create training program. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      {error && <ErrorMessage message={error} />}
      
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">Create Training Program</h1>
        <p className="text-gray-600 dark:text-gray-300">Add a new training program for your facility</p>
      </div>

      {/* Quick Actions */}
      <div className="mb-6 flex flex-wrap gap-3">
        <button
          onClick={() => navigate('/training/programs')}
          className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center transition-colors"
        >
          <X className="h-4 w-4 mr-2" />
          Cancel
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Information */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
            <BookOpen className="h-5 w-5 mr-2" />
            Basic Information
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Program Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                required
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                placeholder="Enter training program title"
              />
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                placeholder="Describe the training program objectives and content"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Category
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleInputChange}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="">Select category</option>
                <option value="Safety">Safety</option>
                <option value="Compliance">Compliance</option>
                <option value="Technical">Technical</option>
                <option value="Administrative">Administrative</option>
                <option value="Clinical">Clinical</option>
                <option value="Emergency">Emergency</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Delivery Method
              </label>
              <select
                name="delivery_method"
                value={formData.delivery_method}
                onChange={handleInputChange}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="online">Online</option>
                <option value="in_person">In Person</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </div>
          </div>
        </div>

        {/* Training Details */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
            <Clock className="h-5 w-5 mr-2" />
            Training Details
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Estimated Duration (minutes)
              </label>
              <input
                type="number"
                name="estimated_duration_minutes"
                value={formData.estimated_duration_minutes}
                onChange={handleInputChange}
                min="1"
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="e.g., 60"
              />
            </div>
            
            <div className="space-y-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_mandatory"
                  checked={formData.is_mandatory}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Mandatory Training</span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="auto_assign_new_staff"
                  checked={formData.auto_assign_new_staff}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Auto-assign to new staff</span>
              </label>
            </div>
          </div>
        </div>

        {/* Certification */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
            <Award className="h-5 w-5 mr-2" />
            Certification
          </h2>
          
          <div className="space-y-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                name="requires_certification"
                checked={formData.requires_certification}
                onChange={handleInputChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Requires Certification</span>
            </label>
            
            {formData.requires_certification && (
              <div className="ml-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Certification Valid For (months)
                </label>
                <input
                  type="number"
                  name="certification_valid_months"
                  value={formData.certification_valid_months}
                  onChange={handleInputChange}
                  min="1"
                  max="60"
                  className="w-32 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            )}
          </div>
        </div>

        {/* Reminder Schedule */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Reminder Schedule
          </h2>
          
          <div className="space-y-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Set reminder days before the training due date
            </p>
            
            <div className="space-y-2">
              {formData.reminder_schedule_days.map((days, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <input
                    type="number"
                    value={days}
                    onChange={(e) => handleReminderDaysChange(index, e.target.value)}
                    min="1"
                    className="w-20 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                  <span className="text-sm text-gray-600 dark:text-gray-400">days before due date</span>
                  {formData.reminder_schedule_days.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeReminderDay(index)}
                      className="p-1 text-red-500 hover:text-red-700 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
              
              <button
                type="button"
                onClick={addReminderDay}
                className="flex items-center text-blue-600 hover:text-blue-700 text-sm transition-colors"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add reminder
              </button>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => navigate('/training/programs')}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-6 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center transition-colors"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            {loading ? 'Creating...' : 'Create Program'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateTrainingProgramPage; 