import api from './api';

export interface UsageLog {
  tokens_used: number;
  cost_usd: number;
  created_at: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  model_name?: string;
}

export interface UsageSummary {
  month_tokens: number;
  month_cost: number;
  logs: UsageLog[];
}

export const usageBillingService = {
  async getSummary(): Promise<UsageSummary> {
    const response = await api.get<UsageSummary>('/usage-billing/summary');
    return response.data;
  },

  async getFacilitySummary(): Promise<{ tokens: number; cost: number }> {
    const response = await api.get('/usage-billing/facility-summary');
    return response.data;
  },
};

export default usageBillingService;

