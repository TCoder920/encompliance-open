/*
  Description: Training Assignments page for managing and tracking training assignments.
  Purpose: Allows facility administrators to create, monitor, and manage training assignments with progress tracking.
  
  Note: Facility administrators are users with a pro subscription who manage facility operations.
*/

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Plus, 
  Search, 
  Filter, 
  Edit, 
  Trash2, 
  ClipboardList, 
  Calendar, 
  Clock, 
  User,
  AlertTriangle,
  CheckCircle,
  Eye,
  Play,
  BarChart3
} from 'lucide-react';
import { trainingAssignmentService, trainingProgramService, trainingMaterialService, TrainingAssignment } from '../services/trainingService';
import ErrorMessage from '../components/ErrorMessage';
import FeaturePreview from '../components/ui/FeaturePreview';
import { useAuth } from '../contexts/AuthContext';
import { getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature } from '../utils/accessControl';
import { SAMPLE_TRAINING_ASSIGNMENTS } from '../utils/previewData';

const TrainingAssignmentsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [assignments, setAssignments] = useState<TrainingAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    priority: '',
    training_program_id: '',
    staff_member_id: '',
    due_date_from: '',
    due_date_to: '',
    overdue_only: searchParams.get('overdue') === 'true' || searchParams.get('due_soon') === 'true'
  });
  const [showFilters, setShowFilters] = useState(false);

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUse = canUseFeature(userTier, 'training_certification');

  useEffect(() => {
    loadAssignments();
  }, [filters, canUse]);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      
      if (canUse) {
        // Load real data for paid users
        const params = {
          search: searchTerm || undefined,
          status: filters.status || undefined,
          priority: filters.priority || undefined,
          training_program_id: filters.training_program_id ? parseInt(filters.training_program_id) : undefined,
          staff_member_id: filters.staff_member_id ? parseInt(filters.staff_member_id) : undefined,
          due_date_from: filters.due_date_from || undefined,
          due_date_to: filters.due_date_to || undefined,
          overdue_only: filters.overdue_only || undefined,
        };
        
        const response = await trainingAssignmentService.getAll(params);
        setAssignments(response.assignments);
      } else {
        // Use sample data for free users
        let filteredAssignments = [...SAMPLE_TRAINING_ASSIGNMENTS];
        
        // Apply filters to sample data
        if (filters.status) {
          filteredAssignments = filteredAssignments.filter(a => a.status === filters.status);
        }
        if (filters.priority) {
          filteredAssignments = filteredAssignments.filter(a => a.priority === filters.priority);
        }
        if (filters.overdue_only) {
          const now = new Date();
          filteredAssignments = filteredAssignments.filter(a => 
            new Date(a.due_date) < now && a.status !== 'completed'
          );
        }
        
        setAssignments(filteredAssignments as unknown as TrainingAssignment[]);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load training assignments');
      console.error('Assignments error:', err);
      
      // Fallback to sample data on error for free users
      if (!canUse) {
        setAssignments(SAMPLE_TRAINING_ASSIGNMENTS as unknown as TrainingAssignment[]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadAssignments();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this training assignment?')) return;
    
    try {
      await trainingAssignmentService.delete(id);
      setAssignments(assignments.filter(a => a.id !== id));
    } catch (err) {
      console.error('Delete error:', err);
      alert('Failed to delete training assignment');
    }
  };

  const handleStartTraining = async (id: number) => {
    try {
      // Get the assignment to find the training program and check for custom training URL
      const assignment = await trainingAssignmentService.getById(id);
      
      // Only mark as started if it's currently assigned (not already in progress)
      if (assignment.status === 'assigned') {
        await trainingAssignmentService.markStarted(id);
      }
      
      // Check if assignment has a custom training URL
      if (assignment.training_url) {
        // Use the custom training URL specified in the assignment
        window.open(assignment.training_url, '_blank');
        // Refresh the assignments list to show updated status (only if we marked it as started)
        if (assignment.status === 'assigned') {
          loadAssignments();
        }
        return;
      }
      
      // If no custom URL, fall back to training program materials
      // Get the training program details
      const program = await trainingProgramService.getById(assignment.training_program_id);
      
      // Get the training materials for this program
      const materials = await trainingMaterialService.getByProgram(assignment.training_program_id);
      
      // Find the first material with an external URL or determine the training route
      const externalMaterial = materials.find(material => material.external_url);
      
      if (externalMaterial && externalMaterial.external_url) {
        // Redirect to external training URL from materials
        window.open(externalMaterial.external_url, '_blank');
      } else if (materials.length > 0) {
        // Redirect to internal training content page
        navigate(`/training/programs/${assignment.training_program_id}/content?assignment_id=${id}`);
      } else {
        // No materials found, redirect to program details
        navigate(`/training/programs/${assignment.training_program_id}?assignment_id=${id}`);
      }
      
      // Refresh the assignments list to show updated status (only if we marked it as started)
      if (assignment.status === 'assigned') {
        loadAssignments();
      }
    } catch (err) {
      console.error('Start training error:', err);
      alert('Failed to start training. Please try again.');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (assignment: TrainingAssignment) => {
    if (assignment.is_overdue) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">Overdue</span>;
    }
    
    switch (assignment.status) {
      case 'completed':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">Completed</span>;
      case 'in_progress':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">In Progress</span>;
      case 'assigned':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300">Assigned</span>;
      case 'cancelled':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">Cancelled</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">{assignment.status}</span>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">Urgent</span>;
      case 'high':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300">High</span>;
      case 'medium':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300">Medium</span>;
      case 'low':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">Low</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">{priority}</span>;
    }
  };

  const getDaysUntilDue = (assignment: TrainingAssignment) => {
    if (assignment.days_until_due === null || assignment.days_until_due === undefined) return null;
    
    if (assignment.days_until_due < 0) {
      return `${Math.abs(assignment.days_until_due)} days overdue`;
    } else if (assignment.days_until_due === 0) {
      return 'Due today';
    } else {
      return `${assignment.days_until_due} days remaining`;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center h-64">
        <div className="animate-pulse text-navy-blue dark:text-white">Loading training assignments...</div>
      </div>
    );
  }

  return (
    <FeaturePreview featureKey="training_certification">
      <div className="container mx-auto px-4 py-6">
        {error && <ErrorMessage message={error} />}
        
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">Training Assignments</h1>
          <p className="text-gray-600 dark:text-gray-300">Manage and track training assignments for your facility</p>
        </div>

        {/* Quick Actions */}
        <div className="mb-6 flex flex-wrap gap-3">
          <button
            onClick={() => navigate('/training')}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Back to Dashboard
          </button>
          {/* New Assignment button - Only show for facility administrators */}
          {user?.user_role !== 'team_member' && (
          <button
            onClick={() => navigate('/training/assignments/new')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Assignment
          </button>
          )}
        </div>

        {/* Search and Filters */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
            <div className="flex-1 flex items-center space-x-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Search assignments..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full dark:bg-gray-700 dark:text-white"
                />
              </div>
              <button
                onClick={handleSearch}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Search
              </button>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center transition-colors"
              >
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </button>
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
                  <select
                    value={filters.status}
                    onChange={(e) => setFilters({...filters, status: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Status</option>
                    <option value="assigned">Assigned</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="overdue">Overdue</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Priority</label>
                  <select
                    value={filters.priority}
                    onChange={(e) => setFilters({...filters, priority: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Priorities</option>
                    <option value="urgent">Urgent</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Due Date From</label>
                  <input
                    type="date"
                    value={filters.due_date_from}
                    onChange={(e) => setFilters({...filters, due_date_from: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Due Date To</label>
                  <input
                    type="date"
                    value={filters.due_date_to}
                    onChange={(e) => setFilters({...filters, due_date_to: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Show Only</label>
                  <select
                    value={filters.overdue_only ? 'overdue' : ''}
                    onChange={(e) => setFilters({...filters, overdue_only: e.target.value === 'overdue'})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Assignments</option>
                    <option value="overdue">Overdue/Due Soon</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Assignments List */}
        {assignments.length === 0 ? (
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-12 text-center">
            <ClipboardList className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Training Assignments</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">Get started by creating your first training assignment</p>
          </div>
        ) :
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md overflow-hidden">
            {/* Assignments Grid */}
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {assignments.map((assignment) => (
                <div key={assignment.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Training Assignment #{assignment.id}</h3>
                        {getStatusBadge(assignment)}
                        {getPriorityBadge(assignment.priority)}
                      </div>
                      
                      <div className="mt-2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-gray-600 dark:text-gray-400">
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
                        
                        <div className="flex items-center">
                          <User className="h-4 w-4 mr-2" />
                          <span>Staff ID: {assignment.staff_member_id}</span>
                        </div>
                      </div>
                      
                      {assignment.assignment_notes && (
                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{assignment.assignment_notes}</p>
                      )}
                      
                      {/* Progress Bar */}
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                          <span>Progress</span>
                          <span>{assignment.progress_percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                            style={{ width: `${assignment.progress_percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {(assignment.status === 'assigned' || assignment.status === 'in_progress') && (
                        <button
                          onClick={() => handleStartTraining(assignment.id)}
                          className="p-2 text-gray-400 hover:text-green-600 transition-colors"
                          title={assignment.status === 'assigned' ? 'Start Training' : 'Resume Training'}
                        >
                          <Play className="h-4 w-4" />
                        </button>
                      )}
                      
                      <button
                        onClick={() => navigate(`/training/assignments/${assignment.id}`)}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                        title="View Details"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => navigate(`/training/assignments/${assignment.id}/edit`)}
                        className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                        title="Edit Assignment"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => handleDelete(assignment.id)}
                        className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                        title="Delete Assignment"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        }
      </div>
    </FeaturePreview>
  );
};

export default TrainingAssignmentsPage; 