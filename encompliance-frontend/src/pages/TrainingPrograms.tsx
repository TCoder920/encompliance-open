/*
  Description: Training Programs management page for creating and managing training programs.
  Purpose: Allows facility administrators to create, edit, and manage training programs with materials and assignments.
  
  Note: Facility administrators are users with a pro subscription who manage facility operations.
*/

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Search, 
  Filter, 
  Edit, 
  Trash2, 
  BookOpen, 
  Users, 
  Clock, 
  Award,
  AlertTriangle,
  CheckCircle,
  Eye
} from 'lucide-react';
import { trainingProgramService, TrainingProgram } from '../services/trainingService';
import ErrorMessage from '../components/ErrorMessage';
import FeaturePreview from '../components/ui/FeaturePreview';
import { useAuth } from '../contexts/AuthContext';
import { getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature } from '../utils/accessControl';
import { SAMPLE_TRAINING_PROGRAMS } from '../utils/previewData';

const TrainingProgramsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [programs, setPrograms] = useState<TrainingProgram[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    is_mandatory: '',
    requires_certification: '',
    is_active: 'true'
  });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedPrograms, setSelectedPrograms] = useState<number[]>([]);

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUse = canUseFeature(userTier, 'training_certification');

  useEffect(() => {
    loadPrograms();
  }, [filters, canUse]);

  const loadPrograms = async () => {
    try {
      setLoading(true);
      
      if (canUse) {
        // Load real data for paid users
        const params = {
          search: searchTerm || undefined,
          category: filters.category || undefined,
          is_mandatory: filters.is_mandatory ? filters.is_mandatory === 'true' : undefined,
          requires_certification: filters.requires_certification ? filters.requires_certification === 'true' : undefined,
          is_active: filters.is_active ? filters.is_active === 'true' : undefined,
        };
        
        const response = await trainingProgramService.getAll(params);
        setPrograms(response.programs);
      } else {
        // Use sample data for free users
        let filteredPrograms = [...SAMPLE_TRAINING_PROGRAMS];
        
        // Apply filters to sample data
        if (filters.category) {
          filteredPrograms = filteredPrograms.filter(p => p.category === filters.category);
        }
        if (filters.is_mandatory) {
          filteredPrograms = filteredPrograms.filter(p => p.is_mandatory === (filters.is_mandatory === 'true'));
        }
        if (filters.requires_certification) {
          filteredPrograms = filteredPrograms.filter(p => p.requires_certification === (filters.requires_certification === 'true'));
        }
        if (searchTerm) {
          const searchLower = searchTerm.toLowerCase();
          filteredPrograms = filteredPrograms.filter(p => 
            p.title.toLowerCase().includes(searchLower) ||
            (p.description && p.description.toLowerCase().includes(searchLower))
          );
        }
        
        setPrograms(filteredPrograms as unknown as TrainingProgram[]);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load training programs');
      console.error('Programs error:', err);
      
      // Fallback to sample data on error for free users
      if (!canUse) {
        setPrograms(SAMPLE_TRAINING_PROGRAMS as unknown as TrainingProgram[]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadPrograms();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this training program?')) return;
    
    try {
      await trainingProgramService.delete(id);
      setPrograms(programs.filter(p => p.id !== id));
    } catch (err) {
      console.error('Delete error:', err);
      alert('Failed to delete training program');
    }
  };

  const handleBulkDelete = async () => {
    if (!confirm(`Are you sure you want to delete ${selectedPrograms.length} training programs?`)) return;
    
    try {
      await Promise.all(selectedPrograms.map(id => trainingProgramService.delete(id)));
      setPrograms(programs.filter(p => !selectedPrograms.includes(p.id)));
      setSelectedPrograms([]);
    } catch (err) {
      console.error('Bulk delete error:', err);
      alert('Failed to delete some training programs');
    }
  };

  const toggleProgramSelection = (id: number) => {
    setSelectedPrograms(prev => 
      prev.includes(id) 
        ? prev.filter(pid => pid !== id)
        : [...prev, id]
    );
  };

  const toggleAllPrograms = () => {
    setSelectedPrograms(
      selectedPrograms.length === programs.length 
        ? [] 
        : programs.map(p => p.id)
    );
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
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">Inactive</span>;
    }
    if (program.is_mandatory) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">Mandatory</span>;
    }
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">Optional</span>;
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center h-64">
        <div className="animate-pulse text-navy-blue dark:text-white">Loading training programs...</div>
      </div>
    );
  }

  return (
    <FeaturePreview featureKey="training_certification">
      <div className="container mx-auto px-4 py-6">
        {error && <ErrorMessage message={error} />}
        
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">Training Programs</h1>
          <p className="text-gray-600 dark:text-gray-300">Create and manage training programs for your facility</p>
        </div>

        {/* Quick Actions */}
        <div className="mb-6 flex flex-wrap gap-3">
          <button
            onClick={() => navigate('/training')}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Back to Dashboard
          </button>
          {/* New Program button - Only show for facility administrators */}
          {user?.user_role !== 'team_member' && (
          <button
            onClick={() => navigate('/training/programs/new')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Program
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
                  placeholder="Search programs..."
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
              
              {selectedPrograms.length > 0 && (
                <button
                  onClick={handleBulkDelete}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex items-center transition-colors"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete ({selectedPrograms.length})
                </button>
              )}
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Category</label>
                  <select
                    value={filters.category}
                    onChange={(e) => setFilters({...filters, category: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Categories</option>
                    <option value="Safety">Safety</option>
                    <option value="Compliance">Compliance</option>
                    <option value="Technical">Technical</option>
                    <option value="Administrative">Administrative</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
                  <select
                    value={filters.is_mandatory}
                    onChange={(e) => setFilters({...filters, is_mandatory: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Types</option>
                    <option value="true">Mandatory</option>
                    <option value="false">Optional</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Certification</label>
                  <select
                    value={filters.requires_certification}
                    onChange={(e) => setFilters({...filters, requires_certification: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Programs</option>
                    <option value="true">With Certification</option>
                    <option value="false">No Certification</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
                  <select
                    value={filters.is_active}
                    onChange={(e) => setFilters({...filters, is_active: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Status</option>
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Programs List */}
        {programs.length === 0 ? (
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-12 text-center">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Training Programs</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">Get started by creating your first training program</p>
            {/* Create Training Program button - Only show for facility administrators */}
            {user?.user_role !== 'team_member' && (
            <button
              onClick={() => navigate('/training/programs/new')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 flex items-center mx-auto transition-colors"
            >
              <Plus className="h-5 w-5 mr-2" />
              Create Training Program
            </button>
            )}
          </div>
        ) : (
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md overflow-hidden">
            {/* Table Header */}
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedPrograms.length === programs.length}
                  onChange={toggleAllPrograms}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                  {selectedPrograms.length > 0 ? `${selectedPrograms.length} selected` : 'Select all'}
                </span>
              </div>
            </div>

            {/* Programs Table */}
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {programs.map((program) => (
                <div key={program.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <input
                        type="checkbox"
                        checked={selectedPrograms.includes(program.id)}
                        onChange={() => toggleProgramSelection(program.id)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{program.title}</h3>
                          {getStatusBadge(program)}
                          {program.requires_certification && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                              <Award className="h-3 w-3 mr-1" />
                              Certification
                            </span>
                          )}
                        </div>
                        
                        {program.description && (
                          <p className="mt-1 text-gray-600 dark:text-gray-400 text-sm">{program.description}</p>
                        )}
                        
                        <div className="mt-2 flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                          {program.category && (
                            <span className="flex items-center">
                              <BookOpen className="h-4 w-4 mr-1" />
                              {program.category}
                            </span>
                          )}
                          
                          <span className="flex items-center">
                            <Clock className="h-4 w-4 mr-1" />
                            {formatDuration(program.estimated_duration_minutes)}
                          </span>
                          
                          <span className="flex items-center">
                            <Users className="h-4 w-4 mr-1" />
                            {program.delivery_method}
                          </span>
                          
                          {program.requires_certification && (
                            <span className="flex items-center">
                              <Award className="h-4 w-4 mr-1" />
                              Valid {program.certification_valid_months} months
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => navigate(`/training/programs/${program.id}`)}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                        title="View Details"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => navigate(`/training/programs/${program.id}/edit`)}
                        className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                        title="Edit Program"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => handleDelete(program.id)}
                        className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                        title="Delete Program"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </FeaturePreview>
  );
};

export default TrainingProgramsPage; 