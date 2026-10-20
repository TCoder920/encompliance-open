/*
  Description: Training service for managing training programs, staff, assignments, and certifications.
  Purpose: Provides API methods for the complete training and certification management system.
*/

import api from './api';

// Types for training system
export interface TrainingProgram {
  id: number;
  title: string;
  description?: string;
  category?: string;
  is_mandatory: boolean;
  requires_certification: boolean;
  certification_valid_months: number;
  estimated_duration_minutes?: number;
  delivery_method: string;
  prerequisites?: number[];
  reminder_schedule_days: number[];
  auto_assign_new_staff: boolean;
  is_active: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
  facility_types: any[];
}

export interface StaffMember {
  id: number;
  employee_id?: string;
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string;
  role: 'staff' | 'supervisor' | 'manager' | 'administrator';
  department?: string;
  position_title?: string;
  hire_date?: string;
  status: 'active' | 'inactive' | 'terminated' | 'on_leave';
  facility_administrator_id: number;
  facility_name?: string;
  facility_location?: string;
  training_completion_rate: number;
  certifications_current: number;
  certifications_expired: number;
  last_training_date?: string;
  notification_preferences?: any;
  created_at: string;
  updated_at: string;
}

export interface TrainingAssignment {
  id: number;
  training_program_id: number;
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
  verification_method?: string;
  verification_score?: number;
  verification_notes?: string;
  reminder_sent_dates?: string[];
  escalation_sent: boolean;
  assignment_notes?: string;
  completion_notes?: string;
  training_url?: string;
  created_at: string;
  updated_at: string;
  is_overdue: boolean;
  days_until_due?: number;
}

export interface TrainingMaterial {
  id: number;
  title: string;
  description?: string;
  material_type: 'document' | 'video' | 'link' | 'quiz' | 'assessment' | 'presentation' | 'interactive';
  file_path?: string;
  file_name?: string;
  file_size?: number;
  mime_type?: string;
  external_url?: string;
  embed_code?: string;
  duration_minutes?: number;
  reading_time_minutes?: number;
  difficulty_level?: string;
  version: string;
  status: 'draft' | 'active' | 'archived' | 'under_review';
  is_required: boolean;
  sort_order: number;
  section?: string;
  quiz_questions?: any[];
  passing_score?: number;
  max_attempts: number;
  access_restrictions?: any;
  training_program_id: number;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface TrainingCompletion {
  id: number;
  training_assignment_id: number;
  staff_member_id: number;
  training_program_id: number;
  completion_status: 'completed' | 'verified' | 'expired' | 'revoked';
  completed_date: string;
  completion_method?: string;
  verified_by?: number;
  verification_date?: string;
  verification_notes?: string;
  final_score?: number;
  passing_score_required?: number;
  attempts_taken: number;
  time_spent_minutes?: number;
  certificate_status: 'pending' | 'generated' | 'issued' | 'expired' | 'revoked';
  certificate_number?: string;
  certificate_file_path?: string;
  certificate_issued_date?: string;
  expires_date?: string;
  renewal_required: boolean;
  renewal_reminder_sent: boolean;
  compliance_notes?: string;
  audit_trail?: any[];
  created_at: string;
  updated_at: string;
  is_expired: boolean;
  days_until_expiry?: number;
  is_certificate_valid: boolean;
}

export interface TrainingDashboard {
  total_staff: number;
  total_programs: number;
  total_assignments: number;
  completed_assignments: number;
  overdue_assignments: number;
  due_soon_assignments: number;
  completion_rate: number;
  certifications_expiring: number;
  recent_completions: TrainingCompletion[];
  upcoming_due_dates: TrainingAssignment[];
}

// Training Programs API
export const trainingProgramService = {
  // Get all training programs
  getAll: async (params?: {
    category?: string;
    is_mandatory?: boolean;
    requires_certification?: boolean;
    facility_type_id?: number;
    is_active?: boolean;
    search?: string;
    page?: number;
    per_page?: number;
  }): Promise<{ programs: TrainingProgram[]; total: number; page: number; per_page: number }> => {
    const response = await api.get('/training/programs', { params });
    return response.data;
  },

  // Get training program by ID
  getById: async (id: number): Promise<TrainingProgram> => {
    const response = await api.get(`/training/programs/${id}`);
    return response.data;
  },

  // Create training program
  create: async (data: {
    title: string;
    description?: string;
    category?: string;
    is_mandatory?: boolean;
    requires_certification?: boolean;
    certification_valid_months?: number;
    estimated_duration_minutes?: number;
    delivery_method?: string;
    prerequisites?: number[];
    reminder_schedule_days?: number[];
    auto_assign_new_staff?: boolean;
    facility_type_ids?: number[];
  }): Promise<TrainingProgram> => {
    const response = await api.post('/training/programs', data);
    return response.data;
  },

  // Update training program
  update: async (id: number, data: Partial<TrainingProgram>): Promise<TrainingProgram> => {
    const response = await api.put(`/training/programs/${id}`, data);
    return response.data;
  },

  // Delete training program
  delete: async (id: number): Promise<void> => {
    await api.delete(`/training/programs/${id}`);
  },
};

// Staff Members API
export const staffMemberService = {
  // Get all staff members
  getAll: async (params?: {
    role?: string;
    status?: string;
    department?: string;
    search?: string;
    page?: number;
    per_page?: number;
  }): Promise<{ staff_members: StaffMember[]; total: number; page: number; per_page: number }> => {
    const response = await api.get('/training/staff', { params });
    return response.data;
  },

  // Get staff member by ID
  getById: async (id: number): Promise<StaffMember> => {
    const response = await api.get(`/training/staff/${id}`);
    return response.data;
  },

  // Create staff member
  create: async (data: {
    employee_id?: string;
    first_name: string;
    last_name: string;
    email: string;
    phone_number?: string;
    role?: string;
    department?: string;
    position_title?: string;
    hire_date?: string;
    status?: string;
    facility_name?: string;
    facility_location?: string;
    notification_preferences?: any;
  }): Promise<StaffMember> => {
    const response = await api.post('/training/staff', data);
    return response.data;
  },

  // Update staff member
  update: async (id: number, data: Partial<StaffMember>): Promise<StaffMember> => {
    const response = await api.put(`/training/staff/${id}`, data);
    return response.data;
  },

  // Delete staff member
  delete: async (id: number): Promise<void> => {
    await api.delete(`/training/staff/${id}`);
  },

  // Get staff training progress
  getTrainingProgress: async (id: number): Promise<{
    staff_member: StaffMember;
    assigned_trainings: TrainingAssignment[];
    completed_trainings: TrainingCompletion[];
    overdue_count: number;
    completion_rate: number;
    next_due_date?: string;
  }> => {
    const response = await api.get(`/training/staff/${id}/progress`);
    return response.data;
  },
};

// Training Assignments API
export const trainingAssignmentService = {
  // Get all assignments
  getAll: async (params?: {
    status?: string;
    priority?: string;
    training_program_id?: number;
    staff_member_id?: number;
    due_date_from?: string;
    due_date_to?: string;
    overdue_only?: boolean;
    page?: number;
    per_page?: number;
  }): Promise<{ assignments: TrainingAssignment[]; total: number; page: number; per_page: number }> => {
    const response = await api.get('/training/assignments', { params });
    return response.data;
  },

  // Get assignment by ID
  getById: async (id: number): Promise<TrainingAssignment> => {
    const response = await api.get(`/training/assignments/${id}`);
    return response.data;
  },

  // Create single assignment
  create: async (data: {
    training_program_id: number;
    staff_member_id: number;
    due_date: string;
    priority?: string;
    assignment_notes?: string;
    training_url?: string;
  }): Promise<TrainingAssignment> => {
    const response = await api.post('/training/assignments', data);
    return response.data;
  },

  // Create bulk assignments
  createBulk: async (data: {
    training_program_id: number;
    staff_member_ids: number[];
    due_date: string;
    priority?: string;
    assignment_notes?: string;
    training_url?: string;
  }): Promise<TrainingAssignment[]> => {
    const response = await api.post('/training/assignments/bulk', data);
    return response.data;
  },

  // Update assignment
  update: async (id: number, data: {
    due_date?: string;
    priority?: string;
    status?: string;
    progress_percentage?: number;
    assignment_notes?: string;
    completion_notes?: string;
    training_url?: string;
  }): Promise<TrainingAssignment> => {
    const response = await api.put(`/training/assignments/${id}`, data);
    return response.data;
  },

  // Delete assignment
  delete: async (id: number): Promise<void> => {
    await api.delete(`/training/assignments/${id}`);
  },

  // Mark assignment as started
  markStarted: async (id: number): Promise<TrainingAssignment> => {
    const response = await api.post(`/training/assignments/${id}/start`);
    return response.data;
  },

  // Update progress
  updateProgress: async (id: number, progress: number): Promise<TrainingAssignment> => {
    const response = await api.put(`/training/assignments/${id}/progress`, { progress_percentage: progress });
    return response.data;
  },
};

// Training Materials API
export const trainingMaterialService = {
  // Get materials for a training program
  getByProgram: async (programId: number): Promise<TrainingMaterial[]> => {
    const response = await api.get(`/training/programs/${programId}/materials`);
    return response.data;
  },

  // Get material by ID
  getById: async (id: number): Promise<TrainingMaterial> => {
    const response = await api.get(`/training/materials/${id}`);
    return response.data;
  },

  // Create material
  create: async (data: {
    title: string;
    description?: string;
    material_type: string;
    training_program_id: number;
    file_path?: string;
    file_name?: string;
    external_url?: string;
    embed_code?: string;
    duration_minutes?: number;
    reading_time_minutes?: number;
    difficulty_level?: string;
    is_required?: boolean;
    sort_order?: number;
    section?: string;
    quiz_questions?: any[];
    passing_score?: number;
    max_attempts?: number;
  }): Promise<TrainingMaterial> => {
    const response = await api.post('/training/materials', data);
    return response.data;
  },

  // Update material
  update: async (id: number, data: Partial<TrainingMaterial>): Promise<TrainingMaterial> => {
    const response = await api.put(`/training/materials/${id}`, data);
    return response.data;
  },

  // Delete material
  delete: async (id: number): Promise<void> => {
    await api.delete(`/training/materials/${id}`);
  },

  // Upload material file
  uploadFile: async (file: File, materialData: {
    title: string;
    description?: string;
    material_type: string;
    training_program_id: number;
    is_required?: boolean;
    section?: string;
  }): Promise<TrainingMaterial> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', materialData.title);
    formData.append('material_type', materialData.material_type);
    formData.append('training_program_id', materialData.training_program_id.toString());
    
    if (materialData.description) formData.append('description', materialData.description);
    if (materialData.is_required !== undefined) formData.append('is_required', materialData.is_required.toString());
    if (materialData.section) formData.append('section', materialData.section);

    const response = await api.post('/training/materials/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Training Completions API
export const trainingCompletionService = {
  // Get completions
  getAll: async (params?: {
    staff_member_id?: number;
    training_program_id?: number;
    completion_status?: string;
    page?: number;
    per_page?: number;
  }): Promise<TrainingCompletion[]> => {
    const response = await api.get('/training/completions', { params });
    return response.data;
  },

  // Get completion by ID
  getById: async (id: number): Promise<TrainingCompletion> => {
    const response = await api.get(`/training/completions/${id}`);
    return response.data;
  },

  // Create completion
  create: async (data: {
    training_assignment_id: number;
    completion_method?: string;
    final_score?: number;
    attempts_taken?: number;
    time_spent_minutes?: number;
    verification_notes?: string;
    compliance_notes?: string;
  }): Promise<TrainingCompletion> => {
    const response = await api.post('/training/completions', data);
    return response.data;
  },

  // Update completion
  update: async (id: number, data: {
    completion_status?: string;
    verification_notes?: string;
    final_score?: number;
    compliance_notes?: string;
    certificate_status?: string;
  }): Promise<TrainingCompletion> => {
    const response = await api.put(`/training/completions/${id}`, data);
    return response.data;
  },

  // Verify completion
  verify: async (id: number, notes?: string): Promise<TrainingCompletion> => {
    const response = await api.post(`/training/completions/${id}/verify`, { verification_notes: notes });
    return response.data;
  },

  // Generate certificate
  generateCertificate: async (id: number): Promise<{ certificate_url: string }> => {
    const response = await api.post(`/training/completions/${id}/certificate`);
    return response.data;
  },

  // Download certificate
  downloadCertificate: async (id: number): Promise<Blob> => {
    const response = await api.get(`/training/completions/${id}/certificate/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// Dashboard and Analytics API
export const trainingDashboardService = {
  // Get dashboard data
  getDashboard: async (): Promise<TrainingDashboard> => {
    const response = await api.get('/training/dashboard');
    return response.data;
  },

  // Get analytics
  getAnalytics: async (params?: {
    date_from?: string;
    date_to?: string;
  }): Promise<{
    completion_rates_by_program: Record<string, number>;
    completion_rates_by_department: Record<string, number>;
    average_completion_time: Record<string, number>;
    overdue_trends: Array<{ month: string; overdue_count: number }>;
    certification_expiry_forecast: Array<{ month: string; expiring_count: number }>;
    effectiveness_metrics: {
      average_score: number;
      pass_rate: number;
      retry_rate: number;
    };
    summary_stats: {
      total_programs_analyzed: number;
      total_departments: number;
      analysis_period: {
        from: string;
        to: string;
      };
    };
  }> => {
    const response = await api.get('/training/analytics', { params });
    return response.data;
  },
};

// Reports API
export const trainingReportsService = {
  // Generate compliance reports
  generateComplianceReport: async (params: {
    report_type: 'staff_summary' | 'program_compliance' | 'certification_status';
    date_from?: string;
    date_to?: string;
    department?: string;
    program_id?: number;
    format?: 'json' | 'csv';
  }): Promise<{
    report_type: string;
    generated_at: string;
    filters: {
      date_from?: string;
      date_to?: string;
      department?: string;
      program_id?: number;
    };
    data: any[];
    summary: {
      total_records: number;
      report_period: string;
    };
  }> => {
    const response = await api.get('/training/reports/compliance', { params });
    return response.data;
  },

  // Export report data
  exportReport: async (reportData: any, format: 'csv' | 'pdf' = 'csv'): Promise<Blob> => {
    if (format === 'csv') {
      return trainingReportsService.exportToCsv(reportData);
    }
    // PDF export would be implemented here
    throw new Error('PDF export not yet implemented');
  },

  // Convert report data to CSV
  exportToCsv: (reportData: any): Blob => {
    if (!reportData.data || reportData.data.length === 0) {
      throw new Error('No data to export');
    }

    const headers = Object.keys(reportData.data[0]);
    const csvContent = [
      headers.join(','),
      ...reportData.data.map((row: any) => 
        headers.map(header => {
          const value = row[header];
          // Escape commas and quotes in CSV
          if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value || '';
        }).join(',')
      )
    ].join('\n');

    return new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  },

  // Download file helper
  downloadFile: (blob: Blob, filename: string): void => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};

// Notification API
export const trainingNotificationService = {
  // Send training notification
  sendNotification: async (data: {
    staff_member_id: number;
    notification_type: string;
    training_program_title: string;
    message_data: any;
  }): Promise<void> => {
    await api.post('/training/notifications', data);
  },

  // Send bulk notifications
  sendBulkNotifications: async (data: {
    staff_member_ids: number[];
    notification_type: string;
    training_data: any;
  }): Promise<{ success_count: number }> => {
    const response = await api.post('/training/notifications/bulk', data);
    return response.data;
  },
};

export default {
  programs: trainingProgramService,
  staff: staffMemberService,
  assignments: trainingAssignmentService,
  materials: trainingMaterialService,
  completions: trainingCompletionService,
  dashboard: trainingDashboardService,
  notifications: trainingNotificationService,
  reports: trainingReportsService,
}; 