"""
RBAC Service
"""

from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.role import Role, Permission, UserRoleAssignment
from app.schemas.rbac import RoleCreate, RoleAssignmentCreate


class RBACService:
    """Manage roles, permissions, and assignments."""

    @staticmethod
    def create_role(db: Session, payload: RoleCreate) -> Role:
        role = Role(
            name=payload.name,
            description=payload.description,
            scope=payload.scope,
        )
        for code in payload.permissions:
            permission = RBACService._get_or_create_permission(db, code)
            role.permissions.append(permission)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def assign_role(db: Session, payload: RoleAssignmentCreate) -> UserRoleAssignment:
        assignment = UserRoleAssignment(
            user_id=payload.user_id,
            role_id=payload.role_id,
            facility_id=payload.facility_id,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def _get_or_create_permission(db: Session, code: str) -> Permission:
        permission = db.execute(
            select(Permission).where(Permission.code == code)
        ).scalar_one_or_none()
        if not permission:
            permission = Permission(code=code)
            db.add(permission)
            db.flush()
        return permission

