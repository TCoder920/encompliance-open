"""
Schema Compatibility Utilities
-----------------------------
Utility helpers that make sure legacy SQLite/PostgreSQL databases
are brought up-to-date with the latest ORM schema expectations
without requiring a dedicated Alembic migration run on developer
machines. These helpers only run lightweight compatibility checks
such as creating missing tables or columns when we know the change
is backwards-compatible.
"""

from typing import Iterable, Set

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


def _get_columns(inspector, table_name: str) -> Set[str]:
    try:
        return {column["name"] for column in inspector.get_columns(table_name)}
    except SQLAlchemyError:
        return set()


def ensure_organization_schema(engine: Engine, logger=None) -> None:
    """
    Ensure legacy databases have the organizations table and the
    facilities.organization_id column that newer code depends on.
    """
    inspector = inspect(engine)

    def _log(message: str):
        if logger:
            logger.info(message)

    table_names: Iterable[str] = inspector.get_table_names()

    # Create organizations table when older databases are missing it.
    if "organizations" not in table_names:
        from app.models.organization import Organization  # Local import to avoid circular refs

        Organization.__table__.create(bind=engine, checkfirst=True)
        _log("Created missing organizations table for legacy database.")

        # Refresh inspector cache so subsequent calls see the new table
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

    # Add organization_id column to facilities when absent.
    facility_columns = _get_columns(inspector, "facilities")
    if "organization_id" not in facility_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE facilities ADD COLUMN organization_id INTEGER"))
        _log("Added organization_id column to facilities table for legacy database.")

