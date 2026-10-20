/*
  Description: Utility function for formatting elapsed time from a timestamp into a human-readable string.
  Purpose: Provides user-friendly relative time displays (e.g., 'just now', '2 hours ago') for UI components.
*/
export function formatElapsedTime(timestamp: string | number): string {
    const elapsed = Date.now() - new Date(timestamp).getTime();
    const TEN_MINUTES = 10 * 60 * 1000;
    const ONE_HOUR = 60 * 60 * 1000;
    const ONE_DAY = 24 * 60 * 60 * 1000;

    if (elapsed < TEN_MINUTES) {
        return 'just now';
    } else if (elapsed < ONE_HOUR) {
        // Round down to the nearest 10 minutes
        const minutes = Math.floor(elapsed / TEN_MINUTES) * 10;
        return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    } else if (elapsed < ONE_DAY) {
        const hours = Math.floor(elapsed / ONE_HOUR);
        return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    } else {
        const days = Math.floor(elapsed / ONE_DAY);
        return `${days} day${days !== 1 ? 's' : ''} ago`;
    }
} 