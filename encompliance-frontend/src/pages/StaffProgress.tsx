import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  ArrowLeft, 
  TrendingUp, 
  Award, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Calendar,
  BarChart3,
  User,
  BookOpen,
  Target
} from 'lucide-react';
import { staffMemberService, trainingAssignmentService, trainingCompletionService } from '../services/trainingService';
import type { StaffMember, TrainingAssignment, TrainingCompletion } from '../services/trainingService';

const StaffProgressPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [staff, setStaff] = useState<StaffMember | null>(null);
  const [assignments, setAssignments] = useState<TrainingAssignment[]>([]);
  const [completions, setCompletions] = useState<TrainingCompletion[]>([]);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (id) {
      loadStaffProgress(parseInt(id));
    }
  }, [id]);

  const loadStaffProgress = async (staffId: number) => {
    try {
      setLoading(true);
      const [staffData, assignmentsData] = await Promise.all([
        staffMemberService.getById(staffId),
        trainingAssignmentService.getAll({ staff_member_id: staffId })
      ]);
      
      setStaff(staffData);
      setAssignments(assignmentsData.assignments);
      
      // Try to load completions, but handle if endpoint is not implemented
      try {
        const completionsData = await trainingCompletionService.getAll({ staff_member_id: staffId });
        // Check if the response is an array (actual data) or an object (placeholder)
        if (Array.isArray(completionsData)) {
          setCompletions(completionsData);
        } else {
          // Endpoint returns placeholder response, set empty array
          setCompletions([]);
        }
      } catch (completionsError) {
        console.warn('Completions endpoint not fully implemented, using empty array:', completionsError);
        setCompletions([]);
      }
    } catch (error) {
      console.error('Error loading staff progress:', error);
      setError('Failed to load staff progress. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: React.ComponentType<any> }> = {
      assigned: { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400', icon: Clock },
      in_progress: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400', icon: TrendingUp },
      completed: { color: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400', icon: CheckCircle },
      overdue: { color: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400', icon: XCircle },
      cancelled: { color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400', icon: XCircle }
    };

    const config = statusConfig[status] || statusConfig.assigned;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="h-3 w-3 mr-1" />
        {status.replace('_', ' ').toUpperCase()}
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

  const getCompletionStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: React.ComponentType<any> }> = {
      completed: { color: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400', icon: CheckCircle },
      verified: { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400', icon: Award },
      expired: { color: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400', icon: XCircle },
      revoked: { color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400', icon: XCircle }
    };

    const config = statusConfig[status] || statusConfig.completed;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="h-3 w-3 mr-1" />
        {status.toUpperCase()}
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

  const getProgressStats = () => {
    const totalAssignments = assignments.length;
    const completedAssignments = assignments.filter(a => a.status === 'completed').length;
    const overdueAssignments = assignments.filter(a => a.is_overdue && a.status !== 'completed').length;
    const inProgressAssignments = assignments.filter(a => a.status === 'in_progress').length;

    return {
      total: totalAssignments,
      completed: completedAssignments,
      overdue: overdueAssignments,
      inProgress: inProgressAssignments,
      completionRate: totalAssignments > 0 ? Math.round((completedAssignments / totalAssignments) * 100) : 0
    };
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="ml-4 text-gray-600 dark:text-gray-400">Loading training progress...</p>
        </div>
      </div>
    );
  }

  if (error || !staff) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <XCircle className="h-12 w-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">Error Loading Progress</h3>
          <p className="text-red-700 dark:text-red-300 mb-4">{error || 'Staff member not found'}</p>
          <button
            onClick={() => navigate('/training/staff')}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Back to Staff Management
          </button>
        </div>
      </div>
    );
  }

  const stats = getProgressStats();

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(`/training/staff/${staff.id}`)}
          className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Staff Details
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
              Training Progress: {staff.first_name} {staff.last_name}
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Detailed training assignments and completion history
            </p>
          </div>
          <button
            onClick={() => navigate(`/training/assignments/new?staff_id=${staff.id}`)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors"
          >
            <BookOpen className="h-4 w-4 mr-2" />
            Assign Training
          </button>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 text-center">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.total}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Total Assignments</div>
        </div>
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 text-center">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.completed}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Completed</div>
        </div>
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 text-center">
          <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.inProgress}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">In Progress</div>
        </div>
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 text-center">
          <div className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.overdue}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Overdue</div>
        </div>
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 text-center">
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">{stats.completionRate}%</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Completion Rate</div>
        </div>
      </div>

      {/* Training Assignments */}
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md mb-6">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <Target className="h-5 w-5 mr-2" />
            Training Assignments ({assignments.length})
          </h3>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {assignments.length === 0 ? (
            <div className="p-12 text-center">
              <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Training Assignments</h4>
              <p className="text-gray-600 dark:text-gray-400 mb-4">This staff member has no training assignments yet.</p>
              <button
                onClick={() => navigate(`/training/assignments/new?staff_id=${staff.id}`)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Assign Training
              </button>
            </div>
          ) : (
            assignments.map((assignment) => (
              <div key={assignment.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Assignment #{assignment.id}
                      </h4>
                      {getStatusBadge(assignment.status)}
                      {getPriorityBadge(assignment.priority)}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600 dark:text-gray-400 mb-3">
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 mr-2" />
                        <span>Due: {formatDate(assignment.due_date)}</span>
                      </div>
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-2" />
                        <span>{getDaysUntilDue(assignment)}</span>
                      </div>
                      <div className="flex items-center">
                        <BarChart3 className="h-4 w-4 mr-2" />
                        <span>Progress: {assignment.progress_percentage}%</span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-3">
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-300 ${
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

                    {assignment.assignment_notes && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                        "{assignment.assignment_notes}"
                      </p>
                    )}
                  </div>
                  
                  <div className="ml-4">
                    <button
                      onClick={() => navigate(`/training/assignments/${assignment.id}`)}
                      className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-3 py-1 rounded text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Training Completions */}
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <Award className="h-5 w-5 mr-2" />
            Training Completions ({completions.length})
          </h3>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {completions.length === 0 ? (
            <div className="p-12 text-center">
              <Award className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Completions Yet</h4>
              <p className="text-gray-600 dark:text-gray-400">This staff member hasn't completed any training yet.</p>
            </div>
          ) : (
            completions.map((completion) => (
              <div key={completion.id} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Training Program #{completion.training_program_id}
                      </h4>
                      {getCompletionStatusBadge(completion.completion_status)}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600 dark:text-gray-400 mb-3">
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 mr-2" />
                        <span>Completed: {formatDate(completion.completed_date)}</span>
                      </div>
                      {completion.final_score && (
                        <div className="flex items-center">
                          <Target className="h-4 w-4 mr-2" />
                          <span>Score: {completion.final_score}%</span>
                        </div>
                      )}
                      {completion.time_spent_minutes && (
                        <div className="flex items-center">
                          <Clock className="h-4 w-4 mr-2" />
                          <span>Time: {completion.time_spent_minutes} minutes</span>
                        </div>
                      )}
                    </div>

                    {completion.certificate_number && (
                      <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 mb-3">
                        <div className="flex items-center">
                          <Award className="h-4 w-4 text-green-600 dark:text-green-400 mr-2" />
                          <span className="text-sm text-green-800 dark:text-green-300">
                            Certificate: {completion.certificate_number}
                          </span>
                        </div>
                      </div>
                    )}

                    {completion.verification_notes && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                        Verification: "{completion.verification_notes}"
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default StaffProgressPage; 