/*
  Description: Customer History Timeline component for visualizing customer interaction history.
  Purpose: Displays a chronological timeline of all tickets, comments, and events for a customer.
*/
import React, { useState, useEffect } from 'react';
import customerSupportApi from '../services/customerSupportApi';
import {
  Ticket,
  MessageSquare,
  CheckCircle,
  ArrowUp,
  Clock,
  User,
  AlertCircle,
} from 'lucide-react';
import { useCustomerSupportAuth } from '../contexts/CustomerSupportAuthContext';

interface TimelineEvent {
  type: string;
  ticket_id: number;
  ticket_number: string;
  subject?: string;
  status?: string;
  priority?: string;
  category?: string;
  commenter_type?: string;
  is_internal?: boolean;
  timestamp: string | null;
  description: string;
}

interface CustomerHistoryTimelineProps {
  ticketId: number;
  canViewHistory: boolean;
}

const CustomerHistoryTimeline: React.FC<CustomerHistoryTimelineProps> = ({ ticketId, canViewHistory }) => {
  const { supportToken } = useCustomerSupportAuth();
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!supportToken || !ticketId || !canViewHistory) {
      setTimeline([]);
      setLoading(false);
      return;
    }

    const fetchHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await customerSupportApi.get<TimelineEvent[]>(
          `/api/v1/support/tickets/${ticketId}/customer-history`
        );
        setTimeline(response.data);
      } catch (err) {
        console.error('Error fetching customer history:', err);
        setError('Failed to load customer history');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [ticketId, supportToken, canViewHistory]);

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'ticket_created':
        return <Ticket className="w-5 h-5 text-blue-500" />;
      case 'ticket_resolved':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'ticket_escalated':
        return <ArrowUp className="w-5 h-5 text-red-500" />;
      case 'comment_added':
        return <MessageSquare className="w-5 h-5 text-purple-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'ticket_created':
        return 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700';
      case 'ticket_resolved':
        return 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700';
      case 'ticket_escalated':
        return 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700';
      case 'comment_added':
        return 'bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700';
      default:
        return 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-700';
    }
  };

  const formatDate = (timestamp: string | null) => {
    if (!timestamp) return 'Unknown date';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  if (!canViewHistory) {
    return (
      <div className="text-center p-8 text-gray-500 dark:text-gray-400">
        Customer history is available once a ticket is assigned to you.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-pulse text-gray-600 dark:text-gray-400">Loading history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-4">
        <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
        <p className="text-red-600 dark:text-red-400">{error}</p>
      </div>
    );
  }

  if (timeline.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500 dark:text-gray-400">
        <User className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No customer history available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Clock className="w-5 h-5 text-gray-500" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Customer Interaction History ({timeline.length} events)
        </h3>
      </div>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-300 dark:bg-gray-700"></div>

        <div className="space-y-4">
          {timeline.map((event, index) => (
            <div key={index} className="relative flex items-start gap-4">
              {/* Timeline dot */}
              <div className="relative z-10 flex-shrink-0">
                <div className={`w-8 h-8 rounded-full ${getEventColor(event.type)} flex items-center justify-center border-2`}>
                  {getEventIcon(event.type)}
                </div>
              </div>

              {/* Event content */}
              <div className={`flex-1 rounded-lg p-4 border-2 ${getEventColor(event.type)}`}>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {event.description}
                    </p>
                    {event.subject && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {event.subject}
                      </p>
                    )}
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap ml-4">
                    {formatDate(event.timestamp)}
                  </span>
                </div>

                {/* Additional details */}
                <div className="flex flex-wrap gap-2 mt-2">
                  {event.status && (
                    <span className="px-2 py-1 text-xs rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                      Status: {event.status}
                    </span>
                  )}
                  {event.priority && (
                    <span className="px-2 py-1 text-xs rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                      Priority: {event.priority}
                    </span>
                  )}
                  {event.category && (
                    <span className="px-2 py-1 text-xs rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                      Category: {event.category}
                    </span>
                  )}
                  {event.commenter_type && (
                    <span className="px-2 py-1 text-xs rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                      {event.commenter_type === 'customer' ? 'Customer' : 'Support'} Comment
                      {event.is_internal && ' (Internal)'}
                    </span>
                  )}
                </div>

                {/* Ticket number link */}
                <div className="mt-2">
                  <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
                    Ticket: {event.ticket_number}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CustomerHistoryTimeline;
