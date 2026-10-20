/**
 * Description: Preview data constants for the EnCompliance application.
 * Purpose: Provides sample data for freemium preview mode, allowing free tier users
 * to see what premium features look like without accessing real functionality.
 */

import { Tier } from './tiers';

/**
 * Sample calendar events for preview mode
 */
export const SAMPLE_CALENDAR_EVENTS = [
  {
    id: 'preview-1',
    title: 'Quarterly Compliance Review',
    start: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week from now
    end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000 + 2 * 60 * 60 * 1000).toISOString(), // 2 hours later
    description: 'Review all compliance documentation and update policies as needed.',
    location: 'Conference Room A',
    allDay: false,
    isPreview: true
  },
  {
    id: 'preview-2',
    title: 'Staff Training: Safety Protocols',
    start: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(), // 2 weeks from now
    end: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000 + 3 * 60 * 60 * 1000).toISOString(), // 3 hours later
    description: 'Mandatory training session for all staff on updated safety protocols.',
    location: 'Main Training Room',
    allDay: false,
    isPreview: true
  },
  {
    id: 'preview-3',
    title: 'License Renewal Deadline',
    start: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 1 month from now
    end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    description: 'Submit license renewal application and required documentation.',
    location: '',
    allDay: true,
    isPreview: true
  },
  {
    id: 'preview-4',
    title: 'Monthly Inspection',
    start: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000).toISOString(), // 3 weeks from now
    end: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000 + 1 * 60 * 60 * 1000).toISOString(), // 1 hour later
    description: 'Routine monthly inspection of facilities and equipment.',
    location: 'All Facilities',
    allDay: false,
    isPreview: true
  }
];

/**
 * Sample scheduling data for preview mode
 */
export const SAMPLE_SHIFTS = [
  {
    id: 88001,
    facilityId: 1,
    title: 'AM Classroom Coverage',
    description: 'Lead teacher coverage for toddler classroom',
    role: 'Lead Teacher',
    department: 'Toddler Program',
    location: 'Room 2',
    startTime: new Date().setHours(8, 0, 0, 0),
    endTime: new Date().setHours(12, 30, 0, 0),
    breakMinutes: 30,
    timezone: 'America/New_York',
    status: 'published' as const,
    colorCode: '#3b82f6',
    coverageTags: ['classroom', 'toddler'],
    complianceNotes: 'Meets ratio 1:6',
    recurrencePattern: 'weekly' as const,
    recurrenceInterval: 1,
    recurrenceDays: ['monday', 'wednesday', 'friday'],
    recurrenceEndsAt: null,
    staffMemberId: 501,
    createdBy: 1,
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date().toISOString(),
    isLocked: false,
    isDeleted: false,
    conflictCode: null,
    conflictReason: null,
    isPreview: true
  },
  {
    id: 88002,
    facilityId: 1,
    title: 'Coverage Float',
    description: 'Floating support for classrooms and meal coverage',
    role: 'Support Staff',
    department: 'Operations',
    location: 'Facility-wide',
    startTime: new Date().setHours(11, 0, 0, 0),
    endTime: new Date().setHours(15, 0, 0, 0),
    breakMinutes: 15,
    timezone: 'America/New_York',
    status: 'draft' as const,
    colorCode: '#f97316',
    coverageTags: ['float', 'meals'],
    complianceNotes: 'Ensure coverage for nap ratios',
    recurrencePattern: 'none' as const,
    recurrenceInterval: 1,
    recurrenceDays: [],
    recurrenceEndsAt: null,
    staffMemberId: null,
    createdBy: 1,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    isLocked: false,
    isDeleted: false,
    conflictCode: 'UNASSIGNED',
    conflictReason: 'Awaiting staff assignment',
    isPreview: true
  },
  {
    id: 88003,
    facilityId: 1,
    title: 'Extended Care PM',
    description: 'Late pick-up coverage and closing tasks',
    role: 'Afternoon Lead',
    department: 'Extended Care',
    location: 'Main Lobby',
    startTime: new Date().setHours(15, 0, 0, 0),
    endTime: new Date().setHours(18, 30, 0, 0),
    breakMinutes: 15,
    timezone: 'America/New_York',
    status: 'published' as const,
    colorCode: '#10b981',
    coverageTags: ['extended', 'closing'],
    complianceNotes: 'Document late pick-ups',
    recurrencePattern: 'weekly' as const,
    recurrenceInterval: 1,
    recurrenceDays: ['monday', 'tuesday', 'wednesday', 'thursday'],
    recurrenceEndsAt: null,
    staffMemberId: 502,
    createdBy: 1,
    createdAt: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date().toISOString(),
    isLocked: false,
    isDeleted: false,
    conflictCode: null,
    conflictReason: null,
    isPreview: true
  }
].map((shift) => ({
  ...shift,
  startTime: new Date(shift.startTime).toISOString(),
  endTime: new Date(shift.endTime).toISOString()
}));

export const SAMPLE_SCHEDULING_SUMMARY = {
  totalShifts: 18,
  publishedShifts: 14,
  openShifts: 3,
  pendingSwapRequests: 1,
  coverageAlerts: [
    {
      id: 'alert-1',
      message: 'Tuesday 11am coverage unassigned for Infant Room',
      severity: 'high'
    },
    {
      id: 'alert-2',
      message: 'Two overlapping time-off requests next Friday',
      severity: 'medium'
    }
  ],
  isPreview: true
};

/**
 * Sample operational tasks for preview mode
 */
export const SAMPLE_TASKS = [
  {
    id: 999991,
    title: 'Daily Safety Inspection',
    description: 'Conduct daily inspection of playground equipment and facility safety measures',
    category: 'Safety',
    task_type: 'recurring' as const,
    priority: 'high' as const,
    estimated_duration_minutes: 30,
    location: 'Playground & Main Facility',
    min_age_required: 18,
    max_age_allowed: undefined,
    start_date: new Date().toISOString(),
    end_date: undefined,
    is_active: true,
    is_recurring: true,
    has_age_restrictions: true,
    age_range_description: '18+ years required',
    created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    isPreview: true
  },
  {
    id: 999992,
    title: 'Weekly Inventory Check',
    description: 'Count and verify all supplies, equipment, and emergency items',
    category: 'Inventory',
    task_type: 'recurring' as const,
    priority: 'medium' as const,
    estimated_duration_minutes: 45,
    location: 'Storage Room & Kitchen',
    min_age_required: 16,
    max_age_allowed: undefined,
    start_date: new Date().toISOString(),
    end_date: undefined,
    is_active: true,
    is_recurring: true,
    has_age_restrictions: true,
    age_range_description: '16+ years required',
    created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    isPreview: true
  },
  {
    id: 999993,
    title: 'Deep Clean Activity Room',
    description: 'Thorough cleaning and sanitization of the main activity room',
    category: 'Cleaning',
    task_type: 'one_time' as const,
    priority: 'urgent' as const,
    estimated_duration_minutes: 120,
    location: 'Activity Room',
    min_age_required: undefined,
    max_age_allowed: undefined,
    start_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    end_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    is_active: true,
    is_recurring: false,
    has_age_restrictions: false,
    age_range_description: 'No age restrictions',
    created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    isPreview: true
  },
  {
    id: 999994,
    title: 'Kitchen Deep Clean with Photo Documentation',
    description: 'Complete deep cleaning of kitchen facilities with before and after photo documentation',
    category: 'Cleaning',
    task_type: 'one_time' as const,
    priority: 'high' as const,
    estimated_duration_minutes: 90,
    location: 'Kitchen',
    min_age_required: 16,
    max_age_allowed: undefined,
    start_date: new Date().toISOString(),
    end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    is_active: true,
    is_recurring: false,
    has_age_restrictions: true,
    age_range_description: '16+ years required',
    requires_before_photos: true,
    requires_after_photos: true,
    photo_instructions: 'Take photos of all work surfaces, equipment, and storage areas. Focus on cleanliness and organization. Include close-ups of cleaned appliances.',
    special_instructions: 'Pay special attention to food prep areas and ensure all surfaces are sanitized according to health department standards.',
    created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    isPreview: true
  }
];

/**
 * Sample task assignments for preview mode
 */
export const SAMPLE_TASK_ASSIGNMENTS = [
  {
    id: 999991,
    operational_task_id: 999991,
    staff_member_id: 999991,
    assigned_by: 999999,
    status: 'in_progress' as const,
    priority: 'high' as const,
    assigned_date: new Date().toISOString(),
    due_date: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
    started_date: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 mins ago
    completed_date: undefined,
    progress_percentage: 60,
    time_spent_minutes: 18,
    last_accessed: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    completion_verified: false,
    verification_notes: undefined,
    completion_photo_url: undefined,
    assignment_notes: 'Regular daily inspection - focus on new equipment',
    completion_notes: undefined,
    supervisor_notes: undefined,
    quality_rating: undefined,
    efficiency_rating: undefined,
    requires_followup: false,
    created_at: new Date().toISOString(),
    updated_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    is_overdue: false,
    days_until_due: 0,
    days_overdue: 0,
    is_completed: false,
    is_in_progress: true,
    completion_time_minutes: 0,
    has_photo_verification: false,
    operational_task: {
      id: 999991,
      title: 'Daily Safety Inspection',
      category: 'Safety'
    },
    staff_member: {
      id: 999991,
      first_name: 'Sarah',
      last_name: 'Johnson',
      full_name: 'Sarah Johnson',
      email: 'sarah.johnson@sample.com',
      role: 'Lead Caregiver'
    },
    isPreview: true
  },
  {
    id: 999992,
    operational_task_id: 999992,
    staff_member_id: 999992,
    assigned_by: 999999,
    status: 'completed' as const,
    priority: 'medium' as const,
    assigned_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    due_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    started_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    completed_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000 + 45 * 60 * 1000).toISOString(),
    progress_percentage: 100,
    time_spent_minutes: 45,
    last_accessed: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000 + 45 * 60 * 1000).toISOString(),
    completion_verified: true,
    verification_notes: 'All items accounted for and properly stored',
    completion_photo_url: undefined,
    assignment_notes: 'Weekly inventory check completed',
    completion_notes: 'Everything is in good condition. Found minor shortage in art supplies.',
    supervisor_notes: 'Well done. Please order more art supplies.',
    quality_rating: 5,
    efficiency_rating: 4,
    requires_followup: true,
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000 + 45 * 60 * 1000).toISOString(),
    is_overdue: false,
    days_until_due: undefined,
    days_overdue: 0,
    is_completed: true,
    is_in_progress: false,
    completion_time_minutes: 45,
    has_photo_verification: false,
    operational_task: {
      id: 999992,
      title: 'Weekly Inventory Check',
      category: 'Inventory'
    },
    staff_member: {
      id: 999992,
      first_name: 'Mike',
      last_name: 'Chen',
      full_name: 'Mike Chen',
      email: 'mike.chen@sample.com',
      role: 'Assistant Director'
    },
    isPreview: true
  },
  {
    id: 999993,
    operational_task_id: 999994,
    staff_member_id: 999991,
    assigned_by: 999999,
    status: 'assigned' as const,
    priority: 'high' as const,
    assigned_date: new Date().toISOString(),
    due_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 1 day from now
    started_date: undefined,
    completed_date: undefined,
    progress_percentage: 0,
    time_spent_minutes: 0,
    last_accessed: new Date().toISOString(),
    completion_verified: false,
    verification_notes: undefined,
    completion_photo_url: undefined,
    assignment_notes: 'New assignment with photo documentation requirements',
    completion_notes: undefined,
    supervisor_notes: undefined,
    quality_rating: undefined,
    efficiency_rating: undefined,
    requires_followup: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_overdue: false,
    days_until_due: 1,
    days_overdue: 0,
    is_completed: false,
    is_in_progress: false,
    completion_time_minutes: 0,
    has_photo_verification: true,
    operational_task: {
      id: 999994,
      title: 'Kitchen Deep Clean with Photo Documentation',
      category: 'Cleaning',
      requires_before_photos: true,
      requires_after_photos: true,
      photo_instructions: 'Take photos of all work surfaces, equipment, and storage areas. Focus on cleanliness and organization. Include close-ups of cleaned appliances.',
      special_instructions: 'Pay special attention to food prep areas and ensure all surfaces are sanitized according to health department standards.',
      location: 'Kitchen',
      estimated_duration_minutes: 90
    },
    staff_member: {
      id: 999991,
      first_name: 'Sarah',
      last_name: 'Johnson',
      full_name: 'Sarah Johnson',
      email: 'sarah.johnson@sample.com',
      role: 'Lead Caregiver'
    },
    isPreview: true
  }
];

/**
 * Sample task dashboard data for preview mode
 */
export const SAMPLE_TASK_DASHBOARD = {
  total_tasks: 8,
  active_tasks: 6,
  recurring_tasks: 5,
  total_assignments: 15,
  pending_assignments: 4,
  in_progress_assignments: 3,
  completed_assignments: 8,
  overdue_assignments: 0,
  completion_rate: 85.7,
  average_completion_time: 38.5,
  upcoming_due_dates: [
    {
      id: 999991,
      title: 'Daily Safety Inspection',
      due_date: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
      staff_member: 'Sarah Johnson',
      priority: 'high'
    },
    {
      id: 999993,
      title: 'Deep Clean Activity Room',
      due_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      staff_member: 'Unassigned',
      priority: 'urgent'
    }
  ],
  recent_completions: [
    {
      id: 999992,
      title: 'Weekly Inventory Check',
      completed_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000 + 45 * 60 * 1000).toISOString(),
      staff_member: 'Mike Chen',
      completion_time: 45
    }
  ],
  isPreview: true
};

/**
 * Sample notes for preview mode
 */
export const SAMPLE_NOTES = [
  {
    id: 999991,
    user_id: 999999,
    title: 'Emergency Procedures Update',
    content: 'Updated emergency evacuation procedures based on new state guidelines. Key changes include:\n\n• New assembly point locations\n• Updated contact information for emergency services\n• Revised communication protocols\n\nNext steps: Schedule staff training session and update posted procedures.',
    created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
    is_pinned: true,
    is_archived: false,
    isPreview: true
  },
  {
    id: 999992,
    user_id: 999999,
    title: 'Compliance Checklist - Q1 2024',
    content: '✅ Staff background checks completed\n✅ Fire safety inspection passed\n✅ Health department review completed\n⏳ License renewal application submitted\n⏳ Staff training certificates updated\n❌ Equipment maintenance logs review\n\nDeadlines:\n• Equipment review: End of month\n• Training completion: March 15th',
    created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days ago
    updated_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
    is_pinned: false,
    is_archived: false,
    isPreview: true
  },
  {
    id: 999993,
    user_id: 999999,
    title: 'New Regulation Summary',
    content: 'Summary of new childcare regulations effective January 2024:\n\n1. Enhanced background check requirements\n2. Updated staff-to-child ratios\n3. New nutritional guidelines for meals\n4. Revised outdoor play area safety standards\n\nAction items:\n• Review current policies against new requirements\n• Update staff handbook\n• Schedule compliance audit',
    created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(), // 10 days ago
    updated_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    is_pinned: false,
    is_archived: false,
    isPreview: true
  }
];

/**
 * Feature benefit descriptions for paywall modal
 */
export const FEATURE_BENEFITS = {
  calendar: {
    title: 'Compliance Calendar',
    description: 'Never miss important compliance deadlines again',
    benefits: [
      'Schedule compliance reviews and inspections',
      'Set automated reminders for license renewals',
      'Track staff training deadlines',
      'Sync with Google and Apple calendars',
      'AI-powered scheduling with natural language'
    ],
    requiredTier: Tier.PRO
  },
  notes: {
    title: 'Compliance Notes',
    description: 'Organize and track your compliance documentation',
    benefits: [
      'Create detailed compliance notes and checklists',
      'Pin important notes for quick access',
      'Search through all your compliance documentation',
      'Archive completed items for record keeping',
      'Export notes for reporting and audits'
    ],
    requiredTier: Tier.PRO
  },
  task_management: {
    title: 'Task & Chore Management',
    description: 'Streamline operational tasks and staff assignments',
    benefits: [
      'Create and manage operational tasks and chores',
      'Assign tasks to staff with age-based restrictions',
      'Track task progress and completion rates',
      'Set recurring tasks for routine operations',
      'Monitor staff performance and efficiency',
      'Photo verification for completed tasks',
      'Comprehensive task analytics and reporting'
    ],
    requiredTier: Tier.PRO
  },
  ai_pro_mode: {
    title: 'AI Pro Mode',
    description: 'Enhanced AI assistance with real-time information',
    benefits: [
      'Access to latest compliance regulations',
      'Real-time internet search capabilities',
      'More detailed and comprehensive responses',
      'Priority processing for faster responses',
      'Advanced document analysis features'
    ],
    requiredTier: Tier.PRO
  },
  data_export: {
    title: 'Data Export',
    description: 'Export all your compliance data for backup and portability',
    benefits: [
      'Export all your data in CSV, PDF, or JSON format',
      'One export per quarter included with Pro subscription',
      'Comprehensive data types: profiles, documents, policies, training',
      'Facility management data for administrators',
      'Training programs, assignments, and certifications',
      'Policy management with acknowledgment tracking',
      'Calendar events and external integrations',
      'Translation preferences and usage metrics',
      'Complete audit trail and activity logs',
      'Secure file generation with 72-hour access window',
      'Perfect for compliance audits and data portability'
    ],
    requiredTier: Tier.PRO
  },
  training_certification: {
    title: 'Training & Certification Management',
    description: 'Comprehensive staff training and certification tracking',
    benefits: [
      'Create and manage training programs',
      'Track staff certifications and expiration dates',
      'Automated training assignment and reminders',
      'Generate compliance reports and certificates',
      'Monitor training progress and completion rates',
      'OSHA and regulatory compliance tracking',
      'Staff competency management'
    ],
    requiredTier: Tier.PRO
  }
};

/**
 * Subscription tier information for comparison
 */
export const TIER_COMPARISON = {
  [Tier.FREE]: {
    name: 'Free',
    price: '$0/month',
    features: [
      'Basic compliance tools',
      'Standard document uploads',
      'Basic AI assistance',
      'Limited daily queries'
    ]
  },
  [Tier.PRO]: {
    name: 'Pro',
    price: '$50 base + $20/additional user',
    features: [
      'All Free features',
      'Compliance calendar',
      'Advanced notes system',
      'Training & certification management',
      'AI Pro Mode',
      'Unlimited queries',
      'Calendar integrations',
      'Priority support'
    ]
  },
  [Tier.ENTERPRISE]: {
    name: 'Enterprise',
    price: 'Contact Sales',
    features: [
      'All Pro features',
      'Dedicated account manager',
      'Custom integrations',
      'Priority support SLAs',
      'Volume discounts',
      'Advanced reporting'
    ]
  }
};

/**
 * Sample training programs for preview mode
 */
export const SAMPLE_TRAINING_PROGRAMS = [
  {
    id: 'preview-1',
    title: 'Safety Protocols & Emergency Procedures',
    description: 'Comprehensive training on workplace safety protocols, emergency evacuation procedures, and incident reporting.',
    category: 'Safety',
    is_mandatory: true,
    requires_certification: true,
    certification_valid_months: 12,
    estimated_duration_minutes: 120,
    delivery_method: 'online',
    is_active: true,
    isPreview: true
  },
  {
    id: 'preview-2',
    title: 'OSHA Compliance Training',
    description: 'Essential OSHA regulations and compliance requirements for healthcare facilities.',
    category: 'Compliance',
    is_mandatory: true,
    requires_certification: true,
    certification_valid_months: 24,
    estimated_duration_minutes: 180,
    delivery_method: 'hybrid',
    is_active: true,
    isPreview: true
  },
  {
    id: 'preview-3',
    title: 'Data Privacy & HIPAA',
    description: 'Patient data privacy, HIPAA compliance, and secure information handling procedures.',
    category: 'Privacy',
    is_mandatory: true,
    requires_certification: true,
    certification_valid_months: 12,
    estimated_duration_minutes: 90,
    delivery_method: 'online',
    is_active: true,
    isPreview: true
  },
  {
    id: 'preview-4',
    title: 'Equipment Maintenance Procedures',
    description: 'Proper maintenance and calibration procedures for medical equipment and devices.',
    category: 'Technical',
    is_mandatory: false,
    requires_certification: false,
    certification_valid_months: 6,
    estimated_duration_minutes: 60,
    delivery_method: 'in_person',
    is_active: true,
    isPreview: true
  }
];

/**
 * Sample staff members for preview mode
 */
export const SAMPLE_STAFF_MEMBERS = [
  {
    id: 'preview-1',
    employee_id: 'EMP001',
    first_name: 'Sarah',
    last_name: 'Johnson',
    email: 'sarah.johnson@example.com',
    phone: '(555) 123-4567',
    role: 'Nurse',
    department: 'Emergency',
    hire_date: '2023-01-15',
    status: 'active',
    isPreview: true
  },
  {
    id: 'preview-2',
    employee_id: 'EMP002',
    first_name: 'Michael',
    last_name: 'Chen',
    email: 'michael.chen@example.com',
    phone: '(555) 234-5678',
    role: 'Technician',
    department: 'Radiology',
    hire_date: '2022-08-20',
    status: 'active',
    isPreview: true
  },
  {
    id: 'preview-3',
    employee_id: 'EMP003',
    first_name: 'Emily',
    last_name: 'Rodriguez',
    email: 'emily.rodriguez@example.com',
    phone: '(555) 345-6789',
    role: 'Administrator',
    department: 'Administration',
    hire_date: '2021-03-10',
    status: 'active',
    isPreview: true
  }
];

/**
 * Sample training assignments for preview mode
 */
export const SAMPLE_TRAINING_ASSIGNMENTS = [
  {
    id: 'preview-1',
    training_program_id: 'preview-1',
    staff_member_id: 'preview-1',
    assigned_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    due_date: new Date(Date.now() + 25 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'assigned',
    priority: 'high',
    progress_percentage: 0,
    isPreview: true
  },
  {
    id: 'preview-2',
    training_program_id: 'preview-2',
    staff_member_id: 'preview-2',
    assigned_date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    due_date: new Date(Date.now() + 20 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'in_progress',
    priority: 'medium',
    progress_percentage: 45,
    isPreview: true
  },
  {
    id: 'preview-3',
    training_program_id: 'preview-3',
    staff_member_id: 'preview-3',
    assigned_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    due_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'overdue',
    priority: 'high',
    progress_percentage: 20,
    isPreview: true
  }
];

/**
 * Sample training completions for preview mode
 */
export const SAMPLE_TRAINING_COMPLETIONS = [
  {
    id: 'preview-1',
    training_assignment_id: 'preview-1',
    staff_member_id: 'preview-1',
    training_program_id: 'preview-1',
    completion_status: 'completed',
    completed_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    final_score: 95,
    certificate_status: 'issued',
    certificate_number: 'CERT-2024-001',
    expires_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
    isPreview: true
  },
  {
    id: 'preview-2',
    training_assignment_id: 'preview-2',
    staff_member_id: 'preview-2',
    training_program_id: 'preview-2',
    completion_status: 'verified',
    completed_date: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    final_score: 88,
    certificate_status: 'issued',
    certificate_number: 'CERT-2024-002',
    expires_date: new Date(Date.now() + 730 * 24 * 60 * 60 * 1000).toISOString(),
    isPreview: true
  }
]; 