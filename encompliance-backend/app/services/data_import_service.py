"""
Data Import Service

Consumes exported datasets and restores core entities for a facility.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session

from app.models.note import Note
from app.models.document import Document
from app.models.user import User
from app.schemas.data_import import DataImportResult

logger = logging.getLogger(__name__)


class DataImportService:
    """Simple importer focused on documents and notes for now."""

    SUPPORTED_SECTIONS = {"notes", "documents"}

    @staticmethod
    def run_import(
        db: Session,
        facility_admin: User,
        payload: Dict[str, Any],
        dry_run: bool = True,
    ) -> DataImportResult:
        DataImportService._validate_sections(payload)
        created = 0
        warnings: List[str] = []

        try:
            if "notes" in payload:
                created += DataImportService._import_notes(
                    db=db,
                    facility_admin=facility_admin,
                    notes_payload=payload["notes"],
                    dry_run=dry_run,
                )
            if "documents" in payload:
                created += DataImportService._import_documents(
                    db=db,
                    facility_admin=facility_admin,
                    docs_payload=payload["documents"],
                    dry_run=dry_run,
                )
            if dry_run:
                db.rollback()
            else:
                db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("Import failed: %s", exc)
            warnings.append(str(exc))
            raise

        return DataImportResult(dry_run=dry_run, records_created=created, warnings=warnings)

    @staticmethod
    def _validate_sections(payload: Dict[str, Any]) -> None:
        unsupported = set(payload.keys()) - DataImportService.SUPPORTED_SECTIONS
        if unsupported:
            raise ValueError(f"Unsupported sections: {', '.join(sorted(unsupported))}")

    @staticmethod
    def _import_notes(
        db: Session,
        facility_admin: User,
        notes_payload: List[Dict[str, Any]],
        dry_run: bool,
    ) -> int:
        count = 0
        for raw_note in notes_payload:
            note = Note(
                user_id=facility_admin.id,
                title=raw_note.get("title", "Imported Note"),
                content=raw_note.get("content", ""),
            )
            db.add(note)
            count += 1
        if not dry_run:
            db.flush()
        return count

    @staticmethod
    def _import_documents(
        db: Session,
        facility_admin: User,
        docs_payload: List[Dict[str, Any]],
        dry_run: bool,
    ) -> int:
        count = 0
        for raw_doc in docs_payload:
            document = Document(
                title=raw_doc.get("title", "Imported Document"),
                user_id=facility_admin.id,
                storage_path=raw_doc.get("storage_path", ""),
                description=raw_doc.get("description"),
            )
            db.add(document)
            count += 1
        if not dry_run:
            db.flush()
        return count

