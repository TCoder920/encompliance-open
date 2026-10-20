/**
 * Description: Calendar page for the EnCompliance application.
 * Purpose: Provides a container for the Calendar component with appropriate page layout.
 * This is a premium feature only available to Pro and Enterprise subscription tiers.
 */

import React from 'react';
import Calendar from '../components/ui/Calendar/Calendar';

const CalendarPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-6">Compliance Calendar</h1>
        <p className="text-gray-600 dark:text-gray-300 mb-6">
          Manage your compliance schedule, deadlines, and important events. This calendar helps you stay organized 
          and ensures you never miss important compliance-related dates.
        </p>
        
        {/* Calendar component with paywall enforcement */}
        <Calendar />
      </div>
    </div>
  );
};

export default CalendarPage; 