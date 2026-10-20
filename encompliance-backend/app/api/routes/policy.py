"""
Policy Management API Routes

This module defines FastAPI routes for policy management functionality.
Includes endpoints for policies, assignments, and acknowledgments.

Key functionalities:
- Policy CRUD operations
- Policy assignment management
- Policy acknowledgment tracking
- Compliance reporting
- Dashboard analytics

Dependencies:
- fastapi: For API route definitions
- sqlalchemy: For database operations
- datetime: For timestamp handling
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.policy import Policy as PolicyModel
from app.models.policy_assignment import PolicyAssignment as PolicyAssignmentModel
from app.models.policy_acknowledgment import PolicyAcknowledgment as PolicyAcknowledmentModel
from app.models.staff_member import StaffMember as StaffMemberModel
from app.schemas.policy import (
    Policy, PolicyCreate, PolicyUpdate,
    PolicyAssignment, PolicyAssignmentCreate, PolicyAssignmentUpdate,
    PolicyAcknowledgment, PolicyAcknowledgmentCreate, PolicyAcknowledgmentUpdate,
    PolicyDashboard, PolicyAnalytics, PolicyComplianceReport
)
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType, NotificationPriority
from app.schemas.notification import NotificationCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy", tags=["policy"])

# Policy CRUD Operations

@router.post("/", response_model=Policy)
async def create_policy(
    policy_data: PolicyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new policy."""
    
    # Create policy
    policy = PolicyModel(
        **policy_data.dict(),
        created_by=current_user.id,
        facility_administrator_id=current_user.id
    )
    
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    # Log policy creation
    logger.info(f"Policy created: id={policy.id}, title={policy.title}, user_id={current_user.id}, ip={request.client.host}")
    
    return policy

@router.get("/", response_model=List[Policy])
async def get_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in title, description, and category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page")
):
    """Get policies for the current facility administrator with search functionality."""
    
    query = db.query(PolicyModel).filter(
        PolicyModel.facility_administrator_id == current_user.id
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                PolicyModel.title.ilike(search_term),
                PolicyModel.description.ilike(search_term),
                PolicyModel.category.ilike(search_term),
                PolicyModel.content_summary.ilike(search_term)
            )
        )
    
    # Apply filters
    if category:
        query = query.filter(PolicyModel.category == category)
    if status:
        query = query.filter(PolicyModel.status == status)
    if is_active is not None:
        query = query.filter(PolicyModel.is_active == is_active)
    
    # Pagination
    offset = (page - 1) * per_page
    policies = query.order_by(desc(PolicyModel.created_at)).offset(offset).limit(per_page).all()
    
    return policies

@router.get("/{policy_id}", response_model=Policy)
async def get_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific policy."""
    
    policy = db.query(PolicyModel).filter(
        PolicyModel.id == policy_id,
        PolicyModel.facility_administrator_id == current_user.id
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return policy

@router.put("/{policy_id}", response_model=Policy)
async def update_policy(
    policy_id: int,
    policy_data: PolicyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a policy."""
    
    policy = db.query(PolicyModel).filter(
        PolicyModel.id == policy_id,
        PolicyModel.facility_administrator_id == current_user.id
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Track changes for audit
    changes = []
    update_data = policy_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        old_value = getattr(policy, field, None)
        if old_value != value:
            changes.append(f"{field}: {old_value} -> {value}")
        setattr(policy, field, value)
    
    db.commit()
    db.refresh(policy)
    
    # Log policy update
    logger.info(f"Policy updated: id={policy.id}, title={policy.title}, user_id={current_user.id}, changes={changes}, ip={request.client.host}")
    
    return policy

@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a policy."""
    
    policy = db.query(PolicyModel).filter(
        PolicyModel.id == policy_id,
        PolicyModel.facility_administrator_id == current_user.id
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy_title = policy.title
    db.delete(policy)
    db.commit()
    
    # Log policy deletion
    logger.info(f"Policy deleted: id={policy_id}, title={policy_title}, user_id={current_user.id}, ip={request.client.host}")
    
    return {"message": "Policy deleted successfully"}

# Policy Assignment Operations

@router.post("/assignments", response_model=List[PolicyAssignment])
async def create_policy_assignments(
    assignment_data: PolicyAssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create policy assignments for multiple staff members."""
    
    # Verify policy exists and belongs to current user
    policy = db.query(PolicyModel).filter(
        PolicyModel.id == assignment_data.policy_id,
        PolicyModel.facility_administrator_id == current_user.id
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Verify staff members exist and belong to current user
    staff_members = db.query(StaffMemberModel).filter(
        StaffMemberModel.id.in_(assignment_data.staff_member_ids),
        StaffMemberModel.facility_administrator_id == current_user.id
    ).all()
    
    if len(staff_members) != len(assignment_data.staff_member_ids):
        raise HTTPException(status_code=400, detail="Some staff members not found")
    
    # Create assignments
    assignments = []
    for staff_member in staff_members:
        assignment = PolicyAssignmentModel(
            policy_id=assignment_data.policy_id,
            staff_member_id=staff_member.id,
            assigned_by=current_user.id,
            due_date=assignment_data.due_date,
            priority=assignment_data.priority,
            assignment_reason=assignment_data.assignment_reason,
            custom_message=assignment_data.custom_message,
            requires_immediate_attention=assignment_data.requires_immediate_attention,
            is_mandatory=assignment_data.is_mandatory,
            compliance_deadline=assignment_data.compliance_deadline,
            regulatory_requirement=assignment_data.regulatory_requirement,
            assignment_notes=assignment_data.assignment_notes
        )
        
        db.add(assignment)
        assignments.append(assignment)
    
    db.commit()
    
    # Refresh all assignments and send notifications
    for assignment in assignments:
        db.refresh(assignment)
        
        # Get staff member user account by email if exists
        staff_user = db.query(User).filter(User.email == staff_member.email).first() if staff_member.email else None
        
        if staff_user:
            # Create notification for policy assignment
            try:
                priority = NotificationPriority.HIGH if assignment_data.requires_immediate_attention else NotificationPriority.MEDIUM
                # Format due_date safely (handle both datetime and string)
                due_date_str = assignment.due_date.strftime('%Y-%m-%d') if isinstance(assignment.due_date, datetime) else str(assignment.due_date)
                notification_data = NotificationCreate(
                    title=f"New Policy Assignment: {policy.title}",
                    message=assignment_data.custom_message or f"You have been assigned to review and acknowledge the policy: {policy.title}. Due date: {due_date_str}",
                    type=NotificationType.SYSTEM,
                    priority=priority,
                    related_id=str(assignment.id),
                    related_type="policy_assignment",
                    action_url=f"/policies/{policy.id}/acknowledge"
                )
                await NotificationService.create_notification(
                    db, 
                    notification_data, 
                    staff_user.id,
                    send_email=True,
                    send_push=True
                )
            except Exception as e:
                logger.error(f"Failed to send notification for policy assignment {assignment.id}: {e}")
    
    # Log assignment creation
    logger.info(f"Policy assignments created: policy_id={policy.id}, count={len(assignments)}, user_id={current_user.id}, ip={request.client.host}")
    
    return assignments

@router.put("/assignments/{assignment_id}/view", response_model=PolicyAssignment)
async def mark_policy_viewed(
    assignment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    time_spent_reading: Optional[int] = Query(None, description="Time spent reading in minutes")
):
    """Mark a policy assignment as viewed (read receipt tracking)."""
    
    # Get assignment with policy - allow staff members to mark their own assignments as viewed
    assignment = db.query(PolicyAssignmentModel).join(
        PolicyModel, PolicyAssignmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyAssignmentModel.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Policy assignment not found")
    
    # Get policy to verify access
    policy = db.query(PolicyModel).filter(PolicyModel.id == assignment.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Verify access: either admin owns the policy or staff member is assigned
    is_admin = policy.facility_administrator_id == current_user.id
    staff_member = db.query(StaffMemberModel).filter(StaffMemberModel.id == assignment.staff_member_id).first()
    is_assigned_staff = staff_member and staff_member.email == current_user.email
    
    if not (is_admin or is_assigned_staff):
        raise HTTPException(status_code=403, detail="You do not have permission to view this assignment")
    
    # Update viewed_date if not already set
    if not assignment.viewed_date:
        assignment.viewed_date = datetime.utcnow()
    
    # Update time spent reading if provided
    if time_spent_reading is not None:
        assignment.time_spent_reading = time_spent_reading
    
    db.commit()
    db.refresh(assignment)
    
    # Log read receipt
    logger.info(f"Policy viewed: assignment_id={assignment_id}, policy_id={assignment.policy_id}, user_id={current_user.id}, ip={request.client.host}")
    
    return assignment

@router.get("/assignments", response_model=List[PolicyAssignment])
async def get_policy_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    policy_id: Optional[int] = Query(None, description="Filter by policy ID"),
    staff_member_id: Optional[int] = Query(None, description="Filter by staff member ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    overdue_only: bool = Query(False, description="Show only overdue assignments"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page")
):
    """Get policy assignments."""
    
    query = db.query(PolicyAssignmentModel).join(
        PolicyModel, PolicyAssignmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyModel.facility_administrator_id == current_user.id
    )
    
    # Apply filters
    if policy_id:
        query = query.filter(PolicyAssignmentModel.policy_id == policy_id)
    if staff_member_id:
        query = query.filter(PolicyAssignmentModel.staff_member_id == staff_member_id)
    if status:
        query = query.filter(PolicyAssignmentModel.status == status)
    if overdue_only:
        query = query.filter(
            PolicyAssignmentModel.due_date < datetime.utcnow(),
            PolicyAssignmentModel.status != "acknowledged"
        )
    
    # Pagination
    offset = (page - 1) * per_page
    assignments = query.order_by(desc(PolicyAssignmentModel.created_at)).offset(offset).limit(per_page).all()
    
    return assignments

@router.put("/assignments/{assignment_id}", response_model=PolicyAssignment)
async def update_policy_assignment(
    assignment_id: int,
    assignment_data: PolicyAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a policy assignment."""
    
    assignment = db.query(PolicyAssignmentModel).join(
        PolicyModel, PolicyAssignmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyAssignmentModel.id == assignment_id,
        PolicyModel.facility_administrator_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Policy assignment not found")
    
    # Update fields
    update_data = assignment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    db.commit()
    db.refresh(assignment)
    
    return assignment

# Policy Acknowledgment Operations

@router.post("/acknowledgments", response_model=PolicyAcknowledgment)
async def create_policy_acknowledgment(
    acknowledgment_data: PolicyAcknowledgmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a policy acknowledgment."""
    
    # Get assignment with policy - allow staff members to acknowledge their own assignments
    assignment = db.query(PolicyAssignmentModel).join(
        PolicyModel, PolicyAssignmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyAssignmentModel.id == acknowledgment_data.policy_assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Policy assignment not found")
    
    # Get policy to verify access
    policy = db.query(PolicyModel).filter(PolicyModel.id == assignment.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Verify access: either admin owns the policy or staff member is assigned
    is_admin = policy.facility_administrator_id == current_user.id
    staff_member = db.query(StaffMemberModel).filter(StaffMemberModel.id == assignment.staff_member_id).first()
    is_assigned_staff = staff_member and staff_member.email == current_user.email
    
    if not (is_admin or is_assigned_staff):
        raise HTTPException(status_code=403, detail="You do not have permission to acknowledge this policy")
    
    # Check if already acknowledged
    existing_ack = db.query(PolicyAcknowledmentModel).filter(
        PolicyAcknowledmentModel.policy_assignment_id == acknowledgment_data.policy_assignment_id,
        PolicyAcknowledmentModel.status == "acknowledged"
    ).first()
    
    if existing_ack:
        raise HTTPException(status_code=400, detail="Policy already acknowledged")
    
    # Create acknowledgment
    acknowledgment = PolicyAcknowledmentModel(
        policy_id=assignment.policy_id,
        staff_member_id=assignment.staff_member_id,
        policy_assignment_id=assignment.id,
        acknowledged_date=datetime.utcnow(),
        acknowledgment_method=acknowledgment_data.acknowledgment_method,
        status="acknowledged",
        digital_signature=acknowledgment_data.digital_signature,
        signature_metadata=acknowledgment_data.signature_metadata,
        ip_address=acknowledgment_data.ip_address or request.client.host,
        user_agent=acknowledgment_data.user_agent or request.headers.get("user-agent"),
        device_fingerprint=acknowledgment_data.device_fingerprint,
        geolocation=acknowledgment_data.geolocation,
        acknowledgment_text=acknowledgment_data.acknowledgment_text,
        witness_name=acknowledgment_data.witness_name,
        witness_signature=acknowledgment_data.witness_signature,
        notes=acknowledgment_data.notes
    )
    
    db.add(acknowledgment)
    
    # Update assignment status
    assignment.status = "acknowledged"
    assignment.acknowledged_date = datetime.utcnow()
    
    db.commit()
    db.refresh(acknowledgment)
    
    # Get policy and notify facility administrator
    policy = db.query(PolicyModel).filter(PolicyModel.id == assignment.policy_id).first()
    if policy and policy.facility_administrator_id:
        try:
            admin_user = db.query(User).filter(User.id == policy.facility_administrator_id).first()
            staff_member = db.query(StaffMemberModel).filter(StaffMemberModel.id == assignment.staff_member_id).first()
            
            if admin_user and staff_member:
                notification_data = NotificationCreate(
                    title=f"Policy Acknowledged: {policy.title}",
                    message=f"{staff_member.first_name} {staff_member.last_name} has acknowledged the policy: {policy.title}",
                    type=NotificationType.SYSTEM,
                    priority=NotificationPriority.LOW,
                    related_id=str(acknowledgment.id),
                    related_type="policy_acknowledgment",
                    action_url=f"/policies/{policy.id}/acknowledgments"
                )
                await NotificationService.create_notification(
                    db,
                    notification_data,
                    admin_user.id,
                    send_email=False,
                    send_push=False
                )
        except Exception as e:
            logger.error(f"Failed to send notification for policy acknowledgment {acknowledgment.id}: {e}")
    
    # Log acknowledgment
    logger.info(f"Policy acknowledged: policy_id={assignment.policy_id}, assignment_id={assignment.id}, user_id={current_user.id}, ip={request.client.host}")
    
    return acknowledgment

@router.get("/acknowledgments", response_model=List[PolicyAcknowledgment])
async def get_policy_acknowledgments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    policy_id: Optional[int] = Query(None, description="Filter by policy ID"),
    staff_member_id: Optional[int] = Query(None, description="Filter by staff member ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page")
):
    """Get policy acknowledgments."""
    
    query = db.query(PolicyAcknowledmentModel).join(
        PolicyModel, PolicyAcknowledmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyModel.facility_administrator_id == current_user.id
    )
    
    # Apply filters
    if policy_id:
        query = query.filter(PolicyAcknowledmentModel.policy_id == policy_id)
    if staff_member_id:
        query = query.filter(PolicyAcknowledmentModel.staff_member_id == staff_member_id)
    if status:
        query = query.filter(PolicyAcknowledmentModel.status == status)
    
    # Pagination
    offset = (page - 1) * per_page
    acknowledgments = query.order_by(desc(PolicyAcknowledmentModel.created_at)).offset(offset).limit(per_page).all()
    
    return acknowledgments

# Dashboard and Analytics

@router.get("/dashboard", response_model=PolicyDashboard)
async def get_policy_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get policy dashboard data."""
    
    # Get policy counts
    total_policies = db.query(PolicyModel).filter(
        PolicyModel.facility_administrator_id == current_user.id
    ).count()
    
    active_policies = db.query(PolicyModel).filter(
        PolicyModel.facility_administrator_id == current_user.id,
        PolicyModel.status == "active"
    ).count()
    
    draft_policies = db.query(PolicyModel).filter(
        PolicyModel.facility_administrator_id == current_user.id,
        PolicyModel.status == "draft"
    ).count()
    
    expired_policies = db.query(PolicyModel).filter(
        PolicyModel.facility_administrator_id == current_user.id,
        PolicyModel.status == "expired"
    ).count()
    
    # Get assignment counts
    total_assignments = db.query(PolicyAssignmentModel).join(
        PolicyModel, PolicyAssignmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyModel.facility_administrator_id == current_user.id
    ).count()
    
    pending_acknowledgments = db.query(PolicyAssignmentModel).join(
        PolicyModel, PolicyAssignmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyModel.facility_administrator_id == current_user.id,
        PolicyAssignmentModel.status == "assigned"
    ).count()
    
    overdue_acknowledgments = db.query(PolicyAssignmentModel).join(
        PolicyModel, PolicyAssignmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyModel.facility_administrator_id == current_user.id,
        PolicyAssignmentModel.due_date < datetime.utcnow(),
        PolicyAssignmentModel.status != "acknowledged"
    ).count()
    
    # Calculate acknowledgment rate
    acknowledged_assignments = db.query(PolicyAssignmentModel).join(
        PolicyModel, PolicyAssignmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyModel.facility_administrator_id == current_user.id,
        PolicyAssignmentModel.status == "acknowledged"
    ).count()
    
    acknowledgment_rate = (acknowledged_assignments / total_assignments * 100) if total_assignments > 0 else 0
    
    # Policies expiring soon (next 30 days)
    policies_expiring_soon = db.query(PolicyModel).filter(
        PolicyModel.facility_administrator_id == current_user.id,
        PolicyModel.expiry_date.between(datetime.utcnow(), datetime.utcnow() + timedelta(days=30))
    ).count()
    
    # Recent acknowledgments
    recent_acknowledgments = db.query(PolicyAcknowledmentModel).join(
        PolicyModel, PolicyAcknowledmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyModel.facility_administrator_id == current_user.id
    ).order_by(desc(PolicyAcknowledmentModel.created_at)).limit(5).all()
    
    # Overdue assignments
    overdue_assignments = db.query(PolicyAssignmentModel).join(
        PolicyModel, PolicyAssignmentModel.policy_id == PolicyModel.id
    ).filter(
        PolicyModel.facility_administrator_id == current_user.id,
        PolicyAssignmentModel.due_date < datetime.utcnow(),
        PolicyAssignmentModel.status != "acknowledged"
    ).order_by(PolicyAssignmentModel.due_date).limit(10).all()
    
    return PolicyDashboard(
        total_policies=total_policies,
        active_policies=active_policies,
        draft_policies=draft_policies,
        expired_policies=expired_policies,
        total_assignments=total_assignments,
        pending_acknowledgments=pending_acknowledgments,
        overdue_acknowledgments=overdue_acknowledgments,
        acknowledgment_rate=acknowledgment_rate,
        policies_expiring_soon=policies_expiring_soon,
        recent_acknowledgments=recent_acknowledgments,
        overdue_assignments=overdue_assignments
    )

# Compliance Reporting

@router.get("/reports/compliance")
async def generate_policy_compliance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    report_type: str = Query(..., description="Type of report: policy_summary, acknowledgment_status, overdue_report"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    policy_id: Optional[int] = Query(None, description="Filter by policy"),
    format: str = Query("json", description="Report format: json, csv")
):
    """Generate policy compliance reports."""
    
    # Base filters
    policy_filter = [PolicyModel.facility_administrator_id == current_user.id]
    assignment_filter = []
    
    if department:
        assignment_filter.append(StaffMemberModel.department == department)
    
    if policy_id:
        assignment_filter.append(PolicyAssignmentModel.policy_id == policy_id)
    
    if date_from:
        assignment_filter.append(PolicyAssignmentModel.assigned_date >= datetime.fromisoformat(date_from))
    
    if date_to:
        assignment_filter.append(PolicyAssignmentModel.assigned_date <= datetime.fromisoformat(date_to))
    
    if report_type == "policy_summary":
        # Policy summary report
        policy_data = db.query(
            PolicyModel.id,
            PolicyModel.title,
            PolicyModel.category,
            PolicyModel.status,
            func.count(PolicyAssignmentModel.id).label('total_assignments'),
            func.count(
                case(
                    (PolicyAssignmentModel.status == 'acknowledged', 1)
                )
            ).label('acknowledged_assignments'),
            func.count(
                case(
                    (and_(PolicyAssignmentModel.status != 'acknowledged', 
                          PolicyAssignmentModel.due_date < datetime.utcnow()), 1)
                )
            ).label('overdue_assignments')
        ).outerjoin(
            PolicyAssignmentModel, PolicyModel.id == PolicyAssignmentModel.policy_id
        ).filter(
            *policy_filter
        ).group_by(PolicyModel.id).all()
        
        report_data = []
        for policy in policy_data:
            acknowledgment_rate = (policy.acknowledged_assignments / policy.total_assignments * 100) if policy.total_assignments > 0 else 0
            report_data.append({
                'policy_title': policy.title,
                'category': policy.category,
                'status': policy.status,
                'total_assignments': policy.total_assignments,
                'acknowledged_assignments': policy.acknowledged_assignments,
                'overdue_assignments': policy.overdue_assignments,
                'acknowledgment_rate': round(acknowledgment_rate, 2),
                'compliance_status': 'Compliant' if acknowledgment_rate >= 95 else 'Needs Attention'
            })
    
    elif report_type == "acknowledgment_status":
        # Acknowledgment status report
        ack_data = db.query(
            StaffMemberModel.first_name,
            StaffMemberModel.last_name,
            StaffMemberModel.employee_id,
            StaffMemberModel.department,
            PolicyModel.title,
            PolicyAcknowledmentModel.acknowledged_date,
            PolicyAcknowledmentModel.acknowledgment_method,
            PolicyAcknowledmentModel.status
        ).join(
            PolicyAcknowledmentModel, StaffMemberModel.id == PolicyAcknowledmentModel.staff_member_id
        ).join(
            PolicyModel, PolicyAcknowledmentModel.policy_id == PolicyModel.id
        ).filter(
            PolicyModel.facility_administrator_id == current_user.id
        ).all()
        
        report_data = []
        for ack in ack_data:
            report_data.append({
                'employee_id': ack.employee_id,
                'name': f"{ack.first_name} {ack.last_name}",
                'department': ack.department,
                'policy_title': ack.title,
                'acknowledged_date': ack.acknowledged_date.isoformat() if ack.acknowledged_date else None,
                'acknowledgment_method': ack.acknowledgment_method,
                'status': ack.status
            })
    
    elif report_type == "overdue_report":
        # Overdue assignments report
        overdue_data = db.query(
            StaffMemberModel.first_name,
            StaffMemberModel.last_name,
            StaffMemberModel.employee_id,
            StaffMemberModel.department,
            PolicyModel.title,
            PolicyAssignmentModel.assigned_date,
            PolicyAssignmentModel.due_date,
            PolicyAssignmentModel.priority
        ).join(
            PolicyAssignmentModel, StaffMemberModel.id == PolicyAssignmentModel.staff_member_id
        ).join(
            PolicyModel, PolicyAssignmentModel.policy_id == PolicyModel.id
        ).filter(
            PolicyModel.facility_administrator_id == current_user.id,
            PolicyAssignmentModel.due_date < datetime.utcnow(),
            PolicyAssignmentModel.status != "acknowledged"
        ).all()
        
        report_data = []
        for overdue in overdue_data:
            days_overdue = (datetime.utcnow() - overdue.due_date).days
            report_data.append({
                'employee_id': overdue.employee_id,
                'name': f"{overdue.first_name} {overdue.last_name}",
                'department': overdue.department,
                'policy_title': overdue.title,
                'assigned_date': overdue.assigned_date.isoformat(),
                'due_date': overdue.due_date.isoformat(),
                'days_overdue': days_overdue,
                'priority': overdue.priority
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
            'policy_id': policy_id
        },
        'data': report_data,
        'summary': {
            'total_records': len(report_data),
            'report_period': f"{date_from or 'All time'} to {date_to or 'Present'}"
        }
    } 