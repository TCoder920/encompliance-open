import React, { useEffect } from 'react';
import App from './App';
import { reportWebVitals, webVitalsHandler } from './utils/webVitals';
import { initSentry } from './utils/sentry';
import { initLogger } from './utils/logger';

/*
  Description: Entry point wrapper for the React application. Initializes web vitals, Sentry, and custom logger before rendering the main App component.
  Purpose: Ensures all monitoring and logging tools are set up before the application starts, providing a single entry for main.tsx to import.
*/
// Simple wrapper component to avoid direct imports in main.tsx
const EntryPoint: React.FC = () => {
  useEffect(() => {
    // Initialize web vitals reporting
    reportWebVitals(webVitalsHandler);
    
    // Initialize Sentry
    initSentry();
    
    // Initialize custom logger to redirect console output to server
    initLogger();
    
    // Removed console.log message as it's now handled inside the logger
  }, []);

  return <App />;
};

export default EntryPoint; 