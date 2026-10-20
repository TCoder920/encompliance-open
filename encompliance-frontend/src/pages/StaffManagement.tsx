/*
  Description: Staff Management page for managing facility staff members and their training progress.
  Purpose: Allows facility administrators to add, edit, and monitor staff training progress and certifications.
  
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
  Users, 
  Mail, 
  Phone, 
  Calendar,
  Award,
  AlertTriangle,
  CheckCircle,
  Eye,
  TrendingUp,
  Clock
} from 'lucide-react';
import { staffMemberService, StaffMember } from '../services/trainingService';
import ErrorMessage from '../components/ErrorMessage';
import FeaturePreview from '../components/ui/FeaturePreview';
import { useAuth } from '../contexts/AuthContext';
import { getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature } from '../utils/accessControl';
import { SAMPLE_STAFF_MEMBERS } from '../utils/previewData';

const StaffManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    role: '',
    status: 'active',
    department: ''
  });
  const [showFilters, setShowFilters] = useState(false);


  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUse = canUseFeature(userTier, 'training_certification');

  useEffect(() => {
    loadStaff();
  }, [filters, canUse]);

  const loadStaff = async () => {
    try {
      setLoading(true);
      
      if (canUse) {
        // Load real data for paid users
        const params = {
          search: searchTerm || undefined,
          role: filters.role || undefined,
          status: filters.status || undefined,
          department: filters.department || undefined,
        };
        
        const response = await staffMemberService.getAll(params);
        setStaff(response.staff_members);
      } else {
        // Use sample data for free users
        let filteredStaff = [...SAMPLE_STAFF_MEMBERS];
        
        // Apply filters to sample data
        if (filters.role) {
          filteredStaff = filteredStaff.filter(s => s.role === filters.role);
        }
        if (filters.status) {
          filteredStaff = filteredStaff.filter(s => s.status === filters.status);
        }
        if (filters.department) {
          filteredStaff = filteredStaff.filter(s => s.department && s.department.toLowerCase().includes(filters.department.toLowerCase()));
        }
        if (searchTerm) {
          const searchLower = searchTerm.toLowerCase();
          filteredStaff = filteredStaff.filter(s => 
            s.first_name.toLowerCase().includes(searchLower) ||
            s.last_name.toLowerCase().includes(searchLower) ||
            s.email.toLowerCase().includes(searchLower) ||
            s.employee_id.toLowerCase().includes(searchLower)
          );
        }
        
        setStaff(filteredStaff as unknown as StaffMember[]);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load staff members');
      console.error('Staff error:', err);
      
      // Fallback to sample data on error for free users
      if (!canUse) {
        setStaff(SAMPLE_STAFF_MEMBERS as unknown as StaffMember[]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadStaff();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this staff member?')) return;
    
    try {
      await staffMemberService.delete(id);
      setStaff(staff.filter(s => s.id !== id));
    } catch (err) {
      console.error('Delete error:', err);
      alert('Failed to delete staff member');
    }
  };



  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">Active</span>;
      case 'inactive':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">Inactive</span>;
      case 'terminated':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">Terminated</span>;
      case 'on_leave':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300">On Leave</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">{status}</span>;
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'administrator':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300">Administrator</span>;
      case 'manager':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">Manager</span>;
      case 'supervisor':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300">Supervisor</span>;
      case 'staff':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">Staff</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">{role}</span>;
    }
  };

  const getCompletionRateColor = (rate: number) => {
    if (rate >= 90) return 'text-green-600';
    if (rate >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center h-64">
        <div className="animate-pulse text-navy-blue dark:text-white">Loading staff members...</div>
      </div>
    );
  }

  return (
    <FeaturePreview featureKey="training_certification">
      <div className="container mx-auto px-4 py-6">
        {error && <ErrorMessage message={error} />}
        
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">Staff Management</h1>
          <p className="text-gray-600 dark:text-gray-300">Manage facility staff and track training progress</p>
        </div>

        {/* Quick Actions */}
        <div className="mb-6 flex flex-wrap gap-3">
          <button
            onClick={() => navigate('/training')}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Back to Dashboard
          </button>
          <button
            onClick={() => navigate('/training/staff/new')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Staff Member
          </button>
        </div>

        {/* Search and Filters */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
            <div className="flex-1 flex items-center space-x-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Search staff..."
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
                  <select
                    value={filters.role}
                    onChange={(e) => setFilters({...filters, role: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Roles</option>
                    <option value="administrator">Administrator</option>
                    <option value="manager">Manager</option>
                    <option value="supervisor">Supervisor</option>
                    <option value="staff">Staff</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
                  <select
                    value={filters.status}
                    onChange={(e) => setFilters({...filters, status: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="on_leave">On Leave</option>
                    <option value="terminated">Terminated</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Department</label>
                  <input
                    type="text"
                    placeholder="Filter by department"
                    value={filters.department}
                    onChange={(e) => setFilters({...filters, department: e.target.value})}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Staff List */}
        {staff.length === 0 ? (
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-12 text-center">
            <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Staff Members</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">Get started by adding your first staff member</p>
            <button
              onClick={() => navigate('/training/staff/new')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 flex items-center mx-auto transition-colors"
            >
              <Plus className="h-5 w-5 mr-2" />
              Add Staff Member
            </button>
          </div>
        ) : (
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Staff Members ({staff.length})
              </h3>
            </div>

            {/* Staff Table */}
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {staff.map((member) => (
                <div key={member.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            {member.first_name} {member.last_name}
                          </h3>
                          {getStatusBadge(member.status)}
                          {getRoleBadge(member.role)}
                        </div>
                        
                        <div className="mt-1 flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                          {member.employee_id && (
                            <span>ID: {member.employee_id}</span>
                          )}
                          
                          <span className="flex items-center">
                            <Mail className="h-4 w-4 mr-1" />
                            {member.email}
                          </span>
                          
                          {member.phone_number && (
                            <span className="flex items-center">
                              <Phone className="h-4 w-4 mr-1" />
                              {member.phone_number}
                            </span>
                          )}
                          
                          {member.department && (
                            <span>{member.department}</span>
                          )}
                        </div>
                        
                        {/* Training Progress */}
                        <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="flex items-center">
                            <TrendingUp className="h-4 w-4 text-blue-500 mr-2" />
                            <span className="text-sm text-gray-600 dark:text-gray-400">Completion Rate:</span>
                            <span className={`ml-2 font-semibold ${getCompletionRateColor(member.training_completion_rate)}`}>
                              {member.training_completion_rate}%
                            </span>
                          </div>
                          
                          <div className="flex items-center">
                            <Award className="h-4 w-4 text-green-500 mr-2" />
                            <span className="text-sm text-gray-600 dark:text-gray-400">Current Certifications:</span>
                            <span className="ml-2 font-semibold text-green-600">
                              {member.certifications_current}
                            </span>
                          </div>
                          
                          {member.certifications_expired > 0 && (
                            <div className="flex items-center">
                              <AlertTriangle className="h-4 w-4 text-red-500 mr-2" />
                              <span className="text-sm text-gray-600 dark:text-gray-400">Expired:</span>
                              <span className="ml-2 font-semibold text-red-600">
                                {member.certifications_expired}
                              </span>
                            </div>
                          )}
                          
                          {member.last_training_date && (
                            <div className="flex items-center">
                              <Clock className="h-4 w-4 text-gray-500 mr-2" />
                              <span className="text-sm text-gray-600 dark:text-gray-400">Last Training:</span>
                              <span className="ml-2 text-sm text-gray-900 dark:text-white">
                                {formatDate(member.last_training_date)}
                              </span>
                            </div>
                          )}
                        </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => navigate(`/training/staff/${member.id}/progress`)}
                        className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                        title="View Training Progress"
                      >
                        <TrendingUp className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => navigate(`/training/staff/${member.id}`)}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                        title="View Details"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => navigate(`/training/staff/${member.id}/edit`)}
                        className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                        title="Edit Staff Member"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => handleDelete(member.id)}
                        className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                        title="Delete Staff Member"
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

export default StaffManagementPage; 