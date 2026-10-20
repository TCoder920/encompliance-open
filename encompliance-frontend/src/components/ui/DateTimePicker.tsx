/*
Description: A date and time picker component with calendar popup and direct input capabilities.
Purpose: Provides an intuitive interface for selecting dates and times with both visual calendar and manual input options.
*/
import React, { useState, useRef, useEffect } from 'react';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';

interface DateTimePickerProps {
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  required?: boolean;
  className?: string;
}

const DateTimePicker: React.FC<DateTimePickerProps> = ({
  value = '',
  onChange,
  placeholder = 'Select date and time',
  label,
  required = false,
  className = ''
}) => {
  const [showCalendar, setShowCalendar] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [dateValue, setDateValue] = useState('');
  const [timeValue, setTimeValue] = useState('');
  const [calendarMonth, setCalendarMonth] = useState(new Date().getMonth());
  const [calendarYear, setCalendarYear] = useState(new Date().getFullYear());
  const calendarRef = useRef<HTMLDivElement>(null);
  const timePickerRef = useRef<HTMLDivElement>(null);

  // Parse initial value
  useEffect(() => {
    if (value) {
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        
        setDateValue(`${year}-${month}-${day}`);
        setTimeValue(`${hours}:${minutes}`);
      }
    }
  }, [value]);

  // Close calendar when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (calendarRef.current && !calendarRef.current.contains(event.target as Node)) {
        setShowCalendar(false);
      }
      if (timePickerRef.current && !timePickerRef.current.contains(event.target as Node)) {
        setShowTimePicker(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleDateChange = (newDate: string) => {
    setDateValue(newDate);
    updateDateTime(newDate, timeValue);
  };

  const handleTimeChange = (newTime: string) => {
    setTimeValue(newTime);
    updateDateTime(dateValue, newTime);
    setShowTimePicker(false);
  };

  const updateDateTime = (date: string, time: string) => {
    if (date && time) {
      const dateTimeString = `${date}T${time}:00`;
      onChange(dateTimeString);
    } else if (date) {
      const dateTimeString = `${date}T00:00:00`;
      onChange(dateTimeString);
    } else {
      onChange('');
    }
  };

  const formatDisplayValue = () => {
    if (!value) return '';
    
    const date = new Date(value);
    if (isNaN(date.getTime())) return '';
    
    return date.toLocaleDateString('en-US', {
      month: '2-digit',
      day: '2-digit',
      year: 'numeric'
    });
  };

  const formatTimeValue = () => {
    if (!value) return '';
    
    const date = new Date(value);
    if (isNaN(date.getTime())) return '';
    
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  const generateCalendarDays = () => {
    const firstDay = new Date(calendarYear, calendarMonth, 1);
    const lastDay = new Date(calendarYear, calendarMonth + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    const days = [];
    const currentDate = new Date(startDate);
    
    for (let i = 0; i < 42; i++) {
      days.push(new Date(currentDate));
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    return days;
  };

  const handleCalendarDateClick = (date: Date) => {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const dateString = `${year}-${month}-${day}`;
    
    handleDateChange(dateString);
    setShowCalendar(false);
  };

  const generateTimeOptions = () => {
    const times = [];
    for (let hour = 0; hour < 24; hour++) {
      for (let minute = 0; minute < 60; minute += 15) {
        const timeString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        times.push(timeString);
      }
    }
    return times;
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      if (calendarMonth === 0) {
        setCalendarMonth(11);
        setCalendarYear(calendarYear - 1);
      } else {
        setCalendarMonth(calendarMonth - 1);
      }
    } else {
      if (calendarMonth === 11) {
        setCalendarMonth(0);
        setCalendarYear(calendarYear + 1);
      } else {
        setCalendarMonth(calendarMonth + 1);
      }
    }
  };

  const navigateToToday = () => {
    const today = new Date();
    setCalendarMonth(today.getMonth());
    setCalendarYear(today.getFullYear());
  };

  const generateYearOptions = () => {
    const currentYear = new Date().getFullYear();
    const years = [];
    // Allow selection from current year to 5 years in the future
    for (let year = currentYear; year <= currentYear + 5; year++) {
      years.push(year);
    }
    return years;
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const calendarDays = generateCalendarDays();
  const today = new Date();
  const timeOptions = generateTimeOptions();

  return (
    <div className={`relative ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      
      <div className="space-y-3">
        {/* Date Input */}
        <div className="relative">
          <input
            type="text"
            value={formatDisplayValue()}
            onChange={(e) => {
              // Allow direct typing in MM/DD/YYYY format
              const inputValue = e.target.value;
              if (inputValue.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
                const [month, day, year] = inputValue.split('/');
                const dateString = `${year}-${month}-${day}`;
                handleDateChange(dateString);
              }
            }}
            placeholder={placeholder}
            className="w-full pl-3 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            type="button"
            onClick={() => setShowCalendar(!showCalendar)}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <Calendar className="h-5 w-5" />
          </button>
        </div>

        {/* Time Input - Clickable Display */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowTimePicker(!showTimePicker)}
            className="w-full pl-3 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-left hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          >
            {formatTimeValue() || 'Select time'}
          </button>
          
          {/* Time Picker Dropdown */}
          {showTimePicker && (
            <div
              ref={timePickerRef}
              className="absolute top-full left-0 mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg z-50 w-full max-h-60 overflow-y-auto"
            >
              {timeOptions.map((time) => (
                <button
                  key={time}
                  type="button"
                  onClick={() => handleTimeChange(time)}
                  className={`w-full px-3 py-2 text-left hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors ${
                    timeValue === time ? 'bg-blue-500 text-white' : 'text-gray-900 dark:text-white'
                  }`}
                >
                  {time}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Calendar Popup */}
      {showCalendar && (
        <div
          ref={calendarRef}
          className="absolute top-full left-0 mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg z-50 p-4 w-80"
        >
          <div className="flex items-center justify-between mb-4">
            <button
              type="button"
              onClick={() => navigateMonth('prev')}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <ChevronLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            </button>
            
            <div className="flex items-center space-x-2">
              <select
                value={calendarMonth}
                onChange={(e) => setCalendarMonth(parseInt(e.target.value))}
                className="text-sm bg-transparent border-none text-gray-900 dark:text-white focus:outline-none cursor-pointer"
              >
                {monthNames.map((month, index) => (
                  <option key={index} value={index} className="bg-white dark:bg-gray-800">
                    {month}
                  </option>
                ))}
              </select>
              
              <select
                value={calendarYear}
                onChange={(e) => setCalendarYear(parseInt(e.target.value))}
                className="text-sm bg-transparent border-none text-gray-900 dark:text-white focus:outline-none cursor-pointer"
              >
                {generateYearOptions().map((year) => (
                  <option key={year} value={year} className="bg-white dark:bg-gray-800">
                    {year}
                  </option>
                ))}
              </select>
            </div>
            
            <button
              type="button"
              onClick={() => navigateMonth('next')}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <ChevronRight className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
          
          <div className="text-center mb-2">
            <button
              type="button"
              onClick={navigateToToday}
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
            >
              Go to Today
            </button>
          </div>
          
          <div className="grid grid-cols-7 gap-1 mb-2">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center text-sm font-medium text-gray-500 dark:text-gray-400 py-2">
                {day}
              </div>
            ))}
          </div>
          
          <div className="grid grid-cols-7 gap-1">
            {calendarDays.map((date, index) => {
              const isCurrentMonth = date.getMonth() === calendarMonth;
              const isToday = date.toDateString() === today.toDateString();
              const isSelected = dateValue === date.toISOString().split('T')[0];
              
              return (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleCalendarDateClick(date)}
                  className={`
                    p-2 text-sm rounded hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors
                    ${!isCurrentMonth ? 'text-gray-300 dark:text-gray-600' : 'text-gray-900 dark:text-white'}
                    ${isToday ? 'bg-blue-100 dark:bg-blue-900 font-semibold' : ''}
                    ${isSelected ? 'bg-blue-500 text-white hover:bg-blue-600' : ''}
                  `}
                >
                  {date.getDate()}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default DateTimePicker; 