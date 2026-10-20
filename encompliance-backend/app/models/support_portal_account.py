# Support portal account model
# ----------------------------
# Represents privileged support staff accounts that authenticate into the
# customer support portal. These accounts back the RBAC logic that powers
# queue management and ticket resolution workflows.

from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.database import SupportPortalBase
from datetime import datetime
import bcrypt

class SupportPortalAccount(SupportPortalBase):
    __tablename__ = "support_portal_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    roles = Column(JSON, nullable=True)  # Store roles as JSON array, e.g., ["super_admin", "viewer"]
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    def set_password(self, password: str):
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))

    def __repr__(self):
        return f"<SupportPortalAccount id={self.id} username={self.username} email={self.email}>"