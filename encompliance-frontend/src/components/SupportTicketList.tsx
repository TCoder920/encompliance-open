/*
  Description: Support Ticket List component for the customer support portal.
  Purpose: Displays a list of support tickets with filtering and sorting capabilities.
*/
import React, { useState, useEffect } from 'react';
import customerSupportApi from '../services/customerSupportApi';
import { Ticket, Search, Filter, Clock, User, AlertCircle, CheckCircle, XCircle, ArrowUp } from 'lucide-react';
import StandardTable, { Column } from './StandardTable';

interface SupportTicket {
  id: number;
  ticket_number: string;
  subject: string;
  description: string;
  status: 'open' | 'in_progress' | 'escalated' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: 'billing' | 'technical' | 'training' | 'account' | 'documentation' | 'other';
  support_tier_required: 'beginner' | 'mid' | 'senior';
  user_id: number | null;
  facility_id: number | null;
  assigned_to_account_id: number | null;
  assigned_to_username: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  last_customer_reply_at: string | null;
  last_support_reply_at: string | null;
}

interface SupportTicketListProps {
  supportToken: string | null;
  onTicketSelect?: (ticket: SupportTicket) => void;
  statusFilter?: string;
  priorityFilter?: string;
  categoryFilter?: string;
  assignedToMe?: boolean;
  unassigned?: boolean;
  refreshTrigger?: number;
}

const SupportTicketList: React.FC<SupportTicketListProps> = ({
  supportToken,
  onTicketSelect,
  statusFilter,
  priorityFilter,
  categoryFilter,
  assignedToMe = false,
  unassigned = false,
  refreshTrigger = 0,
}) => {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);



  useEffect(() => {
    if (!supportToken) return;

    const fetchTickets = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (statusFilter) params.append('status_filter', statusFilter);
        if (priorityFilter) params.append('priority_filter', priorityFilter);
        if (categoryFilter) params.append('category_filter', categoryFilter);
        if (assignedToMe) params.append('assigned_to_me', 'true');
        if (unassigned) params.append('unassigned', 'true');

        const response = await customerSupportApi.get<SupportTicket[]>(
          '/api/v1/support/tickets',
          { params }
        );
        setTickets(response.data);
      } catch (err) {
        console.error('Error fetching tickets:', err);
        setError('Failed to load tickets');
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, [supportToken, statusFilter, priorityFilter, categoryFilter, assignedToMe, unassigned, refreshTrigger]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open':
        return <AlertCircle className="w-4 h-4 text-blue-500" />;
      case 'in_progress':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'resolved':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'closed':
        return <XCircle className="w-4 h-4 text-gray-500" />;
      case 'escalated':
        return <ArrowUp className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'senior':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'mid':
        return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200';
      case 'beginner':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const columns: Column<SupportTicket>[] = [
    {
      key: 'ticket_number',
      header: 'Ticket #',
      sortable: true,
      renderCell: (ticket) => (
        <button
          onClick={() => onTicketSelect?.(ticket)}
          className="text-blue-600 dark:text-blue-400 hover:underline font-mono"
        >
          {ticket.ticket_number}
        </button>
      ),
    },
    {
      key: 'subject',
      header: 'Subject',
      sortable: true,
      renderCell: (ticket) => (
        <button
          onClick={() => onTicketSelect?.(ticket)}
          className="text-left hover:underline"
        >
          {ticket.subject}
        </button>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      renderCell: (ticket) => (
        <div className="flex items-center gap-2">
          {getStatusIcon(ticket.status)}
          <span className="capitalize">{ticket.status.replace('_', ' ')}</span>
        </div>
      ),
    },
    {
      key: 'priority',
      header: 'Priority',
      sortable: true,
      renderCell: (ticket) => (
        <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${getPriorityColor(ticket.priority)}`}>
          {ticket.priority}
        </span>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      sortable: true,
      renderCell: (ticket) => <span className="capitalize">{ticket.category}</span>,
    },
    {
      key: 'support_tier_required',
      header: 'Tier',
      sortable: true,
      renderCell: (ticket) => (
        <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${getTierColor(ticket.support_tier_required)}`}>
          {ticket.support_tier_required}
        </span>
      ),
    },
    {
      key: 'assigned_to_username',
      header: 'Assigned To',
      sortable: true,
      renderCell: (ticket) => ticket.assigned_to_username || <span className="text-gray-400">Unassigned</span>,
    },
    {
      key: 'created_at',
      header: 'Created',
      sortable: true,
      renderCell: (ticket) => new Date(ticket.created_at).toLocaleString(),
    },
  ];

  if (loading) {
    return <div className="text-center p-4">Loading tickets...</div>;
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">{error}</div>;
  }

  if (tickets.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500 dark:text-gray-400">
        <Ticket className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No tickets found</p>
      </div>
    );
  }

  return <StandardTable columns={columns} data={tickets} pageSize={20} />;
};

export default SupportTicketList;

