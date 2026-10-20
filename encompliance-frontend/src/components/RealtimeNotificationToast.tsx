/*
  Description: Real-time notification toast component for WebSocket events.
  Purpose: Displays toast notifications for ticket events received via WebSocket.
*/
import React, { useState, useEffect } from 'react';
import { X, Ticket, CheckCircle, ArrowUp, MessageSquare, Bell } from 'lucide-react';
import { supportWebSocketService, TicketEvent } from '../services/supportWebSocket';

interface Notification {
  id: string;
  type: string;
  message: string;
  timestamp: Date;
  data?: any;
}

const RealtimeNotificationToast: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    const unsubscribe = supportWebSocketService.subscribe('all', (event: TicketEvent) => {
      // Only show notifications for certain event types
      if (['ticket_assigned', 'ticket_escalated', 'ticket_comment'].includes(event.type)) {
        const notification: Notification = {
          id: `${event.type}-${Date.now()}`,
          type: event.type,
          message: getNotificationMessage(event),
          timestamp: new Date(),
          data: event.data,
        };
        
        setNotifications(prev => [...prev, notification]);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
          setNotifications(prev => prev.filter(n => n.id !== notification.id));
        }, 5000);
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const getNotificationMessage = (event: TicketEvent): string => {
    switch (event.type) {
      case 'ticket_assigned':
        return `Ticket ${event.data.ticket_number} assigned to you`;
      case 'ticket_escalated':
        return `Ticket ${event.data.ticket_number} has been escalated`;
      case 'ticket_comment':
        return `New comment on ticket ${event.data.ticket_number}`;
      case 'ticket_created':
        return `New ticket ${event.data.ticket_number} created`;
      case 'ticket_updated':
        return `Ticket ${event.data.ticket_number} updated`;
      case 'ticket_resolved':
        return `Ticket ${event.data.ticket_number} resolved`;
      default:
        return 'Ticket update received';
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'ticket_assigned':
        return <Ticket className="w-5 h-5 text-blue-500" />;
      case 'ticket_escalated':
        return <ArrowUp className="w-5 h-5 text-red-500" />;
      case 'ticket_comment':
        return <MessageSquare className="w-5 h-5 text-purple-500" />;
      case 'ticket_resolved':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      default:
        return <Bell className="w-5 h-5 text-gray-500" />;
    }
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map(notification => (
        <div
          key={notification.id}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4 min-w-[300px] max-w-[400px] animate-slide-in"
        >
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-0.5">
              {getNotificationIcon(notification.type)}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {notification.message}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {notification.timestamp.toLocaleTimeString()}
              </p>
            </div>
            <button
              onClick={() => removeNotification(notification.id)}
              className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RealtimeNotificationToast;

