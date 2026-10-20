/*
  Description: Join facility page component
  Purpose: Allows users to join facilities using invitation codes
  
  Educational Note: Implements secure invitation acceptance flow with
  preview and confirmation steps for healthcare facility onboarding.
*/

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Building, Clock } from 'lucide-react';
import api from '../services/api';
import ErrorMessage from '../components/ErrorMessage';
import LoadingSpinner from '../components/LoadingSpinner';

interface InvitationDetails {
  facility_name: string;
  invited_by: string;
  role_description?: string;
  personal_message?: string;
  expires_at: string;
  days_remaining: number;
  email?: string;
}

const JoinFacilityPage: React.FC = () => {
  const { invitationCode } = useParams<{ invitationCode: string }>();
  const navigate = useNavigate();
  
  const [invitationDetails, setInvitationDetails] = useState<InvitationDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (invitationCode) {
      fetchInvitationDetails();
    }
  }, [invitationCode]);

  const fetchInvitationDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get(`/facilities/join/${invitationCode}`);
      setInvitationDetails(response.data);
    } catch (err: any) {
      console.error('Failed to fetch invitation details:', err);
      setError(err.response?.data?.detail || 'Invalid or expired invitation code');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-dark-bg">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading invitation details...</p>
        </div>
      </div>
    );
  }

  if (error && !invitationDetails) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-dark-bg px-4">
        <div className="max-w-md w-full">
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-lg p-8 text-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center mx-auto mb-4">
              <Clock className="h-8 w-8 text-red-600 dark:text-red-400" />
            </div>
            <h1 className="text-xl font-semibold text-navy-blue dark:text-white mb-2">
              Invitation Not Found
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {error}
            </p>
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-navy-blue text-white py-2 px-4 rounded-lg hover:bg-blue-800 transition-colors"
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-lg overflow-hidden">
          {/* Header */}
          <div className="bg-navy-blue text-white p-6 text-center">
            <Building className="h-12 w-12 mx-auto mb-3" />
            <h1 className="text-2xl font-bold">You're Invited to Join</h1>
            <p className="text-blue-100 mt-1">{invitationDetails?.facility_name}</p>
          </div>

          {/* Content */}
          <div className="p-8">
            {error && (
              <div className="mb-6">
                <ErrorMessage message={error} type="error" onClose={() => setError(null)} />
              </div>
            )}

            {/* Invitation Details */}
            <div className="space-y-6">
              {invitationDetails?.role_description && (
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <h3 className="font-medium text-navy-blue dark:text-white mb-2">Your Role</h3>
                  <p className="text-gray-700 dark:text-gray-300">
                    {invitationDetails.role_description}
                  </p>
                </div>
              )}

              {invitationDetails?.personal_message && (
                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <h3 className="font-medium text-navy-blue dark:text-white mb-2">Personal Message</h3>
                  <p className="text-gray-700 dark:text-gray-300 italic">
                    "{invitationDetails.personal_message}"
                  </p>
                </div>
              )}

              {/* What you'll get access to */}
              <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <h3 className="font-medium text-navy-blue dark:text-white mb-3">
                  What you'll get access to:
                </h3>
                <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                    Facility-wide training programs and compliance resources
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                    Team calendar with shared events and deadlines
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                    AI-powered compliance assistant
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                    Progress tracking and reporting tools
                  </li>
                </ul>
              </div>

              {/* Expiration Warning */}
              {invitationDetails && invitationDetails.days_remaining <= 3 && (
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg">
                  <div className="flex items-center">
                    <Clock className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2" />
                    <p className="text-yellow-800 dark:text-yellow-200">
                      <strong>Invitation expires in {invitationDetails.days_remaining} day{invitationDetails.days_remaining !== 1 ? 's' : ''}!</strong>
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="mt-8 space-y-4">
              <div className="text-center">
                <button
                  onClick={() => navigate(`/signup?invitation=${invitationCode}&email=${invitationDetails?.email}&facility=${invitationDetails?.facility_name}`)}
                  className="w-full bg-navy-blue text-white py-3 px-6 rounded-lg hover:bg-blue-800 transition-colors font-medium"
                >
                  Join Team
                </button>
              </div>
            </div>

            {/* Footer */}
            <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700 text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Having trouble? Contact your facility administrator or{' '}
                <a href="/contact" className="text-navy-blue hover:text-blue-800">
                  reach out to support
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JoinFacilityPage; 