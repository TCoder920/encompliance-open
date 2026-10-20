/**
 * Description: Calendar component for the EnCompliance application.
 * Purpose: Provides a calendar interface for users to manage compliance-related events
 * and deadlines. Implements feature access control (paywall) to restrict access to
 * Pro and Enterprise subscription tiers. Includes an AI scheduling feature that allows
 * creating events using natural language prompts.
 */

import React, { useState, useEffect, useRef } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { Calendar as CalendarIcon, Plus, Bot, X, Save, Trash2, Settings } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Tier, getTierFromSubscriptionStatus } from '../../../utils/tiers';
import { canUseFeature } from '../../../utils/accessControl';
import { SAMPLE_CALENDAR_EVENTS } from '../../../utils/previewData';
import FeaturePreview from '../FeaturePreview';
import api from '../../../services/api';

// Import FullCalendar's core styles
// import '@fullcalendar/common/main.css'; 
// It's possible that the path should be @fullcalendar/core/main.css - will adjust if needed after checking docs

// Import custom dark mode styles
// import './CalendarDark.css';

// Helper function to format Date object to YYYY-MM-DDTHH:MM string for datetime-local input
function formatDateForInput(date: Date): string {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Event interface
interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  description?: string;
  location?: string;
  allDay: boolean;
  isPreview?: boolean;
}

// Event form data interface - make id required when updating
interface EventFormData {
  id?: string; // Optional for new events
  title: string;
  start: string;
  end: string;
  description: string;
  location: string;
  allDay: boolean;
}

// Props interface
interface CalendarProps {
  // Add any custom props here
}

const Calendar: React.FC<CalendarProps> = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [showAIModal, setShowAIModal] = useState(false);
  const [currentEvent, setCurrentEvent] = useState<Partial<CalendarEvent>>({});
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiLoading, setAILoading] = useState(false);
  const calendarRef = useRef<FullCalendar>(null);
  
  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUse = canUseFeature(userTier, 'calendar');

  // State for direct date navigation modal
  const currentYear = new Date().getFullYear();
  const [navYear, setNavYear] = useState<number>(currentYear);
  const [navMonth, setNavMonth] = useState<number>(new Date().getMonth()); // 0-indexed (0 for Jan, 11 for Dec)
  const [showDateNavModal, setShowDateNavModal] = useState(false);

  // Apply dark mode styling
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .fc {
        background-color: var(--bg-color);
        color: var(--text-color);
      }
      
      .fc-theme-standard .fc-scrollgrid {
        border-color: var(--border-color);
      }
      
      .fc-theme-standard td, .fc-theme-standard th {
        border-color: var(--border-color);
      }
      
      .fc-col-header-cell {
        background-color: var(--header-bg);
        color: var(--header-text);
      }
      
      .fc-daygrid-day {
        background-color: var(--day-bg);
      }
      
      .fc-daygrid-day:hover {
        background-color: var(--day-hover-bg);
      }
      
      .fc-event {
        background-color: var(--event-bg);
        border-color: var(--event-border);
        color: var(--event-text);
      }
      
      .fc-event:hover {
        background-color: var(--event-hover-bg);
      }
      
      .fc-button {
        background-color: var(--button-bg);
        border-color: var(--button-border);
        color: var(--button-text);
      }
      
      .fc-button:hover {
        background-color: var(--button-hover-bg);
      }
      
      .fc-button:disabled {
        opacity: 0.6;
      }
      
      .fc-today {
        background-color: var(--today-bg) !important;
      }
      
      :root {
        --bg-color: white;
        --text-color: #374151;
        --border-color: #e5e7eb;
        --header-bg: #f9fafb;
        --header-text: #374151;
        --day-bg: white;
        --day-hover-bg: #f3f4f6;
        --event-bg: #3b82f6;
        --event-border: #3b82f6;
        --event-text: white;
        --event-hover-bg: #2563eb;
        --button-bg: #f3f4f6;
        --button-border: #d1d5db;
        --button-text: #374151;
        --button-hover-bg: #e5e7eb;
        --today-bg: #fef3c7;
      }
      
      .dark {
        --bg-color: #1f2937;
        --text-color: #f9fafb;
        --border-color: #374151;
        --header-bg: #374151;
        --header-text: #f9fafb;
        --day-bg: #1f2937;
        --day-hover-bg: #374151;
        --event-bg: #3b82f6;
        --event-border: #3b82f6;
        --event-text: white;
        --event-hover-bg: #2563eb;
        --button-bg: #374151;
        --button-border: #4b5563;
        --button-text: #f9fafb;
        --button-hover-bg: #4b5563;
        --today-bg: #92400e;
      }
`;
    document.head.appendChild(style);
    
    // Clean up on unmount
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  // Fetch events
  useEffect(() => {
    fetchEvents();
  }, [userTier]);

  const fetchEvents = async () => {
    try {
      setIsLoading(true);
      
      if (canUse) {
        // Fetch real events for paid users
        const response = await api.get('/calendar/events');
        setEvents(response.data);
      } else {
        // Use sample events for free users
        setEvents(SAMPLE_CALENDAR_EVENTS);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load calendar events');
      console.error('Error fetching events:', err);
      
      // Fallback to sample data on error
      if (!canUse) {
        setEvents(SAMPLE_CALENDAR_EVENTS);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDateClick = (info: any) => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;

    let newStartStr: string;
    let newEndStr: string;
    let newAllDay = info.allDay;

    if (info.allDay) {
      const clickedDay = new Date(info.date);
      const now = new Date();

      let startHour = now.getHours();
      const currentMinutes = now.getMinutes();

      if (currentMinutes > 0) {
        startHour += 1;
      }

      if (startHour >= 24) {
        startHour = 0; 
      }
      
      const finalStartDateTime = new Date(clickedDay);
      finalStartDateTime.setHours(startHour, 0, 0, 0);

      const finalEndDateTime = new Date(finalStartDateTime);
      finalEndDateTime.setHours(finalStartDateTime.getHours() + 1, 0, 0, 0);

      if (finalEndDateTime.getDate() !== finalStartDateTime.getDate()) {
        finalEndDateTime.setDate(finalStartDateTime.getDate());
        finalEndDateTime.setHours(23, 59, 0, 0);
      }
      
      newStartStr = formatDateForInput(finalStartDateTime);
      newEndStr = formatDateForInput(finalEndDateTime);
      newAllDay = false;
    } else {
      newStartStr = formatDateForInput(new Date(info.date));
      newEndStr = formatDateForInput(new Date(info.date.getTime() + 60 * 60 * 1000));
      newAllDay = false;
    }

    setCurrentEvent({
      title: '',
      start: newStartStr,
      end: newEndStr,
      description: '',
      location: '',
      allDay: newAllDay,
    });
    setShowEventModal(true);
  };

  const handleEventClick = (info: any) => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;

    const event = info.event;
    setCurrentEvent({
      id: event.id,
      title: event.title,
      start: formatDateForInput(new Date(event.start)),
      end: formatDateForInput(new Date(event.end || event.start)),
      description: event.extendedProps.description || '',
      location: event.extendedProps.location || '',
      allDay: event.allDay,
    });
    setShowEventModal(true);
  };

  const handleAIScheduling = async () => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;
    
    try {
      setAILoading(true);
      const response = await api.post('/calendar/ai-schedule', { prompt: aiPrompt });
      
      if (response.data && response.data.event) {
        setCurrentEvent({
          title: response.data.event.title,
          start: response.data.event.start,
          end: response.data.event.end,
          description: response.data.event.description || '',
          location: response.data.event.location || '',
          allDay: response.data.event.allDay || false,
        });
      }
      setShowAIModal(false);
      setShowEventModal(true);
    } catch (err) {
      setError('Failed to process AI scheduling request');
      console.error('Error in AI scheduling:', err);
    } finally {
      setAILoading(false);
    }
  };

  const formatDateForInput = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const saveEvent = async () => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;

    try {
      if (currentEvent.id) {
        await api.put(`/calendar/events/${currentEvent.id}`, currentEvent);
      } else {
        await api.post('/calendar/events', currentEvent);
      }
      
      setShowEventModal(false);
      setCurrentEvent({});
      fetchEvents();
    } catch (err) {
      setError('Failed to save event');
      console.error('Error saving event:', err);
    }
  };

  const deleteEvent = async () => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse || !currentEvent.id) return;

    try {
      await api.delete(`/calendar/events/${currentEvent.id}`);
      setShowEventModal(false);
      setCurrentEvent({});
      fetchEvents();
    } catch (err) {
      setError('Failed to delete event');
      console.error('Error deleting event:', err);
    }
  };

  // Create preview content with sample data
  const previewContent = (
    <div className="space-y-6">
      {/* Calendar Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
          <CalendarIcon className="mr-2 h-6 w-6" />
          Compliance Calendar
        </h2>
        <div className="flex space-x-2">
          <button className="bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-gray-700 transition-colors">
            Calendar Sync
          </button>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-blue-700 transition-colors">
            <Plus className="mr-2 h-4 w-4" />
            Add Event
          </button>
          <button className="bg-purple-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-purple-700 transition-colors">
            <Bot className="mr-2 h-4 w-4" />
            AI Schedule
          </button>
        </div>
      </div>

      {/* Calendar Component */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4">
        {isLoading ? (
          <div className="flex justify-center items-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <FullCalendar
            ref={calendarRef}
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            headerToolbar={{
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,timeGridWeek,timeGridDay'
            }}
            events={events}
            dateClick={handleDateClick}
            eventClick={handleEventClick}
            editable={false} // Disable editing in preview mode
            selectable={false} // Disable selection in preview mode
            height="auto"
            eventDisplay="block"
            dayMaxEvents={3}
            moreLinkClick="popover"
          />
        )}
      </div>

      {error && (
        <div className="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-800 text-red-800 dark:text-red-300 px-4 py-3 rounded">
          {error}
        </div>
      )}
    </div>
  );

  // Main calendar content for paid users
  const mainContent = (
    <div className="space-y-6">
      {/* Calendar Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
          <CalendarIcon className="mr-2 h-6 w-6" />
          Compliance Calendar
        </h2>
        <div className="flex space-x-2">
          <button 
            onClick={() => navigate('/calendar-settings')}
            className="bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-gray-700 transition-colors"
          >
            Calendar Sync
          </button>
          <button 
            onClick={() => {
              setCurrentEvent({
                title: '',
                start: formatDateForInput(new Date()),
                end: formatDateForInput(new Date(Date.now() + 60 * 60 * 1000)),
                description: '',
                location: '',
                allDay: false,
              });
              setShowEventModal(true);
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-blue-700 transition-colors"
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Event
          </button>
          <button 
            onClick={() => setShowAIModal(true)}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-purple-700 transition-colors"
          >
            <Bot className="mr-2 h-4 w-4" />
            AI Schedule
          </button>
        </div>
      </div>

      {/* Calendar Component */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4">
        {isLoading ? (
          <div className="flex justify-center items-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <FullCalendar
            ref={calendarRef}
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            headerToolbar={{
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,timeGridWeek,timeGridDay'
            }}
            events={events}
            dateClick={handleDateClick}
            eventClick={handleEventClick}
            editable={true}
            selectable={true}
            height="auto"
            eventDisplay="block"
            dayMaxEvents={3}
            moreLinkClick="popover"
          />
        )}
      </div>

      {error && (
        <div className="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-800 text-red-800 dark:text-red-300 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Event Modal */}
      {showEventModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {currentEvent.id ? 'Edit Event' : 'New Event'}
              </h3>
              <button
                onClick={() => setShowEventModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={currentEvent.title || ''}
                  onChange={(e) => setCurrentEvent({...currentEvent, title: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Event title"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Start
                  </label>
                  <input
                    type="datetime-local"
                    value={currentEvent.start || ''}
                    onChange={(e) => setCurrentEvent({...currentEvent, start: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    End
                  </label>
                  <input
                    type="datetime-local"
                    value={currentEvent.end || ''}
                    onChange={(e) => setCurrentEvent({...currentEvent, end: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  value={currentEvent.location || ''}
                  onChange={(e) => setCurrentEvent({...currentEvent, location: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Event location"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={currentEvent.description || ''}
                  onChange={(e) => setCurrentEvent({...currentEvent, description: e.target.value})}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Event description"
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="allDay"
                  checked={currentEvent.allDay || false}
                  onChange={(e) => setCurrentEvent({...currentEvent, allDay: e.target.checked})}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="allDay" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                  All day event
                </label>
              </div>
            </div>
            
            <div className="flex justify-between items-center p-6 border-t border-gray-200 dark:border-gray-700">
              <div>
                {currentEvent.id && (
                  <button
                    onClick={deleteEvent}
                    className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 flex items-center"
                  >
                    <Trash2 className="mr-1 h-4 w-4" />
                    Delete
                  </button>
                )}
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowEventModal(false)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={saveEvent}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                >
                  <Save className="mr-2 h-4 w-4" />
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Scheduling Modal */}
      {showAIModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <Bot className="mr-2 h-5 w-5" />
                AI Scheduling
              </h3>
              <button
                onClick={() => setShowAIModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="p-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Describe your event in natural language:
              </label>
              <textarea
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="e.g., Schedule a compliance review meeting next Tuesday at 2pm"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Examples: "Staff training next Friday at 10am", "License renewal deadline in 30 days"
              </p>
            </div>
            
            <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => setShowAIModal(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleAIScheduling}
                disabled={!aiPrompt.trim() || aiLoading}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {aiLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Processing...
                  </>
                ) : (
                  <>
                    <Bot className="mr-2 h-4 w-4" />
                    Create Event
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <FeaturePreview
      featureKey="calendar"
      previewContent={previewContent}
      showPreviewBadge={true}
    >
      {mainContent}
    </FeaturePreview>
  );
};

export default Calendar; 