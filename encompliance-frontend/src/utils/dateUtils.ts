/*
  Description: Utility functions for formatting and handling dates and times across the application.
  Purpose: Provides standardized date/time formatting to ensure consistency and localization in user interfaces.
*/

/**
 * Universal date and time formatter that can handle both Date objects and string dates
 * This is the standard function to use for ALL date/time formatting across the application
 * 
 * @param timestamp - The date to format (can be Date object or string)
 * @param options - Optional formatting options (defaults to standard date and time format)
 * @returns Formatted date and time string or 'Unknown' if invalid
 */
export function formatDateTime(timestamp: Date | string | null | undefined, options?: Intl.DateTimeFormatOptions): string {
  try {
    if (!timestamp) return 'Unknown';
    
    // If timestamp is a string, convert it to a Date object
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      return 'Unknown';
    }
    
    // Default formatting options if none provided
    const defaultOptions: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    };
    
    // Use provided options or defaults, always using the user's browser locale settings
    return date.toLocaleString(undefined, options || defaultOptions);
  } catch (error) {
    console.error('Error formatting timestamp:', error);
    return 'Unknown';
  }
}

// Export only the standard date utility
export default {
  formatDateTime
}; 