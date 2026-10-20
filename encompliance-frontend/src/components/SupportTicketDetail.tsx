/*
  Description: Support Ticket Detail component for viewing and managing individual tickets.
  Purpose: Provides detailed ticket view with comments, customer context, and action buttons.
*/
import React, { useState, useEffect } from 'react';

import { 
  X, MessageSquare, User, Calendar, Tag, AlertCircle, CheckCircle, 
  ArrowUp, Clock, Send, FileText, History
} from 'lucide-react';
import CustomerHistoryTimeline from './CustomerHistoryTimeline';
import customerSupportApi from '../services/customerSupportApi';

interface SupportTicket {
  id: number;
  ticket_number: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  category: string;
  support_tier_required: string;
  user_id: number | null;
  facility_id: number | null;
  assigned_to_account_id: number | null;
  assigned_to_username: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  tags: string[];
  attachments: string[];
}

interface TicketComment {
  id: number;
  ticket_id: number;
  commenter_type: 'customer' | 'support' | 'system';
  commenter_id: number | null;
  comment_text: string;
  is_internal: boolean;
  created_at: string;
  commenter_name: string | null;
}

interface CustomerContext {
  user: {
    id: number;
    username?: string;
    email?: string;
    full_name?: string;
    facility_type?: string;
    state?: string;
    phone_number?: string;
    is_active: boolean;
    subscription_status?: string;
    user_role?: string;
    created_at?: string;
  } | null;
  facility: {
    id: number;
    facility_name?: string;
    facility_address?: string;
    facility_city?: string;
    facility_state?: string;
    facility_zip?: string;
    facility_phone?: string;
    facility_email?: string;
    is_active: boolean;
    max_users?: number;
    created_at?: string;
  } | null;
  subscription: {
    id?: number;
    status?: string;
    current_period_start?: string;
    current_period_end?: string;
    seat_count?: number;
    total_amount?: string;
    trial_end?: string;
    cancel_at_period_end: boolean;
  } | null;
  recent_payments: any[];
  ticket_count: number;
  open_ticket_count: number;
}

interface SupportTicketDetailProps {
  ticketId: number;
  supportToken: string | null;
  onClose: () => void;
  onUpdate?: () => void;
  currentAccountId: number | null;
  isSupportAdmin: boolean;
}

const SupportTicketDetail: React.FC<SupportTicketDetailProps> = ({
  ticketId,
  supportToken,
  onClose,
  onUpdate,
  currentAccountId,
  isSupportAdmin,
}) => {
  const [ticket, setTicket] = useState<SupportTicket | null>(null);
  const [comments, setComments] = useState<TicketComment[]>([]);
  const [customerContext, setCustomerContext] = useState<CustomerContext | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [newComment, setNewComment] = useState<string>('');
  const [isInternal, setIsInternal] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [showCustomerContext, setShowCustomerContext] = useState<boolean>(false);
  const [showHistory, setShowHistory] = useState<boolean>(false);

  useEffect(() => {
    if (!supportToken || !ticketId) return;

    let isMounted = true;

    const fetchTicket = async () => {
      setLoading(true);
      setError(null);
      try {
        const [ticketRes, commentsRes] = await Promise.all([
          customerSupportApi.get<SupportTicket>(`/api/v1/support/tickets/${ticketId}`),
          customerSupportApi.get<TicketComment[]>(`/api/v1/support/tickets/${ticketId}/comments?include_internal=true`),
        ]);
        if (!isMounted) return;
        setTicket(ticketRes.data);
        setComments(commentsRes.data);
      } catch (err) {
        console.error('Error fetching ticket:', err);
        if (isMounted) {
          setError('Failed to load ticket details');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchTicket();
    return () => {
      isMounted = false;
    };
  }, [ticketId, supportToken]);

  const canViewCustomerDetails =
    isSupportAdmin || (ticket?.assigned_to_account_id != null && ticket.assigned_to_account_id === currentAccountId);

  useEffect(() => {
    if (!supportToken || !ticketId || !canViewCustomerDetails) {
      setCustomerContext(null);
      return;
    }

    let isMounted = true;
    const fetchContext = async () => {
      try {
        const response = await customerSupportApi.get<CustomerContext>(`/api/v1/support/tickets/${ticketId}/customer-context`);
        if (isMounted) {
          setCustomerContext(response.data);
        }
      } catch (err) {
        if (isMounted) {
          console.warn('Unable to load customer context:', err);
          setCustomerContext(null);
        }
      }
    };

    fetchContext();
    return () => {
      isMounted = false;
    };
  }, [supportToken, ticketId, canViewCustomerDetails]);

  const handleAddComment = async () => {
    if (!newComment.trim() || !supportToken || !ticketId) return;

    setSubmitting(true);
    try {
      await customerSupportApi.post(
        `/api/v1/support/tickets/${ticketId}/comments`,
        {
          comment_text: newComment,
          is_internal: isInternal,
        }
      );
      setNewComment('');
      setIsInternal(false);
      // Refresh comments
      const commentsRes = await customerSupportApi.get<TicketComment[]>(
        `/api/v1/support/tickets/${ticketId}/comments?include_internal=true`
      );
      setComments(commentsRes.data);
      onUpdate?.();
    } catch (err) {
      console.error('Error adding comment:', err);
      alert('Failed to add comment');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
          <p>Loading ticket...</p>
        </div>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md">
          <p className="text-red-500">{error || 'Ticket not found'}</p>
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'resolved':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'closed':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
      case 'escalated':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b dark:border-gray-700 p-4 flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-mono text-sm text-gray-500">{ticket.ticket_number}</span>
              <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${getStatusColor(ticket.status)}`}>
                {ticket.status.replace('_', ' ')}
              </span>
              <span className="px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 capitalize">
                {ticket.priority}
              </span>
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">{ticket.subject}</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Ticket Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500 dark:text-gray-400">Category:</span>
              <span className="ml-2 capitalize">{ticket.category}</span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Tier Required:</span>
              <span className="ml-2 capitalize">{ticket.support_tier_required}</span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Assigned To:</span>
              <span className="ml-2">{ticket.assigned_to_username || 'Unassigned'}</span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Created:</span>
              <span className="ml-2">{new Date(ticket.created_at).toLocaleString()}</span>
            </div>
          </div>

          {/* Customer Context Panel */}
          {canViewCustomerDetails ? (
            customerContext && (
              <div className="border-t dark:border-gray-700 pt-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    <User className="w-5 h-5" />
                    Customer Context
                  </h3>
                  <button
                    onClick={() => setShowCustomerContext(!showCustomerContext)}
                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    {showCustomerContext ? 'Hide' : 'Show'} Details
                  </button>
                </div>
                {showCustomerContext && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    {customerContext.user && (
                      <div>
                        <h4 className="font-semibold mb-2 text-gray-900 dark:text-white">User Information</h4>
                        <div className="space-y-1">
                          <p><span className="text-gray-500 dark:text-gray-400">Name:</span> {customerContext.user.full_name || customerContext.user.username || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Email:</span> {customerContext.user.email || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Phone:</span> {customerContext.user.phone_number || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Status:</span> {customerContext.user.subscription_status || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Role:</span> {customerContext.user.user_role || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Total Tickets:</span> {customerContext.ticket_count}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Open Tickets:</span> {customerContext.open_ticket_count}</p>
                        </div>
                      </div>
                    )}
                    {customerContext.facility && (
                      <div>
                        <h4 className="font-semibold mb-2 text-gray-900 dark:text-white">Facility Information</h4>
                        <div className="space-y-1">
                          <p><span className="text-gray-500 dark:text-gray-400">Name:</span> {customerContext.facility.facility_name || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Address:</span> {customerContext.facility.facility_address || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">City/State:</span> {customerContext.facility.facility_city || ''} {customerContext.facility.facility_state || ''}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Phone:</span> {customerContext.facility.facility_phone || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Email:</span> {customerContext.facility.facility_email || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Max Users:</span> {customerContext.facility.max_users || 'N/A'}</p>
                        </div>
                      </div>
                    )}
                    {customerContext.subscription && (
                      <div>
                        <h4 className="font-semibold mb-2 text-gray-900 dark:text-white">Subscription</h4>
                        <div className="space-y-1">
                          <p><span className="text-gray-500 dark:text-gray-400">Status:</span> {customerContext.subscription.status || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Seats:</span> {customerContext.subscription.seat_count || 'N/A'}</p>
                          <p><span className="text-gray-500 dark:text-gray-400">Amount:</span> {customerContext.subscription.total_amount ? `$${customerContext.subscription.total_amount}` : 'N/A'}</p>
                          {customerContext.subscription.current_period_end && (
                            <p><span className="text-gray-500 dark:text-gray-400">Period End:</span> {new Date(customerContext.subscription.current_period_end).toLocaleDateString()}</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          ) : (
            <div className="border-t dark:border-gray-700 pt-4 text-sm text-gray-500 dark:text-gray-400">
              Customer context becomes available once the ticket is assigned to you or you are a support administrator.
            </div>
          )}

          {/* Description */}
          <div>
            <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">Description</h3>
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{ticket.description}</p>
          </div>

          {/* Tags */}
          {ticket.tags && ticket.tags.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {ticket.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {ticket.status !== 'resolved' && ticket.status !== 'closed' && (
            <div className="flex gap-2 border-t dark:border-gray-700 pt-4">
              <button
                onClick={async () => {
                  const reason = prompt('Escalation reason:');
                  if (!reason) return;
                  try {
                    await customerSupportApi.post(
                      `/api/v1/support/tickets/${ticket.id}/escalate`,
                      { escalation_reason: reason }
                    );
                    onUpdate?.();
                    window.location.reload();
                  } catch (err) {
                    alert('Failed to escalate ticket');
                  }
                }}
                className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
              >
                <ArrowUp className="w-4 h-4" />
                Escalate
              </button>
              <button
                onClick={async () => {
                  try {
                    await customerSupportApi.post(
                      `/api/v1/support/tickets/${ticket.id}/resolve`,
                      {}
                    );
                    onUpdate?.();
                    window.location.reload();
                  } catch (err) {
                    alert('Failed to resolve ticket');
                  }
                }}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                <CheckCircle className="w-4 h-4" />
                Resolve
              </button>
            </div>
          )}

          {/* Customer History Timeline */}
          {canViewCustomerDetails && customerContext && customerContext.user && (
            <div className="border-t dark:border-gray-700 pt-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <History className="w-5 h-5" />
                  Customer History Timeline
                </h3>
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  {showHistory ? 'Hide' : 'Show'} Timeline
                </button>
              </div>
              {showHistory && (
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <CustomerHistoryTimeline ticketId={ticketId} canViewHistory={canViewCustomerDetails} />
                </div>
              )}
            </div>
          )}

          {/* Comments Section */}
          <div>
            <h3 className="font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Comments ({comments.length})
            </h3>
            <div className="space-y-4 mb-4">
              {comments.map((comment) => (
                <div
                  key={comment.id}
                  className={`p-3 rounded ${
                    comment.is_internal
                      ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                      : 'bg-gray-50 dark:bg-gray-700'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4" />
                      <span className="font-medium text-sm">
                        {comment.commenter_name || `ID: ${comment.commenter_id}`}
                      </span>
                      {comment.is_internal && (
                        <span className="text-xs bg-yellow-200 dark:bg-yellow-800 px-2 py-0.5 rounded">
                          Internal
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(comment.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {comment.comment_text}
                  </p>
                </div>
              ))}
            </div>

            {/* Add Comment Form */}
            <div className="border-t dark:border-gray-700 pt-4">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment..."
                className="w-full p-3 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white mb-2"
                rows={3}
              />
              <div className="flex justify-between items-center">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={isInternal}
                    onChange={(e) => setIsInternal(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-gray-600 dark:text-gray-400">Internal note (not visible to customer)</span>
                </label>
                <button
                  onClick={handleAddComment}
                  disabled={!newComment.trim() || submitting}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  {submitting ? 'Sending...' : 'Send'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SupportTicketDetail;
