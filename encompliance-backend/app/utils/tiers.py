"""
Description: User subscription tier definitions for the EnCompliance application.
Purpose: Provides tier constants and utility functions to determine user's access level 
based on their subscription status. Used for paywall and feature access control on the backend.
"""

"""
Tier definitions for subscription levels
Used to determine feature access based on subscription status
"""

# Tier constants
FREE = 0
PRO = 1
ENTERPRISE = 2

def get_tier_from_subscription_status(subscription_status: str) -> int:
    """
    Convert subscription status string to numeric tier value
    
    Args:
        subscription_status: The subscription status string
        
    Returns:
        int: The numeric tier value
    """
    if not subscription_status:
        return FREE
        
    status_lower = subscription_status.lower()
    
    if status_lower in ["pro", "active", "team_member"]:  # Treat 'active' and 'team_member' as PRO tier
        return PRO
    elif status_lower == "enterprise":
        return ENTERPRISE
    else:
        return FREE 