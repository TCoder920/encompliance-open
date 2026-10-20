/*
  Description: Data Import wizard page.
  Purpose: Allows admins to paste export JSON and run dry-run or final import.
*/

import React, { useState } from 'react';
import FeaturePreview from '../components/ui/FeaturePreview';
import ErrorMessage from '../components/ErrorMessage';
import dataImportService from '../services/dataImportService';

const DataImportPage: React.FC = () => {
  const [rawPayload, setRawPayload] = useState('');
  const [dryRunResult, setDryRunResult] = useState<string | null>(null);
  const [applyResult, setApplyResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const parsePayload = (): Record<string, unknown> | null => {
    try {
      setError(null);
      return JSON.parse(rawPayload);
    } catch {
      setError('Invalid JSON payload.');
      return null;
    }
  };

  const handleDryRun = async () => {
    const payload = parsePayload();
    if (!payload) return;
    setIsProcessing(true);
    setDryRunResult(null);
    setApplyResult(null);
    try {
      const response = await dataImportService.submitImport({ payload, dry_run: true });
      setDryRunResult(
        `Dry run success. Records processed: ${response.records_created}. ` +
          `${response.warnings?.join(' ') || ''}`
      );
    } catch (err) {
      console.error('Dry run failed', err);
      setError('Dry run failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApply = async () => {
    const payload = parsePayload();
    if (!payload) return;
    setIsProcessing(true);
    setApplyResult(null);
    try {
      const response = await dataImportService.submitImport({ payload, dry_run: false });
      setApplyResult(`Import complete. Records created: ${response.records_created}.`);
    } catch (err) {
      console.error('Import failed', err);
      setError('Import failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Data Import</h1>
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Paste JSON exported from the compliance platform to rehydrate a facility.
      </p>

      {error && <ErrorMessage message={error} />}

      <FeaturePreview featureKey="data_import">
        <textarea
          className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm min-h-[250px]"
          placeholder='{"notes": [...], "documents": [...]}'
          value={rawPayload}
          onChange={(e) => setRawPayload(e.target.value)}
          disabled={isProcessing}
        />
        <div className="flex gap-3">
          <button
            onClick={handleDryRun}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold disabled:opacity-50"
            disabled={isProcessing}
          >
            Dry Run
          </button>
          <button
            onClick={handleApply}
            className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-semibold disabled:opacity-50"
            disabled={isProcessing}
          >
            Apply Import
          </button>
        </div>
        {dryRunResult && (
          <p className="text-sm text-blue-600 dark:text-blue-300 mt-3">{dryRunResult}</p>
        )}
        {applyResult && (
          <p className="text-sm text-emerald-600 dark:text-emerald-300 mt-3">{applyResult}</p>
        )}
      </FeaturePreview>
    </div>
  );
};

export default DataImportPage;

