import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  ArrowLeft, 
  Edit, 
  Mail, 
  Phone, 
  Calendar, 
  User, 
  Building,
  Award,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  Clock,
  MapPin
} from 'lucide-react';
import { staffMemberService } from '../services/trainingService';
import type { StaffMember } from '../services/trainingService';

const StaffDetailsPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [staff, setStaff] = useState<StaffMember | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (id) {
      loadStaff(parseInt(id));
    }
  }, [id]);

  const loadStaff = async (staffId: number) => {
    try {
      setLoading(true);
      const data = await staffMemberService.getById(staffId);
      setStaff(data);
    } catch (error) {
      console.error('Error loading staff member:', error);
      setError('Failed to load staff member details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: React.ComponentType<any> }> = {
      active: { color: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400', icon: CheckCircle },
      inactive: { color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400', icon: XCircle },
      terminated: { color: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400', icon: XCircle },
      on_leave: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400', icon: Clock }
    };

    const config = statusConfig[status] || statusConfig.active;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="h-3 w-3 mr-1" />
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const getRoleBadge = (role: string) => {
    const roleConfig: Record<string, string> = {
      administrator: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
      manager: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      supervisor: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-400',
      staff: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleConfig[role] || roleConfig.staff}`}>
        <User className="h-3 w-3 mr-1" />
        {role.toUpperCase()}
      </span>
    );
  };

  const getCompletionRateColor = (rate: number) => {
    if (rate >= 90) return 'text-green-600 dark:text-green-400';
    if (rate >= 70) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="ml-4 text-gray-600 dark:text-gray-400">Loading staff member details...</p>
        </div>
      </div>
    );
  }

  if (error || !staff) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <XCircle className="h-12 w-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">Error Loading Staff Member</h3>
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

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/training/staff')}
          className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Staff Management
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
              {staff.first_name} {staff.last_name}
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Staff Member Details and Training Progress
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate(`/training/staff/${staff.id}/progress`)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center transition-colors"
            >
              <TrendingUp className="h-4 w-4 mr-2" />
              View Progress
            </button>
            <button
              onClick={() => navigate(`/training/staff/${staff.id}/edit`)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors"
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit Details
            </button>
          </div>
        </div>
      </div>

      {/* Staff Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status and Role */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Status & Role</h3>
            <div className="flex items-center space-x-4">
              {getStatusBadge(staff.status)}
              {getRoleBadge(staff.role)}
            </div>
          </div>

          {/* Personal Information */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <User className="h-5 w-5 mr-2" />
              Personal Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {staff.employee_id && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Employee ID
                  </label>
                  <p className="text-gray-900 dark:text-white">{staff.employee_id}</p>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email
                </label>
                <div className="flex items-center">
                  <Mail className="h-4 w-4 text-gray-400 mr-2" />
                  <a href={`mailto:${staff.email}`} className="text-blue-600 dark:text-blue-400 hover:underline">
                    {staff.email}
                  </a>
                </div>
              </div>
              {staff.phone_number && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Phone Number
                  </label>
                  <div className="flex items-center">
                    <Phone className="h-4 w-4 text-gray-400 mr-2" />
                    <a href={`tel:${staff.phone_number}`} className="text-blue-600 dark:text-blue-400 hover:underline">
                      {staff.phone_number}
                    </a>
                  </div>
                </div>
              )}
              {staff.hire_date && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Hire Date
                  </label>
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                    <p className="text-gray-900 dark:text-white">{formatDate(staff.hire_date)}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Work Information */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Building className="h-5 w-5 mr-2" />
              Work Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {staff.department && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Department
                  </label>
                  <p className="text-gray-900 dark:text-white">{staff.department}</p>
                </div>
              )}
              {staff.position_title && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Position Title
                  </label>
                  <p className="text-gray-900 dark:text-white">{staff.position_title}</p>
                </div>
              )}
              {staff.facility_name && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Facility Name
                  </label>
                  <p className="text-gray-900 dark:text-white">{staff.facility_name}</p>
                </div>
              )}
              {staff.facility_location && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Facility Location
                  </label>
                  <div className="flex items-center">
                    <MapPin className="h-4 w-4 text-gray-400 mr-2" />
                    <p className="text-gray-900 dark:text-white">{staff.facility_location}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Training Overview */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Training Overview
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className={`text-2xl font-bold ${getCompletionRateColor(staff.training_completion_rate)}`}>
                  {staff.training_completion_rate}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Completion Rate</div>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {staff.certifications_current}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Current Certifications</div>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {staff.certifications_expired}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Expired Certifications</div>
              </div>
            </div>
            {staff.last_training_date && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-center">
                  <Clock className="h-4 w-4 text-blue-600 dark:text-blue-400 mr-2" />
                  <span className="text-sm text-blue-800 dark:text-blue-300">
                    Last training completed on {formatDate(staff.last_training_date)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button
                onClick={() => navigate(`/training/staff/${staff.id}/progress`)}
                className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center justify-center transition-colors"
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                View Training Progress
              </button>
              <button
                onClick={() => navigate(`/training/assignments/new?staff_id=${staff.id}`)}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center justify-center transition-colors"
              >
                <Award className="h-4 w-4 mr-2" />
                Assign Training
              </button>
              <button
                onClick={() => navigate(`/training/staff/${staff.id}/edit`)}
                className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center justify-center transition-colors"
              >
                <Edit className="h-4 w-4 mr-2" />
                Edit Details
              </button>
            </div>
          </div>

          {/* Account Information */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Account Information</h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Created:</span>
                <p className="font-medium">{formatDateTime(staff.created_at)}</p>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Last Updated:</span>
                <p className="font-medium">{formatDateTime(staff.updated_at)}</p>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Administrator ID:</span>
                <p className="font-medium">{staff.facility_administrator_id}</p>
              </div>
            </div>
          </div>

          {/* Certification Status */}
          {(staff.certifications_current > 0 || staff.certifications_expired > 0) && (
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Certification Status</h3>
              <div className="space-y-3">
                {staff.certifications_current > 0 && (
                  <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <div className="flex items-center">
                      <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400 mr-2" />
                      <span className="text-sm text-green-800 dark:text-green-300">Current</span>
                    </div>
                    <span className="font-semibold text-green-600 dark:text-green-400">
                      {staff.certifications_current}
                    </span>
                  </div>
                )}
                {staff.certifications_expired > 0 && (
                  <div className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                    <div className="flex items-center">
                      <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400 mr-2" />
                      <span className="text-sm text-red-800 dark:text-red-300">Expired</span>
                    </div>
                    <span className="font-semibold text-red-600 dark:text-red-400">
                      {staff.certifications_expired}
                    </span>
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

export default StaffDetailsPage; 