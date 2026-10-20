import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Award, 
  Calendar, 
  Search, 
  Filter, 
  Download, 
  ArrowLeft,
  TrendingUp,
  CheckCircle,
  Clock,
  AlertTriangle
} from 'lucide-react';

interface TrainingCompletion {
  id: number;
  staff_member_id: number;
  training_program_id: number;
  training_assignment_id: number;
  completion_status: string;
  completed_date: string;
  final_score?: number;
  time_spent_minutes?: number;
  certificate_number?: string;
  certificate_issued_date?: string;
  expires_date?: string;
  certificate_status?: string;
  staff_name?: string;
  program_title?: string;
  created_at: string;
  updated_at: string;
}

interface CompletionsResponse {
  completions: TrainingCompletion[];
  total: number;
  page: number;
  per_page: number;
}

const TrainingCompletionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [completions, setCompletions] = useState<TrainingCompletion[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    status: '',
    date_from: '',
    date_to: '',
    program_id: '',
    staff_id: ''
  });

  useEffect(() => {
    loadCompletions();
  }, [currentPage, filters]);

  const loadCompletions = async () => {
    try {
      setLoading(true);
      // Note: This would need to be implemented in the backend
      // For now, we'll show a placeholder message
      setCompletions([]);
      setTotalPages(1);
    } catch (error) {
      console.error('Error loading completions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setCurrentPage(1);
    loadCompletions();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      completed: { color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400', icon: CheckCircle },
      in_progress: { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400', icon: Clock },
      failed: { color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400', icon: AlertTriangle },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.completed;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="h-3 w-3 mr-1" />
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const getCertificateStatusBadge = (status?: string) => {
    if (!status) return null;

    const statusConfig = {
      issued: { color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' },
      pending: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' },
      expired: { color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' },
      revoked: { color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400' },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <button
              onClick={() => navigate('/training')}
              className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Training Overview
            </button>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
              Training Completions
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              View and manage all training completion records
            </p>
          </div>
          
          <button
            onClick={() => {/* TODO: Implement export */}}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center transition-colors"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="flex-1 flex items-center space-x-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <input
                type="text"
                placeholder="Search completions..."
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
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center transition-colors"
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </button>
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
                  <option value="completed">Completed</option>
                  <option value="in_progress">In Progress</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">From Date</label>
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => setFilters({...filters, date_from: e.target.value})}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">To Date</label>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => setFilters({...filters, date_to: e.target.value})}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Program</label>
                <input
                  type="text"
                  placeholder="Program ID"
                  value={filters.program_id}
                  onChange={(e) => setFilters({...filters, program_id: e.target.value})}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Staff</label>
                <input
                  type="text"
                  placeholder="Staff ID"
                  value={filters.staff_id}
                  onChange={(e) => setFilters({...filters, staff_id: e.target.value})}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Completions List */}
      {loading ? (
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 dark:text-gray-400 mt-4">Loading completions...</p>
        </div>
      ) : completions.length === 0 ? (
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-12 text-center">
          <Award className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Training Completions</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Training completions will appear here once staff members complete their assigned training programs.
          </p>
          <button
            onClick={() => navigate('/training/assignments')}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 flex items-center mx-auto transition-colors"
          >
            <Calendar className="h-5 w-5 mr-2" />
            View Training Assignments
          </button>
        </div>
      ) : (
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md overflow-hidden">
          {/* Completions Table */}
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {completions.map((completion) => (
              <div key={completion.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {completion.program_title || `Program ${completion.training_program_id}`}
                      </h3>
                      {getStatusBadge(completion.completion_status)}
                      {getCertificateStatusBadge(completion.certificate_status)}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 mr-2" />
                        <span>Completed: {formatDate(completion.completed_date)}</span>
                      </div>
                      
                      {completion.final_score && (
                        <div className="flex items-center">
                          <TrendingUp className="h-4 w-4 mr-2" />
                          <span>Score: {completion.final_score}%</span>
                        </div>
                      )}
                      
                      {completion.time_spent_minutes && (
                        <div className="flex items-center">
                          <Clock className="h-4 w-4 mr-2" />
                          <span>Duration: {Math.round(completion.time_spent_minutes)} min</span>
                        </div>
                      )}
                      
                      {completion.certificate_number && (
                        <div className="flex items-center">
                          <Award className="h-4 w-4 mr-2" />
                          <span>Cert: {completion.certificate_number}</span>
                        </div>
                      )}
                    </div>
                    
                    {completion.expires_date && (
                      <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                        <span>Expires: {formatDate(completion.expires_date)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
              <div className="flex items-center justify-between">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Page {currentPage} of {totalPages}
                </span>
                
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TrainingCompletionsPage; 