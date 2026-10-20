"""
Description: Note service for handling note operations.
Purpose: Provides business logic for creating, retrieving, updating, and deleting notes.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate


class NoteService:
    @staticmethod
    async def create_note(db: Session, note_data: NoteCreate, user_id: int) -> Note:
        """Create a new note for a user."""
        db_note = Note(
            title=note_data.title,
            content=note_data.content,
            is_pinned=note_data.is_pinned,
            is_archived=note_data.is_archived,
            user_id=user_id
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        return db_note

    @staticmethod
    async def get_notes(
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        show_archived: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get all notes for a user with pagination, search, and sorting."""
        query = db.query(Note).filter(Note.user_id == user_id)
        
        # Apply archived filter only if explicitly specified
        if show_archived is not None:
            if not show_archived:
                query = query.filter(Note.is_archived == False)
            # If show_archived is True, return all notes (no additional filter needed)
            
        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Note.title.ilike(search_term)) | 
                (Note.content.ilike(search_term))
            )
            
        # Get total count for pagination
        total = query.count()
        
        # Apply sorting
        if sort_order.lower() == "asc":
            query = query.order_by(asc(getattr(Note, sort_by)))
        else:
            query = query.order_by(desc(getattr(Note, sort_by)))
            
        # Always show pinned notes first
        query = query.order_by(desc(Note.is_pinned))
        
        # Apply pagination
        notes = query.offset(skip).limit(limit).all()
        
        return {
            "notes": notes,
            "total": total
        }

    @staticmethod
    async def get_note(db: Session, note_id: int, user_id: int) -> Optional[Note]:
        """Get a specific note by ID for a user."""
        return db.query(Note).filter(
            Note.id == note_id,
            Note.user_id == user_id
        ).first()

    @staticmethod
    async def update_note(
        db: Session, 
        note_id: int, 
        note_data: NoteUpdate, 
        user_id: int
    ) -> Optional[Note]:
        """Update a note for a user."""
        db_note = await NoteService.get_note(db, note_id, user_id)
        if not db_note:
            return None
            
        update_data = note_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_note, key, value)
            
        db.commit()
        db.refresh(db_note)
        return db_note

    @staticmethod
    async def delete_note(db: Session, note_id: int, user_id: int) -> bool:
        """Delete a note for a user."""
        db_note = await NoteService.get_note(db, note_id, user_id)
        if not db_note:
            return False
            
        db.delete(db_note)
        db.commit()
        return True

    @staticmethod
    async def archive_note(db: Session, note_id: int, user_id: int) -> Optional[Note]:
        """Archive a note for a user."""
        db_note = await NoteService.get_note(db, note_id, user_id)
        if not db_note:
            return None
            
        db_note.is_archived = True
        db.commit()
        db.refresh(db_note)
        return db_note

    @staticmethod
    async def unarchive_note(db: Session, note_id: int, user_id: int) -> Optional[Note]:
        """Unarchive a note for a user."""
        db_note = await NoteService.get_note(db, note_id, user_id)
        if not db_note:
            return None
            
        db_note.is_archived = False
        db.commit()
        db.refresh(db_note)
        return db_note
        
    @staticmethod
    async def pin_note(db: Session, note_id: int, user_id: int) -> Optional[Note]:
        """Pin a note for a user."""
        db_note = await NoteService.get_note(db, note_id, user_id)
        if not db_note:
            return None
            
        db_note.is_pinned = True
        db.commit()
        db.refresh(db_note)
        return db_note
        
    @staticmethod
    async def unpin_note(db: Session, note_id: int, user_id: int) -> Optional[Note]:
        """Unpin a note for a user."""
        db_note = await NoteService.get_note(db, note_id, user_id)
        if not db_note:
            return None
            
        db_note.is_pinned = False
        db.commit()
        db.refresh(db_note)
        return db_note

    @staticmethod
    async def delete_all_notes(db: Session, user_id: int, archived_only: bool = False) -> int:
        """Delete all notes for a user. Returns count of deleted notes."""
        query = db.query(Note).filter(Note.user_id == user_id)
        
        if archived_only:
            query = query.filter(Note.is_archived == True)
        
        # Get count before deletion
        count = query.count()
        
        # Delete all matching notes
        query.delete()
        db.commit()
        
        return count

    @staticmethod
    async def archive_all_notes(db: Session, user_id: int) -> int:
        """Archive all non-archived notes for a user. Returns count of archived notes."""
        query = db.query(Note).filter(
            Note.user_id == user_id,
            Note.is_archived == False
        )
        
        # Get count before archiving
        count = query.count()
        
        # Archive all matching notes
        query.update({"is_archived": True})
        db.commit()
        
        return count 