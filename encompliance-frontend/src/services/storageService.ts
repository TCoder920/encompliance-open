import api from './api';

export interface StorageUsageEvent {
  id: number;
  resource_type: string;
  resource_id: number;
  delta_bytes: number;
  source: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface StorageUsageSummary {
  facility_id: number;
  billing_period_start: string;
  billing_period_end: string;
  tier_name: string;
  included_bytes: number;
  used_bytes: number;
  overage_bytes: number;
  percent_used: number;
  alert_level?: string | null;
  overage_rate: number;
  available_bytes: number;
  recommended_tier?: string | null;
  events: StorageUsageEvent[];
}

const storageService = {
  async getUsage(): Promise<StorageUsageSummary> {
    const response = await api.get<StorageUsageSummary>('/storage/usage');
    return response.data;
  },
  async recalculate(): Promise<StorageUsageSummary> {
    const response = await api.post<StorageUsageSummary>('/storage/recalculate');
    return response.data;
  },
};

export default storageService;

