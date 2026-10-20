import api from './api';

/*
  Description: Scheduling service client that wraps backend scheduling APIs.
  Purpose: Centralizes HTTP calls for shifts, availability, time-off, and shift swaps.
*/

export type ShiftStatus =
  | 'draft'
  | 'published'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'pending_swap';

export interface ShiftPayload {
  facilityId: number;
  title: string;
  description?: string;
  role?: string;
  department?: string;
  location?: string;
  startTime: string;
  endTime: string;
  breakMinutes?: number;
  timezone?: string;
  status?: ShiftStatus;
  colorCode?: string;
  coverageTags?: string[];
  complianceNotes?: string;
  recurrencePattern?: 'none' | 'daily' | 'weekly' | 'biweekly' | 'monthly';
  recurrenceInterval?: number;
  recurrenceDays?: string[];
  recurrenceEndsAt?: string;
  staffMemberId?: number | null;
}

export interface Shift extends ShiftPayload {
  id: number;
  facilityId: number;
  createdBy: number;
  createdAt: string;
  updatedAt: string;
  conflictCode?: string | null;
  conflictReason?: string | null;
  isLocked: boolean;
  isDeleted: boolean;
}

export interface ShiftFilters {
  status?: ShiftStatus;
  startFrom?: string;
  startTo?: string;
}

export interface AvailabilityPayload {
  facilityId: number;
  staffMemberId: number;
  dayOfWeek: string;
  startTime: string;
  endTime: string;
  preferenceLevel?: number;
  effectiveFrom?: string;
  effectiveTo?: string;
  status?: 'active' | 'inactive' | 'unavailable';
  exceptionDates?: string[];
  notes?: string;
}

export interface Availability extends AvailabilityPayload {
  id: number;
  createdBy: number;
  createdAt: string;
  updatedAt: string;
}

export interface TimeOffPayload {
  facilityId: number;
  staffMemberId: number;
  startDate: string;
  endDate: string;
  category?: 'pto' | 'vacation' | 'sick' | 'training' | 'bereavement' | 'other';
  requestedHours?: number;
  isPaid?: boolean;
  reason?: string;
  supportingFiles?: string[];
}

export interface TimeOffRequest extends TimeOffPayload {
  id: number;
  status: 'pending' | 'approved' | 'denied' | 'cancelled';
  requestedBy: number;
  reviewedBy?: number;
  reviewedAt?: string;
  decisionNotes?: string;
  auditTrail?: Record<string, unknown>[];
  overlapsShiftIds?: number[];
  isDeleted: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ShiftSwapPayload {
  facilityId: number;
  shiftId: number;
  requestedByStaffId: number;
  requestedToStaffId?: number;
  reason?: string;
}

export interface ShiftSwapRequest extends ShiftSwapPayload {
  id: number;
  status: 'pending' | 'approved' | 'denied' | 'cancelled' | 'expired';
  adminNotes?: string;
  requestedAt: string;
  respondedAt?: string;
}

export interface ConflictCheckResponse {
  hasConflict: boolean;
  conflictReason?: string | null;
  conflictingShiftIds: number[];
  conflictingTimeOffIds: number[];
}

export const schedulingService = {
  async listShifts(filters: ShiftFilters = {}): Promise<Shift[]> {
    const response = await api.get('/scheduling/shifts', {
      params: {
        status_filter: filters.status,
        start_from: filters.startFrom,
        start_to: filters.startTo,
      },
    });
    return Array.isArray(response.data) ? response.data.map(mapShift) : [];
  },

  async createShift(payload: ShiftPayload): Promise<Shift> {
    const response = await api.post('/scheduling/shifts', serializeShiftPayload(payload));
    return mapShift(response.data);
  },

  async updateShift(id: number, payload: Partial<ShiftPayload>): Promise<Shift> {
    const response = await api.put(
      `/scheduling/shifts/${id}`,
      serializeShiftPayload(payload, true)
    );
    return mapShift(response.data);
  },

  async deleteShift(id: number): Promise<void> {
    await api.delete(`/scheduling/shifts/${id}`);
  },

  async checkConflicts(params: {
    staffMemberId?: number;
    startTime: string;
    endTime: string;
  }): Promise<ConflictCheckResponse> {
    const response = await api.get('/scheduling/shifts/conflicts', {
      params: {
        staff_member_id: params.staffMemberId,
        start_time: params.startTime,
        end_time: params.endTime,
      },
    });
    return response.data;
  },

  async createAvailability(payload: AvailabilityPayload): Promise<Availability> {
    const response = await api.post(
      '/scheduling/availability',
      serializeAvailabilityPayload(payload)
    );
    return mapAvailability(response.data);
  },

  async updateAvailability(
    id: number,
    payload: Partial<AvailabilityPayload>
  ): Promise<Availability> {
    const response = await api.put(
      `/scheduling/availability/${id}`,
      serializeAvailabilityPayload(payload, true)
    );
    return mapAvailability(response.data);
  },

  async deleteAvailability(id: number): Promise<void> {
    await api.delete(`/scheduling/availability/${id}`);
  },

  async createTimeOffRequest(payload: TimeOffPayload): Promise<TimeOffRequest> {
    const response = await api.post('/scheduling/time-off', serializeTimeOffPayload(payload));
    return mapTimeOff(response.data);
  },

  async reviewTimeOff(
    id: number,
    payload: Partial<TimeOffPayload> & { status?: TimeOffRequest['status']; decisionNotes?: string }
  ): Promise<TimeOffRequest> {
    const response = await api.put(
      `/scheduling/time-off/${id}`,
      serializeTimeOffPayload(payload, true)
    );
    return mapTimeOff(response.data);
  },

  async createShiftSwap(payload: ShiftSwapPayload): Promise<ShiftSwapRequest> {
    const response = await api.post(
      '/scheduling/shift-swaps',
      serializeShiftSwapPayload(payload)
    );
    return mapShiftSwap(response.data);
  },

  async respondShiftSwap(
    id: number,
    payload: Partial<ShiftSwapPayload> & { status: ShiftSwapRequest['status']; adminNotes?: string }
  ): Promise<ShiftSwapRequest> {
    const response = await api.put(
      `/scheduling/shift-swaps/${id}`,
      serializeShiftSwapPayload(payload, true)
    );
    return mapShiftSwap(response.data);
  },
};

export default schedulingService;

// ---------- Serialization Helpers ----------

const serializeShiftPayload = (payload: Partial<ShiftPayload>, partial = false) => {
  const body: Record<string, unknown> = {};
  const source = partial ? payload : { ...payload };

  if (source.facilityId !== undefined) body.facility_id = source.facilityId;
  if (source.title !== undefined) body.title = source.title;
  if (source.description !== undefined) body.description = source.description;
  if (source.role !== undefined) body.role = source.role;
  if (source.department !== undefined) body.department = source.department;
  if (source.location !== undefined) body.location = source.location;
  if (source.startTime !== undefined) body.start_time = source.startTime;
  if (source.endTime !== undefined) body.end_time = source.endTime;
  if (source.breakMinutes !== undefined) body.break_minutes = source.breakMinutes;
  if (source.timezone !== undefined) body.timezone = source.timezone;
  if (source.status !== undefined) body.status = source.status;
  if (source.colorCode !== undefined) body.color_code = source.colorCode;
  if (source.coverageTags !== undefined) body.coverage_tags = source.coverageTags;
  if (source.complianceNotes !== undefined) body.compliance_notes = source.complianceNotes;
  if (source.recurrencePattern !== undefined) body.recurrence_pattern = source.recurrencePattern;
  if (source.recurrenceInterval !== undefined) body.recurrence_interval = source.recurrenceInterval;
  if (source.recurrenceDays !== undefined) body.recurrence_days = source.recurrenceDays;
  if (source.recurrenceEndsAt !== undefined) body.recurrence_ends_at = source.recurrenceEndsAt;
  if (source.staffMemberId !== undefined) body.staff_member_id = source.staffMemberId;

  return body;
};

const serializeAvailabilityPayload = (
  payload: Partial<AvailabilityPayload>,
  partial = false
) => {
  const body: Record<string, unknown> = {};
  const source = partial ? payload : { ...payload };

  if (source.facilityId !== undefined) body.facility_id = source.facilityId;
  if (source.staffMemberId !== undefined) body.staff_member_id = source.staffMemberId;
  if (source.dayOfWeek !== undefined) body.day_of_week = source.dayOfWeek;
  if (source.startTime !== undefined) body.start_time = source.startTime;
  if (source.endTime !== undefined) body.end_time = source.endTime;
  if (source.preferenceLevel !== undefined) body.preference_level = source.preferenceLevel;
  if (source.effectiveFrom !== undefined) body.effective_from = source.effectiveFrom;
  if (source.effectiveTo !== undefined) body.effective_to = source.effectiveTo;
  if (source.status !== undefined) body.status = source.status;
  if (source.exceptionDates !== undefined) body.exception_dates = source.exceptionDates;
  if (source.notes !== undefined) body.notes = source.notes;

  return body;
};

const serializeTimeOffPayload = (payload: Partial<TimeOffPayload>, partial = false) => {
  const body: Record<string, unknown> = {};
  const source = partial ? payload : { ...payload };

  if (source.facilityId !== undefined) body.facility_id = source.facilityId;
  if (source.staffMemberId !== undefined) body.staff_member_id = source.staffMemberId;
  if (source.startDate !== undefined) body.start_date = source.startDate;
  if (source.endDate !== undefined) body.end_date = source.endDate;
  if (source.category !== undefined) body.category = source.category;
  if (source.requestedHours !== undefined) body.requested_hours = source.requestedHours;
  if (source.isPaid !== undefined) body.is_paid = source.isPaid;
  if (source.reason !== undefined) body.reason = source.reason;
  if (source.supportingFiles !== undefined) body.supporting_files = source.supportingFiles;
  if ('status' in source) body.status = source.status;
  if ('decisionNotes' in source) body.decision_notes = source.decisionNotes;

  return body;
};

const serializeShiftSwapPayload = (
  payload: Partial<ShiftSwapPayload>,
  partial = false
) => {
  const body: Record<string, unknown> = {};
  const source = partial ? payload : { ...payload };

  if (source.facilityId !== undefined) body.facility_id = source.facilityId;
  if (source.shiftId !== undefined) body.shift_id = source.shiftId;
  if (source.requestedByStaffId !== undefined) body.requested_by_staff_id = source.requestedByStaffId;
  if (source.requestedToStaffId !== undefined) body.requested_to_staff_id = source.requestedToStaffId;
  if (source.reason !== undefined) body.reason = source.reason;
  if ('status' in source) body.status = source.status;
  if ('adminNotes' in source) body.admin_notes = source.adminNotes;

  return body;
};

// ---------- Deserialization Helpers ----------

const mapShift = (shift: any): Shift => ({
  id: shift.id,
  facilityId: shift.facility_id,
  title: shift.title,
  description: shift.description,
  role: shift.role,
  department: shift.department,
  location: shift.location,
  startTime: shift.start_time,
  endTime: shift.end_time,
  breakMinutes: shift.break_minutes,
  timezone: shift.timezone,
  status: shift.status,
  colorCode: shift.color_code,
  coverageTags: shift.coverage_tags || [],
  complianceNotes: shift.compliance_notes,
  recurrencePattern: shift.recurrence_pattern,
  recurrenceInterval: shift.recurrence_interval,
  recurrenceDays: shift.recurrence_days || [],
  recurrenceEndsAt: shift.recurrence_ends_at,
  staffMemberId: shift.staff_member_id,
  createdBy: shift.created_by,
  createdAt: shift.created_at,
  updatedAt: shift.updated_at,
  conflictCode: shift.conflict_code,
  conflictReason: shift.conflict_reason,
  isLocked: Boolean(shift.is_locked),
  isDeleted: Boolean(shift.is_deleted),
});

const mapAvailability = (availability: any): Availability => ({
  id: availability.id,
  facilityId: availability.facility_id,
  staffMemberId: availability.staff_member_id,
  dayOfWeek: availability.day_of_week,
  startTime: availability.start_time,
  endTime: availability.end_time,
  preferenceLevel: availability.preference_level,
  effectiveFrom: availability.effective_from,
  effectiveTo: availability.effective_to,
  status: availability.status,
  exceptionDates: availability.exception_dates || [],
  notes: availability.notes,
  createdBy: availability.created_by,
  createdAt: availability.created_at,
  updatedAt: availability.updated_at,
});

const mapTimeOff = (request: any): TimeOffRequest => ({
  id: request.id,
  facilityId: request.facility_id,
  staffMemberId: request.staff_member_id,
  startDate: request.start_date,
  endDate: request.end_date,
  category: request.category,
  requestedHours: request.requested_hours,
  isPaid: request.is_paid,
  reason: request.reason,
  supportingFiles: request.supporting_files || [],
  status: request.status,
  requestedBy: request.requested_by,
  reviewedBy: request.reviewed_by,
  reviewedAt: request.reviewed_at,
  decisionNotes: request.decision_notes,
  auditTrail: request.audit_trail || [],
  overlapsShiftIds: request.overlaps_shift_ids || [],
  isDeleted: Boolean(request.is_deleted),
  createdAt: request.created_at,
  updatedAt: request.updated_at,
});

const mapShiftSwap = (swap: any): ShiftSwapRequest => ({
  id: swap.id,
  facilityId: swap.facility_id,
  shiftId: swap.shift_id,
  requestedByStaffId: swap.requested_by_staff_id,
  requestedToStaffId: swap.requested_to_staff_id,
  reason: swap.reason,
  status: swap.status,
  adminNotes: swap.admin_notes,
  requestedAt: swap.requested_at,
  respondedAt: swap.responded_at,
});

