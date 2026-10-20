/*
  Description: Policy Management page for facility administrators
  Purpose: Allows admins to create, manage, assign, and track policy acknowledgments
*/
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  Edit,
  Trash2,
  FileText,
  Users,
  CheckCircle,
  Clock,
  AlertTriangle,
  Eye,
  Share2,
  Calendar,
  Tag
} from 'lucide-react';
import policyService, {
  Policy,
  PolicyAssignment,
  PolicyDashboard
} from '../services/policyService';
import { staffMemberService, StaffMember } from '../services/trainingService';
import documentService from '../services/documentService';
import ErrorMessage from '../components/ErrorMessage';
import { useAuth } from '../contexts/AuthContext';

const PolicyManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [dashboard, setDashboard] = useState<PolicyDashboard | null>(null);
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    is_active: undefined as boolean | undefined
  });
  const [showFilters, setShowFilters] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null);
  const [selectedStaffIds, setSelectedStaffIds] = useState<number[]>([]);

  useEffect(() => {
    loadData();
  }, [searchTerm, filters]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [policiesData, dashboardData, staffData] = await Promise.all([
        policyService.getPolicies({
          search: searchTerm || undefined,
          category: filters.category || undefined,
          status: filters.status || undefined,
          is_active: filters.is_active,
          page: 1,
          per_page: 100
        }),
        policyService.getPolicyDashboard(),
        staffMemberService.getAll({ status: 'active' })
      ]);
      
      setPolicies(policiesData);
      setDashboard(dashboardData);
      setStaff(staffData.staff_members);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load policies');
      console.error('Error loading policies:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (policyId: number) => {
    if (!window.confirm('Are you sure you want to delete this policy?')) {
      return;
    }
    
    try {
      await policyService.deletePolicy(policyId);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete policy');
    }
  };

  const handleAssign = async () => {
    if (!selectedPolicy || selectedStaffIds.length === 0) {
      setError('Please select a policy and at least one staff member');
      return;
    }

    try {
      const dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + 30); // Default 30 days

      await policyService.createPolicyAssignments({
        policy_id: selectedPolicy.id,
        staff_member_ids: selectedStaffIds,
        due_date: dueDate.toISOString(),
        priority: 'medium',
        is_mandatory: true
      });

      setShowAssignModal(false);
      setSelectedPolicy(null);
      setSelectedStaffIds([]);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to assign policy');
    }
  };

  const getStatusBadge = (policy: Policy) => {
    if (policy.status === 'active') {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
          Active
        </span>
      );
    } else if (policy.status === 'draft') {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
          Draft
        </span>
      );
    } else if (policy.status === 'expired') {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
          Expired
        </span>
      );
    }
    return null;
  };

  if (loading && policies.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading policies...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Policy Management</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Manage facility policies and track staff acknowledgments
            </p>
          </div>
          <button
            onClick={() => navigate('/policies/create')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Create Policy
          </button>
        </div>

        {/* Dashboard Stats */}
        {dashboard && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Policies</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{dashboard.total_policies}</p>
                </div>
                <FileText className="w-8 h-8 text-blue-500" />
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Active Policies</p>
                  <p className="text-2xl font-bold text-green-600">{dashboard.active_policies}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Pending Acknowledgments</p>
                  <p className="text-2xl font-bold text-yellow-600">{dashboard.pending_acknowledgments}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-500" />
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Overdue</p>
                  <p className="text-2xl font-bold text-red-600">{dashboard.overdue_acknowledgments}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
            </div>
          </div>
        )}

        {/* Search and Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search policies..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <Filter className="w-5 h-5" />
              Filters
            </button>
          </div>

          {showFilters && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Category
                </label>
                <select
                  value={filters.category}
                  onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">All Categories</option>
                  <option value="safety">Safety</option>
                  <option value="hr">HR</option>
                  <option value="operations">Operations</option>
                  <option value="compliance">Compliance</option>
                  <option value="training">Training</option>
                  <option value="security">Security</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Status
                </label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">All Statuses</option>
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="expired">Expired</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Active Status
                </label>
                <select
                  value={filters.is_active === undefined ? '' : filters.is_active.toString()}
                  onChange={(e) => setFilters({
                    ...filters,
                    is_active: e.target.value === '' ? undefined : e.target.value === 'true'
                  })}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">All</option>
                  <option value="true">Active Only</option>
                  <option value="false">Inactive Only</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {error && <ErrorMessage message={error} onClose={() => setError(null)} />}

        {/* Policies List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          {policies.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">No policies found</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {policies.map((policy) => (
                <div key={policy.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {policy.title}
                        </h3>
                        {getStatusBadge(policy)}
                        {policy.category && (
                          <span className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
                            <Tag className="w-4 h-4" />
                            {policy.category}
                          </span>
                        )}
                      </div>
                      {policy.description && (
                        <p className="text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">
                          {policy.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          Version {policy.version}
                        </span>
                        {policy.effective_date && (
                          <span>
                            Effective: {new Date(policy.effective_date).toLocaleDateString()}
                          </span>
                        )}
                        {policy.expiry_date && (
                          <span>
                            Expires: {new Date(policy.expiry_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => navigate(`/policies/${policy.id}`)}
                        className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                        title="View"
                      >
                        <Eye className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => {
                          setSelectedPolicy(policy);
                          setShowAssignModal(true);
                        }}
                        className="p-2 text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400"
                        title="Assign to Staff"
                      >
                        <Share2 className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => navigate(`/policies/${policy.id}/edit`)}
                        className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                        title="Edit"
                      >
                        <Edit className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(policy.id)}
                        className="p-2 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                        title="Delete"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Assign Policy Modal */}
      {showAssignModal && selectedPolicy && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
              Assign Policy: {selectedPolicy.title}
            </h2>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Staff Members
              </label>
              <div className="max-h-60 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-lg p-2">
                {staff.map((member) => (
                  <label
                    key={member.id}
                    className="flex items-center gap-2 p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedStaffIds.includes(member.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedStaffIds([...selectedStaffIds, member.id]);
                        } else {
                          setSelectedStaffIds(selectedStaffIds.filter(id => id !== member.id));
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-gray-900 dark:text-white">
                      {member.first_name} {member.last_name}
                      {member.department && ` - ${member.department}`}
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowAssignModal(false);
                  setSelectedPolicy(null);
                  setSelectedStaffIds([]);
                }}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleAssign}
                disabled={selectedStaffIds.length === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Assign to {selectedStaffIds.length} Staff Member{selectedStaffIds.length !== 1 ? 's' : ''}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PolicyManagementPage;


