/*
  Description: Usage billing overview page.
*/

import React, { useEffect, useState } from 'react';
import FeaturePreview from '../components/ui/FeaturePreview';
import ErrorMessage from '../components/ErrorMessage';
import usageBillingService, { UsageSummary } from '../services/usageBillingService';

const UsageBillingPage: React.FC = () => {
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [facilitySummary, setFacilitySummary] = useState<{ tokens: number; cost: number } | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const response = await usageBillingService.getSummary();
        setSummary(response);
        const facilityResponse = await usageBillingService.getFacilitySummary();
        setFacilitySummary(facilityResponse);
      } catch (err) {
        console.error('Failed to load usage summary', err);
        setError('Unable to load usage summary.');
      }
    })();
  }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Usage-Based Billing</h1>
      {error && <ErrorMessage message={error} />}

      <FeaturePreview featureKey="usage_billing">
        {summary ? (
          <div className="space-y-4 text-sm text-gray-800 dark:text-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                <p className="text-gray-500">User tokens this month</p>
                <p className="text-2xl font-semibold">{summary.month_tokens}</p>
              </div>
              <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                <p className="text-gray-500">User cost (USD)</p>
                <p className="text-2xl font-semibold">${summary.month_cost.toFixed(4)}</p>
              </div>
              <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                <p className="text-gray-500">Facility total (USD)</p>
                <p className="text-2xl font-semibold">
                  {facilitySummary ? `$${facilitySummary.cost.toFixed(4)}` : '—'}
                </p>
              </div>
            </div>
            <div>
              <h2 className="font-semibold mb-2">Recent Usage</h2>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left">
                    <th>Date</th>
                    <th>Tokens</th>
                    <th>Prompt Tokens</th>
                    <th>Completion Tokens</th>
                    <th>Model</th>
                    <th>Cost (USD)</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.logs.map((log, idx) => (
                    <tr key={idx}>
                      <td>{new Date(log.created_at).toLocaleString()}</td>
                      <td>{log.tokens_used}</td>
                      <td>{log.prompt_tokens ?? 0}</td>
                      <td>{log.completion_tokens ?? 0}</td>
                      <td>{log.model_name || 'default'}</td>
                      <td>${log.cost_usd.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500">Loading usage data...</p>
        )}
      </FeaturePreview>
    </div>
  );
};

export default UsageBillingPage;

