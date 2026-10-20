import React, { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import staffDirectoryService, {
  DirectoryQueryParams,
  StaffDirectoryEntry,
  StaffDirectoryResponse,
} from '../services/staffDirectoryService';
import ErrorMessage from '../components/ErrorMessage';

interface TransferModalState {
  open: boolean;
  staff?: StaffDirectoryEntry;
}

const StaffDirectoryPage: React.FC = () => {
  const { user } = useAuth();
  const primaryFacilityId = user?.administered_facility?.id;
  const [directory, setDirectory] = useState<StaffDirectoryResponse | null>(null);
  const [filters, setFilters] = useState<DirectoryQueryParams>({
    page: 1,
    pageSize: 25,
  });
  const [searchInput, setSearchInput] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [assignStaffId, setAssignStaffId] = useState('');
  const [assignLoading, setAssignLoading] = useState(false);
  const [transferModal, setTransferModal] = useState<TransferModalState>({ open: false });
  const [transferFacilityId, setTransferFacilityId] = useState<number | undefined>(undefined);
  const [transferReason, setTransferReason] = useState('');
  const [transferLoading, setTransferLoading] = useState(false);

  const fetchDirectory = async () => {
    if (!primaryFacilityId) {
      setError('Facility context unavailable.');
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const response = await staffDirectoryService.fetchDirectory({
        ...filters,
        search: searchInput || undefined,
        status: statusFilter || undefined,
      });
      setDirectory(response);
    } catch (err) {
      console.error('Failed to load staff directory', err);
      setError('Unable to load staff directory. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const debounce = setTimeout(() => {
      fetchDirectory();
    }, 250);
    return () => clearTimeout(debounce);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.page, filters.pageSize, searchInput, statusFilter]);

  const facilityOptions = useMemo(() => {
    const map = new Map<number, string>();
    if (directory?.items) {
      directory.items.forEach((entry) => {
        if (!map.has(entry.facilityId)) {
          map.set(entry.facilityId, entry.facilityName);
        }
      });
    }
    if (primaryFacilityId && user?.administered_facility?.facility_name) {
      map.set(primaryFacilityId, user.administered_facility.facility_name);
    }
    return Array.from(map.entries()).map(([id, name]) => ({ id, name }));
  }, [directory?.items, primaryFacilityId, user?.administered_facility?.facility_name]);

  const openTransferModal = (staff: StaffDirectoryEntry) => {
    setTransferModal({ open: true, staff });
    setTransferFacilityId(undefined);
    setTransferReason('');
  };

  const handleAssign = async () => {
    if (!assignStaffId || !primaryFacilityId) {
      setError('Staff ID and facility context are required.');
      return;
    }
    try {
      setAssignLoading(true);
      await staffDirectoryService.assignStaff({
        staffMemberId: Number(assignStaffId),
        facilityId: primaryFacilityId,
      });
      setAssignStaffId('');
      fetchDirectory();
    } catch (err) {
      console.error('Failed to assign staff', err);
      setError('Unable to assign staff member. Confirm the ID and try again.');
    } finally {
      setAssignLoading(false);
    }
  };

  const handleTransferSubmit = async () => {
    if (!transferModal.staff || !transferFacilityId) {
      setError('Select a target facility to continue.');
      return;
    }
    try {
      setTransferLoading(true);
      await staffDirectoryService.requestTransfer({
        staffMemberId: transferModal.staff.staffMemberId,
        sourceFacilityId: transferModal.staff.facilityId,
        targetFacilityId: transferFacilityId,
        reason: transferReason,
      });
      setTransferModal({ open: false });
      fetchDirectory();
    } catch (err) {
      console.error('Failed to submit transfer', err);
      setError('Unable to submit transfer request.');
    } finally {
      setTransferLoading(false);
    }
  };

  const tableRows = directory?.items || [];
  const totalPages = directory ? Math.ceil(directory.total / (directory.pageSize || 25)) : 1;

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Staff Directory</h1>
          <p className="text-sm text-gray-500">
            Cross-facility roster with assignment and transfer controls.
          </p>
        </div>
        <div className="flex gap-3">
          <input
            type="number"
            placeholder="Assign staff ID"
            value={assignStaffId}
            onChange={(e) => setAssignStaffId(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          />
          <button
            onClick={handleAssign}
            disabled={assignLoading}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {assignLoading ? 'Assigning...' : 'Assign to My Facility'}
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      <section className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="grid gap-4 md:grid-cols-4">
          <input
            type="text"
            placeholder="Search staff"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          />
          <select
            value={filters.facilityId ?? ''}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, facilityId: e.target.value ? Number(e.target.value) : undefined }))
            }
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          >
            <option value="">All facilities</option>
            {facilityOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.name}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          >
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="terminated">Terminated</option>
            <option value="on_leave">On Leave</option>
          </select>
          <select
            value={filters.pageSize}
            onChange={(e) => setFilters((prev) => ({ ...prev, pageSize: Number(e.target.value), page: 1 }))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          >
            {[25, 50, 100].map((size) => (
              <option value={size} key={size}>
                Show {size}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section className="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        {loading ? (
          <p className="p-6 text-sm text-gray-500">Loading staff directory...</p>
        ) : tableRows.length === 0 ? (
          <p className="p-6 text-sm text-gray-500">No staff found for the current filters.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900/40">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-300">Name</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-300">Email</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-300">Department</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-300">Facility</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-300">Status</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-300">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {tableRows.map((entry) => (
                  <tr key={`${entry.assignmentId}-${entry.staffMemberId}`}>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{entry.fullName}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{entry.email}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{entry.department || '—'}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{entry.facilityName}</td>
                    <td className="px-4 py-3">
                      <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-gray-700 dark:bg-gray-700 dark:text-gray-100">
                        {entry.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => openTransferModal(entry)}
                        disabled={!primaryFacilityId || entry.facilityId === primaryFacilityId}
                        className="rounded-md border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                      >
                        Transfer
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3 text-sm dark:border-gray-700">
            <span className="text-gray-500">
              Page {filters.page} of {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setFilters((prev) => ({ ...prev, page: Math.max(1, (prev.page || 1) - 1) }))}
                disabled={(filters.page || 1) === 1}
                className="rounded-md border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-200"
              >
                Previous
              </button>
              <button
                onClick={() => setFilters((prev) => ({ ...prev, page: Math.min(totalPages, (prev.page || 1) + 1) }))}
                disabled={(filters.page || 1) >= totalPages}
                className="rounded-md border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-200"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </section>

      {transferModal.open && transferModal.staff && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl dark:bg-gray-900">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Transfer {transferModal.staff.fullName}
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Current facility: {transferModal.staff.facilityName}
            </p>
            <div className="mt-4 space-y-4">
              <select
                value={transferFacilityId ?? ''}
                onChange={(e) => setTransferFacilityId(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
              >
                <option value="">Select target facility</option>
                {facilityOptions
                  .filter((option) => option.id !== transferModal.staff?.facilityId)
                  .map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.name}
                    </option>
                  ))}
              </select>
              <textarea
                placeholder="Transfer reason (optional)"
                value={transferReason}
                onChange={(e) => setTransferReason(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setTransferModal({ open: false })}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleTransferSubmit}
                disabled={transferLoading || !transferFacilityId}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {transferLoading ? 'Submitting...' : 'Submit Transfer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StaffDirectoryPage;

