"""
Description: Admin sync service for triggering real-time synchronization events.
Purpose: Monitors facility administrator actions and triggers sync events to notify
team members of changes to shared data like facility settings, documents, etc.

Educational Note: This service implements the observer pattern to decouple admin
operations from sync notifications, ensuring team members are immediately notified
of relevant changes without tight coupling between components.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.api.routes.sync import broadcast_sync_event
from app.services.sync_service import SyncService
from app.models.user import User
from app.models.facility import Facility

logger = logging.getLogger(__name__)


class AdminSyncService:
    """
    Description: Service for triggering synchronization events when admins make changes.
    Purpose: Ensures team members receive real-time updates when facility data changes.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.sync_service = SyncService(db)
    
    async def trigger_account_sync(self, facility_id: int, admin_user_id: int) -> None:
        """
        Description: Triggers account overview sync when facility settings change.
        Purpose: Notifies team members when admin updates facility name, state, types, etc.
        """
        try:
            # Get all team members for this facility
            team_members = self._get_facility_team_members(facility_id)
            
            # Update each team member individually and trigger their sync
            for member in team_members:
                # Get updated account data with user_id to trigger profile updates
                account_data = await self.sync_service.get_account_overview(facility_id, member.id)
                
                # Broadcast to specific team member
                await broadcast_sync_event(
                    facility_id=facility_id,
                    event_type="account_update",
                    data=account_data,
                    target_user_ids=[member.id]
                )
                
                # Store sync event in database
                await self.sync_service.create_sync_event(
                    facility_id=facility_id,
                    event_type="account_update",
                    data=account_data,
                    target_user_ids=[member.id]
                )
            
            logger.info(f"Account sync triggered for facility {facility_id}, notified {len(team_members)} team members")
            
        except Exception as e:
            logger.error(f"Failed to trigger account sync for facility {facility_id}: {e}")
    
    async def trigger_document_sync(self, facility_id: int, admin_user_id: int) -> None:
        """
        Description: Triggers document library sync when documents are added/removed.
        Purpose: Notifies team members when admin changes document accessibility.
        """
        try:
            # Get updated document library data
            document_data = await self.sync_service.get_document_library(facility_id)
            
            # Get all team members for this facility
            team_members = self._get_facility_team_members(facility_id)
            target_user_ids = [member.id for member in team_members]
            
            # Broadcast to connected team members
            await broadcast_sync_event(
                facility_id=facility_id,
                event_type="document_update",
                data=document_data,
                target_user_ids=target_user_ids
            )
            
            # Store sync event in database
            await self.sync_service.create_sync_event(
                facility_id=facility_id,
                event_type="document_update",
                data=document_data,
                target_user_ids=target_user_ids
            )
            
            logger.info(f"Document sync triggered for facility {facility_id}, notified {len(target_user_ids)} team members")
            
        except Exception as e:
            logger.error(f"Failed to trigger document sync for facility {facility_id}: {e}")
    
    async def trigger_calendar_sync(self, facility_id: int, admin_user_id: int, target_user_id: Optional[int] = None) -> None:
        """
        Description: Triggers calendar sync when admin creates/modifies events.
        Purpose: Notifies team members when admin changes calendar events affecting them.
        """
        try:
            # If specific user targeted, only sync for them
            if target_user_id:
                from app.models.user import UserRole
                target_users = [self.db.query(User).filter(User.id == target_user_id).first()]
                target_users = [user for user in target_users if user and user.user_role == UserRole.TEAM_MEMBER]
            else:
                # Get all team members for this facility
                target_users = self._get_facility_team_members(facility_id)
            
            # Generate calendar sync for each target user
            for user in target_users:
                calendar_data = await self.sync_service.get_calendar_events(facility_id, user.id)
                
                # Broadcast to specific user
                await broadcast_sync_event(
                    facility_id=facility_id,
                    event_type="calendar_update",
                    data=calendar_data,
                    target_user_ids=[user.id]
                )
                
                # Store sync event in database
                await self.sync_service.create_sync_event(
                    facility_id=facility_id,
                    event_type="calendar_update",
                    data=calendar_data,
                    target_user_ids=[user.id]
                )
            
            logger.info(f"Calendar sync triggered for facility {facility_id}, notified {len(target_users)} team members")
            
        except Exception as e:
            logger.error(f"Failed to trigger calendar sync for facility {facility_id}: {e}")
    
    async def trigger_training_sync(self, facility_id: int, admin_user_id: int, target_user_id: Optional[int] = None) -> None:
        """
        Description: Triggers training sync when admin assigns/modifies training.
        Purpose: Notifies team members when admin changes their training assignments.
        """
        try:
            # If specific user targeted, only sync for them
            if target_user_id:
                from app.models.user import UserRole
                target_users = [self.db.query(User).filter(User.id == target_user_id).first()]
                target_users = [user for user in target_users if user and user.user_role == UserRole.TEAM_MEMBER]
            else:
                # Get all team members for this facility
                target_users = self._get_facility_team_members(facility_id)
            
            # Generate training sync for each target user
            for user in target_users:
                training_data = await self.sync_service.get_training_data(facility_id, user.id)
                
                # Broadcast to specific user
                await broadcast_sync_event(
                    facility_id=facility_id,
                    event_type="training_update",
                    data=training_data,
                    target_user_ids=[user.id]
                )
                
                # Store sync event in database
                await self.sync_service.create_sync_event(
                    facility_id=facility_id,
                    event_type="training_update",
                    data=training_data,
                    target_user_ids=[user.id]
                )
            
            logger.info(f"Training sync triggered for facility {facility_id}, notified {len(target_users)} team members")
            
        except Exception as e:
            logger.error(f"Failed to trigger training sync for facility {facility_id}: {e}")
    
    async def trigger_facility_wide_sync(self, facility_id: int, admin_user_id: int) -> None:
        """
        Description: Triggers comprehensive sync of all data types.
        Purpose: Full synchronization when major facility changes occur.
        """
        try:
            # Trigger all sync types
            await self.trigger_account_sync(facility_id, admin_user_id)
            await self.trigger_document_sync(facility_id, admin_user_id)
            await self.trigger_calendar_sync(facility_id, admin_user_id)
            await self.trigger_training_sync(facility_id, admin_user_id)
            
            logger.info(f"Facility-wide sync triggered for facility {facility_id}")
            
        except Exception as e:
            logger.error(f"Failed to trigger facility-wide sync for facility {facility_id}: {e}")
    
    def _get_facility_team_members(self, facility_id: int) -> List[User]:
        """
        Description: Gets all team members for a facility.
        Purpose: Helper method to retrieve target users for sync notifications.
        """
        from app.models.user import UserRole
        return self.db.query(User).filter(
            User.facility_id == facility_id,
            User.user_role == UserRole.TEAM_MEMBER,
            User.is_active == True
        ).all()


# Decorator to automatically trigger sync events
def sync_on_admin_action(sync_type: str, target_user_param: Optional[str] = None):
    """
    Description: Decorator to automatically trigger sync events after admin operations.
    Purpose: Simplifies adding sync notifications to existing admin endpoints.
    
    Educational Note: This decorator uses the decorator pattern to add cross-cutting
    concerns (sync notifications) without modifying core business logic.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Execute original function
            result = await func(*args, **kwargs)
            
            try:
                # Extract facility_id and user info from function context
                # This assumes standard patterns in admin endpoints
                current_user = kwargs.get('current_user')
                facility_id = None
                target_user_id = None
                
                # Try to extract facility_id from various sources
                if hasattr(current_user, 'facility_id') and current_user.facility_id:
                    facility_id = current_user.facility_id
                elif 'facility_id' in kwargs:
                    facility_id = kwargs['facility_id']
                
                # Extract target user if specified
                if target_user_param and target_user_param in kwargs:
                    target_user_id = kwargs[target_user_param]
                
                # If we have facility context, trigger sync
                if facility_id and current_user:
                    db = kwargs.get('db')
                    if db:
                        admin_sync_service = AdminSyncService(db)
                        
                        if sync_type == "account":
                            await admin_sync_service.trigger_account_sync(facility_id, current_user.id)
                        elif sync_type == "document":
                            await admin_sync_service.trigger_document_sync(facility_id, current_user.id)
                        elif sync_type == "calendar":
                            await admin_sync_service.trigger_calendar_sync(facility_id, current_user.id, target_user_id)
                        elif sync_type == "training":
                            await admin_sync_service.trigger_training_sync(facility_id, current_user.id, target_user_id)
                        elif sync_type == "facility_wide":
                            await admin_sync_service.trigger_facility_wide_sync(facility_id, current_user.id)
                
            except Exception as e:
                # Log sync failure but don't affect main operation
                logger.error(f"Failed to trigger {sync_type} sync after admin action: {e}")
            
            return result
        return wrapper
    return decorator 