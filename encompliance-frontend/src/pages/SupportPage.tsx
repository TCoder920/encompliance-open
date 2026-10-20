/*
  Description: Support page for customers to create and view support tickets.
  Purpose: Provides ticket creation form and ticket tracking interface for end users.
*/
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { Ticket, Plus, MessageSquare, Clock, CheckCircle, AlertCircle, Send } from 'lucide-react';
import ErrorMessage from '../components/ErrorMessage';

interface SupportTicket {
  id: number;
  ticket_number: string;
  subject: string;
  description: string;
  status: 'open' | 'in_progress' | 'escalated' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: 'billing' | 'technical' | 'training' | 'account' | 'documentation' | 'other';
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  assigned_to_username: string | null;
}

interface TicketComment {
  id: number;
  commenter_type: 'customer' | 'support' | 'system';
  comment_text: string;
  created_at: string;
  commenter_name: string | null;
}

const SupportPage: React.FC = () => {
  const { user } = useAuth();
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [comments, setComments] = useState<TicketComment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [newComment, setNewComment] = useState<string>('');

  // Form state
  const [formData, setFormData] = useState({
    subject: '',
    description: '',
    category: 'other' as SupportTicket['category'],
    priority: 'medium' as SupportTicket['priority'],
  });

  useEffect(() => {
    if (user) {
      fetchTickets();
    }
  }, [user]);

  useEffect(() => {
    if (selectedTicket) {
      fetchComments(selectedTicket.id);
    }
  }, [selectedTicket]);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const response = await api.get('/support/tickets');
      setTickets(response.data);
    } catch (err: any) {
      console.error('Error fetching tickets:', err);
      setError('Failed to load tickets');
    } finally {
      setLoading(false);
    }
  };

  const fetchComments = async (ticketId: number) => {
    try {
      const response = await api.get(`/support/tickets/${ticketId}/comments`);
      setComments(response.data);
    } catch (err) {
      console.error('Error fetching comments:', err);
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.subject.trim() || !formData.description.trim()) {
      setError('Subject and description are required');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await api.post('/support/tickets', formData);
      setShowCreateForm(false);
      setFormData({ subject: '', description: '', category: 'other', priority: 'medium' });
      fetchTickets();
    } catch (err: any) {
      console.error('Error creating ticket:', err);
      setError(err.response?.data?.detail || 'Failed to create ticket');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddComment = async () => {
    if (!selectedTicket || !newComment.trim()) return;

    try {
      await api.post(`/support/tickets/${selectedTicket.id}/comments`, {
        comment_text: newComment,
        is_internal: false,
      });
      setNewComment('');
      fetchComments(selectedTicket.id);
    } catch (err: any) {
      console.error('Error adding comment:', err);
      setError('Failed to add comment');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open':
        return <AlertCircle className="w-4 h-4 text-blue-500" />;
      case 'in_progress':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'resolved':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'closed':
        return <CheckCircle className="w-4 h-4 text-gray-500" />;
      default:
        return null;
    }
  };

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
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage message="Please log in to access support" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Ticket className="w-8 h-8" />
          Support Tickets
        </h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          New Ticket
        </button>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* Create Ticket Form */}
      {showCreateForm && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Create Support Ticket</h2>
          <form onSubmit={handleCreateTicket} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                Subject *
              </label>
              <input
                type="text"
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                Description *
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                rows={5}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                  Category
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value as SupportTicket['category'] })}
                  className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="billing">Billing</option>
                  <option value="technical">Technical</option>
                  <option value="training">Training</option>
                  <option value="account">Account</option>
                  <option value="documentation">Documentation</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                  Priority
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value as SupportTicket['priority'] })}
                  className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Creating...' : 'Create Ticket'}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tickets List */}
      {loading ? (
        <div className="text-center p-8">Loading tickets...</div>
      ) : tickets.length === 0 ? (
        <div className="text-center p-8 bg-white dark:bg-gray-800 rounded-lg shadow-md">
          <Ticket className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-500 dark:text-gray-400">No tickets yet. Create your first ticket to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Ticket List */}
          <div className="lg:col-span-1 space-y-2">
            {tickets.map((ticket) => (
              <div
                key={ticket.id}
                onClick={() => setSelectedTicket(ticket)}
                className={`p-4 rounded-lg shadow-md cursor-pointer transition-colors ${
                  selectedTicket?.id === ticket.id
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500'
                    : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(ticket.status)}
                    <span className="font-mono text-sm text-gray-500">{ticket.ticket_number}</span>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${getStatusColor(ticket.status)}`}>
                    {ticket.status.replace('_', ' ')}
                  </span>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{ticket.subject}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {new Date(ticket.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>

          {/* Ticket Detail */}
          {selectedTicket && (
            <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-mono text-sm text-gray-500">{selectedTicket.ticket_number}</span>
                  <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${getStatusColor(selectedTicket.status)}`}>
                    {selectedTicket.status.replace('_', ' ')}
                  </span>
                  <span className="px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 capitalize">
                    {selectedTicket.priority}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">{selectedTicket.subject}</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Created: {new Date(selectedTicket.created_at).toLocaleString()}
                  {selectedTicket.assigned_to_username && (
                    <> • Assigned to: {selectedTicket.assigned_to_username}</>
                  )}
                </p>
              </div>

              <div className="mb-6">
                <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">Description</h3>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{selectedTicket.description}</p>
              </div>

              {/* Comments */}
              <div className="mb-6">
                <h3 className="font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Comments ({comments.length})
                </h3>
                <div className="space-y-4 mb-4 max-h-96 overflow-y-auto">
                  {comments.map((comment) => (
                    <div
                      key={comment.id}
                      className="p-3 rounded bg-gray-50 dark:bg-gray-700"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-medium text-sm text-gray-900 dark:text-white">
                          {comment.commenter_name || 'Support'}
                        </span>
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

                {/* Add Comment */}
                {selectedTicket.status !== 'closed' && selectedTicket.status !== 'resolved' && (
                  <div className="border-t dark:border-gray-700 pt-4">
                    <textarea
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      placeholder="Add a comment..."
                      className="w-full p-3 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white mb-2"
                      rows={3}
                    />
                    <button
                      onClick={handleAddComment}
                      disabled={!newComment.trim()}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Send className="w-4 h-4" />
                      Send Comment
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SupportPage;

