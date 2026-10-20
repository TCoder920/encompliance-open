import logging, os, json, shutil
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.document import Document
from app.models.query_log import QueryLog
from app.models.user_document import UserDocument
from app.core.config import get_settings
import enum

logger = logging.getLogger(__name__)

def serialize_value(value):
    """
    Convert SQLAlchemy model values to JSON-serializable format.
    Handles enums, datetime objects, and other non-serializable types.
    """
    if isinstance(value, enum.Enum):
        return value.value
    elif isinstance(value, datetime):
        return value.isoformat()
    elif hasattr(value, '__dict__'):
        # For complex objects, try to convert to dict
        return str(value)
    else:
        return value

def export_deleted_user_data(user: User, db: Session) -> str:
    """
    Exports all of a user's data and settings to a JSON file in storage/deleted-user-data.
    Returns the filepath of the exported directory.
    """
    settings = get_settings()
    # Determine export base directory from config (relative to project root or absolute)
    project_root = Path(__file__).resolve().parents[3]
    export_path_config = settings.USER_DATA_EXPORT_PATH
    base_path = Path(export_path_config)
    export_base = base_path if base_path.is_absolute() else project_root / base_path
    try:
        export_base.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create export base directory {export_base}: {e}")
        raise

    # Directory name: {user_id}_{timestamp}
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    folder_name = f"{user.id}_{timestamp}"
    export_dir = export_base / folder_name
    try:
        export_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create user export directory {export_dir}: {e}")
        raise
    data_file = export_dir / 'data.json'

    data = {}
    # Basic user fields, excluding sensitive - properly serialize enum and datetime values
    data['user'] = {}
    for col in user.__table__.columns:
        if col.name not in ('hashed_password', 'encrypted_settings'):
            value = getattr(user, col.name)
            data['user'][col.name] = serialize_value(value)
    
    # Settings (decrypt/parse if possible)
    try:
        if user.encrypted_settings:
            data['settings'] = json.loads(user.encrypted_settings.decode())
        else:
            data['settings'] = {}
    except Exception:
        data['settings'] = None

    # Documents metadata
    docs = db.query(Document).filter(Document.uploaded_by == user.id).all()
    data['documents'] = [
        {'id': d.id, 'filename': d.filename, 'filepath': d.filepath, 'file_type': d.file_type,
         'uploaded_at': d.uploaded_at.isoformat(), 'is_deleted': d.is_deleted,
         'deleted_at': d.deleted_at.isoformat() if d.deleted_at else None}
        for d in docs
    ]

    # Query logs
    qlogs = db.query(QueryLog).filter(QueryLog.user_id == user.id).all()
    data['query_logs'] = [
        {'id': q.id, 'query': q.query, 'response': q.response, 'operation_type': q.operation_type,
         'conversation_id': q.conversation_id, 'ip_address': q.ip_address,
         'created_at': q.created_at.isoformat() if q.created_at else None}
        for q in qlogs
    ]

    # User-document associations
    uds = db.query(UserDocument).filter(UserDocument.user_id == user.id).all()
    data['user_documents'] = [
        {'id': ud.id, 'regulation_id': ud.regulation_id, 'timestamp': ud.timestamp.isoformat()}
        for ud in uds
    ]

    try:
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to write data.json for user {user.id}: {e}")
        raise

    # Copy user files (documents) into files/ subdirectory
    files_dir = export_dir / 'files'
    try:
        files_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create files subdirectory {files_dir}: {e}")
    # Copy each document file
    for d in db.query(Document).filter(Document.uploaded_by == user.id).all():
        src_path = Path(d.filepath)
        # Resolve relative paths
        if not src_path.is_absolute():
            src_path = project_root / src_path
        try:
            if src_path.exists() and src_path.is_file():
                shutil.copy2(src_path, files_dir / src_path.name)
            else:
                logger.warning(f"Document file not found for user {user.id}: {src_path}")
        except Exception as e:
            logger.error(f"Error copying file {src_path} for user {user.id}: {e}")

    # Cleanup exports older than 30 days
    now = datetime.utcnow()
    retention = settings.USER_DATA_EXPORT_RETENTION_DAYS
    for entry in export_base.iterdir():
        try:
            mtime = datetime.utcfromtimestamp(entry.stat().st_mtime)
            if now - mtime > timedelta(days=retention):
                if entry.is_dir():
                    shutil.rmtree(entry)
                    logger.info(f"Removed old export directory {entry}")
                else:
                    entry.unlink()
                    logger.info(f"Removed old export file {entry}")
        except Exception as e:
            logger.error(f"Error cleaning up entry {entry}: {e}")

    return str(export_dir) 