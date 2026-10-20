import api from './api';

export interface StaffDirectoryEntry {
  staffMemberId: number;
  assignmentId: number;
  fullName: string;
  email: string;
  department?: string | null;
  role?: string | null;
  status: string;
  facilityId: number;
  facilityName: string;
  assignedAt: string;
}

export interface StaffDirectoryResponse {
  items: StaffDirectoryEntry[];
  page: number;
  pageSize: number;
  total: number;
}

export interface DirectoryQueryParams {
  search?: string;
  facilityId?: number;
  status?: string;
  page?: number;
  pageSize?: number;
}

export interface AssignStaffPayload {
  staffMemberId: number;
  facilityId: number;
}

export interface TransferRequestPayload {
  staffMemberId: number;
  sourceFacilityId: number;
  targetFacilityId: number;
  reason?: string;
}

export interface TransferResponse {
  id: number;
  staffMemberId: number;
  sourceFacilityId: number;
  targetFacilityId: number;
  status: string;
  reason?: string | null;
  resolutionNotes?: string | null;
  createdAt: string;
  resolvedAt?: string | null;
}

const mapEntry = (data: any): StaffDirectoryEntry => ({
  staffMemberId: data.staff_member_id,
  assignmentId: data.assignment_id,
  fullName: data.full_name,
  email: data.email,
  department: data.department,
  role: data.role,
  status: data.status,
  facilityId: data.facility_id,
  facilityName: data.facility_name,
  assignedAt: data.assigned_at,
});

const mapTransfer = (data: any): TransferResponse => ({
  id: data.id,
  staffMemberId: data.staff_member_id,
  sourceFacilityId: data.source_facility_id,
  targetFacilityId: data.target_facility_id,
  status: data.status,
  reason: data.reason,
  resolutionNotes: data.resolution_notes,
  createdAt: data.created_at,
  resolvedAt: data.resolved_at,
});

const staffDirectoryService = {
  async fetchDirectory(params: DirectoryQueryParams = {}): Promise<StaffDirectoryResponse> {
    const response = await api.get('/enterprise/staff-directory', { params });
    return {
      items: response.data.items.map(mapEntry),
      page: response.data.page,
      pageSize: response.data.page_size,
      total: response.data.total,
    };
  },

  async assignStaff(payload: AssignStaffPayload): Promise<StaffDirectoryEntry> {
    const response = await api.post('/enterprise/staff-directory/assign', {
      staff_member_id: payload.staffMemberId,
      facility_id: payload.facilityId,
    });
    return mapEntry(response.data);
  },

  async requestTransfer(payload: TransferRequestPayload): Promise<TransferResponse> {
    const response = await api.post('/enterprise/staff-directory/transfer', {
      staff_member_id: payload.staffMemberId,
      source_facility_id: payload.sourceFacilityId,
      target_facility_id: payload.targetFacilityId,
      reason: payload.reason,
    });
    return mapTransfer(response.data);
  },

  async approveTransfer(requestId: number, resolutionNotes?: string): Promise<TransferResponse> {
    const response = await api.post(`/enterprise/staff-directory/transfer/${requestId}/approve`, {
      resolution_notes: resolutionNotes,
    });
    return mapTransfer(response.data);
  },

  async rejectTransfer(requestId: number, resolutionNotes?: string): Promise<TransferResponse> {
    const response = await api.post(`/enterprise/staff-directory/transfer/${requestId}/reject`, {
      resolution_notes: resolutionNotes,
    });
    return mapTransfer(response.data);
  },
};

export default staffDirectoryService;

