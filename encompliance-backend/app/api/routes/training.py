"""
Training API Routes Module

This module provides API endpoints for training and certification management.
It handles training programs, staff management, assignments, materials, and completions.

Key functionalities:
- Training program CRUD operations
- Staff member management
- Training assignment tracking
- Training material management
- Training completion and certification
- Dashboard and analytics
- Push notifications

Dependencies:
- FastAPI: For API routing and validation
- SQLAlchemy: For database operations
- Pydantic: For request/response validation
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, case

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.training import (
    TrainingProgram as TrainingProgramModel,
    StaffMember as StaffMemberModel,
    TrainingAssignment as TrainingAssignmentModel,
    TrainingMaterial as TrainingMaterialModel,
    TrainingCompletion as TrainingCompletionModel,
    training_program_facility_types
)
from app.schemas.training import (
    TrainingProgram,
    TrainingProgramCreate,
    TrainingProgramUpdate,
    TrainingProgramListResponse,
    StaffMember,
    StaffMemberCreate,
    StaffMemberUpdate,
    StaffMemberListResponse,
    TrainingAssignment,
    TrainingAssignmentCreate,
    TrainingAssignmentUpdate,
    TrainingAssignmentListResponse,
    TrainingMaterial,
    TrainingMaterialCreate,
    TrainingMaterialUpdate,
    TrainingCompletion,
    TrainingCompletionCreate,
    TrainingCompletionUpdate,
    TrainingDashboard,
    TrainingNotificationCreate,
    BulkTrainingNotification,
    TrainingAssignmentBulkCreate
)
from app.services.training_calendar_integration_service import TrainingCalendarIntegrationService
from app.utils.access_control import can_access_feature
from app.utils.tiers import get_tier_from_subscription_status
from app.utils.preview_data import (
    get_sample_training_programs, 
    get_sample_staff_members, 
    get_sample_training_assignments,
    get_sample_training_completions
)

router = APIRouter()

# Test endpoint to verify routes are working
@router.get("/test")
async def test_training_routes():
    """Test endpoint to verify training routes are working."""
    return {"message": "Training routes are working!", "status": "success"}

# Training Programs Endpoints

@router.get("/programs", response_model=TrainingProgramListResponse)
async def get_training_programs(
    category: Optional[str] = None,
    is_mandatory: Optional[bool] = None,
    requires_certification: Optional[bool] = None,
    facility_type_id: Optional[int] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all training programs with filtering and pagination."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access training feature
    if not can_access_feature(user_tier, "training_certification"):
        # Return preview data for free users
        sample_programs = get_sample_training_programs()
        
        # Apply basic filtering to sample data
        filtered_programs = sample_programs
        if category:
            filtered_programs = [p for p in filtered_programs if p.get('category') == category]
        if is_mandatory is not None:
            filtered_programs = [p for p in filtered_programs if p.get('is_mandatory') == is_mandatory]
        if requires_certification is not None:
            filtered_programs = [p for p in filtered_programs if p.get('requires_certification') == requires_certification]
        if search:
            search_lower = search.lower()
            filtered_programs = [p for p in filtered_programs if 
                               search_lower in p.get('title', '').lower() or 
                               search_lower in p.get('description', '').lower()]
        
        # Apply pagination to sample data
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_programs = filtered_programs[start_idx:end_idx]
        
        return TrainingProgramListResponse(
            programs=paginated_programs,
            total=len(filtered_programs),
            page=page,
            per_page=per_page
        )
    
    # For paid users, return real data
    query = db.query(TrainingProgramModel).filter(
        TrainingProgramModel.created_by == current_user.id
    )
    
    if category:
        query = query.filter(TrainingProgramModel.category == category)
    if is_mandatory is not None:
        query = query.filter(TrainingProgramModel.is_mandatory == is_mandatory)
    if requires_certification is not None:
        query = query.filter(TrainingProgramModel.requires_certification == requires_certification)
    if is_active is not None:
        query = query.filter(TrainingProgramModel.is_active == is_active)
    if search:
        query = query.filter(
            or_(
                TrainingProgramModel.title.ilike(f"%{search}%"),
                TrainingProgramModel.description.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    programs = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return TrainingProgramListResponse(
        programs=programs,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/programs/{program_id}", response_model=TrainingProgram)
async def get_training_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific training program by ID."""
    program = db.query(TrainingProgramModel).filter(
        TrainingProgramModel.id == program_id,
        TrainingProgramModel.created_by == current_user.id
    ).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training program not found"
        )
    
    return program

@router.post("/programs", response_model=TrainingProgram)
async def create_training_program(
    program_data: TrainingProgramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new training program."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access training feature
    if not can_access_feature(user_tier, "training_certification"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Training & Certification management requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    program = TrainingProgramModel(
        **program_data.dict(exclude={'facility_type_ids'}),
        created_by=current_user.id
    )
    
    db.add(program)
    db.commit()
    db.refresh(program)
    
    return program

@router.put("/programs/{program_id}", response_model=TrainingProgram)
async def update_training_program(
    program_id: int,
    program_data: TrainingProgramUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a training program."""
    program = db.query(TrainingProgramModel).filter(
        TrainingProgramModel.id == program_id,
        TrainingProgramModel.created_by == current_user.id
    ).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training program not found"
        )
    
    update_data = program_data.dict(exclude_unset=True, exclude={'facility_type_ids'})
    for field, value in update_data.items():
        setattr(program, field, value)
    
    program.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(program)
    
    return program

@router.delete("/programs/{program_id}")
async def delete_training_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a training program."""
    program = db.query(TrainingProgramModel).filter(
        TrainingProgramModel.id == program_id,
        TrainingProgramModel.created_by == current_user.id
    ).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training program not found"
        )
    
    db.delete(program)
    db.commit()
    
    return {"message": "Training program deleted successfully"}

# Staff Members Endpoints

@router.get("/staff", response_model=StaffMemberListResponse)
async def get_staff_members(
    role: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all staff members with filtering and pagination."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access training feature
    if not can_access_feature(user_tier, "training_certification"):
        # Return preview data for free users
        sample_staff = get_sample_staff_members()
        
        # Apply basic filtering to sample data
        filtered_staff = sample_staff
        if role:
            filtered_staff = [s for s in filtered_staff if s.get('role') == role]
        if status:
            filtered_staff = [s for s in filtered_staff if s.get('status') == status]
        if department:
            filtered_staff = [s for s in filtered_staff if department.lower() in s.get('department', '').lower()]
        if search:
            search_lower = search.lower()
            filtered_staff = [s for s in filtered_staff if 
                            search_lower in s.get('first_name', '').lower() or 
                            search_lower in s.get('last_name', '').lower() or
                            search_lower in s.get('email', '').lower() or
                            search_lower in s.get('employee_id', '').lower()]
        
        # Apply pagination to sample data
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_staff = filtered_staff[start_idx:end_idx]
        
        return StaffMemberListResponse(
            staff_members=paginated_staff,
            total=len(filtered_staff),
            page=page,
            per_page=per_page
        )
    
    # For paid users, return real data
    query = db.query(StaffMemberModel).filter(
        StaffMemberModel.facility_administrator_id == current_user.id
    )
    
    if role:
        query = query.filter(StaffMemberModel.role == role)
    if status:
        query = query.filter(StaffMemberModel.status == status)
    if department:
        query = query.filter(StaffMemberModel.department.ilike(f"%{department}%"))
    if search:
        query = query.filter(
            or_(
                StaffMemberModel.first_name.ilike(f"%{search}%"),
                StaffMemberModel.last_name.ilike(f"%{search}%"),
                StaffMemberModel.email.ilike(f"%{search}%"),
                StaffMemberModel.employee_id.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    staff_members = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return StaffMemberListResponse(
        staff_members=staff_members,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/staff/{staff_id}", response_model=StaffMember)
async def get_staff_member(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific staff member by ID."""
    staff = db.query(StaffMemberModel).filter(
        StaffMemberModel.id == staff_id,
        StaffMemberModel.facility_administrator_id == current_user.id
    ).first()
    
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    
    return staff

@router.post("/staff", response_model=StaffMember)
async def create_staff_member(
    staff_data: StaffMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new staff member."""
    staff = StaffMemberModel(
        **staff_data.dict(),
        facility_administrator_id=current_user.id
    )
    
    db.add(staff)
    db.commit()
    db.refresh(staff)
    
    return staff

@router.put("/staff/{staff_id}", response_model=StaffMember)
async def update_staff_member(
    staff_id: int,
    staff_data: StaffMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a staff member."""
    staff = db.query(StaffMemberModel).filter(
        StaffMemberModel.id == staff_id,
        StaffMemberModel.facility_administrator_id == current_user.id
    ).first()
    
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    
    update_data = staff_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(staff, field, value)
    
    staff.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(staff)
    
    return staff

@router.delete("/staff/{staff_id}")
async def delete_staff_member(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a staff member."""
    staff = db.query(StaffMemberModel).filter(
        StaffMemberModel.id == staff_id,
        StaffMemberModel.facility_administrator_id == current_user.id
    ).first()
    
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    
    db.delete(staff)
    db.commit()
    
    return {"message": "Staff member deleted successfully"}

# Training Assignments Endpoints

@router.get("/assignments", response_model=TrainingAssignmentListResponse)
async def get_training_assignments(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    training_program_id: Optional[int] = None,
    staff_member_id: Optional[int] = None,
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    overdue_only: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all training assignments with filtering and pagination."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access training feature
    if not can_access_feature(user_tier, "training_certification"):
        # Return preview data for free users
        sample_assignments = get_sample_training_assignments()
        
        # Apply basic filtering to sample data
        filtered_assignments = sample_assignments
        if status:
            filtered_assignments = [a for a in filtered_assignments if a.get('status') == status]
        if priority:
            filtered_assignments = [a for a in filtered_assignments if a.get('priority') == priority]
        if training_program_id:
            filtered_assignments = [a for a in filtered_assignments if a.get('training_program_id') == f"preview-{training_program_id}"]
        if staff_member_id:
            filtered_assignments = [a for a in filtered_assignments if a.get('staff_member_id') == f"preview-{staff_member_id}"]
        if overdue_only:
            from datetime import datetime
            now = datetime.now()
            filtered_assignments = [a for a in filtered_assignments if 
                                  datetime.fromisoformat(a.get('due_date', '').replace('Z', '+00:00')) < now]
        
        # Apply pagination to sample data
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_assignments = filtered_assignments[start_idx:end_idx]
        
        return TrainingAssignmentListResponse(
            assignments=paginated_assignments,
            total=len(filtered_assignments),
            page=page,
            per_page=per_page
        )
    
    # For paid users, return real data
    query = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.assigned_by == current_user.id
    )
    
    if status:
        query = query.filter(TrainingAssignmentModel.status == status)
    if priority:
        query = query.filter(TrainingAssignmentModel.priority == priority)
    if training_program_id:
        query = query.filter(TrainingAssignmentModel.training_program_id == training_program_id)
    if staff_member_id:
        query = query.filter(TrainingAssignmentModel.staff_member_id == staff_member_id)
    if due_date_from:
        query = query.filter(TrainingAssignmentModel.due_date >= due_date_from)
    if due_date_to:
        query = query.filter(TrainingAssignmentModel.due_date <= due_date_to)
    if overdue_only:
        query = query.filter(TrainingAssignmentModel.due_date < datetime.utcnow())
    
    total = query.count()
    assignments = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return TrainingAssignmentListResponse(
        assignments=assignments,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/assignments/{assignment_id}", response_model=TrainingAssignment)
async def get_training_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific training assignment by ID."""
    assignment = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.id == assignment_id,
        TrainingAssignmentModel.assigned_by == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training assignment not found"
        )
    
    return assignment

@router.post("/assignments", response_model=TrainingAssignment)
async def create_training_assignment(
    assignment_data: TrainingAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new training assignment."""
    # Get facility_id from current user if they're a facility admin
    facility_id = None
    if hasattr(current_user, 'administered_facility') and current_user.administered_facility:
        facility_id = current_user.administered_facility.id
    elif hasattr(current_user, 'facility_id') and current_user.facility_id:
        facility_id = current_user.facility_id
    
    assignment = TrainingAssignmentModel(
        **assignment_data.dict(),
        assigned_by=current_user.id,
        assigned_date=datetime.utcnow(),
        facility_id=facility_id,
        assigned_by_admin_id=current_user.id if facility_id else None
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    # Create calendar event for the assignment
    try:
        training_program = db.query(TrainingProgramModel).filter(
            TrainingProgramModel.id == assignment.training_program_id
        ).first()
        
        if training_program:
            await TrainingCalendarIntegrationService.create_training_assignment_calendar_event(
                db=db,
                assignment=assignment,
                training_program=training_program,
                assigned_by_user=current_user
            )
    except Exception as e:
        # Don't fail the entire request if calendar creation fails
        print(f"Failed to create calendar event for training assignment {assignment.id}: {str(e)}")
    
    return assignment

@router.post("/assignments/bulk", response_model=List[TrainingAssignment])
async def create_bulk_training_assignments(
    assignment_data: TrainingAssignmentBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple training assignments."""
    # Get facility_id from current user if they're a facility admin
    facility_id = None
    if hasattr(current_user, 'administered_facility') and current_user.administered_facility:
        facility_id = current_user.administered_facility.id
    elif hasattr(current_user, 'facility_id') and current_user.facility_id:
        facility_id = current_user.facility_id
    
    assignments = []
    
    for staff_id in assignment_data.staff_member_ids:
        assignment = TrainingAssignmentModel(
            training_program_id=assignment_data.training_program_id,
            staff_member_id=staff_id,
            due_date=assignment_data.due_date,
            priority=assignment_data.priority,
            assignment_notes=assignment_data.assignment_notes,
            assigned_by=current_user.id,
            assigned_date=datetime.utcnow(),
            facility_id=facility_id,
            assigned_by_admin_id=current_user.id if facility_id else None
        )
        assignments.append(assignment)
        db.add(assignment)
    
    db.commit()
    
    for assignment in assignments:
        db.refresh(assignment)
    
    # Create calendar events for bulk assignments
    try:
        training_program = db.query(TrainingProgramModel).filter(
            TrainingProgramModel.id == assignment_data.training_program_id
        ).first()
        
        if training_program:
            await TrainingCalendarIntegrationService.create_bulk_assignment_calendar_events(
                db=db,
                assignments=assignments,
                training_program=training_program,
                assigned_by_user=current_user
            )
    except Exception as e:
        # Don't fail the entire request if calendar creation fails
        print(f"Failed to create calendar events for bulk training assignments: {str(e)}")
    
    return assignments

@router.put("/assignments/{assignment_id}", response_model=TrainingAssignment)
async def update_training_assignment(
    assignment_id: int,
    assignment_data: TrainingAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a training assignment."""
    assignment = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.id == assignment_id,
        TrainingAssignmentModel.assigned_by == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training assignment not found"
        )
    
    update_data = assignment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    assignment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assignment)
    
    # Update calendar event for the assignment
    try:
        training_program = db.query(TrainingProgramModel).filter(
            TrainingProgramModel.id == assignment.training_program_id
        ).first()
        
        if training_program:
            await TrainingCalendarIntegrationService.update_training_assignment_calendar_event(
                db=db,
                assignment=assignment,
                training_program=training_program
            )
    except Exception as e:
        # Don't fail the entire request if calendar update fails
        print(f"Failed to update calendar event for training assignment {assignment.id}: {str(e)}")
    
    return assignment

@router.delete("/assignments/{assignment_id}")
async def delete_training_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a training assignment."""
    assignment = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.id == assignment_id,
        TrainingAssignmentModel.assigned_by == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training assignment not found"
        )
    
    # Delete calendar event before deleting assignment
    try:
        await TrainingCalendarIntegrationService.delete_training_assignment_calendar_event(
            db=db,
            assignment_id=assignment_id
        )
    except Exception as e:
        # Don't fail the entire request if calendar deletion fails
        print(f"Failed to delete calendar event for training assignment {assignment_id}: {str(e)}")
    
    db.delete(assignment)
    db.commit()
    
    return {"message": "Training assignment deleted successfully"}

@router.post("/assignments/{assignment_id}/start", response_model=TrainingAssignment)
async def mark_assignment_started(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a training assignment as started."""
    assignment = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.id == assignment_id,
        TrainingAssignmentModel.assigned_by == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training assignment not found"
        )
    
    if assignment.status != 'assigned':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment can only be started from 'assigned' status"
        )
    
    assignment.status = 'in_progress'
    assignment.started_date = datetime.utcnow()
    assignment.last_accessed = datetime.utcnow()
    assignment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assignment)
    
    return assignment

@router.put("/assignments/{assignment_id}/progress", response_model=TrainingAssignment)
async def update_assignment_progress(
    assignment_id: int,
    progress_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update training assignment progress."""
    assignment = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.id == assignment_id,
        TrainingAssignmentModel.assigned_by == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training assignment not found"
        )
    
    progress_percentage = progress_data.get('progress_percentage', 0)
    
    if not isinstance(progress_percentage, (int, float)) or progress_percentage < 0 or progress_percentage > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Progress percentage must be between 0 and 100"
        )
    
    assignment.progress_percentage = progress_percentage
    assignment.last_accessed = datetime.utcnow()
    assignment.updated_at = datetime.utcnow()
    
    # Update status based on progress
    if progress_percentage == 100:
        assignment.status = 'completed'
        assignment.completed_date = datetime.utcnow()
    elif progress_percentage > 0 and assignment.status == 'assigned':
        assignment.status = 'in_progress'
        assignment.started_date = datetime.utcnow()
    
    db.commit()
    db.refresh(assignment)
    
    return assignment

# Training Materials Endpoints

@router.get("/programs/{program_id}/materials", response_model=List[TrainingMaterial])
async def get_training_materials_by_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all training materials for a specific program."""
    # First verify the program exists and belongs to the user
    program = db.query(TrainingProgramModel).filter(
        TrainingProgramModel.id == program_id,
        TrainingProgramModel.created_by == current_user.id
    ).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training program not found"
        )
    
    materials = db.query(TrainingMaterialModel).filter(
        TrainingMaterialModel.training_program_id == program_id
    ).order_by(TrainingMaterialModel.sort_order).all()
    
    return materials

@router.get("/materials/{material_id}", response_model=TrainingMaterial)
async def get_training_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training material by ID."""
    material = db.query(TrainingMaterialModel).join(
        TrainingProgramModel, TrainingMaterialModel.training_program_id == TrainingProgramModel.id
    ).filter(
        TrainingMaterialModel.id == material_id,
        TrainingProgramModel.created_by == current_user.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training material not found"
        )
    
    return material

@router.post("/materials", response_model=TrainingMaterial)
async def create_training_material(
    material_data: TrainingMaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new training material."""
    # Verify the program exists and belongs to the user
    program = db.query(TrainingProgramModel).filter(
        TrainingProgramModel.id == material_data.training_program_id,
        TrainingProgramModel.created_by == current_user.id
    ).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training program not found"
        )
    
    material = TrainingMaterialModel(
        **material_data.dict(),
        created_by=current_user.id
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    return material

@router.put("/materials/{material_id}", response_model=TrainingMaterial)
async def update_training_material(
    material_id: int,
    material_data: TrainingMaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a training material."""
    material = db.query(TrainingMaterialModel).join(
        TrainingProgramModel, TrainingMaterialModel.training_program_id == TrainingProgramModel.id
    ).filter(
        TrainingMaterialModel.id == material_id,
        TrainingProgramModel.created_by == current_user.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training material not found"
        )
    
    update_data = material_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)
    
    material.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(material)
    
    return material

@router.delete("/materials/{material_id}")
async def delete_training_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a training material."""
    material = db.query(TrainingMaterialModel).join(
        TrainingProgramModel, TrainingMaterialModel.training_program_id == TrainingProgramModel.id
    ).filter(
        TrainingMaterialModel.id == material_id,
        TrainingProgramModel.created_by == current_user.id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training material not found"
        )
    
    db.delete(material)
    db.commit()
    
    return {"message": "Training material deleted successfully"}

# Dashboard and Analytics Endpoints

@router.get("/dashboard", response_model=TrainingDashboard)
async def get_training_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training dashboard data."""
    # Get counts
    total_staff = db.query(StaffMemberModel).filter(
        StaffMemberModel.facility_administrator_id == current_user.id
    ).count()
    
    total_programs = db.query(TrainingProgramModel).filter(
        TrainingProgramModel.created_by == current_user.id
    ).count()
    
    total_assignments = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.assigned_by == current_user.id
    ).count()
    
    completed_assignments = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.assigned_by == current_user.id,
        TrainingAssignmentModel.status == "completed"
    ).count()
    
    overdue_assignments = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.assigned_by == current_user.id,
        TrainingAssignmentModel.due_date < datetime.utcnow(),
        TrainingAssignmentModel.status != "completed"
    ).count()
    
    due_soon_assignments = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.assigned_by == current_user.id,
        TrainingAssignmentModel.due_date <= datetime.utcnow() + timedelta(days=7),
        TrainingAssignmentModel.due_date >= datetime.utcnow(),
        TrainingAssignmentModel.status != "completed"
    ).count()
    
    # Calculate completion rate
    completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
    
    # Get recent completions
    recent_completions = db.query(TrainingCompletionModel).filter(
        TrainingCompletionModel.staff_member_id.in_(
            db.query(StaffMemberModel.id).filter(
                StaffMemberModel.facility_administrator_id == current_user.id
            )
        )
    ).order_by(desc(TrainingCompletionModel.completed_date)).limit(5).all()
    
    # Get upcoming due dates
    upcoming_due_dates = db.query(TrainingAssignmentModel).filter(
        TrainingAssignmentModel.assigned_by == current_user.id,
        TrainingAssignmentModel.due_date >= datetime.utcnow(),
        TrainingAssignmentModel.status != "completed"
    ).order_by(TrainingAssignmentModel.due_date).limit(5).all()
    
    return TrainingDashboard(
        total_staff=total_staff,
        total_programs=total_programs,
        total_assignments=total_assignments,
        completed_assignments=completed_assignments,
        overdue_assignments=overdue_assignments,
        due_soon_assignments=due_soon_assignments,
        completion_rate=completion_rate,
        certifications_expiring=0,  # TODO: Implement certification expiry logic
        recent_completions=recent_completions,
        upcoming_due_dates=upcoming_due_dates
    )

@router.get("/analytics")
async def get_training_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_from: Optional[str] = Query(None, description="Start date for analytics (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date for analytics (YYYY-MM-DD)")
):
    """Get comprehensive training analytics data."""
    
    # Base query for user's data
    staff_ids = db.query(StaffMemberModel.id).filter(
        StaffMemberModel.facility_administrator_id == current_user.id
    ).subquery()
    
    # Date filtering
    date_filter = []
    if date_from:
        date_filter.append(TrainingAssignmentModel.assigned_date >= datetime.fromisoformat(date_from))
    if date_to:
        date_filter.append(TrainingAssignmentModel.assigned_date <= datetime.fromisoformat(date_to))
    
    # Completion rates by program
    program_completion_rates = db.query(
        TrainingProgramModel.title,
        func.count(TrainingAssignmentModel.id).label('total_assignments'),
        func.count(
            case(
                (TrainingAssignmentModel.status == 'completed', 1)
            )
        ).label('completed_assignments')
    ).join(
        TrainingAssignmentModel, TrainingProgramModel.id == TrainingAssignmentModel.training_program_id
    ).filter(
        TrainingAssignmentModel.assigned_by == current_user.id,
        *date_filter
    ).group_by(TrainingProgramModel.id, TrainingProgramModel.title).all()
    
    completion_rates_by_program = {}
    for program in program_completion_rates:
        rate = (program.completed_assignments / program.total_assignments * 100) if program.total_assignments > 0 else 0
        completion_rates_by_program[program.title] = round(rate, 2)
    
    # Completion rates by department
    department_completion_rates = db.query(
        StaffMemberModel.department,
        func.count(TrainingAssignmentModel.id).label('total_assignments'),
        func.count(
            case(
                (TrainingAssignmentModel.status == 'completed', 1)
            )
        ).label('completed_assignments')
    ).join(
        TrainingAssignmentModel, StaffMemberModel.id == TrainingAssignmentModel.staff_member_id
    ).filter(
        StaffMemberModel.facility_administrator_id == current_user.id,
        *date_filter
    ).group_by(StaffMemberModel.department).all()
    
    completion_rates_by_department = {}
    for dept in department_completion_rates:
        rate = (dept.completed_assignments / dept.total_assignments * 100) if dept.total_assignments > 0 else 0
        completion_rates_by_department[dept.department or 'Unassigned'] = round(rate, 2)
    
    # Average completion time by program
    avg_completion_times = db.query(
        TrainingProgramModel.title,
        func.avg(TrainingCompletionModel.time_spent_minutes).label('avg_time')
    ).join(
        TrainingAssignmentModel, TrainingProgramModel.id == TrainingAssignmentModel.training_program_id
    ).join(
        TrainingCompletionModel, TrainingAssignmentModel.id == TrainingCompletionModel.training_assignment_id
    ).filter(
        TrainingAssignmentModel.assigned_by == current_user.id,
        TrainingCompletionModel.completion_status == 'completed'
    ).group_by(TrainingProgramModel.id, TrainingProgramModel.title).all()
    
    average_completion_time = {}
    for program in avg_completion_times:
        average_completion_time[program.title] = round(program.avg_time or 0, 2)
    
    # Overdue trends (last 12 months)
    overdue_trends = []
    for i in range(12):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        
        overdue_count = db.query(TrainingAssignmentModel).filter(
            TrainingAssignmentModel.assigned_by == current_user.id,
            TrainingAssignmentModel.due_date >= month_start,
            TrainingAssignmentModel.due_date < month_end,
            TrainingAssignmentModel.status != 'completed',
            TrainingAssignmentModel.due_date < datetime.utcnow()
        ).count()
        
        overdue_trends.append({
            'month': month_start.strftime('%Y-%m'),
            'overdue_count': overdue_count
        })
    
    # Certification expiry forecast (next 6 months)
    certification_expiry_forecast = []
    for i in range(6):
        month_start = datetime.utcnow().replace(day=1) + timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        
        expiring_count = db.query(TrainingCompletionModel).filter(
            TrainingCompletionModel.staff_member_id.in_(staff_ids),
            TrainingCompletionModel.expires_date >= month_start,
            TrainingCompletionModel.expires_date < month_end,
            TrainingCompletionModel.certificate_status == 'issued'
        ).count()
        
        certification_expiry_forecast.append({
            'month': month_start.strftime('%Y-%m'),
            'expiring_count': expiring_count
        })
    
    # Training effectiveness metrics
    effectiveness_metrics = {
        'average_score': db.query(func.avg(TrainingCompletionModel.final_score)).filter(
            TrainingCompletionModel.staff_member_id.in_(staff_ids),
            TrainingCompletionModel.final_score.isnot(None)
        ).scalar() or 0,
        'pass_rate': 0,  # Calculate based on passing scores
        'retry_rate': 0   # Calculate based on multiple attempts
    }
    
    # Pass rate calculation
    total_completions = db.query(TrainingCompletionModel).filter(
        TrainingCompletionModel.staff_member_id.in_(staff_ids)
    ).count()
    
    passed_completions = db.query(TrainingCompletionModel).filter(
        TrainingCompletionModel.staff_member_id.in_(staff_ids),
        TrainingCompletionModel.completion_status == 'completed'
    ).count()
    
    effectiveness_metrics['pass_rate'] = (passed_completions / total_completions * 100) if total_completions > 0 else 0
    
    return {
        'completion_rates_by_program': completion_rates_by_program,
        'completion_rates_by_department': completion_rates_by_department,
        'average_completion_time': average_completion_time,
        'overdue_trends': overdue_trends,
        'certification_expiry_forecast': certification_expiry_forecast,
        'effectiveness_metrics': effectiveness_metrics,
        'summary_stats': {
            'total_programs_analyzed': len(completion_rates_by_program),
            'total_departments': len(completion_rates_by_department),
            'analysis_period': {
                'from': date_from or 'All time',
                'to': date_to or 'Present'
            }
        }
    }

@router.get("/reports/compliance")
async def generate_compliance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    report_type: str = Query(..., description="Type of report: staff_summary, program_compliance, certification_status"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    program_id: Optional[int] = Query(None, description="Filter by training program"),
    format: str = Query("json", description="Report format: json, csv")
):
    """Generate compliance reports for regulatory requirements."""
    
    # Base filters
    staff_filter = [StaffMemberModel.facility_administrator_id == current_user.id]
    assignment_filter = [TrainingAssignmentModel.assigned_by == current_user.id]
    
    if department:
        staff_filter.append(StaffMemberModel.department == department)
    
    if program_id:
        assignment_filter.append(TrainingAssignmentModel.training_program_id == program_id)
    
    if date_from:
        assignment_filter.append(TrainingAssignmentModel.assigned_date >= datetime.fromisoformat(date_from))
    
    if date_to:
        assignment_filter.append(TrainingAssignmentModel.assigned_date <= datetime.fromisoformat(date_to))
    
    if report_type == "staff_summary":
        # Staff training summary report
        staff_data = db.query(
            StaffMemberModel.id,
            StaffMemberModel.first_name,
            StaffMemberModel.last_name,
            StaffMemberModel.employee_id,
            StaffMemberModel.department,
            StaffMemberModel.role,
            func.count(TrainingAssignmentModel.id).label('total_assignments'),
            func.count(
                case(
                    (TrainingAssignmentModel.status == 'completed', 1)
                )
            ).label('completed_assignments'),
            func.count(
                case(
                    (TrainingAssignmentModel.status == 'overdue', 1)
                )
            ).label('overdue_assignments')
        ).outerjoin(
            TrainingAssignmentModel, StaffMemberModel.id == TrainingAssignmentModel.staff_member_id
        ).filter(
            *staff_filter
        ).group_by(StaffMemberModel.id).all()
        
        report_data = []
        for staff in staff_data:
            completion_rate = (staff.completed_assignments / staff.total_assignments * 100) if staff.total_assignments > 0 else 0
            report_data.append({
                'employee_id': staff.employee_id,
                'name': f"{staff.first_name} {staff.last_name}",
                'department': staff.department,
                'role': staff.role,
                'total_assignments': staff.total_assignments,
                'completed_assignments': staff.completed_assignments,
                'overdue_assignments': staff.overdue_assignments,
                'completion_rate': round(completion_rate, 2),
                'compliance_status': 'Compliant' if staff.overdue_assignments == 0 else 'Non-Compliant'
            })
    
    elif report_type == "program_compliance":
        # Program compliance report
        program_data = db.query(
            TrainingProgramModel.id,
            TrainingProgramModel.title,
            TrainingProgramModel.category,
            TrainingProgramModel.is_mandatory,
            func.count(TrainingAssignmentModel.id).label('total_assignments'),
            func.count(
                case(
                    (TrainingAssignmentModel.status == 'completed', 1)
                )
            ).label('completed_assignments'),
            func.count(
                case(
                    (TrainingAssignmentModel.status == 'overdue', 1)
                )
            ).label('overdue_assignments')
        ).join(
            TrainingAssignmentModel, TrainingProgramModel.id == TrainingAssignmentModel.training_program_id
        ).filter(
            TrainingProgramModel.created_by == current_user.id,
            *assignment_filter
        ).group_by(TrainingProgramModel.id).all()
        
        report_data = []
        for program in program_data:
            completion_rate = (program.completed_assignments / program.total_assignments * 100) if program.total_assignments > 0 else 0
            report_data.append({
                'program_title': program.title,
                'category': program.category,
                'is_mandatory': program.is_mandatory,
                'total_assignments': program.total_assignments,
                'completed_assignments': program.completed_assignments,
                'overdue_assignments': program.overdue_assignments,
                'completion_rate': round(completion_rate, 2),
                'compliance_status': 'Compliant' if completion_rate >= 95 else 'Needs Attention'
            })
    
    elif report_type == "certification_status":
        # Certification status report
        cert_data = db.query(
            StaffMemberModel.first_name,
            StaffMemberModel.last_name,
            StaffMemberModel.employee_id,
            TrainingProgramModel.title,
            TrainingCompletionModel.certificate_number,
            TrainingCompletionModel.certificate_issued_date,
            TrainingCompletionModel.expires_date,
            TrainingCompletionModel.certificate_status
        ).join(
            TrainingCompletionModel, StaffMemberModel.id == TrainingCompletionModel.staff_member_id
        ).join(
            TrainingProgramModel, TrainingCompletionModel.training_program_id == TrainingProgramModel.id
        ).filter(
            StaffMemberModel.facility_administrator_id == current_user.id,
            TrainingProgramModel.requires_certification == True
        ).all()
        
        report_data = []
        for cert in cert_data:
            days_until_expiry = None
            if cert.expires_date:
                days_until_expiry = (cert.expires_date - datetime.utcnow().date()).days
            
            report_data.append({
                'employee_id': cert.employee_id,
                'name': f"{cert.first_name} {cert.last_name}",
                'program_title': cert.title,
                'certificate_number': cert.certificate_number,
                'issued_date': cert.certificate_issued_date.isoformat() if cert.certificate_issued_date else None,
                'expires_date': cert.expires_date.isoformat() if cert.expires_date else None,
                'days_until_expiry': days_until_expiry,
                'status': cert.certificate_status,
                'compliance_status': 'Valid' if cert.certificate_status == 'issued' and (not cert.expires_date or days_until_expiry > 0) else 'Expired/Invalid'
            })
    
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    return {
        'report_type': report_type,
        'generated_at': datetime.utcnow().isoformat(),
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
            'department': department,
            'program_id': program_id
        },
        'data': report_data,
        'summary': {
            'total_records': len(report_data),
            'report_period': f"{date_from or 'All time'} to {date_to or 'Present'}"
        }
    }

# Placeholder endpoints for materials, completions, and notifications
# These would be fully implemented based on the schemas

@router.get("/completions")
async def get_training_completions():
    """Get training completions."""
    return {"message": "Training completions endpoint - to be implemented"}

@router.post("/notifications")
async def send_training_notification(notification_data: TrainingNotificationCreate):
    """Send training notification."""
    return {"message": "Training notification sent"}

@router.post("/notifications/bulk")
async def send_bulk_training_notifications(notification_data: BulkTrainingNotification):
    """Send bulk training notifications."""
    return {"success_count": len(notification_data.staff_member_ids)} 