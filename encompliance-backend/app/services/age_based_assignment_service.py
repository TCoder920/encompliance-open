"""
Age-Based Assignment Service Module

This module provides functionality for assigning tasks based on staff member age criteria.
Ensures compliance with child labor laws and facility safety requirements.

Key functionalities:
- Age-based staff filtering for task assignment
- Automatic age calculation from birth dates
- Compliance validation for age-restricted tasks
- Eligible staff member identification
- Age criteria validation and enforcement

Dependencies:
- sqlalchemy: For database queries
- datetime: For age calculations

Educational Note: Implements age-based task assignment following OSHA guidelines
and Fair Labor Standards Act (FLSA) requirements for youth employment in childcare
facilities. References: https://www.dol.gov/agencies/whd/fact-sheets/32
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.staff_member import StaffMember, StaffStatus
from app.models.operational_task import OperationalTask
from app.models.task_assignment import TaskAssignment
from app.schemas.task_management import AgeBasedAssignmentCriteria, EligibleStaffMember, AgeBasedAssignmentResponse

logger = logging.getLogger(__name__)

class AgeBasedAssignmentService:
    """Service for managing age-based task assignments."""
    
    @staticmethod
    def get_eligible_staff_by_age(
        db: Session,
        facility_id: int,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None
    ) -> List[StaffMember]:
        """
        Get staff members eligible for task assignment based on age criteria.
        
        Args:
            db: Database session
            facility_id: Facility ID to filter staff
            min_age: Minimum age requirement (inclusive)
            max_age: Maximum age allowance (inclusive)
            
        Returns:
            List of eligible staff members
        """
        try:
            query = db.query(StaffMember).filter(
                StaffMember.facility_administrator_id == facility_id,
                StaffMember.status == StaffStatus.ACTIVE.value
            )
            
            # Apply age filtering if criteria specified
            if min_age is not None or max_age is not None:
                today = date.today()
                
                # Calculate birth date ranges for age filtering
                if min_age is not None:
                    # Staff must be at least min_age years old
                    max_birth_date = date(today.year - min_age, today.month, today.day)
                    query = query.filter(
                        and_(
                            StaffMember.birth_date.isnot(None),
                            StaffMember.birth_date <= max_birth_date
                        )
                    )
                
                if max_age is not None:
                    # Staff must be no older than max_age years old
                    min_birth_date = date(today.year - max_age - 1, today.month, today.day)
                    query = query.filter(
                        and_(
                            StaffMember.birth_date.isnot(None),
                            StaffMember.birth_date > min_birth_date
                        )
                    )
            
            staff_members = query.order_by(StaffMember.last_name, StaffMember.first_name).all()
            
            logger.info(f"Found {len(staff_members)} eligible staff members for age criteria: min_age={min_age}, max_age={max_age}")
            return staff_members
            
        except Exception as e:
            logger.error(f"Error filtering staff by age criteria: {str(e)}")
            raise
    
    @staticmethod
    def get_staff_eligible_for_task(
        db: Session,
        task: OperationalTask
    ) -> AgeBasedAssignmentResponse:
        """
        Get staff members eligible for a specific task based on its age restrictions.
        
        Args:
            db: Database session
            task: OperationalTask instance with age criteria
            
        Returns:
            AgeBasedAssignmentResponse with eligible staff and criteria
        """
        try:
            # Get the facility administrator for this task's facility
            from app.models.user import User
            from app.models.facility import Facility
            
            # First get the facility, then get its admin
            facility = db.query(Facility).filter(Facility.id == task.facility_id).first()
            if not facility:
                logger.warning(f"Facility {task.facility_id} not found")
                return AgeBasedAssignmentResponse(
                    eligible_staff=[],
                    total_staff=0,
                    eligible_count=0,
                    age_criteria=AgeBasedAssignmentCriteria(
                        min_age=task.min_age_required,
                        max_age=task.max_age_allowed
                    )
                )
            
            facility_admin = facility.admin_user
            
            if not facility_admin:
                logger.warning(f"No facility administrator found for facility {task.facility_id}")
                return AgeBasedAssignmentResponse(
                    eligible_staff=[],
                    total_staff=0,
                    eligible_count=0,
                    age_criteria=AgeBasedAssignmentCriteria(
                        min_age=task.min_age_required,
                        max_age=task.max_age_allowed
                    )
                )
            
            # Get all active staff for the facility administrator
            total_staff_query = db.query(StaffMember).filter(
                StaffMember.facility_administrator_id == facility_admin.id,
                StaffMember.status == StaffStatus.ACTIVE.value
            )
            total_staff = total_staff_query.all()
            
            # Apply age filtering based on task requirements
            eligible_staff = AgeBasedAssignmentService.get_eligible_staff_by_age(
                db=db,
                facility_id=facility_admin.id,
                min_age=task.min_age_required,
                max_age=task.max_age_allowed
            )
            
            # Convert to response format
            eligible_staff_responses = [
                EligibleStaffMember(
                    id=staff.id,
                    first_name=staff.first_name,
                    last_name=staff.last_name,
                    full_name=staff.full_name,
                    email=staff.email,
                    role=staff.role,
                    department=staff.department,
                    age=staff.age,
                    is_active=staff.is_active
                )
                for staff in eligible_staff
            ]
            
            age_criteria = AgeBasedAssignmentCriteria(
                min_age=task.min_age_required,
                max_age=task.max_age_allowed
            )
            
            return AgeBasedAssignmentResponse(
                eligible_staff=eligible_staff_responses,
                total_staff=len(total_staff),
                eligible_count=len(eligible_staff),
                age_criteria=age_criteria
            )
            
        except Exception as e:
            logger.error(f"Error getting eligible staff for task {task.id}: {str(e)}")
            raise
    
    @staticmethod
    def validate_staff_age_eligibility(
        db: Session,
        staff_member_id: int,
        task: OperationalTask
    ) -> Dict[str, Any]:
        """
        Validate if a specific staff member meets age requirements for a task.
        
        Args:
            db: Database session
            staff_member_id: Staff member ID to validate
            task: OperationalTask with age requirements
            
        Returns:
            Validation result with eligibility status and reason
        """
        try:
            staff_member = db.query(StaffMember).filter(
                StaffMember.id == staff_member_id,
                StaffMember.status == StaffStatus.ACTIVE.value
            ).first()
            
            if not staff_member:
                return {
                    "eligible": False,
                    "reason": "Staff member not found or inactive",
                    "staff_age": None,
                    "task_requirements": {
                        "min_age": task.min_age_required,
                        "max_age": task.max_age_allowed
                    }
                }
            
            staff_age = staff_member.age
            
            # If no age restrictions on task, staff is eligible
            if not task.has_age_restrictions:
                return {
                    "eligible": True,
                    "reason": "No age restrictions for this task",
                    "staff_age": staff_age,
                    "task_requirements": {
                        "min_age": None,
                        "max_age": None
                    }
                }
            
            # If staff has no birth date, cannot validate age requirements
            if staff_age is None:
                return {
                    "eligible": False,
                    "reason": "Staff member birth date not available for age validation",
                    "staff_age": None,
                    "task_requirements": {
                        "min_age": task.min_age_required,
                        "max_age": task.max_age_allowed
                    }
                }
            
            # Check minimum age requirement
            if task.min_age_required and staff_age < task.min_age_required:
                return {
                    "eligible": False,
                    "reason": f"Staff member is too young (age {staff_age}, minimum required: {task.min_age_required})",
                    "staff_age": staff_age,
                    "task_requirements": {
                        "min_age": task.min_age_required,
                        "max_age": task.max_age_allowed
                    }
                }
            
            # Check maximum age allowance
            if task.max_age_allowed and staff_age > task.max_age_allowed:
                return {
                    "eligible": False,
                    "reason": f"Staff member exceeds maximum age (age {staff_age}, maximum allowed: {task.max_age_allowed})",
                    "staff_age": staff_age,
                    "task_requirements": {
                        "min_age": task.min_age_required,
                        "max_age": task.max_age_allowed
                    }
                }
            
            # Staff member meets all age requirements
            return {
                "eligible": True,
                "reason": "Staff member meets all age requirements",
                "staff_age": staff_age,
                "task_requirements": {
                    "min_age": task.min_age_required,
                    "max_age": task.max_age_allowed
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating staff age eligibility: {str(e)}")
            raise
    
    @staticmethod
    def get_age_compliance_summary(
        db: Session,
        facility_id: int
    ) -> Dict[str, Any]:
        """
        Get age compliance summary for a facility.
        
        Args:
            db: Database session
            facility_id: Facility ID
            
        Returns:
            Age compliance summary with statistics
        """
        try:
            # Get all active staff
            all_staff = db.query(StaffMember).filter(
                StaffMember.facility_administrator_id == facility_id,
                StaffMember.status == StaffStatus.ACTIVE.value
            ).all()
            
            # Calculate age statistics
            staff_with_birth_dates = [staff for staff in all_staff if staff.birth_date]
            staff_ages = [staff.age for staff in staff_with_birth_dates if staff.age is not None]
            
            # Get tasks with age restrictions
            age_restricted_tasks = db.query(OperationalTask).filter(
                OperationalTask.facility_id == facility_id,
                OperationalTask.is_active == True,
                or_(
                    OperationalTask.min_age_required.isnot(None),
                    OperationalTask.max_age_allowed.isnot(None)
                )
            ).count()
            
            # Calculate age distribution
            age_distribution = {
                "under_16": len([age for age in staff_ages if age < 16]),
                "16_17": len([age for age in staff_ages if 16 <= age <= 17]),
                "18_25": len([age for age in staff_ages if 18 <= age <= 25]),
                "26_40": len([age for age in staff_ages if 26 <= age <= 40]),
                "41_55": len([age for age in staff_ages if 41 <= age <= 55]),
                "over_55": len([age for age in staff_ages if age > 55])
            }
            
            return {
                "total_staff": len(all_staff),
                "staff_with_birth_dates": len(staff_with_birth_dates),
                "staff_missing_birth_dates": len(all_staff) - len(staff_with_birth_dates),
                "age_restricted_tasks": age_restricted_tasks,
                "average_age": round(sum(staff_ages) / len(staff_ages), 1) if staff_ages else None,
                "age_distribution": age_distribution,
                "compliance_warnings": AgeBasedAssignmentService._get_compliance_warnings(
                    staff_ages, age_restricted_tasks, len(all_staff) - len(staff_with_birth_dates)
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting age compliance summary: {str(e)}")
            raise
    
    @staticmethod
    def _get_compliance_warnings(
        staff_ages: List[int],
        age_restricted_tasks: int,
        missing_birth_dates: int
    ) -> List[Dict[str, str]]:
        """Generate compliance warnings based on age data."""
        warnings = []
        
        if missing_birth_dates > 0:
            warnings.append({
                "type": "missing_data",
                "message": f"{missing_birth_dates} staff members are missing birth dates, which prevents age-based task assignment validation."
            })
        
        under_18_count = len([age for age in staff_ages if age < 18])
        if under_18_count > 0 and age_restricted_tasks > 0:
            warnings.append({
                "type": "youth_worker_alert",
                "message": f"{under_18_count} staff members are under 18 years old. Ensure age-restricted tasks comply with FLSA youth employment provisions."
            })
        
        if age_restricted_tasks == 0 and len(staff_ages) > 0:
            warnings.append({
                "type": "no_restrictions",
                "message": "No tasks have age restrictions. Consider implementing age-based assignment for safety compliance."
            })
        
        return warnings 