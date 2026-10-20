/*
Description: Training calendar integration component for assignment due dates
Purpose: Provides calendar event creation/management for training assignments
Key functionalities: Auto-create calendar events, due date visualization, external sync

Educational Note: React component pattern with TypeScript for calendar integration
Reference: React 18 documentation on component composition and hooks
*/

import React, { useState, useEffect, useRef } from 'react';
import { Calendar, Clock, Bell, Settings, ExternalLink, Plus, Eye } from 'lucide-react';
import { trainingCalendarService, TrainingCalendarEvent, TrainingCalendarSettings } from '../services/trainingCalendarService';
import { TrainingAssignment } from '../services/trainingService';

interface TrainingCalendarIntegrationProps {
  assignments?: TrainingAssignment[];
  onEventCreated?: (event: TrainingCalendarEvent) => void;
  onSettingsChanged?: (settings: TrainingCalendarSettings) => void;
  showSettings?: boolean;
  compactView?: boolean;
}

const TrainingCalendarIntegration: React.FC<TrainingCalendarIntegrationProps> = ({
  assignments = [],
  onEventCreated,
  onSettingsChanged,
  showSettings = false,
  compactView = false
}) => {
  const [events, setEvents] = useState<TrainingCalendarEvent[]>([]);
  const [settings, setSettings] = useState<TrainingCalendarSettings>({
    autoCreateEvents: true,
    reminderDays: [7, 3, 1],
    certificationReminderDays: 30,
    syncToExternalCalendar: false,
    eventVisibility: 'private'
  });
  const [loading, setLoading] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [stats, setStats] = useState({
    totalEvents: 0,
    upcomingAssignments: 0,
    overdueTasks: 0,
    certificationRenewals: 0
  });
  
  // Use refs to track if we've already loaded data and prevent duplicate calls
  const hasLoadedData = useRef(false);
  const isLoadingData = useRef(false);

  // Load training calendar data
  useEffect(() => {
    // Only load if we haven't already loaded and aren't currently loading
    if (!hasLoadedData.current && !isLoadingData.current) {
    loadTrainingCalendarData();
    }
  }, []);

  const loadTrainingCalendarData = async () => {
    // Prevent multiple simultaneous calls
    if (isLoadingData.current) {
      console.log('Already loading training calendar data, skipping duplicate call');
      return;
    }
    
    isLoadingData.current = true;
    setLoading(true);
    
    try {
      console.log('Loading training calendar data...');
      
      // Load settings
      const calendarSettings = await trainingCalendarService.getTrainingCalendarSettings();
      setSettings(calendarSettings);

      // Load events
      const trainingEvents = await trainingCalendarService.getTrainingEvents();
      setEvents(trainingEvents);

      // Load stats
      const calendarStats = await trainingCalendarService.getTrainingCalendarStats();
      setStats(calendarStats);
      
      // Mark as successfully loaded
      hasLoadedData.current = true;
      console.log('Training calendar data loaded successfully');
    } catch (error) {
      console.error('Failed to load training calendar data:', error);
      // Set default values on error to prevent further API calls
      setSettings({
        autoCreateEvents: true,
        reminderDays: [7, 3, 1],
        certificationReminderDays: 30,
        syncToExternalCalendar: false,
        eventVisibility: 'private'
      });
      setEvents([]);
      setStats({
        totalEvents: 0,
        upcomingAssignments: 0,
        overdueTasks: 0,
        certificationRenewals: 0
      });
      // Still mark as loaded to prevent retries
      hasLoadedData.current = true;
    } finally {
      setLoading(false);
      isLoadingData.current = false;
    }
  };

  const createCalendarEventForAssignment = async (assignmentId: number) => {
    try {
      const event = await trainingCalendarService.createAssignmentCalendarEvent(assignmentId);
      setEvents(prev => [...prev, event]);
      onEventCreated?.(event);
    } catch (error) {
      console.error('Failed to create calendar event:', error);
    }
  };

  const updateSettings = async (newSettings: Partial<TrainingCalendarSettings>) => {
    try {
      const updatedSettings = await trainingCalendarService.updateTrainingCalendarSettings(newSettings);
      setSettings(updatedSettings);
      onSettingsChanged?.(updatedSettings);
    } catch (error) {
      console.error('Failed to update settings:', error);
    }
  };

  const getUpcomingEvents = () => {
    const now = new Date();
    const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    
    return events.filter(event => {
      const eventDate = new Date(event.start);
      return eventDate >= now && eventDate <= nextWeek;
    }).sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getEventTypeIcon = (eventType: string) => {
    switch (eventType) {
      case 'training_assignment':
        return <Calendar className="h-4 w-4" />;
      case 'certification_renewal':
        return <Bell className="h-4 w-4" />;
      case 'training_deadline':
        return <Clock className="h-4 w-4" />;
      default:
        return <Calendar className="h-4 w-4" />;
    }
  };

  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'training_assignment':
        return 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30';
      case 'certification_renewal':
        return 'text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-900/30';
      case 'training_deadline':
        return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
      default:
        return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30';
    }
  };

  if (compactView) {
    return (
      <div className="space-y-3">
        {/* Stats Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-white dark:bg-dark-surface rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-blue-600 dark:text-blue-400">{stats.upcomingAssignments}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Upcoming</div>
          </div>
          <div className="bg-white dark:bg-dark-surface rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-red-600 dark:text-red-400">{stats.overdueTasks}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Overdue</div>
          </div>
          <div className="bg-white dark:bg-dark-surface rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-orange-600 dark:text-orange-400">{stats.certificationRenewals}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Renewals</div>
          </div>
          <div className="bg-white dark:bg-dark-surface rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-green-600 dark:text-green-400">{stats.totalEvents}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Total Events</div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSettingsModal(true)}
            className="flex items-center px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            <Settings className="h-4 w-4 mr-1" />
            Settings
          </button>
          <a
            href="/calendar"
            className="flex items-center px-3 py-2 text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50"
          >
            <Eye className="h-4 w-4 mr-1" />
            View Calendar
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <Calendar className="h-5 w-5 mr-2" />
            Training Calendar Integration
          </h3>
          <div className="flex items-center space-x-2">
            {showSettings && (
              <button
                onClick={() => setShowSettingsModal(true)}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <Settings className="h-4 w-4" />
              </button>
            )}
            <a
              href="/calendar"
              className="flex items-center px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <ExternalLink className="h-4 w-4 mr-1" />
              Open Calendar
            </a>
          </div>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Loading calendar data...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Calendar Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.upcomingAssignments}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Upcoming Assignments</div>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.overdueTasks}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Overdue Tasks</div>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">{stats.certificationRenewals}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Renewal Reminders</div>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.totalEvents}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Total Events</div>
              </div>
            </div>

            {/* Upcoming Events */}
            <div>
              <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">Upcoming Events</h4>
              {getUpcomingEvents().length === 0 ? (
                <p className="text-gray-600 dark:text-gray-400 text-center py-4">No upcoming training events</p>
              ) : (
                <div className="space-y-3">
                  {getUpcomingEvents().slice(0, 5).map((event) => (
                    <div key={event.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg ${getEventTypeColor(event.eventType)}`}>
                          {getEventTypeIcon(event.eventType)}
                        </div>
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{event.title}</div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">{formatDate(event.start)}</div>
                        </div>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${getEventTypeColor(event.eventType)}`}>
                        {event.eventType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Training Assignments without Calendar Events */}
            {assignments.length > 0 && (
              <div>
                <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
                  Assignments Missing Calendar Events
                </h4>
                <div className="space-y-2">
                  {assignments
                    .filter(assignment => !events.some(event => event.trainingAssignmentId === assignment.id))
                    .slice(0, 3)
                    .map((assignment) => (
                      <div key={assignment.id} className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">Training Assignment #{assignment.id}</div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            Due: {formatDate(assignment.due_date)}
                          </div>
                        </div>
                        <button
                          onClick={() => createCalendarEventForAssignment(assignment.id)}
                          className="flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Add to Calendar
                        </button>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Calendar Integration Status */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-blue-900 dark:text-blue-100">Calendar Integration Active</h4>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    {settings.autoCreateEvents ? 'Automatically creating calendar events for new assignments' : 'Manual calendar event creation enabled'}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  {settings.syncToExternalCalendar && (
                    <span className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded">
                      External Sync On
                    </span>
                  )}
                  <span className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                    {events.length} Events
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Settings Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Training Calendar Settings</h3>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Auto-create events for new assignments
                </label>
                <input
                  type="checkbox"
                  checked={settings.autoCreateEvents}
                  onChange={(e) => updateSettings({ autoCreateEvents: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Sync to external calendar
                </label>
                <input
                  type="checkbox"
                  checked={settings.syncToExternalCalendar}
                  onChange={(e) => updateSettings({ syncToExternalCalendar: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Certification renewal reminder (days before expiry)
                </label>
                <input
                  type="number"
                  value={settings.certificationReminderDays}
                  onChange={(e) => updateSettings({ certificationReminderDays: parseInt(e.target.value) })}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  min="1"
                  max="90"
                />
              </div>
            </div>
            <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end">
              <button
                onClick={() => setShowSettingsModal(false)}
                className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrainingCalendarIntegration; 