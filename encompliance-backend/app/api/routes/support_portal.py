"""
Support Portal Routes
---------------------
High-level API surface area for internal support tooling. Provides:
- Support staff account management
- Audit logging visibility
- Operational diagnostics for support tooling
- Access to aggregated customer data needed by support
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import inspect, MetaData, text
from sqlalchemy.exc import OperationalError
import sqlalchemy.orm

from app.database import (
    get_support_portal_db,
    support_portal_engine,
    get_db,
    engine as user_engine,
)
from app.models.support_portal_account import SupportPortalAccount
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.query_log import QueryLog
from app.schemas.support_portal_account_schemas import (
    SupportPortalAccountCreate,
    SupportPortalAccountOut,
    SupportPortalAccountUpdate,
    SupportPortalAuditLogOut,
)
from app.schemas.user import User as UserOut
from app.auth.support_portal_auth_utils import (
    get_current_support_account,
    require_role,
    get_password_hash,
    SUPPORT_ADMIN_ROLE,
    SUPPORT_AGENT_ROLE,
    normalize_role_names,
)
from app.services.audit_service import log_support_audit_event
from app.services.file_watcher import get_file_tree # Import the file tree function
from app.utils.owasp_protections import PasswordPolicy
from pathlib import Path
import httpx # Add httpx for making requests
import os # Add os for environment variable access
from app.core.config import get_settings
from app.core.openai_utils import get_or_create_user_assistant
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Tiered role dependencies for support portal staff
require_support_agent = require_role([SUPPORT_AGENT_ROLE])
require_support_lead = require_role([SUPPORT_ADMIN_ROLE])

# --- User API Configuration ---
# Assuming the user API runs locally on port 8000, adjust if needed
USER_API_BASE_URL = os.getenv("USER_API_BASE_URL", "http://localhost:8000") 

# --- Support Account Management (Requires Support Lead) ---

@router.post(
    "/users",
    response_model=SupportPortalAccountOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_support_lead)],
)
async def create_support_account(
    request: Request,
    user_in: SupportPortalAccountCreate, 
    db: Session = Depends(get_support_portal_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account) # For audit log
):
    """Creates a new support portal account."""
    db_user = db.query(SupportPortalAccount).filter(SupportPortalAccount.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    db_user = db.query(SupportPortalAccount).filter(SupportPortalAccount.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Validate password strength
    password_validation = PasswordPolicy.validate_password_strength(user_in.password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_validation["message"]
        )

    hashed_password = get_password_hash(user_in.password)
    requested_roles = normalize_role_names(user_in.roles or [SUPPORT_AGENT_ROLE])
    new_user = SupportPortalAccount(
        username=user_in.username, 
        email=user_in.email, 
        hashed_password=hashed_password,
        roles=requested_roles
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    await log_support_audit_event(
        db=db,
        support_account_id=current_user.id,
        action="create_support_account",
        target=f"user:{new_user.id}",
        ip_address=request.client.host,
        details={"username": new_user.username, "email": new_user.email, "roles": new_user.roles},
    )
    return new_user

@router.get(
    "/users",
    response_model=List[SupportPortalAccountOut],
    dependencies=[Depends(require_support_lead)],
)
async def list_support_accounts(
    request: Request,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_support_portal_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account) # For audit log
):
    """Retrieves a list of support accounts."""
    users = db.query(SupportPortalAccount).offset(skip).limit(limit).all()
    # Avoid logging every single view unless necessary - consider sampling or specific needs
    # await log_support_audit_event(db, current_user.id, "view_support_accounts", ip_address=request.client.host)
    return users

@router.get(
    "/users/{user_id}",
    response_model=SupportPortalAccountOut,
    dependencies=[Depends(require_support_lead)],
)
async def get_support_account(
    request: Request,
    user_id: int, 
    db: Session = Depends(get_support_portal_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account) # For audit log
):
    """Retrieves a specific support account by ID."""
    account = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == user_id).first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support account not found")
    # await log_support_audit_event(db, current_user.id, "view_support_account", target=f"user:{user_id}", ip_address=request.client.host)
    return account

@router.put(
    "/users/{user_id}",
    response_model=SupportPortalAccountOut,
    dependencies=[Depends(require_support_lead)],
)
async def update_support_account(
    request: Request,
    user_id: int, 
    user_in: SupportPortalAccountUpdate, 
    db: Session = Depends(get_support_portal_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account) # For audit log
):
    """Updates a support account."""
    account = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == user_id).first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support account not found")

    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        # Validate password strength
        password_validation = PasswordPolicy.validate_password_strength(update_data["password"])
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_validation["message"]
            )
        account.set_password(update_data["password"])
        del update_data["password"] # Don't store plain password in update_data

    changed_fields = {}
    for key, value in update_data.items():
        if getattr(account, key) != value:
             changed_fields[key] = {"old": getattr(account, key), "new": value}
        if key == "roles":
            value = normalize_role_names(value)
        setattr(account, key, value)

    if changed_fields:
        db.commit()
        db.refresh(account)
        await log_support_audit_event(
            db=db, 
            support_account_id=current_user.id, 
            action="update_support_account", 
            target=f"user:{user_id}", 
            ip_address=request.client.host, # Let service handle internal/public
            details=changed_fields
        )
    return account

@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_support_lead)],
)
async def delete_support_account(
    request: Request,
    user_id: int, 
    db: Session = Depends(get_support_portal_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account) # For audit log
):
    """Deletes a support account."""
    account = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == user_id).first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support account not found")
    
    if account.id == current_user.id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete self")

    username = account.username # Store username for logging
    db.delete(account)
    db.commit()
    await log_support_audit_event(
        db=db, 
        support_account_id=current_user.id, 
        action="delete_support_account", 
        target=f"user:{user_id}", 
        ip_address=request.client.host, # Let service handle internal/public
        details={"deleted_username": username}
    )
    return

# --- Audit Log Viewing (Requires Support Agent Role) ---

@router.get(
    "/audit-logs",
    response_model=List[SupportPortalAuditLogOut],
    dependencies=[Depends(require_support_lead)],
)
async def read_audit_logs(
    request: Request,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_support_portal_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account)
):
    """Retrieves audit log entries."""
    # Build a more flexible query that will work even if internal_ip_address column doesn't exist
    try:
        logs = (
            db.query(AuditLog, SupportPortalAccount.username.label("account_username"))
            .join(SupportPortalAccount, AuditLog.support_account_id == SupportPortalAccount.id)
            .order_by(AuditLog.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Combine log and username into the output schema structure
        result = []
        for log, username in logs:
            log_data = SupportPortalAuditLogOut.model_validate(log)
            log_data.account_username = username
            result.append(log_data)
            
    except OperationalError as e:
        # Special handling for the "no such column" error
        if "no such column: audit_logs.internal_ip_address" in str(e):
            # Fallback query: explicitly select only the columns we know exist
            logs = (
                db.query(
                    AuditLog.id,
                    AuditLog.support_account_id,
                    AuditLog.action,
                    AuditLog.target,
                    AuditLog.timestamp,
                    AuditLog.ip_address,
                    AuditLog.details,
                    SupportPortalAccount.username.label("account_username"),
                )
                .join(SupportPortalAccount, AuditLog.support_account_id == SupportPortalAccount.id)
                .order_by(AuditLog.timestamp.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            
            # Convert to dictionary and then to AuditLogOut objects
            result = []
            for log in logs:
                # Create a dictionary of the result
                log_dict = {
                    "id": log.id,
                    "support_account_id": log.support_account_id,
                    "action": log.action,
                    "target": log.target,
                    "timestamp": log.timestamp,
                    "ip_address": log.ip_address,
                    "details": log.details,
                    "account_username": log.account_username,
                }
                # Convert to schema
                log_data = SupportPortalAuditLogOut.model_validate(log_dict) 
                result.append(log_data)
        else:
            # Re-raise if it's a different error
            raise

    await log_support_audit_event(
        db=db,
        support_account_id=current_user.id,
        action="view_audit_logs",
        ip_address=request.client.host,
        details={"limit": limit, "skip": skip},
    )
    return result

# --- System Information (Requires Support Agent Role) ---

@router.get("/db-schema", response_model=Dict[str, Any], dependencies=[Depends(require_support_lead)])
async def get_database_schema(
    request: Request,
    db: Session = Depends(get_support_portal_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account)
):
    """Returns information about the support portal database schema and tables."""
    inspector = inspect(support_portal_engine)
    schema_info = {
        "tables": {}
    }
    table_names = inspector.get_table_names()
    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        schema_info["tables"][table_name] = [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "default": col.get("default"),
                "primary_key": col.get("primary_key", 0) == 1,
            }
            for col in columns
        ]
        # You could add constraints, indexes etc. here too
        # schema_info["tables"][table_name]["indexes"] = inspector.get_indexes(table_name)
        # schema_info["tables"][table_name]["foreign_keys"] = inspector.get_foreign_keys(table_name)
        
    await log_support_audit_event(db=db, support_account_id=current_user.id, action="view_db_schema", ip_address=request.client.host) # Let service handle internal/public
    return schema_info

@router.get("/service-status", response_model=Dict[str, str], dependencies=[Depends(require_support_lead)])
async def get_service_status(
    request: Request,
    support_db: Session = Depends(get_support_portal_db),
    user_db: Session = Depends(get_db), # Add user DB session
    current_user: SupportPortalAccount = Depends(get_current_support_account)
):
    """Returns basic status information about the support portal and user APIs."""
    # Basic health check: try connecting to the database
    support_db_status = "Unknown"
    user_db_status = "Unknown"
    user_api_status = "Unknown"
    
    try:
        # Perform a simple query
        support_db.query(SupportPortalAccount).first() 
        support_db_status = "Connected"
    except Exception as e:
        support_db_status = f"Error connecting to support DB: {str(e)[:100]}..."

    try:
        # Perform a simple query on the user database
        user_db.query(User).first() # Assuming User model exists
        user_db_status = "Connected"
    except Exception as e:
        user_db_status = f"Error connecting to user DB: {str(e)[:100]}..."

    # Check User API Status
    try:
        # Use httpx for async request. Check a known endpoint, like /docs or a dedicated /health
        async with httpx.AsyncClient(timeout=5.0) as client: # 5 second timeout
            # Try hitting the /docs endpoint first as it's usually available
            response = await client.get(f"{USER_API_BASE_URL}/docs")
            if response.status_code == 200:
                 user_api_status = "Running"
            else:
                # Optionally, try a /health endpoint if /docs fails
                try:
                    response = await client.get(f"{USER_API_BASE_URL}/health") # Replace /health if different
                    if response.status_code == 200:
                        user_api_status = "Running (via /health)"
                    else:
                        user_api_status = f"Unexpected Status: {response.status_code}"
                except httpx.RequestError as health_err:
                     user_api_status = f"Error reaching /health: {str(health_err)[:100]}..."
                except Exception as health_e:
                     user_api_status = f"Error checking /health: {str(health_e)[:100]}..."
    except httpx.RequestError as req_err:
         user_api_status = f"Connection Error: {str(req_err)[:100]}..."
    except Exception as api_e:
         user_api_status = f"API Check Error: {str(api_e)[:100]}..."
             
    status_info = {
        "support_portal_status": "Running",
        "support_database_status": support_db_status,
        "user_api_status": user_api_status,
        "user_database_status": user_db_status,
        # Add checks for other dependent services if applicable
    }
    await log_support_audit_event(db=support_db, support_account_id=current_user.id, action="view_service_status", ip_address=request.client.host if request.client else None)
    return status_info 

# --- File Structure Endpoint (Requires Support Agent Role) ---

@router.get("/file-structure", response_model=Dict[str, Any], dependencies=[Depends(require_support_lead)])
async def get_project_file_structure(
    request: Request,
    # Optional query param to specify which root to view, defaults to project root
    # target_dir: Optional[str] = None, 
    db: Session = Depends(get_support_portal_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account)
):
    """Returns the file structure of the project directories as JSON."""
    project_root = Path(__file__).resolve().parents[4] # Adjust based on file location relative to project root
    # Define the paths to include in the structure view
    # Exclude sensitive or large directories like node_modules, .git etc. via the get_file_tree function itself
    paths_to_scan = {
        "backend": str(project_root / 'encompliance-backend'),
        "frontend": str(project_root / 'encompliance-frontend'),
        "storage": str(project_root / 'storage')
        # Add other relevant top-level dirs if needed
    }
    
    full_tree = {}
    for name, path_str in paths_to_scan.items():
        try:
            full_tree[name] = get_file_tree(path_str)
        except ValueError as e:
            full_tree[name] = {"error": str(e), "path": path_str}
        except Exception as e:
            # Catch other potential errors during scanning
            full_tree[name] = {"error": f"Unexpected error scanning {path_str}: {e}", "path": path_str}

    await log_support_audit_event(
        db=db, 
        support_account_id=current_user.id, 
        action="view_file_structure", 
        ip_address=request.client.host, # Let service handle internal/public
        details={"roots_scanned": list(paths_to_scan.keys())}
    )
    return full_tree 

# --- Regular User Listing (Requires Support Agent Role) ---
@router.get("/user-data", response_model=List[Dict[str, Any]], dependencies=[Depends(require_support_lead)])
async def read_regular_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account)
):
    """Retrieves a list of all user data."""
    try:
        # Load users with all their attributes
        users_query = db.query(User)
        
        # Execute query and convert to dictionaries with all fields
        users_data = []
        for user in users_query:
            # Get most recent QueryLog for this user to find their IP
            recent_query_log = db.query(QueryLog).filter(
                QueryLog.user_id == user.id,
                QueryLog.ip_address != None
            ).order_by(QueryLog.created_at.desc()).first()
            
            # Convert to dict and add all attributes dynamically, but skip sensitive fields
            user_dict = {}
            for column in inspect(User).columns:
                field_name = column.name
                if field_name not in ("hashed_password", "encrypted_settings"):
                    user_dict[field_name] = getattr(user, field_name)
            
            # Add IP address from query logs if available
            user_dict["ip_address"] = recent_query_log.ip_address if recent_query_log else None
            
            # Add query count
            query_count = db.query(QueryLog).filter(
                QueryLog.user_id == user.id
            ).count()
            user_dict["query_count"] = query_count
            
            users_data.append(user_dict)
        
        try:
            await log_support_audit_event(db=db, support_account_id=current_user.id, action="view_user_data", ip_address=request.client.host)
        except Exception as log_error:
            print(f"Non-critical error logging support action: {log_error}")
            
        return users_data
    except Exception as e:
        print(f"Error in read_regular_users: {str(e)}")
        # Return empty list instead of throwing 500 error
        return []

# --- User Data Export Management (Requires Admin Role) ---
@router.get("/user-data-exports", response_model=List[str], dependencies=[Depends(require_support_lead)])
async def list_user_data_exports(
    current_user: SupportPortalAccount = Depends(get_current_support_account)
):
    """
    Lists all folders containing archived deleted user data.
    """
    settings = get_settings()
    project_root = Path(__file__).resolve().parents[4]
    export_path = project_root / settings.USER_DATA_EXPORT_PATH
    exports = []
    if export_path.exists():
        for entry in sorted(export_path.iterdir()):
            if entry.is_dir():
                exports.append(entry.name)
    return exports

# --- AI Assistant Management (Requires Admin Role) ---
@router.post("/update-all-assistants", response_model=Dict[str, Any], dependencies=[Depends(require_support_lead)])
async def update_all_assistants(
    request: Request,
    db: Session = Depends(get_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account)
):
    """
    Updates all existing AI assistants with the latest system prompt.
    This will force update all user assistants to use the new instructions.
    """
    try:
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API key not configured"
            )
        
        openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Get all users who have OpenAI assistant IDs
        users_with_assistants = db.query(User).filter(
            User.openai_assistant_id.isnot(None)
        ).all()
        
        results = {
            "total_users": len(users_with_assistants),
            "updated_assistants": 0,
            "failed_updates": 0,
            "errors": []
        }
        
        for user in users_with_assistants:
            try:
                # Determine the model based on user's subscription
                model_name = "gpt-4.1-mini" if user.subscription_status == "pro" else "gpt-4.1-nano"
                
                # This will check and update the assistant if needed
                await get_or_create_user_assistant(
                    user_id=user.id,
                    db=db,
                    openai_client=openai_client,
                    model_name=model_name
                )
                
                results["updated_assistants"] += 1
                logger.info(f"Updated assistant for user {user.id}")
                
            except Exception as e:
                results["failed_updates"] += 1
                error_msg = f"Failed to update assistant for user {user.id}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        # Log the support action
        await log_support_audit_event(
            db=db,
            support_account_id=current_user.id,
            action="update_all_assistants",
            ip_address=request.client.host,
            details=results
        )
        
        return results
        
    except Exception as e:
        error_msg = f"Error updating assistants: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

# --- Database Data Viewer --- 
@router.get("/db-data", response_model=Dict[str, Any], dependencies=[Depends(require_support_lead)])
async def get_database_data(
    request: Request,
    support_db: Session = Depends(get_support_portal_db), 
    user_db: Session = Depends(get_db),
    current_user: SupportPortalAccount = Depends(get_current_support_account)
):
    """Returns information about tables and row counts for both databases."""
    db_data = {
        "support_db": {"type": "SQLite", "tables": {}},
        "user_db": {"type": "PostgreSQL", "tables": {}}
    }

    # --- Inspect Support DB (SQLite) ---
    try:
        support_inspector = inspect(support_portal_engine)
        support_table_names = support_inspector.get_table_names()
        for table_name in support_table_names:
            count = -1 # Default to -1 if count fails
            try:
                # Use Session for transaction context, though count is simple
                count_result = support_db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                count = count_result.scalar_one()
            except Exception as count_e:
                print(f"Error counting rows in support table {table_name}: {count_e}")
                
            columns = support_inspector.get_columns(table_name)
            db_data["support_db"]["tables"][table_name] = {
                "row_count": count,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "primary_key": col.get("primary_key", 0) == 1,
                    }
                    for col in columns
                ]
            }
    except Exception as support_e:
        print(f"Error inspecting support DB: {support_e}")
        db_data["support_db"]["error"] = str(support_e)

    # --- Inspect User DB (PostgreSQL) ---
    try:
        user_inspector = inspect(user_engine) # Use the main engine
        user_table_names = user_inspector.get_table_names()
        for table_name in user_table_names:
            count = -1
            try:
                # Use Session for transaction context
                count_result = user_db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                count = count_result.scalar_one()
            except Exception as count_e:
                print(f"Error counting rows in user table {table_name}: {count_e}")

            columns = user_inspector.get_columns(table_name)
            db_data["user_db"]["tables"][table_name] = {
                "row_count": count,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "primary_key": col.get("primary_key", 0) == 1,
                    }
                    for col in columns
                ]
            }
    except Exception as user_e:
        print(f"Error inspecting user DB: {user_e}")
        db_data["user_db"]["error"] = str(user_e)

    await log_support_audit_event(db=support_db, support_account_id=current_user.id, action="view_db_data", ip_address=request.client.host)
    return db_data 