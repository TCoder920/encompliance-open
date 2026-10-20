import React, { useEffect, useState } from 'react';
import auditService, { AuditEntry } from '../services/auditService';
import ErrorMessage from '../components/ErrorMessage';

const AuditLogPage: React.FC = () => {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const response = await auditService.fetchLogs(page, pageSize);
      setEntries(response.items);
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to load audit logs', err);
      setError('Unable to load audit logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const handleExport = async () => {
    try {
      const blob = await auditService.exportCsv();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'audit-log.csv');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      console.error('Export failed', err);
      setError('Unable to export audit logs.');
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Audit Trail</h1>
          <p className="text-sm text-gray-500">Append-only history of administrative actions.</p>
        </div>
        <button
          onClick={handleExport}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
        >
          Export CSV
        </button>
      </div>
      {error && <ErrorMessage message={error} />}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        {loading ? (
          <p className="p-6 text-sm text-gray-500">Loading audit entries...</p>
        ) : entries.length === 0 ? (
          <p className="p-6 text-sm text-gray-500">No audit entries found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-100 text-sm dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900/40">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-300">Timestamp</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-300">Event</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-300">Description</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-300">Actor</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-300">Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                      {new Date(entry.createdAt).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{entry.eventType}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{entry.description}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{entry.actorUserId || 'System'}</td>
                    <td className="px-4 py-3 text-xs text-gray-400 dark:text-gray-500">{entry.entryHash.slice(0, 16)}…</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3 text-sm dark:border-gray-700">
            <span className="text-gray-500">
              Page {page} of {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                disabled={page === 1}
                className="rounded-md border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-200"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={page >= totalPages}
                className="rounded-md border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-200"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditLogPage;

