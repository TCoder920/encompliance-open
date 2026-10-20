/*
  Description: Task Management page for facility administrators to manage operational tasks and chores.
  Purpose: Provides comprehensive task management with age-based assignment, recurring tasks, and progress tracking.
  This is a premium feature with freemium preview functionality for Free tier users.
  
  Note: Facility administrators are users with a pro subscription who manage facility operations.
*/

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Filter, 
  Calendar, 
  Users, 
  Clock, 
  CheckCircle,
  AlertTriangle,
  Repeat,
  MapPin,
  User,
  Timer,
  Star,
  Camera,
  MessageSquare,
  PlayCircle,
  XCircle,
  ClipboardCheck,
  Eye
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Tier, getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature } from '../utils/accessControl';
import { SAMPLE_TASKS, SAMPLE_TASK_ASSIGNMENTS, SAMPLE_TASK_DASHBOARD } from '../utils/previewData';
import FeaturePreview from '../components/ui/FeaturePreview';
import { operationalTaskService, TaskAssignment, OperationalTask } from '../services/operationalTaskService';
import ErrorMessage from '../components/ErrorMessage';
import AssignmentCompletionModal from '../components/AssignmentCompletionModal';
import AssignmentDetailsModal from '../components/AssignmentDetailsModal';

interface TaskDashboard {
  total_tasks: number;
  active_tasks: number;
  recurring_tasks: number;
  total_assignments: number;
  pending_assignments: number;
  in_progress_assignments: number;
  completed_assignments: number;
  overdue_assignments: number;
  completion_rate: number;
  average_completion_time: number;
  upcoming_due_dates: any[];
  recent_completions: any[];
}

const TaskManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [tasks, setTasks] = useState<OperationalTask[]>([]);
  const [assignments, setAssignments] = useState<TaskAssignment[]>([]);
  const [dashboard, setDashboard] = useState<TaskDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'tasks' | 'assignments'>('overview');
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<TaskAssignment | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUse = canUseFeature(userTier, 'task_management');

  useEffect(() => {
    loadData();
  }, [canUse]);

  const loadData = async () => {
    if (!canUse) {
      // For preview mode, use sample data
      setTasks(SAMPLE_TASKS as any);
      setAssignments(SAMPLE_TASK_ASSIGNMENTS as any);
      setDashboard(SAMPLE_TASK_DASHBOARD as any);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const [dashboardResponse, tasksResponse, assignmentsResponse] = await Promise.all([
        operationalTaskService.getDashboard(),
        operationalTaskService.getTasks({}),
        operationalTaskService.getAssignments({})
      ]);
      
      setDashboard(dashboardResponse);
      setTasks(tasksResponse);
      setAssignments(assignmentsResponse);
    } catch (err) {
      setError('Failed to load task data');
      console.error('Error loading tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = () => {
    // For preview mode, this will be intercepted by FeaturePreview
    navigate('/tasks/new');
  };

  const handleTaskClick = (taskId: number) => {
    // For preview mode, this will be intercepted by FeaturePreview
    navigate(`/tasks/${taskId}`);
  };

  const getPriorityBadge = (priority: string) => {
    const colors = {
      urgent: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
      high: 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300',
      medium: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
      low: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[priority as keyof typeof colors] || colors.medium}`}>
        {priority.charAt(0).toUpperCase() + priority.slice(1)}
      </span>
    );
  };

  const getCategoryBadge = (category?: string) => {
    if (!category) return null;
    
    return (
      <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
        {category}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      assigned: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
      in_progress: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
      completed: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
      overdue: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
      cancelled: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status as keyof typeof colors] || colors.assigned}`}>
        {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
      </span>
    );
  };

  const formatDueDate = (dueDate: string) => {
    const date = new Date(dueDate);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return `${Math.abs(diffDays)} days ago`;
    } else if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Tomorrow';
    } else {
      return `${diffDays} days`;
    }
  };

  const handleAssignmentAction = async (assignmentId: number, action: string) => {
    // For preview mode, this will be intercepted by FeaturePreview
    try {
      if (action === 'start') {
        await operationalTaskService.updateAssignment(assignmentId, { 
          status: 'in_progress',
          started_date: new Date().toISOString()
        });
        loadData(); // Reload data after action
      } else if (action === 'complete') {
        // Find the assignment and open completion modal
        const assignment = assignments.find(a => a.id === assignmentId);
        if (assignment) {
          setSelectedAssignment(assignment);
          setShowCompletionModal(true);
        }
        return; // Don't reload data here, will be handled by modal
      } else if (action === 'cancel') {
        await operationalTaskService.updateAssignment(assignmentId, { 
          status: 'cancelled'
        });
        loadData(); // Reload data after action
      }
    } catch (err) {
      setError(`Failed to ${action} assignment`);
      console.error(`Error ${action} assignment:`, err);
    }
  };

  const handleCompletionModalClose = () => {
    setShowCompletionModal(false);
    setSelectedAssignment(null);
  };

  const handleCompletionSuccess = () => {
    loadData(); // Reload data after successful completion
    handleCompletionModalClose();
  };

  const handleViewDetails = (assignment: TaskAssignment) => {
    setSelectedAssignment(assignment);
    setShowDetailsModal(true);
  };

  const handleDetailsModalClose = () => {
    setShowDetailsModal(false);
    setSelectedAssignment(null);
  };

  const handleDetailsUpdate = () => {
    loadData(); // Reload data after updates
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <FeaturePreview featureKey="task_management">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-navy-blue dark:text-white flex items-center">
                <ClipboardCheck className="mr-3 h-8 w-8" />
                Task & Chore Management
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Create, assign, and track operational tasks with age-based assignment
              </p>
            </div>
            <button
              onClick={handleCreateTask}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center space-x-2"
            >
              <Plus className="h-5 w-5" />
              <span>Create Task</span>
            </button>
          </div>

          {/* Tab Navigation */}
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'overview', label: 'Overview', icon: CheckCircle },
                { id: 'tasks', label: 'Tasks', icon: Calendar },
                { id: 'assignments', label: 'Assignments', icon: Users }
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setSelectedTab(id as any)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    selectedTab === id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Overview Tab */}
          {selectedTab === 'overview' && dashboard && (
            <div className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-blue-100 dark:bg-blue-900/30">
                      <Calendar className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Tasks</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{dashboard.total_tasks}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-green-100 dark:bg-green-900/30">
                      <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Tasks</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{dashboard.active_tasks}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-purple-100 dark:bg-purple-900/30">
                      <Repeat className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Recurring Tasks</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{dashboard.recurring_tasks}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-yellow-100 dark:bg-yellow-900/30">
                      <AlertTriangle className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Overdue</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{dashboard.overdue_assignments}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Assignment Stats */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Assignment Status</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Pending</span>
                      <span className="font-medium">{dashboard.pending_assignments}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">In Progress</span>
                      <span className="font-medium">{dashboard.in_progress_assignments}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Completed</span>
                      <span className="font-medium">{dashboard.completed_assignments}</span>
                    </div>
                    <div className="flex justify-between items-center pt-2 border-t">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">Completion Rate</span>
                      <span className="font-bold text-green-600">{dashboard.completion_rate}%</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Performance Metrics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Total Assignments</span>
                      <span className="font-medium">{dashboard.total_assignments}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Average Completion Time</span>
                      <span className="font-medium">{dashboard.average_completion_time}h</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tasks Tab */}
          {selectedTab === 'tasks' && (
            <div className="space-y-6">
              {/* Tasks List */}
              <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Tasks ({tasks.length})</h3>
                </div>
                
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {tasks.map((task) => (
                    <div 
                      key={task.id} 
                      className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                      onClick={() => handleTaskClick(task.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h4 className="text-lg font-semibold text-gray-900 dark:text-white">{task.title}</h4>
                            {getPriorityBadge(task.priority)}
                            {getCategoryBadge(task.category)}
                            {task.is_recurring && (
                              <div className="flex items-center space-x-1 text-purple-600 dark:text-purple-400">
                                <Repeat className="h-4 w-4" />
                                <span className="text-xs font-medium">Recurring</span>
                              </div>
                            )}
                            {!canUse && (
                              <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-xs">
                                Sample
                              </span>
                            )}
                          </div>
                          
                          {task.description && (
                            <p className="text-gray-600 dark:text-gray-400 mb-2">{task.description}</p>
                          )}
                          
                          <div className="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                            {task.estimated_duration_minutes && (
                              <div className="flex items-center space-x-1">
                                <Clock className="h-4 w-4" />
                                <span>{task.estimated_duration_minutes} min</span>
                              </div>
                            )}
                            
                            {task.location && (
                              <div className="flex items-center space-x-1">
                                <MapPin className="h-4 w-4" />
                                <span>{task.location}</span>
                              </div>
                            )}
                            
                            {task.has_age_restrictions && (
                              <div className="flex items-center space-x-1">
                                <Users className="h-4 w-4" />
                                <span>{task.age_range_description}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <div className={`w-3 h-3 rounded-full ${task.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {tasks.length === 0 && (
                    <div className="px-6 py-12 text-center">
                      <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No tasks found</h3>
                      <p className="text-gray-600 dark:text-gray-400 mb-4">Get started by creating your first task.</p>
                      <button
                        onClick={handleCreateTask}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                      >
                        Create Task
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Assignments Tab */}
          {selectedTab === 'assignments' && (
            <div className="space-y-6">
              {/* Assignments List */}
              <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Assignments ({assignments.length})
                  </h3>
                </div>
                
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {assignments.map((assignment) => (
                    <div key={assignment.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                              {assignment.operational_task?.title || `Task #${assignment.operational_task_id}`}
                            </h4>
                            {getStatusBadge(assignment.status)}
                            {getPriorityBadge(assignment.priority)}
                            {assignment.is_overdue && (
                              <div className="flex items-center space-x-1 text-red-600 dark:text-red-400">
                                <AlertTriangle className="h-4 w-4" />
                                <span className="text-xs font-medium">Overdue</span>
                              </div>
                            )}
                            {!canUse && (
                              <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-xs">
                                Sample
                              </span>
                            )}
                          </div>
                          
                          <div className="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400 mb-2">
                            {assignment.staff_member && (
                              <div className="flex items-center space-x-1">
                                <User className="h-4 w-4" />
                                <span>{assignment.staff_member.full_name}</span>
                              </div>
                            )}
                            
                            <div className="flex items-center space-x-1">
                              <Clock className="h-4 w-4" />
                              <span>{formatDueDate(assignment.due_date)}</span>
                            </div>
                            
                            {assignment.time_spent_minutes > 0 && (
                              <div className="flex items-center space-x-1">
                                <Timer className="h-4 w-4" />
                                <span>{Math.round(assignment.time_spent_minutes / 60)}h spent</span>
                              </div>
                            )}
                            
                            {assignment.progress_percentage > 0 && (
                              <div className="flex items-center space-x-1">
                                <span>{assignment.progress_percentage}% complete</span>
                              </div>
                            )}
                          </div>

                          {/* Progress Bar */}
                          {assignment.progress_percentage > 0 && (
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                                style={{ width: `${assignment.progress_percentage}%` }}
                              ></div>
                            </div>
                          )}

                          {/* Assignment Notes */}
                          {assignment.assignment_notes && (
                            <p className="text-gray-600 dark:text-gray-400 text-sm mb-2">
                              <MessageSquare className="h-4 w-4 inline mr-1" />
                              {assignment.assignment_notes}
                            </p>
                          )}

                          {/* Quality Rating */}
                          {assignment.quality_rating && (
                            <div className="flex items-center space-x-1 text-sm">
                              <Star className="h-4 w-4 text-yellow-500" />
                              <span>Quality: {assignment.quality_rating}/5</span>
                            </div>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {/* View Details Button - Always Visible */}
                          <button
                            onClick={() => handleViewDetails(assignment)}
                            className="flex items-center space-x-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm transition-colors"
                          >
                            <Eye className="h-4 w-4" />
                            <span>Details</span>
                          </button>

                          {/* Action Buttons */}
                          {assignment.status === 'assigned' && (
                            <button
                              onClick={() => handleAssignmentAction(assignment.id, 'start')}
                              className="flex items-center space-x-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm transition-colors"
                            >
                              <PlayCircle className="h-4 w-4" />
                              <span>Start</span>
                            </button>
                          )}
                          
                          {assignment.status === 'in_progress' && (
                            <button
                              onClick={() => handleAssignmentAction(assignment.id, 'complete')}
                              className="flex items-center space-x-1 bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm transition-colors"
                            >
                              <CheckCircle className="h-4 w-4" />
                              <span>Complete</span>
                            </button>
                          )}
                          
                          {assignment.status !== 'completed' && assignment.status !== 'cancelled' && (
                            <button
                              onClick={() => handleAssignmentAction(assignment.id, 'cancel')}
                              className="flex items-center space-x-1 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition-colors"
                            >
                              <XCircle className="h-4 w-4" />
                              <span>Cancel</span>
                            </button>
                          )}

                          {assignment.has_photo_verification && (
                            <div className="text-green-600 dark:text-green-400">
                              <Camera className="h-4 w-4" />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {assignments.length === 0 && (
                    <div className="px-6 py-12 text-center">
                      <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No assignments found</h3>
                      <p className="text-gray-600 dark:text-gray-400 mb-4">
                        Assignments will appear here when tasks are assigned to staff members.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {error && (
            <ErrorMessage message={error} />
          )}
        </div>
      </FeaturePreview>

      {showCompletionModal && selectedAssignment && (
        <AssignmentCompletionModal
          isOpen={showCompletionModal}
          onClose={handleCompletionModalClose}
          onComplete={handleCompletionSuccess}
          assignment={selectedAssignment}
        />
      )}

      {showDetailsModal && selectedAssignment && (
        <AssignmentDetailsModal
          isOpen={showDetailsModal}
          onClose={handleDetailsModalClose}
          onUpdate={handleDetailsUpdate}
          assignment={selectedAssignment}
        />
      )}
    </div>
  );
};

export default TaskManagementPage; 