/*
  Description: Training Overview page for facility administrators to manage training and certification programs.
  Purpose: Provides comprehensive overview of training status, staff progress, and quick access to training management features.
  
  Note: Facility administrators are users with a pro subscription who manage facility operations.
*/

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  BookOpen, 
  ClipboardList, 
  Award, 
  AlertTriangle, 
  Calendar,
  TrendingUp,
  Plus,
  Download,
  Bell,
  Clock
} from 'lucide-react';
import { trainingDashboardService, TrainingDashboard } from '../services/trainingService';
import ErrorMessage from '../components/ErrorMessage';
import FeaturePreview from '../components/ui/FeaturePreview';
import { useAuth } from '../contexts/AuthContext';
import { getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature } from '../utils/accessControl';
import { SAMPLE_TRAINING_PROGRAMS, SAMPLE_STAFF_MEMBERS, SAMPLE_TRAINING_ASSIGNMENTS } from '../utils/previewData';

interface DashboardStats {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  trend?: string;
  onClick?: () => void;
}

const TrainingOverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<TrainingDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  // Memoize canUse to prevent unnecessary re-renders
  const canUse = useMemo(() => canUseFeature(userTier, 'training_certification'), [userTier]);

  useEffect(() => {
    loadDashboard();
  }, [canUse]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      
      if (canUse) {
        // Load real data for paid users
        const data = await trainingDashboardService.getDashboard();
        setDashboard(data);
      } else {
        // Create sample dashboard data for free users
        const sampleDashboard: TrainingDashboard = {
          total_staff: SAMPLE_STAFF_MEMBERS.length,
          total_programs: SAMPLE_TRAINING_PROGRAMS.length,
          total_assignments: SAMPLE_TRAINING_ASSIGNMENTS.length,
          completed_assignments: SAMPLE_TRAINING_ASSIGNMENTS.filter(a => a.status === 'completed').length,
          overdue_assignments: SAMPLE_TRAINING_ASSIGNMENTS.filter(a => a.status === 'overdue').length,
          due_soon_assignments: SAMPLE_TRAINING_ASSIGNMENTS.filter(a => a.status === 'assigned').length,
          completion_rate: 75, // Sample completion rate
          certifications_expiring: 2, // Sample expiring certifications
          recent_completions: [],
          upcoming_due_dates: SAMPLE_TRAINING_ASSIGNMENTS.filter(a => a.status === 'assigned') as unknown as any[]
        };
        setDashboard(sampleDashboard);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load training dashboard');
      console.error('Dashboard error:', err);
      
      // Fallback to sample data on error for free users
      if (!canUse) {
        const sampleDashboard: TrainingDashboard = {
          total_staff: SAMPLE_STAFF_MEMBERS.length,
          total_programs: SAMPLE_TRAINING_PROGRAMS.length,
          total_assignments: SAMPLE_TRAINING_ASSIGNMENTS.length,
          completed_assignments: 1,
          overdue_assignments: 1,
          due_soon_assignments: 1,
          completion_rate: 75,
          certifications_expiring: 2,
          recent_completions: [],
          upcoming_due_dates: []
        };
        setDashboard(sampleDashboard);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-300';
      case 'in_progress': return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-300';
      case 'overdue': return 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-300';
      case 'assigned': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-300';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-300';
      case 'high': return 'text-orange-600 bg-orange-100 dark:bg-orange-900/30 dark:text-orange-300';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'low': return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-300';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center h-64">
        <div className="animate-pulse text-navy-blue dark:text-white">Loading training dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage message={error} />
        <div className="text-center mt-4">
          <button
            onClick={loadDashboard}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Data Available</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">Unable to load training dashboard data</p>
          <button
            onClick={loadDashboard}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const stats: DashboardStats[] = user?.user_role === 'team_member' 
    ? [
        // Team member-specific stats
        {
          title: 'My Training Programs',
          value: dashboard.total_programs,
          icon: <BookOpen className="h-6 w-6" />,
          color: 'bg-green-500',
          onClick: () => navigate('/training/programs')
        },
        {
          title: 'My Active Assignments',
          value: dashboard.total_assignments,
          icon: <ClipboardList className="h-6 w-6" />,
          color: 'bg-purple-500',
          onClick: () => navigate('/training/assignments')
        },
        {
          title: 'My Completed',
          value: dashboard.completed_assignments,
          icon: <Award className="h-6 w-6" />,
          color: 'bg-yellow-500',
          onClick: () => navigate('/training/assignments?status=completed')
        },
        {
          title: 'Overdue Tasks',
          value: dashboard.overdue_assignments,
          icon: <AlertTriangle className="h-6 w-6" />,
          color: 'bg-red-500',
          onClick: () => navigate('/training/assignments?status=overdue')
        }
      ]
    : [
        // Facility admin stats (original)
    {
      title: 'Total Staff',
      value: dashboard.total_staff,
      icon: <Users className="h-6 w-6" />,
      color: 'bg-blue-500',
      onClick: () => navigate('/training/staff')
    },
    {
      title: 'Training Programs',
      value: dashboard.total_programs,
      icon: <BookOpen className="h-6 w-6" />,
      color: 'bg-green-500',
      onClick: () => navigate('/training/programs')
    },
    {
      title: 'Active Assignments',
      value: dashboard.total_assignments,
      icon: <ClipboardList className="h-6 w-6" />,
      color: 'bg-purple-500',
      onClick: () => navigate('/training/assignments')
    },
    {
      title: 'Completed',
      value: dashboard.completed_assignments,
      icon: <Award className="h-6 w-6" />,
      color: 'bg-green-600',
      onClick: () => navigate('/training/assignments?status=completed')
    },
    {
      title: 'Overdue',
      value: dashboard.overdue_assignments,
      icon: <AlertTriangle className="h-6 w-6" />,
      color: 'bg-red-500',
      onClick: () => navigate('/training/assignments?status=overdue')
    },
    {
      title: 'Due Soon',
      value: dashboard.due_soon_assignments,
      icon: <Calendar className="h-6 w-6" />,
      color: 'bg-orange-500',
      onClick: () => navigate('/training/assignments?due_soon=true')
    }
  ];

  return (
    <FeaturePreview featureKey="training_certification">
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">
            {user?.user_role === 'team_member' ? 'My Training Overview' : 'Training Overview'}
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            {user?.user_role === 'team_member' 
              ? 'Track your training progress and upcoming assignments' 
              : 'Manage staff training programs and track compliance'
            }
          </p>
        </div>

        {/* Quick Actions - Only show for facility administrators */}
        {user?.user_role !== 'team_member' && (
        <div className="mb-8 flex flex-wrap gap-3">
          <button
            onClick={() => navigate('/training/programs/new')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Program
          </button>
          <button
            onClick={() => navigate('/training/analytics')}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center transition-colors"
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            Analytics
          </button>
          <button
            onClick={() => navigate('/training/reports')}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center transition-colors"
          >
            <Download className="h-4 w-4 mr-2" />
            Reports
          </button>
        </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <div
              key={index}
              onClick={stat.onClick}
              className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center">
                <div className={`${stat.color} text-white p-3 rounded-lg flex-shrink-0`}>
                  {stat.icon}
                </div>
                <div className="ml-4 min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400 truncate" title={stat.title}>
                    {stat.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stat.value}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Completion Rate */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {user?.user_role === 'team_member' ? 'My Completion Rate' : 'Overall Completion Rate'}
            </h3>
            <span className="text-2xl font-bold text-green-600">{dashboard.completion_rate.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div
              className="bg-green-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${dashboard.completion_rate}%` }}
            ></div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Upcoming Deadlines</h3>
                <div className="mt-4">
                  {dashboard.upcoming_due_dates.length === 0 ? (
                    <p className="text-gray-500 dark:text-gray-400 text-center py-4">No upcoming due dates</p>
                  ) : (
                    <div className="space-y-4">
                      {dashboard.upcoming_due_dates.slice(0, 5).map((assignment) => (
                        <div key={assignment.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <div className="flex items-center">
                            <div className={`p-2 rounded-full ${assignment.is_overdue ? 'bg-red-100 dark:bg-red-900/30' : 'bg-orange-100 dark:bg-orange-900/30'}`}>
                              <Calendar className={`h-4 w-4 ${assignment.is_overdue ? 'text-red-600 dark:text-red-400' : 'text-orange-600 dark:text-orange-400'}`} />
                            </div>
                            <div className="ml-3">
                              <p className="text-sm font-medium text-gray-900 dark:text-white">Training Due</p>
                              <p className="text-xs text-gray-600 dark:text-gray-400">
                                Due: {formatDate(assignment.due_date)}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(assignment.priority)}`}>
                              {assignment.priority}
                            </span>
                            <span className={`block mt-1 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(assignment.status)}`}>
                              {assignment.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Alerts */}
        {dashboard.overdue_assignments > 0 && (
          <div className="mt-8 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 mr-3" />
              <div>
                <h4 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Overdue Training Assignments
                </h4>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  {dashboard.overdue_assignments} training assignments are overdue and require immediate attention.
                </p>
              </div>
              <button
                onClick={() => navigate('/training/assignments?status=overdue')}
                className="ml-auto bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 text-sm"
              >
                View Overdue
              </button>
            </div>
          </div>
        )}
      </div>
    </FeaturePreview>
  );
};

export default TrainingOverviewPage; 