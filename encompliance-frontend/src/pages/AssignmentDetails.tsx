import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  ArrowLeft, 
  Edit, 
  Calendar, 
  User, 
  BookOpen, 
  AlertTriangle,
  Clock,
  CheckCircle,
  XCircle,
  Play,
  BarChart3
} from 'lucide-react';
import { trainingAssignmentService } from '../services/trainingService';
import type { TrainingAssignment } from '../services/trainingService';

const AssignmentDetailsPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [assignment, setAssignment] = useState<TrainingAssignment | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (id) {
      loadAssignment(parseInt(id));
    }
  }, [id]);

  const loadAssignment = async (assignmentId: number) => {
    try {
      setLoading(true);
      const data = await trainingAssignmentService.getById(assignmentId);
      setAssignment(data);
    } catch (error) {
      console.error('Error loading assignment:', error);
      setError('Failed to load assignment details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (assignment: TrainingAssignment) => {
    const statusConfig = {
      assigned: { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400', icon: Clock },
      in_progress: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400', icon: Play },
      completed: { color: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400', icon: CheckCircle },
      overdue: { color: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400', icon: XCircle },
      cancelled: { color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400', icon: XCircle }
    };

    const config = statusConfig[assignment.status] || statusConfig.assigned;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="h-3 w-3 mr-1" />
        {assignment.status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const getPriorityBadge = (priority: string) => {
    const priorityConfig: Record<string, string> = {
      urgent: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
      high: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
      low: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${priorityConfig[priority] || priorityConfig.medium}`}>
        <AlertTriangle className="h-3 w-3 mr-1" />
        {priority.toUpperCase()}
      </span>
    );
  };

  const getDaysUntilDue = (assignment: TrainingAssignment) => {
    const dueDate = new Date(assignment.due_date);
    const today = new Date();
    const diffTime = dueDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return `${Math.abs(diffDays)} days overdue`;
    } else if (diffDays === 0) {
      return 'Due today';
    } else if (diffDays === 1) {
      return 'Due tomorrow';
    } else {
      return `${diffDays} days remaining`;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="ml-4 text-gray-600 dark:text-gray-400">Loading assignment details...</p>
        </div>
      </div>
    );
  }

  if (error || !assignment) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <XCircle className="h-12 w-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">Error Loading Assignment</h3>
          <p className="text-red-700 dark:text-red-300 mb-4">{error || 'Assignment not found'}</p>
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
          onClick={() => navigate('/training/assignments')}
          className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Training Assignments
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
              Training Assignment #{assignment.id}
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              View and manage assignment details
            </p>
          </div>
          <button
            onClick={() => navigate(`/training/assignments/${assignment.id}/edit`)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors"
          >
            <Edit className="h-4 w-4 mr-2" />
            Edit Assignment
          </button>
        </div>
      </div>

      {/* Assignment Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status and Priority */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Status & Priority</h3>
            <div className="flex items-center space-x-4">
              {getStatusBadge(assignment)}
              {getPriorityBadge(assignment.priority)}
            </div>
          </div>

          {/* Assignment Information */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <BookOpen className="h-5 w-5 mr-2" />
              Assignment Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Training Program ID
                </label>
                <p className="text-gray-900 dark:text-white">{assignment.training_program_id}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Staff Member ID
                </label>
                <p className="text-gray-900 dark:text-white">{assignment.staff_member_id}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Assigned By
                </label>
                <p className="text-gray-900 dark:text-white">User #{assignment.assigned_by}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Assigned Date
                </label>
                <p className="text-gray-900 dark:text-white">{formatDate(assignment.assigned_date)}</p>
              </div>
            </div>
          </div>

          {/* Progress */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <BarChart3 className="h-5 w-5 mr-2" />
              Progress
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-gray-600 dark:text-gray-400">Completion Progress</span>
                  <span className="font-medium">{assignment.progress_percentage}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all duration-300 ${
                      assignment.progress_percentage === 100 
                        ? 'bg-green-600' 
                        : assignment.is_overdue 
                          ? 'bg-red-600' 
                          : 'bg-blue-600'
                    }`}
                    style={{ width: `${assignment.progress_percentage}%` }}
                  ></div>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Time Spent:</span>
                  <span className="ml-2 font-medium">{assignment.time_spent_minutes} minutes</span>
                </div>
                {assignment.last_accessed && (
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Last Accessed:</span>
                    <span className="ml-2 font-medium">{formatDateTime(assignment.last_accessed)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Notes */}
          {assignment.assignment_notes && (
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Assignment Notes</h3>
              <p className="text-gray-700 dark:text-gray-300">{assignment.assignment_notes}</p>
            </div>
          )}

          {assignment.completion_notes && (
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Completion Notes</h3>
              <p className="text-gray-700 dark:text-gray-300">{assignment.completion_notes}</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Due Date */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2" />
              Due Date
            </h3>
            <div className="space-y-2">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatDate(assignment.due_date)}
              </p>
              <p className={`text-sm font-medium ${
                assignment.is_overdue 
                  ? 'text-red-600 dark:text-red-400' 
                  : 'text-gray-600 dark:text-gray-400'
              }`}>
                {getDaysUntilDue(assignment)}
              </p>
            </div>
          </div>

          {/* Dates */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Important Dates</h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Created:</span>
                <p className="font-medium">{formatDateTime(assignment.created_at)}</p>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Last Updated:</span>
                <p className="font-medium">{formatDateTime(assignment.updated_at)}</p>
              </div>
              {assignment.started_date && (
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Started:</span>
                  <p className="font-medium">{formatDateTime(assignment.started_date)}</p>
                </div>
              )}
              {assignment.completed_date && (
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Completed:</span>
                  <p className="font-medium">{formatDateTime(assignment.completed_date)}</p>
                </div>
              )}
            </div>
          </div>

          {/* Verification */}
          {assignment.completion_verified && (
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Verification</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span className="text-green-600 font-medium">Verified</span>
                </div>
                {assignment.verification_method && (
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Method:</span>
                    <p className="font-medium">{assignment.verification_method}</p>
                  </div>
                )}
                {assignment.verification_score && (
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Score:</span>
                    <p className="font-medium">{assignment.verification_score}%</p>
                  </div>
                )}
                {assignment.verification_notes && (
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Notes:</span>
                    <p className="font-medium">{assignment.verification_notes}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssignmentDetailsPage; 