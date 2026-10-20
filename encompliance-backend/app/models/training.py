"""
Training Models Module

This module provides a centralized import for all training-related database models.
It consolidates imports from individual model files for easier access.

Available Models:
- TrainingProgram: Training program definitions and metadata
- StaffMember: Facility staff member information
- TrainingAssignment: Training assignments to staff members
- TrainingMaterial: Training content and materials
- TrainingCompletion: Training completion records and certificates

Dependencies:
- Individual model modules for each training entity
"""

# Import all training-related models
from app.models.training_program import TrainingProgram, training_program_facility_types
from app.models.staff_member import StaffMember, StaffRole, StaffStatus
from app.models.training_assignment import TrainingAssignment, AssignmentStatus, AssignmentPriority
from app.models.training_material import TrainingMaterial, MaterialType, MaterialStatus
from app.models.training_completion import TrainingCompletion, CompletionStatus, CertificateStatus

# Export all models for easy importing
__all__ = [
    'TrainingProgram',
    'StaffMember', 
    'TrainingAssignment',
    'TrainingMaterial',
    'TrainingCompletion',
    'training_program_facility_types',
    'StaffRole',
    'StaffStatus', 
    'AssignmentStatus',
    'AssignmentPriority',
    'MaterialType',
    'MaterialStatus',
    'CompletionStatus',
    'CertificateStatus'
] 