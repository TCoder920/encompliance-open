"""
Training Context Service Module

This module provides context gathering for training and certification data
to be included in AI assistant conversations.

Purpose: Fetches user training assignments, completions, and certifications
for AI context integration, following the same pattern as calendar/notes context.

Key functionalities:
- Fetch user training assignments and completions
- Format training data for AI consumption
- Respect subscription tier access controls
- Handle staff member associations

Educational Note: Implements context aggregation pattern for enhanced AI responses
following established patterns from ContextService for consistency.

Dependencies:
- sqlalchemy: For database operations
- app.models.training: For training data models
- app.utils.tiers: For subscription tier validation
- app.utils.access_control: For feature access validation
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.models.training import (
    TrainingProgram, StaffMember, TrainingAssignment, 
    TrainingCompletion, AssignmentStatus, CompletionStatus
)
from app.utils.tiers import get_tier_from_subscription_status
from app.utils.access_control import can_access_feature
import logging

logger = logging.getLogger(__name__)

class TrainingContextService:
    @staticmethod
    async def get_user_training_assignments(
        db: Session,
        user_id: int,
        user_subscription_status: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get user's training assignments for AI context.
        
        Args:
            db: Database session
            user_id: ID of the facility administrator
            user_subscription_status: User's subscription status for access control
            limit: Maximum number of assignments to retrieve
            
        Returns:
            List of formatted training assignments
        """
        try:
            # Check if user can access training feature
            user_tier = get_tier_from_subscription_status(user_subscription_status)
            if not can_access_feature(user_tier, "training"):
                logger.info(f"User {user_id} cannot access training feature")
                return []
            
            # Get staff members associated with this facility administrator
            staff_members = db.query(StaffMember).filter(
                StaffMember.facility_administrator_id == user_id,
                StaffMember.status == "active"
            ).all()
            
            if not staff_members:
                logger.info(f"No active staff members found for user {user_id}")
                return []
            
            staff_ids = [staff.id for staff in staff_members]
            
            # Get recent and upcoming training assignments
            assignments = db.query(TrainingAssignment).join(
                TrainingProgram, TrainingAssignment.training_program_id == TrainingProgram.id
            ).filter(
                TrainingAssignment.staff_member_id.in_(staff_ids),
                TrainingAssignment.status.in_(['assigned', 'in_progress', 'overdue'])
            ).order_by(
                TrainingAssignment.due_date.asc()
            ).limit(limit).all()
            
            # Format assignments for AI context
            formatted_assignments = []
            for assignment in assignments:
                staff_member = next((s for s in staff_members if s.id == assignment.staff_member_id), None)
                if staff_member and assignment.training_program:
                    formatted_assignment = {
                        "id": assignment.id,
                        "staff_name": f"{staff_member.first_name} {staff_member.last_name}",
                        "staff_role": staff_member.role,
                        "program_title": assignment.training_program.title,
                        "program_category": assignment.training_program.category,
                        "is_mandatory": assignment.training_program.is_mandatory,
                        "status": assignment.status,
                        "assigned_date": assignment.assigned_date.isoformat() if assignment.assigned_date else "",
                        "due_date": assignment.due_date.isoformat() if assignment.due_date else "",
                        "priority": assignment.priority,
                        "estimated_duration": assignment.training_program.estimated_duration_minutes
                    }
                    formatted_assignments.append(formatted_assignment)
            
            logger.info(f"Retrieved {len(formatted_assignments)} training assignments for user {user_id}")
            return formatted_assignments
            
        except Exception as e:
            logger.error(f"Error fetching training assignments for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def get_user_training_completions(
        db: Session,
        user_id: int,
        user_subscription_status: str,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Get user's recent training completions and certifications for AI context.
        
        Args:
            db: Database session
            user_id: ID of the facility administrator
            user_subscription_status: User's subscription status for access control
            limit: Maximum number of completions to retrieve
            
        Returns:
            List of formatted training completions
        """
        try:
            # Check if user can access training feature
            user_tier = get_tier_from_subscription_status(user_subscription_status)
            if not can_access_feature(user_tier, "training"):
                logger.info(f"User {user_id} cannot access training feature")
                return []
            
            # Get staff members associated with this facility administrator
            staff_members = db.query(StaffMember).filter(
                StaffMember.facility_administrator_id == user_id
            ).all()
            
            if not staff_members:
                logger.info(f"No staff members found for user {user_id}")
                return []
            
            staff_ids = [staff.id for staff in staff_members]
            
            # Get recent completions and active certifications
            completions = db.query(TrainingCompletion).join(
                TrainingProgram, TrainingCompletion.training_program_id == TrainingProgram.id
            ).filter(
                TrainingCompletion.staff_member_id.in_(staff_ids)
            ).order_by(
                desc(TrainingCompletion.completed_date)
            ).limit(limit).all()
            
            # Format completions for AI context
            formatted_completions = []
            for completion in completions:
                try:
                    staff_member = next((s for s in staff_members if s.id == completion.staff_member_id), None)
                    if staff_member and completion.training_program:
                        days_until_expiry = None
                        if hasattr(completion, 'expires_date') and completion.expires_date:
                            days_until_expiry = (completion.expires_date - datetime.now()).days
                        
                        formatted_completion = {
                            "id": completion.id,
                            "staff_name": f"{staff_member.first_name} {staff_member.last_name}",
                            "program_title": completion.training_program.title,
                            "program_category": completion.training_program.category,
                            "completion_status": completion.completion_status,
                            "completed_date": completion.completed_date.isoformat() if completion.completed_date else "",
                            "certificate_status": getattr(completion, 'certificate_status', ''),
                            "certificate_number": getattr(completion, 'certificate_number', ''),
                            "expires_date": completion.expires_date.isoformat() if hasattr(completion, 'expires_date') and completion.expires_date else "",
                            "days_until_expiry": days_until_expiry,
                            "is_expired": getattr(completion, 'is_expired', False),
                            "is_certificate_valid": getattr(completion, 'is_certificate_valid', False),
                            "final_score": getattr(completion, 'final_score', None)
                        }
                        formatted_completions.append(formatted_completion)
                except Exception as e:
                    logger.warning(f"Error processing completion {completion.id}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(formatted_completions)} training completions for user {user_id}")
            return formatted_completions
            
        except Exception as e:
            logger.error(f"Error fetching training completions for user {user_id}: {e}")
            return []
    
    @staticmethod
    def format_training_context_for_ai(
        assignments: List[Dict[str, Any]],
        completions: List[Dict[str, Any]]
    ) -> str:
        """
        Format training assignments and completions into context string for AI.
        
        Args:
            assignments: List of training assignments
            completions: List of training completions
            
        Returns:
            Formatted context string for AI consumption
        """
        context_parts = []
        
        # Add training assignments context
        if assignments:
            context_parts.append("=== TRAINING ASSIGNMENTS ===")
            context_parts.append("Current and upcoming training assignments:")
            
            for assignment in assignments:
                assignment_info = f"• {assignment['program_title']}"
                
                if assignment['staff_name']:
                    assignment_info += f" - {assignment['staff_name']} ({assignment['staff_role']})"
                
                if assignment['due_date']:
                    try:
                        due_dt = datetime.fromisoformat(assignment['due_date'].replace('Z', '+00:00'))
                        assignment_info += f" | Due: {due_dt.strftime('%Y-%m-%d')}"
                    except:
                        assignment_info += f" | Due: {assignment['due_date']}"
                
                assignment_info += f" | Status: {assignment['status'].title()}"
                
                if assignment['is_mandatory']:
                    assignment_info += " | MANDATORY"
                
                if assignment['priority'] and assignment['priority'] != 'medium':
                    assignment_info += f" | Priority: {assignment['priority'].title()}"
                
                if assignment['program_category']:
                    assignment_info += f" | Category: {assignment['program_category']}"
                
                context_parts.append(assignment_info)
            
            context_parts.append("")  # Empty line for separation
        
        # Add training completions and certifications context
        if completions:
            context_parts.append("=== TRAINING COMPLETIONS & CERTIFICATIONS ===")
            context_parts.append("Recent training completions and certification status:")
            
            for completion in completions:
                completion_info = f"• {completion['program_title']}"
                
                if completion['staff_name']:
                    completion_info += f" - {completion['staff_name']}"
                
                if completion['completed_date']:
                    try:
                        completed_dt = datetime.fromisoformat(completion['completed_date'].replace('Z', '+00:00'))
                        completion_info += f" | Completed: {completed_dt.strftime('%Y-%m-%d')}"
                    except:
                        completion_info += f" | Completed: {completion['completed_date']}"
                
                completion_info += f" | Status: {completion['completion_status'].title()}"
                
                if completion['certificate_status'] and completion['certificate_status'] != 'pending':
                    completion_info += f" | Certificate: {completion['certificate_status'].title()}"
                
                if completion['certificate_number']:
                    completion_info += f" | Cert #: {completion['certificate_number']}"
                
                if completion['expires_date']:
                    try:
                        expires_dt = datetime.fromisoformat(completion['expires_date'].replace('Z', '+00:00'))
                        completion_info += f" | Expires: {expires_dt.strftime('%Y-%m-%d')}"
                        
                        if completion['days_until_expiry'] is not None:
                            if completion['days_until_expiry'] < 0:
                                completion_info += " | EXPIRED"
                            elif completion['days_until_expiry'] <= 30:
                                completion_info += f" | Expires in {completion['days_until_expiry']} days"
                    except:
                        completion_info += f" | Expires: {completion['expires_date']}"
                
                if completion['final_score']:
                    completion_info += f" | Score: {completion['final_score']}%"
                
                context_parts.append(completion_info)
            
            context_parts.append("")  # Empty line for separation
        
        # Add instructions for AI
        if assignments or completions:
            context_parts.append("=== TRAINING CONTEXT USAGE INSTRUCTIONS ===")
            context_parts.append("Use the above training assignments and certifications to provide relevant responses about:")
            context_parts.append("- Training due dates and overdue assignments")
            context_parts.append("- Certification expiration dates and renewal requirements")
            context_parts.append("- Staff training completion status and progress")
            context_parts.append("- Mandatory vs optional training requirements")
            context_parts.append("- Training categories and compliance requirements")
            context_parts.append("Reference specific staff members, programs, and dates when relevant to user questions.")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    @staticmethod
    async def get_full_training_context(
        db: Session,
        user_id: int,
        user_subscription_status: str
    ) -> str:
        """
        Get complete training context including assignments and completions.
        
        Args:
            db: Database session
            user_id: ID of the facility administrator
            user_subscription_status: User's subscription status
            
        Returns:
            Formatted training context string for AI
        """
        try:
            # Fetch training assignments and completions
            assignments = await TrainingContextService.get_user_training_assignments(
                db=db,
                user_id=user_id,
                user_subscription_status=user_subscription_status
            )
            
            completions = await TrainingContextService.get_user_training_completions(
                db=db,
                user_id=user_id,
                user_subscription_status=user_subscription_status
            )
            
            # Format context for AI
            context = TrainingContextService.format_training_context_for_ai(assignments, completions)
            
            logger.info(f"Generated training context for user {user_id}: {len(assignments)} assignments, {len(completions)} completions")
            return context
            
        except Exception as e:
            logger.error(f"Error generating training context for user {user_id}: {e}")
            return "" 