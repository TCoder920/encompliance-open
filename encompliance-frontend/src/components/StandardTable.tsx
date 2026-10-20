/*
  Description: StandardTable component for rendering tabular data with sorting, pagination, and custom cell rendering.
  Purpose: Provides a reusable and flexible table component for displaying structured data throughout the application.
*/
import React, { useState, useMemo } from 'react';

export interface Column<T> {
  /** Key of the data field */
  key: string;
  /** Header label to display */
  header: string;
  /** Whether this column is sortable */
  sortable?: boolean;
  /** Optional custom cell renderer */
  renderCell?: (row: T) => React.ReactNode;
}

interface StandardTableProps<T> {
  /** Columns configuration */
  columns: Column<T>[];
  /** Array of data objects */
  data: T[];
  /** Initial rows per page (default 20) */
  pageSize?: number;
}

function StandardTable<T extends Record<string, any>>({
  columns,
  data,
  pageSize = 20
}: StandardTableProps<T>) {
  const [page, setPage] = useState(0);
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [filterText, setFilterText] = useState('');

  // Filtered data
  const filtered = useMemo(() => {
    if (!filterText) return data;
    const lower = filterText.toLowerCase();
    return data.filter(item =>
      columns.some(col => {
        const raw = item[col.key];
        const str = raw != null ? (typeof raw === 'object' ? JSON.stringify(raw) : String(raw)) : '';
        return str.toLowerCase().includes(lower);
      })
    );
  }, [data, filterText, columns]);

  // Sorted data
  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null && bVal != null) return -1;
      if (aVal != null && bVal == null) return 1;
      if (aVal == null && bVal == null) return 0;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
      }
      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      if (aStr < bStr) return sortDir === 'asc' ? -1 : 1;
      if (aStr > bStr) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filtered, sortKey, sortDir]);

  // Paginated data
  const pageCount = Math.ceil(sorted.length / pageSize);
  const pageData = useMemo(() => sorted.slice(page * pageSize, (page + 1) * pageSize), [sorted, page, pageSize]);
  const canPrev = page > 0;
  const canNext = page + 1 < pageCount;

  const onHeaderClick = (col: Column<T>) => {
    if (!col.sortable) return;
    if (sortKey === col.key) {
      setSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(col.key);
      setSortDir('asc');
    }
    setPage(0);
  };

  return (
    <div className="space-y-4">
      {/* Filter Input */}
      <div className="flex justify-between items-center">
        <input
          type="text"
          placeholder="Filter..."
          value={filterText}
          onChange={e => { setFilterText(e.target.value); setPage(0); }}
          className="border rounded px-3 py-1 focus:outline-none focus:ring focus:border-blue-300 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
        />
        <span className="text-sm text-gray-600 dark:text-gray-400">
          Showing {pageData.length} of {filtered.length}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border dark:border-gray-700 rounded">
        <table className="min-w-full bg-white dark:bg-gray-800 text-gray-800 dark:text-dark-text table-auto">
          <thead className="sticky top-0 bg-gray-100 dark:bg-gray-700 z-10">
            <tr>
              {columns.map(col => (
                <th
                  key={col.key}
                  className={
                    `py-2 px-3 border-b dark:border-gray-600 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider ` +
                    (col.sortable ? 'cursor-pointer select-none' : '')
                  }
                  onClick={() => onHeaderClick(col)}
                >
                  <div className="flex items-center space-x-1">
                    <span>{col.header}</span>
                    {sortKey === col.key && (
                      <span>{sortDir === 'asc' ? '▲' : '▼'}</span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
            {pageData.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">
                {columns.map(col => (
                  <td key={col.key} className="py-2 px-3 border-b dark:border-gray-600 align-top">
                    {col.renderCell ? col.renderCell(row) : String(row[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="text-center py-4 text-gray-500">
                  No data found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex justify-between items-center">
        <button
          onClick={() => canPrev && setPage(p => p - 1)}
          disabled={!canPrev}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <span className="text-sm text-gray-800 dark:text-dark-text">
          Page {page + 1} of {pageCount}
        </span>
        <button
          onClick={() => canNext && setPage(p => p + 1)}
          disabled={!canNext}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default StandardTable; 