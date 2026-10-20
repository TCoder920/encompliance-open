/*
  Description: Policy Acknowledgment page for staff members
  Purpose: Allows staff to view assigned policies and acknowledge them
*/
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  CheckCircle,
  Clock,
  AlertTriangle,
  Eye,
  Calendar,
  User,
  CheckSquare
} from 'lucide-react';
import policyService, {
  PolicyAssignment,
  Policy
} from '../services/policyService';
import ErrorMessage from '../components/ErrorMessage';
import { useAuth } from '../contexts/AuthContext';

const PolicyAcknowledgmentPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<PolicyAssignment[]>([]);
  const [policies, setPolicies] = useState<Record<number, Policy>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewingPolicy, setViewingPolicy] = useState<Policy | null>(null);
  const [acknowledgingAssignment, setAcknowledgingAssignment] = useState<number | null>(null);
  const [acknowledgmentText, setAcknowledgmentText] = useState('');

  useEffect(() => {
    loadAssignments();
  }, []);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const assignmentsData = await policyService.getPolicyAssignments({
        status: 'assigned',
        page: 1,
        per_page: 100
      });
      
      setAssignments(assignmentsData);
      
      // Load policy details for each assignment
      const policyIds = [...new Set(assignmentsData.map(a => a.policy_id))];
      const policyPromises = policyIds.map(id => policyService.getPolicy(id));
      const policiesData = await Promise.all(policyPromises);
      
      const policiesMap: Record<number, Policy> = {};
      policiesData.forEach(policy => {
        policiesMap[policy.id] = policy;
      });
      setPolicies(policiesMap);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load policy assignments');
      console.error('Error loading assignments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewPolicy = async (assignment: PolicyAssignment) => {
    try {
      // Mark as viewed
      await policyService.markPolicyViewed(assignment.id);
      
      // Load policy details
      const policy = await policyService.getPolicy(assignment.policy_id);
      setViewingPolicy(policy);
      
      // Refresh assignments to update viewed status
      await loadAssignments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load policy');
    }
  };

  const handleAcknowledge = async (assignment: PolicyAssignment) => {
    if (!acknowledgmentText.trim()) {
      setError('Please provide acknowledgment text');
      return;
    }

    try {
      setAcknowledgingAssignment(assignment.id);
      
      await policyService.createPolicyAcknowledgment({
        policy_assignment_id: assignment.id,
        acknowledgment_method: 'checkbox_confirmation',
        acknowledgment_text: acknowledgmentText,
        ip_address: undefined, // Will be captured by backend
        user_agent: navigator.userAgent
      });

      setViewingPolicy(null);
      setAcknowledgmentText('');
      setAcknowledgingAssignment(null);
      await loadAssignments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to acknowledge policy');
      setAcknowledgingAssignment(null);
    }
  };

  const getStatusBadge = (assignment: PolicyAssignment) => {
    if (assignment.is_acknowledged) {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 flex items-center gap-1">
          <CheckCircle className="w-3 h-3" />
          Acknowledged
        </span>
      );
    } else if (assignment.is_overdue) {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          Overdue ({assignment.days_overdue} days)
        </span>
      );
    } else if (assignment.viewed_date) {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 flex items-center gap-1">
          <Eye className="w-3 h-3" />
          Viewed
        </span>
      );
    } else {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Pending
        </span>
      );
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading && assignments.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading policy assignments...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Policy Acknowledgments
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Review and acknowledge assigned policies
        </p>
      </div>

      {error && <ErrorMessage message={error} onClose={() => setError(null)} />}

      {/* Policy Assignments List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        {assignments.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">No policy assignments found</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {assignments.map((assignment) => {
              const policy = policies[assignment.policy_id];
              return (
                <div
                  key={assignment.id}
                  className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {policy?.title || 'Loading...'}
                        </h3>
                        {getStatusBadge(assignment)}
                      </div>
                      {policy?.description && (
                        <p className="text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                          {policy.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 mb-3">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          Due: {formatDate(assignment.due_date)}
                        </span>
                        {assignment.viewed_date && (
                          <span className="flex items-center gap-1">
                            <Eye className="w-4 h-4" />
                            Viewed: {formatDate(assignment.viewed_date)}
                          </span>
                        )}
                        {assignment.priority && (
                          <span className={`px-2 py-1 rounded text-xs ${
                            assignment.priority === 'urgent' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                            assignment.priority === 'high' ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' :
                            'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                          }`}>
                            {assignment.priority.toUpperCase()}
                          </span>
                        )}
                      </div>
                      {assignment.custom_message && (
                        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-3">
                          <p className="text-sm text-blue-800 dark:text-blue-200">
                            {assignment.custom_message}
                          </p>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {!assignment.is_acknowledged && (
                        <>
                          <button
                            onClick={() => handleViewPolicy(assignment)}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                          >
                            <Eye className="w-4 h-4" />
                            View Policy
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Policy View Modal */}
      {viewingPolicy && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {viewingPolicy.title}
              </h2>
              <button
                onClick={() => {
                  setViewingPolicy(null);
                  setAcknowledgmentText('');
                }}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {viewingPolicy.description && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Description
                </h3>
                <p className="text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                  {viewingPolicy.description}
                </p>
              </div>
            )}

            {viewingPolicy.content_summary && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Summary
                </h3>
                <p className="text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                  {viewingPolicy.content_summary}
                </p>
              </div>
            )}

            {viewingPolicy.document_url && (
              <div className="mb-4">
                <a
                  href={viewingPolicy.document_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  View Full Document →
                </a>
              </div>
            )}

            {!assignments.find(a => a.policy_id === viewingPolicy.id)?.is_acknowledged && (
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Acknowledge Policy
                </h3>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Acknowledgment Statement *
                  </label>
                  <textarea
                    value={acknowledgmentText}
                    onChange={(e) => setAcknowledgmentText(e.target.value)}
                    placeholder="I acknowledge that I have read and understand this policy..."
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 dark:bg-gray-700 dark:text-white"
                    rows={4}
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => {
                      setViewingPolicy(null);
                      setAcknowledgmentText('');
                    }}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      const assignment = assignments.find(a => a.policy_id === viewingPolicy.id);
                      if (assignment) {
                        handleAcknowledge(assignment);
                      }
                    }}
                    disabled={!acknowledgmentText.trim() || acknowledgingAssignment !== null}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <CheckSquare className="w-4 h-4" />
                    {acknowledgingAssignment ? 'Acknowledging...' : 'Acknowledge Policy'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PolicyAcknowledgmentPage;


