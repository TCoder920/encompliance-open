/*
  Description: Google OAuth setup helper page.
*/

import React, { useEffect, useState } from 'react';
import FeaturePreview from '../components/ui/FeaturePreview';
import ErrorMessage from '../components/ErrorMessage';
import googleIntegrationService, { GoogleOAuthConfig } from '../services/googleIntegrationService';

const GoogleOAuthSetupPage: React.FC = () => {
  const [config, setConfig] = useState<GoogleOAuthConfig | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const response = await googleIntegrationService.getConfig();
        setConfig(response);
      } catch (err) {
        console.error('Failed to load Google config', err);
        setError('Unable to load Google OAuth configuration.');
      }
    })();
  }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Google OAuth Setup</h1>
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Use this client ID in the Google Cloud Console and your frontend .env file.
      </p>

      {error && <ErrorMessage message={error} />}

      <FeaturePreview featureKey="calendar">
        {config ? (
          <div className="space-y-3 text-sm text-gray-800 dark:text-gray-200">
            <div>
              <p className="font-semibold">Client ID</p>
              <code className="break-all bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                {config.clientId || 'Not configured'}
              </code>
            </div>
            <div>
              <p className="font-semibold">Scopes</p>
              <ul className="list-disc ml-5">
                {config.scopes.map((scope) => (
                  <li key={scope}>{scope}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500">Loading configuration...</p>
        )}
      </FeaturePreview>
    </div>
  );
};

export default GoogleOAuthSetupPage;

