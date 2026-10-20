import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  ArrowLeft, 
  Edit, 
  Calendar, 
  Clock, 
  BookOpen, 
  Award,
  Users,
  FileText,
  Video,
  ExternalLink,
  Plus,
  Eye,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { trainingProgramService, trainingMaterialService, trainingAssignmentService } from '../services/trainingService';
import type { TrainingProgram, TrainingMaterial, TrainingAssignment } from '../services/trainingService';

const ProgramDetailsPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [program, setProgram] = useState<TrainingProgram | null>(null);
  const [materials, setMaterials] = useState<TrainingMaterial[]>([]);
  const [assignments, setAssignments] = useState<TrainingAssignment[]>([]);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (id) {
      loadProgramDetails(parseInt(id));
    }
  }, [id]);

  const loadProgramDetails = async (programId: number) => {
    try {
      setLoading(true);
      const [programData, materialsData, assignmentsData] = await Promise.all([
        trainingProgramService.getById(programId),
        trainingMaterialService.getByProgram(programId).catch(() => []),
        trainingAssignmentService.getAll({ training_program_id: programId }).then(res => res.assignments).catch(() => [])
      ]);
      
      setProgram(programData);
      setMaterials(materialsData);
      setAssignments(assignmentsData);
    } catch (error) {
      console.error('Error loading program details:', error);
      setError('Failed to load program details. Please try again.');
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

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'Not specified';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins > 0 ? `${mins}m` : ''}`;
    }
    return `${mins}m`;
  };

  const getStatusBadge = (program: TrainingProgram) => {
    if (!program.is_active) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">
          <XCircle className="h-3 w-3 mr-1" />
          Inactive
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
        <CheckCircle className="h-3 w-3 mr-1" />
        Active
      </span>
    );
  };

  const getMaterialIcon = (type: string) => {
    switch (type) {
      case 'video':
        return <Video className="h-4 w-4" />;
      case 'document':
        return <FileText className="h-4 w-4" />;
      case 'external':
        return <ExternalLink className="h-4 w-4" />;
      default:
        return <BookOpen className="h-4 w-4" />;
    }
  };

  const getAssignmentStats = () => {
    const total = assignments.length;
    const completed = assignments.filter(a => a.status === 'completed').length;
    const inProgress = assignments.filter(a => a.status === 'in_progress').length;
    const overdue = assignments.filter(a => a.is_overdue).length;
    
    return { total, completed, inProgress, overdue };
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="ml-4 text-gray-600 dark:text-gray-400">Loading program details...</p>
        </div>
      </div>
    );
  }

  if (error || !program) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <XCircle className="h-12 w-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">Error Loading Program</h3>
          <p className="text-red-700 dark:text-red-300 mb-4">{error || 'Program not found'}</p>
          <button
            onClick={() => navigate('/training/programs')}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Back to Programs
          </button>
        </div>
      </div>
    );
  }

  const stats = getAssignmentStats();

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/training/programs')}
          className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Training Programs
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
              {program.title}
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Training Program Details
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate(`/training/programs/${program.id}/edit`)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors"
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit Program
            </button>
            <button
              onClick={() => navigate('/training/assignments/new', { state: { training_program_id: program.id } })}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center transition-colors"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Assignment
            </button>
          </div>
        </div>
      </div>

      {/* Program Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <BookOpen className="h-5 w-5 mr-2" />
              Program Information
            </h3>
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                {getStatusBadge(program)}
                {program.is_mandatory && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    Mandatory
                  </span>
                )}
                {program.requires_certification && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                    <Award className="h-3 w-3 mr-1" />
                    Certification Required
                  </span>
                )}
              </div>
              
              {program.description && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <p className="text-gray-900 dark:text-white">{program.description}</p>
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Category
                  </label>
                  <p className="text-gray-900 dark:text-white">{program.category || 'Not specified'}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Delivery Method
                  </label>
                  <p className="text-gray-900 dark:text-white">{program.delivery_method}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Estimated Duration
                  </label>
                  <p className="text-gray-900 dark:text-white flex items-center">
                    <Clock className="h-4 w-4 mr-2" />
                    {formatDuration(program.estimated_duration_minutes)}
                  </p>
                </div>
                
                {program.requires_certification && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Certification Validity
                    </label>
                    <p className="text-gray-900 dark:text-white flex items-center">
                      <Award className="h-4 w-4 mr-2" />
                      {program.certification_valid_months} months
                    </p>
                  </div>
                )}
              </div>
              
              {program.learning_objectives && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Learning Objectives
                  </label>
                  <p className="text-gray-900 dark:text-white">{program.learning_objectives}</p>
                </div>
              )}
              
              {program.prerequisites && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Prerequisites
                  </label>
                  <p className="text-gray-900 dark:text-white">{program.prerequisites}</p>
                </div>
              )}
            </div>
          </div>

          {/* Training Materials */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <FileText className="h-5 w-5 mr-2" />
                Training Materials ({materials.length})
              </h3>
              <button
                onClick={() => navigate(`/training/programs/${program.id}/content`)}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                View All Materials
              </button>
            </div>
            
            {materials.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                No training materials added yet
              </p>
            ) : (
              <div className="space-y-3">
                {materials.slice(0, 5).map((material) => (
                  <div key={material.id} className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="text-gray-400">
                        {getMaterialIcon(material.material_type)}
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white">{material.title}</h4>
                        {material.description && (
                          <p className="text-sm text-gray-500 dark:text-gray-400">{material.description}</p>
                        )}
                      </div>
                    </div>
                    {material.external_url && (
                      <button
                        onClick={() => window.open(material.external_url, '_blank')}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                ))}
                {materials.length > 5 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
                    And {materials.length - 5} more materials...
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Assignment Statistics */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Users className="h-5 w-5 mr-2" />
              Assignment Statistics
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Total Assignments</span>
                <span className="font-semibold text-gray-900 dark:text-white">{stats.total}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Completed</span>
                <span className="font-semibold text-green-600">{stats.completed}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">In Progress</span>
                <span className="font-semibold text-blue-600">{stats.inProgress}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Overdue</span>
                <span className="font-semibold text-red-600">{stats.overdue}</span>
              </div>
              
              {stats.total > 0 && (
                <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Completion Rate</span>
                    <span className="font-medium">{Math.round((stats.completed / stats.total) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(stats.completed / stats.total) * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button
                onClick={() => navigate('/training/assignments/new', { state: { training_program_id: program.id } })}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center justify-center transition-colors"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Assignment
              </button>
              
              <button
                onClick={() => navigate('/training/assignments', { state: { training_program_id: program.id } })}
                className="w-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center justify-center transition-colors"
              >
                <Eye className="h-4 w-4 mr-2" />
                View All Assignments
              </button>
              
              <button
                onClick={() => navigate(`/training/programs/${program.id}/content`)}
                className="w-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center justify-center transition-colors"
              >
                <BookOpen className="h-4 w-4 mr-2" />
                View Training Content
              </button>
            </div>
          </div>

          {/* Program Metadata */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Program Details</h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Created:</span>
                <p className="font-medium text-gray-900 dark:text-white">{formatDate(program.created_at)}</p>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Last Updated:</span>
                <p className="font-medium text-gray-900 dark:text-white">{formatDate(program.updated_at)}</p>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Program ID:</span>
                <p className="font-medium text-gray-900 dark:text-white">{program.id}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgramDetailsPage; 