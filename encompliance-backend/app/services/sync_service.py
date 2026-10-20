"""
Description: Service layer for real-time synchronization operations.
Purpose: Handles business logic for synchronizing data between facility administrators
and team members, including data retrieval, event creation, and update processing.

Educational Note: Service layer pattern separates business logic from API endpoints,
promoting code reusability and testability in enterprise applications.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.user import User
from app.models.facility import Facility
from app.models.document import Document
from app.models.calendar_event import CalendarEvent
from app.models.training_assignment import TrainingAssignment
from app.models.training_completion import TrainingCompletion
from app.models.training_program import TrainingProgram
from app.models.sync_event import SyncEvent
from app.schemas.sync import (
    SyncEventResponse, 
    AccountOverviewData,
    DocumentLibraryData,
    CalendarEventData,
    TrainingData
)

logger = logging.getLogger(__name__)


class SyncService:
    """
    Description: Service class for handling real-time synchronization operations.
    Purpose: Provides centralized business logic for syncing data between 
    facility administrators and team members.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_account_overview(self, facility_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Description: Retrieves current facility account information for synchronization.
        Purpose: Provides team members with updated facility details when admin makes changes.
        """
        
        facility = self.db.query(Facility).filter(Facility.id == facility_id).first()
        if not facility:
            raise ValueError(f"Facility {facility_id} not found")
        
        # Get facility admin for state and facility type info
        from app.models.user import UserRole
        admin = self.db.query(User).filter(
            and_(
                User.facility_id == facility_id,
                User.user_role == UserRole.FACILITY_ADMIN
            )
        ).first()
        
        if not admin:
            raise ValueError(f"No admin found for facility {facility_id}")
        
        # If user_id provided, update the team member's state and facility_type
        if user_id:
            team_member = self.db.query(User).filter(
                and_(
                    User.id == user_id,
                    User.facility_id == facility_id,
                    User.user_role == UserRole.TEAM_MEMBER
                )
            ).first()
            
            if team_member:
                # Check if state or facility_type changed
                state_changed = team_member.state != admin.state
                facility_type_changed = team_member.facility_type != admin.facility_type
                
                # Update team member's state and facility_type to match admin
                team_member.state = admin.state
                team_member.facility_type = admin.facility_type
                self.db.commit()
                logger.info(f"Updated team member {user_id} state to '{admin.state}' and facility_type to '{admin.facility_type}'")
                
                # If state or facility type changed, update document associations
                if state_changed or facility_type_changed:
                    try:
                        from app.api.routes.auth import associate_user_documents
                        
                        facility_types = []
                        if team_member.facility_type:
                            facility_types = [ft.strip() for ft in team_member.facility_type.split(',') if ft.strip()]
                        
                        # Call the async function directly since we're in an async context
                        await associate_user_documents(self.db, team_member.id, team_member.state, facility_types)
                        
                        self.db.commit()
                        logger.info(f"Updated document associations for team member {user_id} after state/facility type change")
                    except Exception as e:
                        logger.error(f"Error updating document associations for team member {user_id}: {str(e)}")
        
        return {
            "operation_name": facility.facility_name,
            "facility_types": admin.facility_type.split(',') if admin.facility_type else [],
            "state": admin.state,
            "subscription_status": admin.subscription_status if admin else "free",
            "facility_name": facility.facility_name,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_document_library(self, facility_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Description: Retrieves current document library state for synchronization.
        Purpose: Provides team members with updated document access when admin changes documents.
        """
        
        # Import models we need
        from app.models.user_document import UserDocument
        from app.models.regulation import Regulation
        
        # If user_id is provided (team member), get their associated documents
        if user_id:
            # Get manually uploaded documents by facility admin
            manual_docs = self.db.query(Document).filter(
                Document.uploaded_by.in_(
                    self.db.query(User.id).filter(
                        and_(
                            User.facility_id == facility_id,
                            User.user_role == UserRole.FACILITY_ADMIN
                        )
                    )
                ),
                Document.is_deleted == False
            ).all()
            
            # Get user's associated regulatory documents
            user_docs = self.db.query(UserDocument).filter(
                UserDocument.user_id == user_id
            ).all()
            
            # Get regulations for the user's associated documents
            regulation_ids = [ud.regulation_id for ud in user_docs if ud.regulation_id]
            regulations = self.db.query(Regulation).filter(
                Regulation.id.in_(regulation_ids)
            ).all() if regulation_ids else []
            
            # Combine all documents
            all_documents = []
            
            # Add manual documents
            for doc in manual_docs:
                all_documents.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "document_type": "manual_upload",
                    "is_public": False,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
                })
            
            # Add regulatory documents
            for reg in regulations:
                all_documents.append({
                    "id": reg.id,
                    "filename": reg.file_name,
                    "file_size": None,  # We don't track size for regulations in DB
                    "document_type": "regulation",
                    "is_public": True,
                    "created_at": reg.created_at.isoformat() if reg.created_at else None,
                    "updated_at": reg.updated_at.isoformat() if reg.updated_at else None
                })
            
            total_size = sum(doc.get('file_size') or 0 for doc in all_documents)
            
            return {
                "total_documents": len(all_documents),
                "total_size_bytes": total_size,
                "documents": all_documents,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Fallback for facility-level sync (no specific user)
            documents = self.db.query(Document).filter(
                or_(
                    Document.facility_id == facility_id,
                    Document.is_public == True
                )
            ).all()
            
            total_size = sum(doc.file_size or 0 for doc in documents)
            
            document_list = []
            for doc in documents:
                document_list.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "document_type": doc.document_type,
                    "is_public": doc.is_public,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
                })
            
            return {
                "total_documents": len(documents),
                "total_size_bytes": total_size,
                "documents": document_list,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_calendar_events(self, facility_id: int, user_id: int) -> Dict[str, Any]:
        """
        Description: Retrieves current calendar events for team member synchronization.
        Purpose: Provides team members with updated calendar when admin creates/modifies events.
        """
        
        # Get events relevant to team member
        events = self.db.query(CalendarEvent).filter(
            and_(
                CalendarEvent.facility_id == facility_id,
                or_(
                    CalendarEvent.assigned_user_id == user_id,
                    CalendarEvent.assigned_user_id.is_(None)  # Facility-wide events
                )
            )
        ).all()
        
        upcoming_events = [
            event for event in events 
            if event.start_datetime and event.start_datetime > datetime.now(timezone.utc)
        ]
        
        event_list = []
        for event in events:
            event_list.append({
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "start_datetime": event.start_datetime.isoformat() if event.start_datetime else None,
                "end_datetime": event.end_datetime.isoformat() if event.end_datetime else None,
                "event_type": event.event_type,
                "assigned_user_id": event.assigned_user_id,
                "created_at": event.created_at.isoformat() if event.created_at else None
            })
        
        return {
            "events": event_list,
            "upcoming_count": len(upcoming_events),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_training_data(self, facility_id: int, user_id: int) -> Dict[str, Any]:
        """
        Description: Retrieves current training data for team member synchronization.
        Purpose: Provides team members with updated training assignments and progress.
        """
        
        # Get user's training assignments
        assignments = self.db.query(TrainingAssignment).filter(
            and_(
                TrainingAssignment.facility_id == facility_id,
                TrainingAssignment.assigned_user_id == user_id
            )
        ).all()
        
        # Get user's training completions
        completions = self.db.query(TrainingCompletion).filter(
            and_(
                TrainingCompletion.facility_id == facility_id,
                TrainingCompletion.user_id == user_id
            )
        ).all()
        
        # Get available training programs
        programs = self.db.query(TrainingProgram).filter(
            TrainingProgram.facility_id == facility_id
        ).all()
        
        assignment_list = []
        for assignment in assignments:
            assignment_list.append({
                "id": assignment.id,
                "training_program_id": assignment.training_program_id,
                "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                "status": assignment.status,
                "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None
            })
        
        completion_list = []
        for completion in completions:
            completion_list.append({
                "id": completion.id,
                "training_program_id": completion.training_program_id,
                "completed_at": completion.completed_at.isoformat() if completion.completed_at else None,
                "score": completion.score,
                "status": completion.status
            })
        
        program_list = []
        for program in programs:
            program_list.append({
                "id": program.id,
                "title": program.title,
                "description": program.description,
                "status": program.status,
                "created_at": program.created_at.isoformat() if program.created_at else None
            })
        
        # Calculate progress summary
        total_assignments = len(assignments)
        completed_assignments = len([a for a in assignments if a.status == "completed"])
        completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
        
        progress_summary = {
            "total_assignments": total_assignments,
            "completed_assignments": completed_assignments,
            "completion_rate": round(completion_rate, 1),
            "overdue_assignments": len([
                a for a in assignments 
                if a.due_date and a.due_date < datetime.now(timezone.utc) and a.status != "completed"
            ])
        }
        
        return {
            "assignments": assignment_list,
            "completions": completion_list,
            "programs": program_list,
            "progress_summary": progress_summary,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def create_sync_event(
        self, 
        facility_id: int, 
        event_type: str, 
        data: Dict[str, Any],
        target_user_ids: Optional[List[int]] = None
    ) -> int:
        """
        Description: Creates synchronization event in database.
        Purpose: Stores sync events for audit trail and polling fallback.
        """
        
        # Set expiration time (7 days from now)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        if target_user_ids:
            # Create individual events for specific users
            event_ids = []
            for user_id in target_user_ids:
                sync_event = SyncEvent(
                    facility_id=facility_id,
                    target_user_id=user_id,
                    event_type=event_type,
                    data=data,
                    expires_at=expires_at
                )
                self.db.add(sync_event)
                self.db.flush()
                event_ids.append(sync_event.id)
            
            self.db.commit()
            return event_ids[0] if event_ids else 0
        else:
            # Create facility-wide event
            sync_event = SyncEvent(
                facility_id=facility_id,
                target_user_id=None,
                event_type=event_type,
                data=data,
                expires_at=expires_at
            )
            self.db.add(sync_event)
            self.db.commit()
            return sync_event.id
    
    async def get_recent_updates(
        self, 
        facility_id: int, 
        user_id: int, 
        since: Optional[datetime] = None
    ) -> List[SyncEventResponse]:
        """
        Description: Retrieves recent sync events for polling fallback.
        Purpose: Allows clients to catch up on missed events when SSE connection fails.
        """
        
        query = self.db.query(SyncEvent).filter(
            and_(
                SyncEvent.facility_id == facility_id,
                or_(
                    SyncEvent.target_user_id == user_id,
                    SyncEvent.target_user_id.is_(None)
                )
            )
        )
        
        if since:
            query = query.filter(SyncEvent.created_at > since)
        
        # Get events from last 24 hours if no since timestamp
        if not since:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            query = query.filter(SyncEvent.created_at > cutoff)
        
        events = query.order_by(desc(SyncEvent.created_at)).limit(100).all()
        
        return [
            SyncEventResponse(
                id=event.id,
                event_type=event.event_type,
                event_data=event.data,
                facility_id=event.facility_id,
                target_user_id=event.target_user_id,
                created_at=event.created_at,
                delivered=event.delivered
            )
            for event in events
        ]
    
    async def mark_event_delivered(self, event_id: int) -> bool:
        """
        Description: Marks sync event as successfully delivered.
        Purpose: Tracks delivery status for audit and retry logic.
        """
        
        event = self.db.query(SyncEvent).filter(SyncEvent.id == event_id).first()
        if event:
            event.delivered = True
            event.delivery_attempts += 1
            self.db.commit()
            return True
        return False
    
    async def cleanup_expired_events(self) -> int:
        """
        Description: Removes expired sync events from database.
        Purpose: Prevents database bloat by cleaning up old sync events.
        """
        
        cutoff = datetime.now(timezone.utc)
        expired_events = self.db.query(SyncEvent).filter(
            SyncEvent.expires_at < cutoff
        ).all()
        
        count = len(expired_events)
        for event in expired_events:
            self.db.delete(event)
        
        self.db.commit()
        logger.info(f"Cleaned up {count} expired sync events")
        return count 