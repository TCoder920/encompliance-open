import React, { useEffect, useMemo, useState } from 'react';
import storageService, { StorageUsageSummary } from '../services/storageService';
import ErrorMessage from '../components/ErrorMessage';

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
};

const BillingPage: React.FC = () => {
  const [summary, setSummary] = useState<StorageUsageSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const loadUsage = async () => {
    try {
      setError(null);
      const response = await storageService.getUsage();
      setSummary(response);
    } catch (err) {
      console.error('Failed to load storage usage', err);
      setError('Unable to load storage usage at the moment.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadUsage();
  }, []);

  const handleRecalculate = async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    try {
      const response = await storageService.recalculate();
      setSummary(response);
    } catch (err) {
      console.error('Failed to recalculate storage usage', err);
      setError('Recalculation failed. Please try again in a few minutes.');
    } finally {
      setIsRefreshing(false);
    }
  };

  const usagePercent = useMemo(() => {
    if (!summary) return 0;
    return Math.round((summary.percent_used || 0) * 100);
  }, [summary]);

  if (isLoading) {
    return (
      <div className="p-6">
        <p className="text-sm text-gray-500">Loading billing data...</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Storage Billing</h1>
          <p className="text-sm text-gray-500">
            Monitor facility storage usage, quotas, and overage risk.
          </p>
        </div>
        <button
          onClick={() => (window.location.href = '/subscription')}
          className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
        >
          Manage Plan
        </button>
      </div>

      {error && <ErrorMessage message={error} />}

      {summary && (
        <>
          <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-sm uppercase tracking-wider text-gray-500">Current Tier</p>
                <p className="text-2xl font-semibold capitalize text-gray-900 dark:text-white">
                  {summary.tier_name}
                </p>
                <p className="text-xs text-gray-500">
                  Billing cycle {new Date(summary.billing_period_start).toLocaleDateString()} -{' '}
                  {new Date(summary.billing_period_end).toLocaleDateString()}
                </p>
              </div>
              <div className="flex gap-8 text-sm">
                <div>
                  <p className="text-gray-500">Included</p>
                  <p className="text-xl font-semibold text-gray-900 dark:text-white">
                    {formatBytes(summary.included_bytes)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Used</p>
                  <p className="text-xl font-semibold text-gray-900 dark:text-white">
                    {formatBytes(summary.used_bytes)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Available</p>
                  <p className="text-xl font-semibold text-gray-900 dark:text-white">
                    {formatBytes(summary.available_bytes)}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Usage</span>
                <span>{usagePercent}%</span>
              </div>
              <div className="mt-2 h-3 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className={`h-3 rounded-full ${
                    usagePercent >= 90
                      ? 'bg-red-500'
                      : usagePercent >= 75
                      ? 'bg-yellow-400'
                      : 'bg-emerald-500'
                  }`}
                  style={{ width: `${Math.min(usagePercent, 100)}%` }}
                />
              </div>
              {summary.alert_level && (
                <p className="mt-3 text-sm font-medium text-red-600 dark:text-red-400">
                  {summary.alert_level === 'critical'
                    ? 'Critical storage level detected. Upgrade immediately to avoid service disruption.'
                    : 'Warning: storage usage is nearing quota.'}
                </p>
              )}
            </div>

            <div className="mt-4 flex flex-wrap gap-3">
              <button
                onClick={handleRecalculate}
                disabled={isRefreshing}
                className="inline-flex items-center rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-600 dark:text-white dark:hover:bg-gray-700"
              >
                {isRefreshing ? 'Recalculating...' : 'Recalculate Usage'}
              </button>
              {summary.recommended_tier && (
                <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                  Recommended upgrade: {summary.recommended_tier.toUpperCase()}
                </span>
              )}
            </div>
          </section>

          <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Storage Events</h2>
            {summary.events.length === 0 ? (
              <p className="mt-2 text-sm text-gray-500">No storage events recorded in this period.</p>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-left text-sm text-gray-600 dark:text-gray-300">
                  <thead>
                    <tr>
                      <th className="px-3 py-2 font-medium">Timestamp</th>
                      <th className="px-3 py-2 font-medium">Resource</th>
                      <th className="px-3 py-2 font-medium">Delta</th>
                      <th className="px-3 py-2 font-medium">Metadata</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.events.map((event) => (
                      <tr key={event.id} className="border-t border-gray-100 dark:border-gray-700">
                        <td className="px-3 py-2 text-xs">
                          {new Date(event.created_at).toLocaleString()}
                        </td>
                        <td className="px-3 py-2 capitalize text-xs">{event.resource_type.replace('_', ' ')}</td>
                        <td className="px-3 py-2 text-xs font-semibold">
                          {event.delta_bytes >= 0 ? '+' : '-'}
                          {formatBytes(Math.abs(event.delta_bytes))}
                        </td>
                        <td className="px-3 py-2 text-xs">
                          {event.metadata && Object.keys(event.metadata).length > 0
                            ? JSON.stringify(event.metadata)
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
};

export default BillingPage;

