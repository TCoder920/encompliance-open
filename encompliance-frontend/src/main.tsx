/*
  Description: Main entry point for the React application. Mounts the EntryPoint component to the DOM using React 18's createRoot API.
  Purpose: Bootstraps the frontend by rendering the application into the DOM and handles version checking for cache busting.
*/
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import EntryPoint from './EntryPoint';
import { checkForUpdates } from './utils/versionCheck';
import './index.css';

// Check if app version has changed and clear caches if needed
checkForUpdates();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <EntryPoint />
  </StrictMode>
);

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js')
      .catch((error) => {
        console.error('Service worker registration failed', error);
      });
  });
}
