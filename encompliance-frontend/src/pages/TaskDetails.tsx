/*
  Description: Task Details page for viewing individual operational task information
  Purpose: Displays comprehensive task details, assignments, and allows task management actions
*/

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Edit, 
  Trash2, 
  Users, 
  Calendar, 
  Clock, 
  MapPin,
  AlertTriangle,
  CheckCircle,
  Plus,
  MoreVertical
} from 'lucide-react';
import { operationalTaskService, OperationalTask, TaskAssignment } from '../services/operationalTaskService';
import ErrorMessage from '../components/ErrorMessage';

const TaskDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<OperationalTask | null>(null);
  const [assignments, setAssignments] = useState<TaskAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadTaskDetails();
    }
  }, [id]);

  const loadTaskDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load task details and assignments in parallel
      const [taskResponse, assignmentsResponse] = await Promise.all([
        operationalTaskService.getTask(parseInt(id!)),
        operationalTaskService.getAssignments({ operational_task_id: parseInt(id!) })
      ]);
      
      setTask(taskResponse);
      setAssignments(assignmentsResponse);
    } catch (err) {
      setError('Failed to load task details');
      console.error('Error loading task details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    navigate(`/tasks/${id}/edit`);
  };

  const handleDelete = async () => {
    if (!task || !window.confirm('Are you sure you want to delete this task?')) {
      return;
    }

    try {
      await operationalTaskService.deleteTask(task.id);
      navigate('/tasks');
    } catch (err) {
      setError('Failed to delete task');
      console.error('Error deleting task:', err);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'in_progress': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'assigned': return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
      case 'overdue': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'cancelled': return 'bg-gray-100 text-gray-500 dark:bg-gray-900 dark:text-gray-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading task details...</p>
        </div>
      </div>
    );
  }

  if (error || !task) {
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
          <ErrorMessage message={error || 'Task not found'} />
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
            onClick={() => navigate('/tasks')}
            className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tasks
          </button>
          
          <div className="flex space-x-2">
            <button
              onClick={handleEdit}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </button>
            <button
              onClick={handleDelete}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </button>
          </div>
        </div>

        {/* Task Details Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {task.title}
              </h1>
              <div className="flex items-center space-x-4">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
                  {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${task.task_type === 'recurring' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'}`}>
                  {task.task_type === 'recurring' ? 'Recurring' : 'One-time'}
                </span>
                {task.is_active ? (
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                    Active
                  </span>
                ) : (
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200">
                    Inactive
                  </span>
                )}
              </div>
            </div>
          </div>

          {task.description && (
            <p className="text-gray-600 dark:text-gray-400 mb-4">{task.description}</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
              <Calendar className="w-4 h-4 mr-2" />
              Start Date: {new Date(task.start_date).toLocaleDateString()}
            </div>
            
            {task.end_date && (
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <Calendar className="w-4 h-4 mr-2" />
                End Date: {new Date(task.end_date).toLocaleDateString()}
              </div>
            )}
            
            {task.estimated_duration_minutes && (
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <Clock className="w-4 h-4 mr-2" />
                Duration: {task.estimated_duration_minutes} minutes
              </div>
            )}
            
            {task.location && (
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <MapPin className="w-4 h-4 mr-2" />
                Location: {task.location}
              </div>
            )}
          </div>

          {task.has_age_restrictions && (
            <div className="flex items-center text-sm text-orange-600 dark:text-orange-400 mb-4">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Age restrictions: {task.age_range_description}
            </div>
          )}

          {task.required_equipment && task.required_equipment.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Required Equipment:</h3>
              <div className="flex flex-wrap gap-2">
                {task.required_equipment.map((item, index) => (
                  <span key={index} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {task.special_instructions && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Special Instructions:</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{task.special_instructions}</p>
            </div>
          )}
        </div>

        {/* Assignments Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Task Assignments ({assignments.length})
            </h2>
            <button
              onClick={() => navigate(`/tasks/${id}/assign`)}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Assign Staff
            </button>
          </div>

          {assignments.length === 0 ? (
            <div className="text-center py-8">
              <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400 mb-4">No staff assignments yet</p>
              <button
                onClick={() => navigate(`/tasks/${id}/assign`)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Assign Staff Members
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {assignments.map((assignment) => (
                <div key={assignment.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-4">
                      <span className="font-medium text-gray-900 dark:text-white">
                        Staff Member ID: {assignment.staff_member_id}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(assignment.status)}`}>
                        {assignment.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      Due: {new Date(assignment.due_date).toLocaleDateString()}
                    </span>
                  </div>
                  
                  {assignment.assignment_notes && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      {assignment.assignment_notes}
                    </p>
                  )}
                  
                  <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                    <span>Progress: {assignment.progress_percentage}%</span>
                    {assignment.time_spent_minutes > 0 && (
                      <span>Time spent: {assignment.time_spent_minutes} minutes</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskDetails; 