"""
Export Quota Service Module

This module provides services for managing quarterly export quotas for Pro/Enterprise users.
It handles quota tracking, validation, and automatic quarterly resets.

Key functionalities:
- Quarterly quota tracking and validation
- Export usage increment and monitoring
- Automatic quota reset each quarter
- Next available export date calculation
- User tier validation integration

Dependencies:
- sqlalchemy: For database operations
- datetime: For date/time calculations
- app.models: For database models
"""

from sqlalchemy.orm import Session
from app.models.export_quota import ExportQuota
from app.models.user import User
from datetime import datetime, timedelta
from typing import Optional, Tuple
import calendar

class ExportQuotaService:
    """Service for managing user export quotas."""
    
    @staticmethod
    def get_current_quarter() -> str:
        """Get current quarter in YYYY-QX format."""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}-Q{quarter}"
    
    @staticmethod
    def get_user_quota(db: Session, user_id: int) -> ExportQuota:
        """Get or create user quota for current quarter."""
        current_quarter = ExportQuotaService.get_current_quarter()
        
        quota = db.query(ExportQuota).filter(
            ExportQuota.user_id == user_id,
            ExportQuota.quarter_year == current_quarter
        ).first()
        
        if not quota:
            quota = ExportQuota(
                user_id=user_id,
                quarter_year=current_quarter,
                exports_used=0,
                total_data_size=0
            )
            db.add(quota)
            db.commit()
            db.refresh(quota)
        
        return quota
    
    @staticmethod
    def check_quota_available(db: Session, user_id: int) -> bool:
        """Check if user has available export quota for current quarter."""
        quota = ExportQuotaService.get_user_quota(db, user_id)
        return quota.exports_used < 1  # One export per quarter
    
    @staticmethod
    def increment_quota_usage(db: Session, user_id: int, data_size: int) -> bool:
        """Increment user's quota usage. Returns True if successful."""
        quota = ExportQuotaService.get_user_quota(db, user_id)
        
        if quota.exports_used >= 1:
            return False  # Quota exceeded
        
        quota.exports_used += 1
        quota.total_data_size += data_size
        quota.last_export_date = datetime.now()
        
        db.commit()
        return True
    
    @staticmethod
    def get_next_available_date(db: Session, user_id: int) -> Optional[datetime]:
        """Calculate when user's next export will be available."""
        quota = ExportQuotaService.get_user_quota(db, user_id)
        
        if quota.exports_used < 1:
            return None  # Available now
        
        # Calculate next quarter start date
        current_quarter = ExportQuotaService.get_current_quarter()
        year, quarter = current_quarter.split('-Q')
        year = int(year)
        quarter = int(quarter)
        
        # Calculate next quarter
        if quarter == 4:
            next_year = year + 1
            next_quarter = 1
        else:
            next_year = year
            next_quarter = quarter + 1
        
        # First day of next quarter
        month = (next_quarter - 1) * 3 + 1
        return datetime(next_year, month, 1)
    
    @staticmethod
    def reset_quarterly_quotas(db: Session) -> int:
        """Reset all quotas for users who have moved to a new quarter. Returns count of reset quotas."""
        current_quarter = ExportQuotaService.get_current_quarter()
        
        # Find all quotas that are not for the current quarter
        old_quotas = db.query(ExportQuota).filter(
            ExportQuota.quarter_year != current_quarter
        ).all()
        
        reset_count = 0
        for quota in old_quotas:
            # Create new quota for current quarter if user doesn't have one
            existing_quota = db.query(ExportQuota).filter(
                ExportQuota.user_id == quota.user_id,
                ExportQuota.quarter_year == current_quarter
            ).first()
            
            if not existing_quota:
                new_quota = ExportQuota(
                    user_id=quota.user_id,
                    quarter_year=current_quarter,
                    exports_used=0,
                    total_data_size=0
                )
                db.add(new_quota)
                reset_count += 1
        
        db.commit()
        return reset_count
    
    @staticmethod
    def get_quota_status(db: Session, user_id: int) -> dict:
        """Get comprehensive quota status for user."""
        quota = ExportQuotaService.get_user_quota(db, user_id)
        available = ExportQuotaService.check_quota_available(db, user_id)
        next_available = ExportQuotaService.get_next_available_date(db, user_id)
        
        return {
            "quarter": quota.quarter_year,
            "exports_used": quota.exports_used,
            "exports_limit": 1,
            "available": available,
            "total_data_size": quota.total_data_size,
            "last_export_date": quota.last_export_date,
            "next_available_date": next_available
        } 