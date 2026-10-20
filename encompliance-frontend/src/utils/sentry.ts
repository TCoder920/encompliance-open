/*
  Description: Sentry integration utility for error monitoring and reporting.
  Purpose: Initializes Sentry, logs errors, and sets user context to enable robust error tracking and diagnostics in production environments.
*/
import * as Sentry from '@sentry/react';

// Import originalConsole to avoid circular dependency issues
const originalConsole = {
  log: console.log,
  info: console.info,
  warn: console.warn,
  error: console.error,
  debug: console.debug,
};

/**
 * Initialize Sentry for error monitoring
 * 
 * @param environment - The environment name (e.g., 'development', 'production')
 */
export const initSentry = (environment: string = import.meta.env.MODE): void => {
  // Only initialize Sentry in production or staging environments
  if (environment === 'production' || environment === 'staging') {
    Sentry.init({
      dsn: import.meta.env.VITE_SENTRY_DSN || '', // Use environment variable for DSN
      integrations: [
        // Enable browser tracing
        Sentry.browserTracingIntegration(),
        // Enable replay for errors
        Sentry.replayIntegration({
          maskAllText: true,
          blockAllMedia: true,
        }),
      ],
      // Set tracesSampleRate to 1.0 to capture 100% of transactions for performance monitoring
      // We recommend adjusting this value in production
      tracesSampleRate: 0.5,
      // Set replaysSessionSampleRate to 0.1 to capture 10% of sessions
      replaysSessionSampleRate: 0.1,
      // Set replaysOnErrorSampleRate to 1.0 to capture 100% of sessions with errors
      replaysOnErrorSampleRate: 1.0,
      
      // App info
      environment,
      release: import.meta.env.VITE_APP_VERSION || '0.1.0',
    });
    
    // Use the original console to avoid circular reference with logger
    originalConsole.log(`Sentry initialized in ${environment} environment`);
  }
  // No need to log in development mode
};

/**
 * Log an error to Sentry
 * 
 * @param error - The error to report
 * @param context - Optional additional context data
 */
export const logError = (error: Error, context?: Record<string, any>): void => {
  // Use original console to avoid circular reference with logger
  originalConsole.error('Error:', error);
  
  if (import.meta.env.MODE === 'production' || import.meta.env.MODE === 'staging') {
    Sentry.captureException(error, { 
      contexts: { 
        custom: context 
      } 
    });
  }
};

/**
 * Set user context for Sentry
 * 
 * @param user - User information
 */
export const setUserContext = (user: { id?: string; email?: string; username?: string }): void => {
  Sentry.setUser(user);
}; 