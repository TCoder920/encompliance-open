import api from './api';

export interface RolePayload {
  name: string;
  description?: string;
  scope?: string;
  permissions?: string[];
}

export interface RoleResponse extends RolePayload {
  id: number;
}

export interface RoleAssignmentPayload {
  user_id: number;
  role_id: number;
  facility_id?: number;
}

export interface CrossFacilityMetric {
  facility_id: number;
  facility_name: string;
  active_staff: number;
  open_policies: number;
}

export interface CrossFacilityAnalytics {
  total_facilities: number;
  staff_count: number;
  policy_distribution_pending: number;
  facilities: CrossFacilityMetric[];
}

export interface PolicyDistributionPayload {
  policy_id: number;
  facility_ids: number[];
  notes?: string;
}

export interface EscalationStepPayload {
  delayMinutes: number;
  channel: string;
  targetRole?: string;
  targetUserId?: number;
  customRecipient?: string;
  messageTemplate?: string;
}

export interface EscalationPolicyPayload {
  name: string;
  incidentType: string;
  description?: string;
  steps: EscalationStepPayload[];
}

export interface EscalationStep {
  id: number;
  stepNumber: number;
  delayMinutes: number;
  channel: string;
  targetRole?: string;
  targetUserId?: number;
  customRecipient?: string;
}

export interface EscalationPolicy {
  id: number;
  name: string;
  incidentType: string;
  description?: string;
  steps: EscalationStep[];
}

export interface OverrideRequestPayload {
  actionType: string;
  payload: Record<string, unknown>;
}

export interface OverrideRequest {
  id: number;
  facility_id: number;
  requested_by_user_id: number;
  approved_by_user_id?: number;
  status: string;
  action_type: string;
  payload: Record<string, unknown>;
  created_at: string;
  resolved_at?: string;
  resolution_notes?: string;
}

export const enterpriseService = {
  async createRole(payload: RolePayload): Promise<RoleResponse> {
    const response = await api.post<RoleResponse>('/rbac/roles', payload);
    return response.data;
  },

  async assignRole(payload: RoleAssignmentPayload) {
    await api.post('/rbac/assignments', payload);
  },

  async fetchAnalytics(): Promise<CrossFacilityAnalytics> {
    const response = await api.get<CrossFacilityAnalytics>('/analytics/cross-facility');
    return response.data;
  },

  async distributePolicy(payload: PolicyDistributionPayload) {
    const response = await api.post('/policy-distribution', payload);
    return response.data;
  },

  async fetchEscalationPolicies(): Promise<EscalationPolicy[]> {
    const response = await api.get('/enterprise/escalations/policies');
    return response.data.map((policy: any) => ({
      id: policy.id,
      name: policy.name,
      incidentType: policy.incident_type,
      description: policy.description,
      steps: (policy.steps || []).map((step: any) => ({
        id: step.id,
        stepNumber: step.step_number,
        delayMinutes: step.delay_minutes,
        channel: step.channel,
        targetRole: step.target_role,
        targetUserId: step.target_user_id,
        customRecipient: step.custom_recipient,
      })),
    }));
  },

  async createEscalationPolicy(payload: EscalationPolicyPayload): Promise<EscalationPolicy> {
    const response = await api.post('/enterprise/escalations/policies', {
      name: payload.name,
      incident_type: payload.incidentType,
      description: payload.description,
      steps: payload.steps.map((step) => ({
        delay_minutes: step.delayMinutes,
        channel: step.channel,
        target_role: step.targetRole,
        target_user_id: step.targetUserId,
        custom_recipient: step.customRecipient,
        message_template: step.messageTemplate,
      })),
    });
    return response.data;
  },

  async triggerEscalationTest(policyId: number) {
    await api.post(`/enterprise/escalations/policies/${policyId}/trigger`);
  },

  async submitOverrideRequest(payload: OverrideRequestPayload): Promise<OverrideRequest> {
    const response = await api.post('/enterprise/manager/requests', {
      action_type: payload.actionType,
      payload: payload.payload,
    });
    return response.data;
  },

  async fetchOverrideRequests(status?: string): Promise<OverrideRequest[]> {
    const response = await api.get('/enterprise/manager/requests', {
      params: { status },
    });
    return response.data;
  },

  async resolveOverrideRequest(requestId: number, action: 'approve' | 'reject', notes?: string): Promise<OverrideRequest> {
    const response = await api.post(`/enterprise/manager/requests/${requestId}/${action}`, {
      resolution_notes: notes,
    });
    return response.data;
  },
};

export default enterpriseService;

