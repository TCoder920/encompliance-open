/*
  Description: Scheduling management page for facility administrators.
  Purpose: Provides shift visibility, conflict detection, and quick scheduling workflows.
*/

import React, { useEffect, useMemo, useState } from 'react';
import {
  CalendarDays,
  RefreshCcw,
  AlertTriangle,
  Users,
  Clock,
  PlusCircle,
} from 'lucide-react';
import FeaturePreview from '../components/ui/FeaturePreview';
import schedulingService, {
  Shift,
  ShiftPayload,
  ConflictCheckResponse,
} from '../services/schedulingService';
import { useAuth } from '../contexts/AuthContext';
import { Tier, getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature } from '../utils/accessControl';
import { SAMPLE_SHIFTS, SAMPLE_SCHEDULING_SUMMARY } from '../utils/previewData';
import ErrorMessage from '../components/ErrorMessage';

type CoverageAlert = {
  id: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
};

interface SchedulingSummary {
  totalShifts: number;
  publishedShifts: number;
  openShifts: number;
  pendingSwapRequests: number;
  coverageAlerts: CoverageAlert[];
}

const SchedulingPage: React.FC = () => {
  const { user } = useAuth();
  const userTier: Tier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUse = canUseFeature(userTier, 'scheduling');
  const facilityId = user?.administered_facility?.id ?? user?.facility_id;

  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    startTime: '',
    endTime: '',
    staffMemberId: '',
    location: '',
    role: '',
  });
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [conflictWarning, setConflictWarning] = useState<ConflictCheckResponse | null>(null);

  useEffect(() => {
    loadShifts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canUse]);

  const loadShifts = async () => {
    setLoading(true);
    setError(null);
    try {
      if (!canUse) {
        setShifts(SAMPLE_SHIFTS as unknown as Shift[]);
      } else {
        const shiftResponse = await schedulingService.listShifts();
        setShifts(shiftResponse);
      }
    } catch (err) {
      console.error('Failed to load shifts', err);
      setError('Unable to load scheduling data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const summary: SchedulingSummary = useMemo(() => {
    if (!canUse) {
      return SAMPLE_SCHEDULING_SUMMARY as SchedulingSummary;
    }

    const publishedShifts = shifts.filter((shift) => shift.status === 'published').length;
    const openShifts = shifts.filter((shift) => !shift.staffMemberId).length;
    const pendingSwapRequests = shifts.filter((shift) => shift.status === 'pending_swap').length;
    const alerts: CoverageAlert[] = [];

    if (openShifts > 0) {
      alerts.push({
        id: 'open-shifts',
        message: `${openShifts} shift(s) still need assignments`,
        severity: 'medium',
      });
    }
    if (pendingSwapRequests > 0) {
      alerts.push({
        id: 'swap-requests',
        message: `${pendingSwapRequests} shift swap request(s) require review`,
        severity: 'low',
      });
    }

    return {
      totalShifts: shifts.length,
      publishedShifts,
      openShifts,
      pendingSwapRequests,
      coverageAlerts: alerts,
    };
  }, [shifts, canUse]);

  const handleInputChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (conflictWarning) {
      setConflictWarning(null);
    }
  };

  const handleCreateShift = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canUse) return;

    if (!facilityId) {
      setError('Facility context missing. Please refresh your session.');
      return;
    }

    if (!formData.title || !formData.startTime || !formData.endTime) {
      setError('Title, start, and end time are required.');
      return;
    }

    const startIso = new Date(formData.startTime).toISOString();
    const endIso = new Date(formData.endTime).toISOString();
    if (new Date(endIso) <= new Date(startIso)) {
      setError('End time must be after start time.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const staffMemberId = formData.staffMemberId
        ? Number(formData.staffMemberId)
        : undefined;

      if (staffMemberId) {
        const conflict = await schedulingService.checkConflicts({
          staffMemberId,
          startTime: startIso,
          endTime: endIso,
        });
        if (conflict.hasConflict) {
          setConflictWarning(conflict);
          setSubmitting(false);
          return;
        }
      }

      const payload: ShiftPayload = {
        facilityId,
        title: formData.title,
        startTime: startIso,
        endTime: endIso,
        staffMemberId: staffMemberId ?? null,
        location: formData.location || undefined,
        role: formData.role || undefined,
      };

      await schedulingService.createShift(payload);
      setFormData({
        title: '',
        startTime: '',
        endTime: '',
        staffMemberId: '',
        location: '',
        role: '',
      });
      setConflictWarning(null);
      await loadShifts();
    } catch (err) {
      console.error('Failed to create shift', err);
      setError('Unable to create shift. Please review the details and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const renderStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-700',
      published: 'bg-green-100 text-green-700',
      in_progress: 'bg-blue-100 text-blue-700',
      completed: 'bg-emerald-100 text-emerald-700',
      cancelled: 'bg-slate-100 text-slate-600',
      pending_swap: 'bg-yellow-100 text-yellow-700',
    };
    const label = status.replace('_', ' ');
    return (
      <span
        className={`px-2 py-1 rounded-full text-xs font-semibold ${
          styles[status] ?? 'bg-gray-100 text-gray-700'
        }`}
      >
        {label}
      </span>
    );
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <CalendarDays className="w-8 h-8 text-blue-500" />
            Scheduling & Coverage
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Build compliant schedules, resolve conflicts, and track workforce coverage.
          </p>
        </div>
        <button
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold shadow hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={loadShifts}
          disabled={loading}
        >
          <RefreshCcw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {error && <ErrorMessage message={error} />}

      <FeaturePreview featureKey="scheduling">
        <div className="space-y-6">
          <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800">
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Shifts</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {summary.totalShifts}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800">
              <p className="text-sm text-gray-500 dark:text-gray-400">Published</p>
              <p className="text-2xl font-semibold text-green-600">{summary.publishedShifts}</p>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800">
              <p className="text-sm text-gray-500 dark:text-gray-400">Open Coverage</p>
              <p className="text-2xl font-semibold text-yellow-600">{summary.openShifts}</p>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800">
              <p className="text-sm text-gray-500 dark:text-gray-400">Swap Requests</p>
              <p className="text-2xl font-semibold text-indigo-600">
                {summary.pendingSwapRequests}
              </p>
            </div>
          </section>

          {summary.coverageAlerts.length > 0 && (
            <section className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-4">
              <div className="flex items-center gap-2 text-amber-800 dark:text-amber-200 font-semibold mb-2">
                <AlertTriangle className="w-5 h-5" />
                Coverage Alerts
              </div>
              <ul className="space-y-2">
                {summary.coverageAlerts.map((alert) => (
                  <li key={alert.id} className="flex items-start gap-3 text-sm text-amber-900 dark:text-amber-100">
                    <span className="mt-0.5">•</span>
                    {alert.message}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Quick Shift Builder
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Capture urgent coverage directly from this dashboard. Advanced tools coming soon.
                </p>
              </div>
            </div>

            <form className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" onSubmit={handleCreateShift}>
              <div>
                <label className="text-sm text-gray-600 dark:text-gray-300 mb-1 block">Title</label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                  placeholder="e.g., Morning Room Coverage"
                  required
                  disabled={!canUse || submitting}
                />
              </div>

              <div>
                <label className="text-sm text-gray-600 dark:text-gray-300 mb-1 block">
                  Start Time
                </label>
                <input
                  type="datetime-local"
                  name="startTime"
                  value={formData.startTime}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                  required
                  disabled={!canUse || submitting}
                />
              </div>

              <div>
                <label className="text-sm text-gray-600 dark:text-gray-300 mb-1 block">
                  End Time
                </label>
                <input
                  type="datetime-local"
                  name="endTime"
                  value={formData.endTime}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                  required
                  disabled={!canUse || submitting}
                />
              </div>

              <div>
                <label className="text-sm text-gray-600 dark:text-gray-300 mb-1 block">
                  Staff Member ID (optional)
                </label>
                <input
                  type="number"
                  name="staffMemberId"
                  value={formData.staffMemberId}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                  placeholder="Assign immediately"
                  disabled={!canUse || submitting}
                />
              </div>

              <div>
                <label className="text-sm text-gray-600 dark:text-gray-300 mb-1 block">Location</label>
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                  placeholder="Classroom, floor, etc."
                  disabled={!canUse || submitting}
                />
              </div>

              <div>
                <label className="text-sm text-gray-600 dark:text-gray-300 mb-1 block">Role</label>
                <input
                  type="text"
                  name="role"
                  value={formData.role}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                  placeholder="Lead, support, float..."
                  disabled={!canUse || submitting}
                />
              </div>

              {conflictWarning?.hasConflict && (
                <div className="md:col-span-2 lg:col-span-3 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/30 px-4 py-3 text-sm text-red-800 dark:text-red-200 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  {conflictWarning.conflictReason || 'Scheduling conflict detected.'}
                </div>
              )}

              <div className="md:col-span-2 lg:col-span-3 flex justify-end">
                <button
                  type="submit"
                  className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold shadow hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
                  disabled={!canUse || submitting}
                >
                  <PlusCircle className="w-4 h-4" />
                  Create Shift
                </button>
              </div>
            </form>
          </section>

          <section className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Upcoming Shifts</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Monitor staff coverage, swaps, and unassigned slots.
                </p>
              </div>
            </div>

            {loading ? (
              <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                Loading schedule...
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-800/60 text-gray-600 dark:text-gray-300">
                    <tr>
                      <th className="px-4 py-2 text-left">Shift</th>
                      <th className="px-4 py-2 text-left">Schedule</th>
                      <th className="px-4 py-2 text-left">Assignment</th>
                      <th className="px-4 py-2 text-left">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shifts.slice(0, 15).map((shift) => (
                      <tr
                        key={shift.id}
                        className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50/80 dark:hover:bg-gray-800/50 transition-colors"
                      >
                        <td className="px-4 py-3">
                          <p className="font-medium text-gray-900 dark:text-white">{shift.title}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {shift.location || 'Unspecified'} • {shift.role || 'General'}
                          </p>
                        </td>
                        <td className="px-4 py-3 text-gray-700 dark:text-gray-200">
                          <div className="flex items-center gap-2 text-xs">
                            <Clock className="w-4 h-4 text-gray-400" />
                            {new Date(shift.startTime).toLocaleString()} -{' '}
                            {new Date(shift.endTime).toLocaleTimeString()}
                          </div>
                          {shift.recurrencePattern && shift.recurrencePattern !== 'none' && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              Repeats {shift.recurrencePattern.toLowerCase()}
                            </p>
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-700 dark:text-gray-200">
                          <div className="flex items-center gap-2 text-xs">
                            <Users className="w-4 h-4 text-gray-400" />
                            {shift.staffMemberId ? `Staff #${shift.staffMemberId}` : 'Unassigned'}
                          </div>
                          {shift.conflictReason && (
                            <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                              <AlertTriangle className="w-3 h-3" />
                              {shift.conflictReason}
                            </p>
                          )}
                        </td>
                        <td className="px-4 py-3">{renderStatusBadge(shift.status || '')}</td>
                      </tr>
                    ))}
                    {shifts.length === 0 && (
                      <tr>
                        <td
                          colSpan={4}
                          className="px-4 py-6 text-center text-gray-500 dark:text-gray-400"
                        >
                          No shifts scheduled yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </FeaturePreview>
    </div>
  );
};

export default SchedulingPage;

