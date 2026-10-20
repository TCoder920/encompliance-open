import api from './api';

export interface AuditEntry {
  id: number;
  actorUserId?: number;
  facilityId?: number;
  eventType: string;
  description: string;
  metadata?: Record<string, unknown>;
  createdAt: string;
  entryHash: string;
}

export interface AuditResponse {
  items: AuditEntry[];
  total: number;
  page: number;
  pageSize: number;
}

const auditService = {
  async fetchLogs(page = 1, pageSize = 50): Promise<AuditResponse> {
    const response = await api.get('/enterprise/audit/logs', {
      params: { page, page_size: pageSize },
    });
    return {
      items: response.data.items.map((entry: any) => ({
        id: entry.id,
        actorUserId: entry.actor_user_id,
        facilityId: entry.facility_id,
        eventType: entry.event_type,
        description: entry.description,
        metadata: entry.metadata,
        createdAt: entry.created_at,
        entryHash: entry.entry_hash,
      })),
      total: response.data.total,
      page: response.data.page,
      pageSize: response.data.page_size,
    };
  },

  async exportCsv(): Promise<Blob> {
    const response = await api.get('/enterprise/audit/export', {
      responseType: 'blob',
    });
    return response.data;
  },
};

export default auditService;

