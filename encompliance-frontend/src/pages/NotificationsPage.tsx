/*
  Description: Notifications page component for managing user notifications.
  Purpose: Allows users to view, mark as read, and manage their notifications.
*/
import React, { useState, useEffect } from 'react';
import { notificationService, Notification, NotificationType } from '../services/notificationService';
import { Bell, Check, Trash2, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { formatDateTime } from '../utils/dateUtils';

const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [totalNotifications, setTotalNotifications] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [page, setPage] = useState(0);
  const limit = 20;
  const navigate = useNavigate();

  // Fetch notifications when component mounts or filters change
  useEffect(() => {
    fetchNotifications();
  }, [showUnreadOnly, page]);

  const fetchNotifications = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await notificationService.getNotifications({
        skip: page * limit,
        limit,
        unread_only: showUnreadOnly
      });
      
      setNotifications(response.notifications);
      setTotalNotifications(response.total);
      setUnreadCount(response.unread_count);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
      setError('Failed to load notifications. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId: number) => {
    try {
      await notificationService.markAsRead(notificationId);
      
      // Update the local state
      setNotifications(notifications.map(notification => 
        notification.id === notificationId 
          ? { ...notification, is_read: true } 
          : notification
      ));
      
      // Update the unread count
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
      setError('Failed to update notification. Please try again later.');
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      
      // Update the local state
      setNotifications(notifications.map(notification => ({ ...notification, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err);
      setError('Failed to update notifications. Please try again later.');
    }
  };

  const handleDeleteNotification = async (notificationId: number) => {
    try {
      await notificationService.deleteNotification(notificationId);
      
      // Update the local state
      const deletedNotification = notifications.find(n => n.id === notificationId);
      setNotifications(notifications.filter(n => n.id !== notificationId));
      
      // Update the total count
      setTotalNotifications(prev => Math.max(0, prev - 1));
      
      // Update the unread count if needed
      if (deletedNotification && !deletedNotification.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (err) {
      console.error('Failed to delete notification:', err);
      setError('Failed to delete notification. Please try again later.');
    }
  };

  const handleDeleteAllNotifications = async () => {
    if (!window.confirm('Are you sure you want to delete all notifications?')) return;
    
    try {
      await notificationService.deleteAllNotifications();
      
      // Update the local state
      setNotifications([]);
      setTotalNotifications(0);
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to delete all notifications:', err);
      setError('Failed to delete notifications. Please try again later.');
    }
  };

  const handleNavigateToAction = (notification: Notification) => {
    if (notification.action_url) {
      // Mark as read before navigating
      handleMarkAsRead(notification.id);
      navigate(notification.action_url);
    }
  };

  const getNotificationTypeIcon = (type: NotificationType) => {
    switch (type) {
      case NotificationType.NOTE:
        return <Bell className="h-5 w-5 text-blue-500" />;
      case NotificationType.DOCUMENT:
        return <Bell className="h-5 w-5 text-green-500" />;
      case NotificationType.SECURITY:
        return <Bell className="h-5 w-5 text-red-500" />;
      case NotificationType.SUBSCRIPTION:
        return <Bell className="h-5 w-5 text-purple-500" />;
      default:
        return <Bell className="h-5 w-5 text-gray-500" />;
    }
  };

  const getNotificationTypeClass = (type: NotificationType) => {
    switch (type) {
      case NotificationType.NOTE:
        return 'border-l-4 border-blue-500';
      case NotificationType.DOCUMENT:
        return 'border-l-4 border-green-500';
      case NotificationType.SECURITY:
        return 'border-l-4 border-red-500';
      case NotificationType.SUBSCRIPTION:
        return 'border-l-4 border-purple-500';
      default:
        return 'border-l-4 border-gray-500';
    }
  };

  const renderNotificationCard = (notification: Notification) => {
    return (
      <div 
        key={notification.id} 
        className={`relative p-4 rounded-lg shadow-md mb-4 ${
          notification.is_read ? 'bg-gray-50 dark:bg-gray-800' : 'bg-white dark:bg-gray-700'
        } ${getNotificationTypeClass(notification.type)}`}
      >
        <div className="flex items-start">
          <div className="mr-3 mt-1">
            {getNotificationTypeIcon(notification.type)}
          </div>
          <div className="flex-1">
            <div className="flex justify-between items-start">
              <h3 className="text-lg font-semibold dark:text-white">{notification.title}</h3>
              <div className="flex space-x-2">
                {!notification.is_read && (
                  <button
                    onClick={() => handleMarkAsRead(notification.id)}
                    className="text-gray-500 hover:text-blue-500 dark:text-gray-400 dark:hover:text-blue-400"
                    title="Mark as read"
                  >
                    <Check size={18} />
                  </button>
                )}
                <button
                  onClick={() => handleDeleteNotification(notification.id)}
                  className="text-gray-500 hover:text-red-500 dark:text-gray-400 dark:hover:text-red-400"
                  title="Delete notification"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
            <div className="mt-2 text-gray-700 dark:text-gray-300">
              {notification.message}
            </div>
            <div className="mt-4 flex justify-between items-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {formatDateTime(notification.created_at)}
              </div>
              {notification.action_url && (
                <button
                  onClick={() => handleNavigateToAction(notification)}
                  className="flex items-center space-x-1 text-sm text-blue-500 hover:text-blue-700 dark:hover:text-blue-300"
                >
                  <span>View</span>
                  <ExternalLink size={14} />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold dark:text-white">Notifications</h1>
        <div className="flex space-x-2">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllAsRead}
              className="px-3 py-1 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition flex items-center space-x-1"
            >
              <Check size={16} />
              <span>Mark All as Read</span>
            </button>
          )}
          {totalNotifications > 0 && (
            <button
              onClick={handleDeleteAllNotifications}
              className="px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600 transition flex items-center space-x-1"
            >
              <Trash2 size={16} />
              <span>Delete All</span>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="mb-6 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showUnreadOnly}
              onChange={() => setShowUnreadOnly(!showUnreadOnly)}
              className="form-checkbox h-5 w-5 text-blue-500"
            />
            <span className="dark:text-white">Show Unread Only</span>
          </label>
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-300">
          {unreadCount} unread / {totalNotifications} total
        </div>
      </div>

      {isLoading && notifications.length === 0 ? (
        <div className="flex justify-center items-center h-40">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-10 dark:text-white">
          <p className="text-lg">No notifications found.</p>
          {showUnreadOnly && unreadCount === 0 && totalNotifications > 0 && (
            <p className="mt-2">You have no unread notifications. <button 
              onClick={() => setShowUnreadOnly(false)}
              className="text-blue-500 hover:underline"
            >
              View all notifications
            </button></p>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {notifications.map(renderNotificationCard)}
          
          {/* Pagination */}
          {totalNotifications > limit && (
            <div className="flex justify-center mt-6 space-x-2">
              <button
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
                className={`px-3 py-1 rounded ${
                  page === 0 
                    ? 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400 cursor-not-allowed' 
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                Previous
              </button>
              <span className="px-3 py-1 dark:text-white">
                Page {page + 1} of {Math.ceil(totalNotifications / limit)}
              </span>
              <button
                onClick={() => setPage(Math.min(Math.ceil(totalNotifications / limit) - 1, page + 1))}
                disabled={page >= Math.ceil(totalNotifications / limit) - 1}
                className={`px-3 py-1 rounded ${
                  page >= Math.ceil(totalNotifications / limit) - 1
                    ? 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400 cursor-not-allowed' 
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationsPage; 