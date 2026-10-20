/*
  Description: Web Vitals utility for collecting and reporting core web performance metrics.
  Purpose: Enables monitoring of user experience and site performance by reporting metrics to analytics or logging systems.
*/
import { Metric, onCLS, onFID, onFCP, onLCP, onTTFB } from 'web-vitals';

/**
 * Reports Web Vitals metrics for performance monitoring
 * @param onPerfEntry - Function to handle reported metrics
 */
export function reportWebVitals(onPerfEntry?: (metric: Metric) => void): void {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    onCLS(onPerfEntry); // Cumulative Layout Shift
    onFID(onPerfEntry); // First Input Delay
    onFCP(onPerfEntry); // First Contentful Paint
    onLCP(onPerfEntry); // Largest Contentful Paint
    onTTFB(onPerfEntry); // Time to First Byte
  }
}

/**
 * Default handler that logs Web Vitals metrics to console and/or sends to analytics endpoint
 */
export const webVitalsHandler = (metric: Metric): void => {
  // Only log metrics to analytics in production
  if (import.meta.env.PROD) {
    try {
      // Example of sending to a backend endpoint
      const body = JSON.stringify({ 
        name: metric.name, 
        value: metric.value, 
        id: metric.id, 
        timestamp: new Date().getTime()
      });
      
      // Using sendBeacon for non-blocking analytics submission
      // This could be replaced with a fetch call to a specific endpoint
      navigator.sendBeacon('/api/v1/analytics/web-vitals', body);
    } catch (e) {
      // Silently fail in production to avoid error logs
    }
  }
}; 