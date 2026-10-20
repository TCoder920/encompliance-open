/*
  Description: Policy service for managing policy CRUD operations, assignments, and acknowledgments.
  Purpose: Provides functions for handling facility policies, including search, versioning, and compliance tracking.
*/
import api from './api';

export interface Policy {
  id: number;
  title: string;
  description?: string;
  category?: string;
  document_id?: number;
  document_url?: string;
  content_summary?: string;
  version: string;
  effective_date: string;
  expiry_date?: string;
  supersedes_policy_id?: number;
  requires_acknowledgment: boolean;
  acknowledgment_deadline_days: number;
  auto_assign_new_staff: boolean;
  acknowledgment_reminder_days?: string;
  regulatory_reference?: string;
  compliance_level: string;
  status: string;
  is_active: boolean;
  created_by: number;
  facility_administrator_id: number;
  approved_by?: number;
  approved_date?: string;
  created_at: string;
  updated_at: string;
  is_expired?: boolean;
  is_effective?: boolean;
  days_until_expiry?: number;
}

export interface PolicyAssignment {
  id: number;
  policy_id: number;
  staff_member_id: number;
  assigned_by: number;
  status: string;
  priority: string;
  assigned_date: string;
  due_date: string;
  acknowledged_date?: string;
  viewed_date?: string;
  time_spent_reading?: number;
  assignment_reason?: string;
  custom_message?: string;
  requires_immediate_attention: boolean;
  is_mandatory: boolean;
  compliance_deadline?: string;
  regulatory_requirement?: string;
  assignment_notes?: string;
  is_overdue?: boolean;
  days_until_due?: number;
  days_overdue?: number;
  is_acknowledged?: boolean;
}

export interface PolicyAcknowledgment {
  id: number;
  policy_id: number;
  staff_member_id: number;
  policy_assignment_id?: number;
  acknowledged_date?: string;
  acknowledgment_method: string;
  status: string;
  digital_signature?: string;
  signature_metadata?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  device_fingerprint?: string;
  geolocation?: Record<string, any>;
  verified_by?: number;
  verification_date?: string;
  verification_notes?: string;
  is_current: boolean;
  compliance_score?: number;
  requires_reacknowledgment: boolean;
  reacknowledgment_reason?: string;
  acknowledgment_text?: string;
  witness_name?: string;
  witness_signature?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  is_overdue?: boolean;
  days_overdue?: number;
  is_verified?: boolean;
}

export interface PolicyCreate {
  title: string;
  description?: string;
  category?: string;
  document_id?: number;
  document_url?: string;
  content_summary?: string;
  version?: string;
  effective_date: string;
  expiry_date?: string;
  supersedes_policy_id?: number;
  requires_acknowledgment?: boolean;
  acknowledgment_deadline_days?: number;
  auto_assign_new_staff?: boolean;
  acknowledgment_reminder_days?: string;
  regulatory_reference?: string;
  compliance_level?: string;
}

export interface PolicyUpdate {
  title?: string;
  description?: string;
  category?: string;
  document_id?: number;
  document_url?: string;
  content_summary?: string;
  version?: string;
  effective_date?: string;
  expiry_date?: string;
  supersedes_policy_id?: number;
  requires_acknowledgment?: boolean;
  acknowledgment_deadline_days?: number;
  auto_assign_new_staff?: boolean;
  acknowledgment_reminder_days?: string;
  regulatory_reference?: string;
  compliance_level?: string;
  status?: string;
  is_active?: boolean;
}

export interface PolicyAssignmentCreate {
  policy_id: number;
  staff_member_ids: number[];
  due_date: string;
  priority?: string;
  assignment_reason?: string;
  custom_message?: string;
  requires_immediate_attention?: boolean;
  is_mandatory?: boolean;
  compliance_deadline?: string;
  regulatory_requirement?: string;
  assignment_notes?: string;
}

export interface PolicyAcknowledgmentCreate {
  policy_assignment_id: number;
  acknowledgment_method?: string;
  digital_signature?: string;
  signature_metadata?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  device_fingerprint?: string;
  geolocation?: Record<string, any>;
  acknowledgment_text?: string;
  witness_name?: string;
  witness_signature?: string;
  notes?: string;
}

export interface PolicyDashboard {
  total_policies: number;
  active_policies: number;
  draft_policies: number;
  expired_policies: number;
  total_assignments: number;
  pending_acknowledgments: number;
  overdue_acknowledgments: number;
  acknowledgment_rate: number;
  policies_expiring_soon: number;
  recent_acknowledgments: PolicyAcknowledgment[];
  overdue_assignments: PolicyAssignment[];
}

class PolicyService {
  async getPolicies(params?: {
    category?: string;
    status?: string;
    is_active?: boolean;
    search?: string;
    page?: number;
    per_page?: number;
  }): Promise<Policy[]> {
    try {
      const response = await api.get('/policy/', { params });
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async getPolicy(policyId: number): Promise<Policy> {
    try {
      const response = await api.get(`/policy/${policyId}`);
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async createPolicy(policyData: PolicyCreate): Promise<Policy> {
    try {
      const response = await api.post('/policy/', policyData);
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async updatePolicy(policyId: number, policyData: PolicyUpdate): Promise<Policy> {
    try {
      const response = await api.put(`/policy/${policyId}`, policyData);
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async deletePolicy(policyId: number): Promise<void> {
    try {
      await api.delete(`/policy/${policyId}`);
    } catch (err) {
      throw err;
    }
  }

  async getPolicyAssignments(params?: {
    policy_id?: number;
    staff_member_id?: number;
    status?: string;
    overdue_only?: boolean;
    page?: number;
    per_page?: number;
  }): Promise<PolicyAssignment[]> {
    try {
      const response = await api.get('/policy/assignments', { params });
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async createPolicyAssignments(assignmentData: PolicyAssignmentCreate): Promise<PolicyAssignment[]> {
    try {
      const response = await api.post('/policy/assignments', assignmentData);
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async updatePolicyAssignment(assignmentId: number, assignmentData: Partial<PolicyAssignment>): Promise<PolicyAssignment> {
    try {
      const response = await api.put(`/policy/assignments/${assignmentId}`, assignmentData);
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async markPolicyViewed(assignmentId: number, timeSpentReading?: number): Promise<PolicyAssignment> {
    try {
      const response = await api.put(`/policy/assignments/${assignmentId}/view`, null, {
        params: timeSpentReading ? { time_spent_reading: timeSpentReading } : {}
      });
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async getPolicyAcknowledgments(params?: {
    policy_id?: number;
    staff_member_id?: number;
    status?: string;
    page?: number;
    per_page?: number;
  }): Promise<PolicyAcknowledgment[]> {
    try {
      const response = await api.get('/policy/acknowledgments', { params });
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async createPolicyAcknowledgment(acknowledgmentData: PolicyAcknowledgmentCreate): Promise<PolicyAcknowledgment> {
    try {
      const response = await api.post('/policy/acknowledgments', acknowledgmentData);
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async getPolicyDashboard(): Promise<PolicyDashboard> {
    try {
      const response = await api.get('/policy/dashboard');
      return response.data;
    } catch (err) {
      throw err;
    }
  }

  async generateComplianceReport(params: {
    report_type: string;
    date_from?: string;
    date_to?: string;
    department?: string;
    policy_id?: number;
    format?: string;
  }): Promise<any> {
    try {
      const response = await api.get('/policy/reports/compliance', { params });
      return response.data;
    } catch (err) {
      throw err;
    }
  }
}

export default new PolicyService();


