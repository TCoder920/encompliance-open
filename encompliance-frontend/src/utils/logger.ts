/*
  Description: Custom logger utility for redirecting console output to the server and filtering sensitive information.
  Purpose: Enhances security and compliance by preventing sensitive data from being logged in the browser and centralizing logs for analysis.
*/
// Custom logger that redirects console output to the server
// This helps keep user information from being logged to the browser console

type LogLevel = 'log' | 'info' | 'warn' | 'error' | 'debug';

// Store original console methods
const originalConsole = {
  log: console.log,
  info: console.info,
  warn: console.warn,
  error: console.error,
  debug: console.debug,
};

// List of sensitive patterns that should be filtered from logs
const sensitivePatterns = [
  /openai/i,
  /assistant_id/i,
  /files_added/i,
  /files_removed/i,
  /synchronizing/i,
  /resources/i,
  /session restored/i,
  /api\/logs/i,
];

// Messages to completely suppress from both server and console logs
const suppressPatterns = [
  /POST http:\/\/localhost:.*\/api\/logs/i,
  /OpenAI resources/i,
  /Synchronizing OpenAI resources/i,
  /Session restored/i,
  /Server logging unavailable/i
];

// Track server logging availability
let serverLoggingAvailable = false; // Start with false to avoid initial errors
let lastErrorTime = 0;
const ERROR_COOLDOWN_MS = 300000; // Wait 5 minutes before retrying

// Get the base URL for the backend API
// Use relative path by default to leverage Vite proxy, fall back to localhost if needed
const rawBaseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
// If rawBaseURL is empty, we use empty string to construct relative path like /api/logs
const API_BASE_URL = rawBaseURL.replace(/\/$/, '');
const LOGS_API_ENDPOINT = `${API_BASE_URL}/api/logs`;

// Function to check if a message contains sensitive information
const containsSensitiveInfo = (message: string): boolean => {
  return sensitivePatterns.some(pattern => pattern.test(message));
};

// Function to check if a message should be completely suppressed
const shouldSuppressMessage = (message: string): boolean => {
  return suppressPatterns.some(pattern => pattern.test(message));
};

// Function to send logs to the server
const sendLogToServer = async (level: LogLevel, ...args: any[]) => {
  // Format the log message
  const message = args
    .map(arg => 
      typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
    )
    .join(' ');
  
  // Check if we should completely suppress this message
  if (shouldSuppressMessage(message)) {
    return; // Don't log to server or console
  }
  
  // Check if message contains sensitive info
  if (containsSensitiveInfo(message)) {
    // If in development, can log a note that info was filtered (but not the actual message)
    if (import.meta.env.DEV && level === 'debug') {
      originalConsole.debug('[Logger] Filtered sensitive information');
    }
    return;
  }
  
  // Skip server logging if we've determined it's not available
  // But allow retries after cooldown period
  const now = Date.now();
  if (!serverLoggingAvailable && now - lastErrorTime < ERROR_COOLDOWN_MS) {
    // Optionally log to original console if server logging is temporarily unavailable
    // originalConsole.debug("[Logger] Server logging temporarily unavailable, logging to console only:", level, message);
    return;
  }

  try {
    // Get token for authenticated logging if available
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Send log to server
    const response = await fetch(LOGS_API_ENDPOINT, { // Use the full backend endpoint
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        level,
        message,
        timestamp: new Date().toISOString(),
      }),
      // Don't wait for response to avoid blocking the UI
      keepalive: true,
    });
    
    // Check response status
    if (!response.ok) {
      throw new Error(`Server logging failed with status: ${response.status}`);
    }
    
    // If we get here, server logging is available
    serverLoggingAvailable = true;
  } catch (e) {
    // Update server availability status and error time
    serverLoggingAvailable = false;
    lastErrorTime = Date.now();
    
    // Don't log error messages about server logging to avoid loops
  }
};

// Initialize logger by overriding console methods
export const initLogger = (redirectToServer = true) => {
  if (!redirectToServer) return;

  // Override console methods
  console.log = (...args: any[]) => {
    sendLogToServer('log', ...args);
  };

  console.info = (...args: any[]) => {
    sendLogToServer('info', ...args);
  };

  console.warn = (...args: any[]) => {
    sendLogToServer('warn', ...args);
  };

  console.error = (...args: any[]) => {
    sendLogToServer('error', ...args);
  };

  console.debug = (...args: any[]) => {
    sendLogToServer('debug', ...args);
  };
};

// Function to restore original console behavior
export const restoreConsole = () => {
  console.log = originalConsole.log;
  console.info = originalConsole.info;
  console.warn = originalConsole.warn;
  console.error = originalConsole.error;
  console.debug = originalConsole.debug;
};
