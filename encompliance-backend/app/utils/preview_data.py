"""
Description: Preview data constants for the EnCompliance application backend.
Purpose: Provides sample data for freemium preview mode API endpoints, allowing free tier users
to see what premium features look like without accessing real functionality.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

def get_sample_calendar_events() -> List[Dict[str, Any]]:
    """
    Get sample calendar events for preview mode
    
    Returns:
        List[Dict]: Sample calendar events with preview flag
    """
    now = datetime.now()
    
    return [
        {
            "id": "preview-1",
            "title": "Quarterly Compliance Review",
            "start": (now + timedelta(days=7)).isoformat(),
            "end": (now + timedelta(days=7, hours=2)).isoformat(),
            "description": "Review all compliance documentation and update policies as needed.",
            "location": "Conference Room A",
            "all_day": False,
            "is_preview": True
        },
        {
            "id": "preview-2", 
            "title": "Staff Training: Safety Protocols",
            "start": (now + timedelta(days=14)).isoformat(),
            "end": (now + timedelta(days=14, hours=3)).isoformat(),
            "description": "Mandatory training session for all staff on updated safety protocols.",
            "location": "Main Training Room",
            "all_day": False,
            "is_preview": True
        },
        {
            "id": "preview-3",
            "title": "License Renewal Deadline",
            "start": (now + timedelta(days=30)).isoformat(),
            "end": (now + timedelta(days=30)).isoformat(),
            "description": "Submit license renewal application and required documentation.",
            "location": "",
            "all_day": True,
            "is_preview": True
        },
        {
            "id": "preview-4",
            "title": "Monthly Inspection",
            "start": (now + timedelta(days=21)).isoformat(),
            "end": (now + timedelta(days=21, hours=1)).isoformat(),
            "description": "Routine monthly inspection of facilities and equipment.",
            "location": "All Facilities",
            "all_day": False,
            "is_preview": True
        }
    ]

def get_sample_training_programs() -> List[Dict[str, Any]]:
    """
    Get sample training programs for preview mode
    
    Returns:
        List[Dict]: Sample training programs with preview flag
    """
    return [
        {
            "id": "preview-1",
            "title": "Safety Protocols & Emergency Procedures",
            "description": "Comprehensive training on workplace safety protocols, emergency evacuation procedures, and incident reporting.",
            "category": "Safety",
            "is_mandatory": True,
            "requires_certification": True,
            "certification_valid_months": 12,
            "estimated_duration_minutes": 120,
            "delivery_method": "online",
            "is_active": True,
            "is_preview": True
        },
        {
            "id": "preview-2",
            "title": "OSHA Compliance Training",
            "description": "Essential OSHA regulations and compliance requirements for healthcare facilities.",
            "category": "Compliance",
            "is_mandatory": True,
            "requires_certification": True,
            "certification_valid_months": 24,
            "estimated_duration_minutes": 180,
            "delivery_method": "hybrid",
            "is_active": True,
            "is_preview": True
        },
        {
            "id": "preview-3",
            "title": "Data Privacy & HIPAA",
            "description": "Patient data privacy, HIPAA compliance, and secure information handling procedures.",
            "category": "Privacy",
            "is_mandatory": True,
            "requires_certification": True,
            "certification_valid_months": 12,
            "estimated_duration_minutes": 90,
            "delivery_method": "online",
            "is_active": True,
            "is_preview": True
        },
        {
            "id": "preview-4",
            "title": "Equipment Maintenance Procedures",
            "description": "Proper maintenance and calibration procedures for medical equipment and devices.",
            "category": "Technical",
            "is_mandatory": False,
            "requires_certification": False,
            "certification_valid_months": 6,
            "estimated_duration_minutes": 60,
            "delivery_method": "in_person",
            "is_active": True,
            "is_preview": True
        }
    ]

def get_sample_staff_members() -> List[Dict[str, Any]]:
    """
    Get sample staff members for preview mode
    
    Returns:
        List[Dict]: Sample staff members with preview flag
    """
    return [
        {
            "id": "preview-1",
            "employee_id": "EMP001",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@example.com",
            "phone": "(555) 123-4567",
            "role": "Nurse",
            "department": "Emergency",
            "hire_date": "2023-01-15",
            "status": "active",
            "is_preview": True
        },
        {
            "id": "preview-2",
            "employee_id": "EMP002",
            "first_name": "Michael",
            "last_name": "Chen",
            "email": "michael.chen@example.com",
            "phone": "(555) 234-5678",
            "role": "Technician",
            "department": "Radiology",
            "hire_date": "2022-08-20",
            "status": "active",
            "is_preview": True
        },
        {
            "id": "preview-3",
            "employee_id": "EMP003",
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@example.com",
            "phone": "(555) 345-6789",
            "role": "Administrator",
            "department": "Administration",
            "hire_date": "2021-03-10",
            "status": "active",
            "is_preview": True
        }
    ]

def get_sample_training_assignments() -> List[Dict[str, Any]]:
    """
    Get sample training assignments for preview mode
    
    Returns:
        List[Dict]: Sample training assignments with preview flag
    """
    now = datetime.now()
    
    return [
        {
            "id": "preview-1",
            "training_program_id": "preview-1",
            "staff_member_id": "preview-1",
            "assigned_date": (now - timedelta(days=5)).isoformat(),
            "due_date": (now + timedelta(days=25)).isoformat(),
            "status": "assigned",
            "priority": "high",
            "progress_percentage": 0,
            "is_preview": True
        },
        {
            "id": "preview-2",
            "training_program_id": "preview-2",
            "staff_member_id": "preview-2",
            "assigned_date": (now - timedelta(days=10)).isoformat(),
            "due_date": (now + timedelta(days=20)).isoformat(),
            "status": "in_progress",
            "priority": "medium",
            "progress_percentage": 45,
            "is_preview": True
        },
        {
            "id": "preview-3",
            "training_program_id": "preview-3",
            "staff_member_id": "preview-3",
            "assigned_date": (now - timedelta(days=30)).isoformat(),
            "due_date": (now - timedelta(days=5)).isoformat(),
            "status": "overdue",
            "priority": "high",
            "progress_percentage": 20,
            "is_preview": True
        }
    ]

def get_sample_training_completions() -> List[Dict[str, Any]]:
    """
    Get sample training completions for preview mode
    
    Returns:
        List[Dict]: Sample training completions with preview flag
    """
    now = datetime.now()
    
    return [
        {
            "id": "preview-1",
            "training_assignment_id": "preview-1",
            "staff_member_id": "preview-1",
            "training_program_id": "preview-1",
            "completion_status": "completed",
            "completed_date": (now - timedelta(days=2)).isoformat(),
            "final_score": 95,
            "certificate_status": "issued",
            "certificate_number": "CERT-2024-001",
            "expires_date": (now + timedelta(days=365)).isoformat(),
            "is_preview": True
        },
        {
            "id": "preview-2",
            "training_assignment_id": "preview-2",
            "staff_member_id": "preview-2",
            "training_program_id": "preview-2",
            "completion_status": "verified",
            "completed_date": (now - timedelta(days=15)).isoformat(),
            "final_score": 88,
            "certificate_status": "issued",
            "certificate_number": "CERT-2024-002",
            "expires_date": (now + timedelta(days=730)).isoformat(),
            "is_preview": True
        }
    ]

def get_sample_notes() -> List[Dict[str, Any]]:
    """
    Get sample notes for preview mode
    
    Returns:
        List[Dict]: Sample notes with preview flag
    """
    now = datetime.now()
    
    return [
        {
            "id": 999991,
            "user_id": 999999,  # Dummy user ID for preview
            "title": "Emergency Procedures Update",
            "content": "Updated emergency evacuation procedures based on new state guidelines. Key changes include:\n\n• New assembly point locations\n• Updated contact information for emergency services\n• Revised communication protocols\n\nNext steps: Schedule staff training session and update posted procedures.",
            "created_at": (now - timedelta(days=2)).isoformat(),
            "updated_at": (now - timedelta(days=1)).isoformat(),
            "is_pinned": True,
            "is_archived": False,
            "is_preview": True
        },
        {
            "id": 999992,
            "user_id": 999999,  # Dummy user ID for preview
            "title": "Compliance Checklist - Q1 2024",
            "content": "✅ Staff background checks completed\n✅ Fire safety inspection passed\n✅ Health department review completed\n⏳ License renewal application submitted\n⏳ Staff training certificates updated\n❌ Equipment maintenance logs review\n\nDeadlines:\n• Equipment review: End of month\n• Training completion: March 15th",
            "created_at": (now - timedelta(days=5)).isoformat(),
            "updated_at": (now - timedelta(days=3)).isoformat(),
            "is_pinned": False,
            "is_archived": False,
            "is_preview": True
        },
        {
            "id": 999993,
            "user_id": 999999,  # Dummy user ID for preview
            "title": "New Regulation Summary",
            "content": "Summary of new childcare regulations effective January 2024:\n\n1. Enhanced background check requirements\n2. Updated staff-to-child ratios\n3. New nutritional guidelines for meals\n4. Revised outdoor play area safety standards\n\nAction items:\n• Review current policies against new requirements\n• Update staff handbook\n• Schedule compliance audit",
            "created_at": (now - timedelta(days=10)).isoformat(),
            "updated_at": (now - timedelta(days=10)).isoformat(),
            "is_pinned": False,
            "is_archived": False,
            "is_preview": True
        }
    ]

def get_feature_benefits() -> Dict[str, Dict[str, Any]]:
    """
    Get feature benefit descriptions for paywall responses
    
    Returns:
        Dict: Feature benefits mapping
    """
    return {
        "calendar": {
            "title": "Compliance Calendar",
            "description": "Never miss important compliance deadlines again",
            "benefits": [
                "Schedule compliance reviews and inspections",
                "Set automated reminders for license renewals", 
                "Track staff training deadlines",
                "Sync with Google and Apple calendars",
                "AI-powered scheduling with natural language"
            ],
            "required_tier": "pro"
        },
        "notes": {
            "title": "Compliance Notes",
            "description": "Organize and track your compliance documentation",
            "benefits": [
                "Create detailed compliance notes and checklists",
                "Pin important notes for quick access",
                "Search through all your compliance documentation",
                "Archive completed items for record keeping",
                "Export notes for reporting and audits"
            ],
            "required_tier": "pro"
        },
        "ai_pro_mode": {
            "title": "AI Pro Mode", 
            "description": "Enhanced AI assistance with real-time information",
            "benefits": [
                "Access to latest compliance regulations",
                "Real-time internet search capabilities",
                "More detailed and comprehensive responses",
                "Priority processing for faster responses",
                "Advanced document analysis features"
            ],
            "required_tier": "pro"
        },
        "data_export": {
            "title": "Data Export",
            "description": "Export all your compliance data for backup and portability",
            "benefits": [
                "Export all your data in CSV, PDF, or JSON format",
                "One export per quarter included with Pro subscription",
                "Secure, encrypted file generation",
                "24-hour download window for security",
                "Complete data portability and backup"
            ],
            "required_tier": "pro"
        },
        "training_certification": {
            "title": "Training & Certification Management",
            "description": "Comprehensive staff training and certification tracking",
            "benefits": [
                "Create and manage training programs",
                "Track staff certifications and expiration dates",
                "Automated training assignment and reminders",
                "Generate compliance reports and certificates",
                "Monitor training progress and completion rates",
                "OSHA and regulatory compliance tracking",
                "Staff competency management"
            ],
            "required_tier": "pro"
        }
    } 