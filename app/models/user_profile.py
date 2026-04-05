"""user_profiles — Supabase auth user rows (see migrations a1b2c3d4e5f6)."""
import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class UserProfile(Base):
    """
    Minimal ORM mapping so other models (e.g. team_members.user_id) can reference
    user_profiles.id. Must be imported before CRM models in app.models.__init__.
    """

    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)
