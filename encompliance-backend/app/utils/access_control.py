"""
Description: Access control utility for the EnCompliance application.
Purpose: Provides functions to determine if a user can access specific premium features
based on their subscription tier. Implements the core paywall logic by comparing
user tier against feature requirements for API endpoints. Enhanced with freemium preview functionality.
"""

"""
Access control utility functions
Provides functions to check if a user can access specific features based on their tier
"""

from app.utils.feature_requirements import feature_requirements
from app.utils.tiers import FREE

def can_access_feature(user_tier: int, feature_key: str) -> bool:
    """
    Check if a user with the given tier can access a specific feature
    
    Args:
        user_tier: The tier of the current user
        feature_key: The key of the feature to check access for
        
    Returns:
        bool: True if the user can access the feature, False otherwise
    """
    # If the feature doesn't exist in requirements, assume it's available to all
    if feature_key not in feature_requirements:
        return True
    
    # Check if user tier meets or exceeds the required tier for the feature
    return user_tier >= feature_requirements[feature_key]

def can_preview_feature(user_tier: int, feature_key: str) -> bool:
    """
    Check if a user can preview a feature (always true for freemium model)
    
    Args:
        user_tier: The tier of the current user
        feature_key: The key of the feature to check preview access for
        
    Returns:
        bool: True (all users can preview all features in freemium model)
    """
    # All users can preview all features in freemium model
    return True

def can_use_feature(user_tier: int, feature_key: str) -> bool:
    """
    Check if a user can actually use/interact with a feature (same as can_access_feature)
    
    Args:
        user_tier: The tier of the current user
        feature_key: The key of the feature to check usage access for
        
    Returns:
        bool: True if the user can use the feature, False otherwise
    """
    return can_access_feature(user_tier, feature_key)

def get_required_tier(feature_key: str) -> int:
    """
    Get the required tier for a specific feature
    
    Args:
        feature_key: The key of the feature
        
    Returns:
        int: The minimum tier required for the feature
    """
    return feature_requirements.get(feature_key, FREE)

def is_premium_feature(feature_key: str) -> bool:
    """
    Check if a feature is premium (requires paid subscription)
    
    Args:
        feature_key: The key of the feature to check
        
    Returns:
        bool: True if the feature is premium, False otherwise
    """
    return feature_key in feature_requirements and feature_requirements[feature_key] > FREE 