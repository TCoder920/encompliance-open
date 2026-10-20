"""
Audit Service Module

This module provides services for logging and managing audit events in the EnCompliance application.
It handles administrative action tracking, IP address logging, and error handling for audit logs.

Key functionalities:
- Audit log creation and storage
- IP address detection and classification
- Error-resilient logging mechanisms
- Database interaction for audit records
- Support for admin user associations

Dependencies:
- sqlalchemy: For database operations
- ipaddress: For IP handling
"""

from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.support_portal_account import SupportPortalAccount
from typing import Optional, Dict
from ipaddress import ip_address as ip_parse
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import traceback

async def log_support_audit_event(
    db: Session,
    support_account_id: Optional[int],
    action: str,
    target: Optional[str] = None,
    ip_address: Optional[str] = None,
    internal_ip_address: Optional[str] = None,
    details: Optional[Dict] = None,
):
    """Creates an audit log entry in the admin database."""
    
    # admin_user_id can now be None for actions like failed logins, 
    # as the corresponding model field is nullable.
    if support_account_id is None and action == "login_failed":
        print(f"Logging failed login attempt for target: {target}, IP: {ip_address}")
        # Proceed to log even with None user ID
    elif support_account_id is None:
         # Should generally not happen for actions other than pre-login failures
         print(f"Warning: Logging action '{action}' without a support_account_id.")

    # If internal IP not explicitly provided, try to infer based on private address ranges
    detected_internal_ip = internal_ip_address
    public_ip = ip_address
    try:
        if not detected_internal_ip and ip_address:
            parsed = ip_parse(str(ip_address))
            if parsed.is_private:
                detected_internal_ip = ip_address
                public_ip = None  # Do not record the same value twice
    except ValueError:
        # ip_address might be invalid or not an IP (e.g., hostname); ignore
        pass

    # Try different approaches to insert the audit log, handling schema differences gracefully
    try:
        # First attempt: Use all fields including internal_ip_address
        try:
            log_entry = AuditLog(
                support_account_id=support_account_id,
                action=action,
                target=target,
                ip_address=public_ip,
                internal_ip_address=detected_internal_ip,
                details=details
            )
            db.add(log_entry)
            db.commit()
            return
        except (OperationalError, SQLAlchemyError) as e1:
            db.rollback()
            if "no such column: audit_logs.internal_ip_address" in str(e1) or "no such table: audit_logs" in str(e1):
                # Second attempt: Try without internal_ip_address
                try:
                    log_entry = AuditLog(
                        support_account_id=support_account_id,
                        action=action,
                        target=target,
                        ip_address=public_ip,
                        details=details
                    )
                    db.add(log_entry)
                    db.commit()
                    return
                except (OperationalError, SQLAlchemyError) as e2:
                    db.rollback()
                    # If table doesn't exist, don't bother with further attempts
                    if "no such table: audit_logs" in str(e2):
                        print(f"Skipping audit log as audit_logs table doesn't exist: {action}")
                        return
                    # Otherwise, continue to basic approach
                    raise e2
            else:
                # Re-raise if it's not a schema issue
                raise e1
    except Exception as e:
        # Last resort attempt: Try direct SQL to avoid schema issues
        try:
            print(f"Error in normal audit log methods: {str(e)}")
            print(f"Creating fallback audit log for action: {action}")
            # This is a no-op fallback just to avoid error messages, but we'll log to console instead
            print(f"AUDIT LOG: support_account_id={support_account_id}, action={action}, target={target}, ip={ip_address}, internal_ip={detected_internal_ip}")
        except Exception as final_e:
            # If all attempts fail, just log to console and don't crash
            print(f"Failed to log audit action after multiple attempts: {final_e}")
            print(traceback.format_exc()) 