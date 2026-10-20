"""
Description: Feature requirements mapping for the EnCompliance application.
Purpose: Defines which subscription tier is required for each premium feature in the backend.
Used in conjunction with access_control.py to enforce paywall restrictions on API endpoints.
"""

"""
Feature requirements mapping
Defines the minimum tier required for each feature in the application
Used for paywall and feature access control
"""

from app.utils.tiers import FREE, PRO, ENTERPRISE

# Feature to tier mapping
feature_requirements = {
    "calendar": PRO,
    "ai_pro_mode": PRO,
    "notes": PRO,
    "data_export": PRO,
    "training_certification": PRO,
    "training": PRO
} 