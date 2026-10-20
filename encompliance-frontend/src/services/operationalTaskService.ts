/*
  Description: Operational Task Service for API communication
  Purpose: Handles all API calls related to operational task and chore management
*/

import apiClient from './api';

export interface OperationalTask {
  id: number;
  title: string;
  description?: string;
  category?: string;
  task_type: 'one_time' | 'recurring';
  recurrence_pattern?: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  recurrence_interval: number;
  min_age_required?: number;
  max_age_allowed?: number;
  estimated_duration_minutes?: number;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  requires_supervision: boolean;
  special_instructions?: string;
  location?: string;
  required_equipment?: string[];
  start_date: string;
  end_date?: string;
  facility_id: number;
  created_by: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  is_recurring: boolean;
  has_age_restrictions: boolean;
  age_range_description: string;
  // Photo requirements
  requires_before_photos?: boolean;
  requires_after_photos?: boolean;
  photo_instructions?: string;
}

export interface TaskAssignment {
  id: number;
  operational_task_id: number;
  staff_member_id: number;
  assigned_by: number;
  status: 'assigned' | 'in_progress' | 'completed' | 'overdue' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_date: string;
  due_date: string;
  started_date?: string;
  completed_date?: string;
  progress_percentage: number;
  time_spent_minutes: number;
  last_accessed?: string;
  completion_verified: boolean;
  verification_notes?: string;
  completion_photo_url?: string;
  verification_method?: string;
  reminder_sent_dates?: string[];
  escalation_sent: boolean;
  escalation_date?: string;
  assignment_notes?: string;
  completion_notes?: string;
  supervisor_notes?: string;
  quality_rating?: number;
  efficiency_rating?: number;
  requires_followup: boolean;
  created_at: string;
  updated_at: string;
  is_overdue: boolean;
  days_until_due?: number;
  days_overdue: number;
  is_completed: boolean;
  is_in_progress: boolean;
  completion_time_minutes: number;
  has_photo_verification: boolean;
  // Full task details
  operational_task?: OperationalTask;
  // Staff member details
  staff_member?: {
    id: number;
    first_name: string;
    last_name: string;
    full_name: string;
    email: string;
    role: string;
  };
}

export interface EligibleStaffMember {
  id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  role: string;
  department?: string;
  age?: number;
  is_active: boolean;
}

export interface AgeBasedAssignmentResponse {
  eligible_staff: EligibleStaffMember[];
  total_staff: number;
  eligible_count: number;
  age_criteria: {
    min_age?: number;
    max_age?: number;
  };
}

export interface TaskDashboard {
  total_tasks: number;
  active_tasks: number;
  recurring_tasks: number;
  total_assignments: number;
  pending_assignments: number;
  in_progress_assignments: number;
  completed_assignments: number;
  overdue_assignments: number;
  completion_rate: number;
  average_completion_time: number;
  upcoming_due_dates: TaskAssignment[];
  recent_completions: TaskAssignment[];
}

export interface CreateTaskData {
  title: string;
  description?: string;
  category?: string;
  task_type: 'one_time' | 'recurring';
  recurrence_pattern?: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  recurrence_interval?: number;
  min_age_required?: number;
  max_age_allowed?: number;
  estimated_duration_minutes?: number;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  requires_supervision?: boolean;
  special_instructions?: string;
  location?: string;
  required_equipment?: string[];
  start_date: string;
  end_date?: string;
  // Photo requirements
  requires_before_photos?: boolean;
  requires_after_photos?: boolean;
  photo_instructions?: string;
}

export interface CreateAssignmentData {
  operational_task_id: number;
  staff_member_ids: number[];
  due_date: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assignment_notes?: string;
}

export interface TaskFilters {
  task_type?: 'one_time' | 'recurring';
  category?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  is_active?: boolean;
  page?: number;
  per_page?: number;
}

class OperationalTaskService {
  private baseUrl = '/operational-tasks';

  // Task CRUD operations
  async createTask(taskData: CreateTaskData): Promise<OperationalTask> {
    const response = await apiClient.post(`${this.baseUrl}/tasks`, taskData);
    return response.data;
  }

  async getTasks(filters?: TaskFilters): Promise<OperationalTask[]> {
    const params = new URLSearchParams();
    
    if (filters?.task_type) params.append('task_type', filters.task_type);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.is_active !== undefined) params.append('is_active', filters.is_active.toString());
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.per_page) params.append('per_page', filters.per_page.toString());

    const queryString = params.toString();
    const url = queryString ? `${this.baseUrl}/tasks?${queryString}` : `${this.baseUrl}/tasks`;

    const response = await apiClient.get(url);
    return response.data;
  }

  async getTask(taskId: number): Promise<OperationalTask> {
    const response = await apiClient.get(`${this.baseUrl}/tasks/${taskId}`);
    return response.data;
  }

  async updateTask(taskId: number, taskData: Partial<CreateTaskData>): Promise<OperationalTask> {
    const response = await apiClient.put(`${this.baseUrl}/tasks/${taskId}`, taskData);
    return response.data;
  }

  async deleteTask(taskId: number): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/tasks/${taskId}`);
  }

  // Age-based assignment
  async getEligibleStaff(taskId: number): Promise<AgeBasedAssignmentResponse> {
    const response = await apiClient.get(`${this.baseUrl}/tasks/${taskId}/eligible-staff`);
    return response.data;
  }

  async getAgeComplianceSummary(): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/age-compliance-summary`);
    return response.data;
  }

  // Task assignments
  async createAssignments(assignmentData: CreateAssignmentData): Promise<TaskAssignment[]> {
    const response = await apiClient.post(`${this.baseUrl}/assignments`, assignmentData);
    return response.data;
  }

  async getAssignments(filters?: any): Promise<TaskAssignment[]> {
    const params = new URLSearchParams();
    
    if (filters?.operational_task_id) params.append('operational_task_id', filters.operational_task_id.toString());
    if (filters?.staff_member_id) params.append('staff_member_id', filters.staff_member_id.toString());
    if (filters?.status) params.append('status', filters.status);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.is_overdue !== undefined) params.append('is_overdue', filters.is_overdue.toString());
    if (filters?.due_date_from) params.append('due_date_from', filters.due_date_from);
    if (filters?.due_date_to) params.append('due_date_to', filters.due_date_to);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.per_page) params.append('per_page', filters.per_page.toString());

    const queryString = params.toString();
    const url = queryString ? `${this.baseUrl}/assignments?${queryString}` : `${this.baseUrl}/assignments`;
    
    const response = await apiClient.get(url);
    return response.data;
  }

  async getAssignment(assignmentId: number): Promise<TaskAssignment> {
    const response = await apiClient.get(`${this.baseUrl}/assignments/${assignmentId}`);
    return response.data;
  }

  async updateAssignment(assignmentId: number, assignmentData: any): Promise<TaskAssignment> {
    const response = await apiClient.put(`${this.baseUrl}/assignments/${assignmentId}`, assignmentData);
    return response.data;
  }

  // Dashboard and analytics
  async getDashboard(): Promise<TaskDashboard> {
    const response = await apiClient.get(`${this.baseUrl}/dashboard`);
    return response.data;
  }

  // Recurring task management
  async pauseRecurringTask(taskId: number): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/tasks/${taskId}/pause`);
    return response.data;
  }

  async resumeRecurringTask(taskId: number): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/tasks/${taskId}/resume`);
    return response.data;
  }
}

export const operationalTaskService = new OperationalTaskService(); 