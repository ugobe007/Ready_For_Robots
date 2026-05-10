"""Marketplace and organization profile foundation for SCOUT workflows."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.database import Base


class OrganizationProfile(Base):
    __tablename__ = "organization_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    organization_type = Column(String(32), nullable=False, server_default="vendor")
    display_name = Column(String(240), nullable=True)
    website = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    automation_needs = Column(JSONB, nullable=False, server_default="[]")
    scout_preferences = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class VendorProfile(Base):
    __tablename__ = "vendor_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    robot_categories = Column(JSONB, nullable=False, server_default="[]")
    target_industries = Column(JSONB, nullable=False, server_default="[]")
    service_regions = Column(JSONB, nullable=False, server_default="[]")
    qualification_rules = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    procurement_categories = Column(JSONB, nullable=False, server_default="[]")
    facility_types = Column(JSONB, nullable=False, server_default="[]")
    buying_process = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class OrganizationAsset(Base):
    __tablename__ = "organization_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    asset_type = Column(String(64), nullable=False)
    filename = Column(String(512), nullable=False)
    mime_type = Column(String(160), nullable=True)
    storage_path = Column(String(1024), nullable=True)
    visibility = Column(String(32), nullable=False, server_default="private")
    asset_metadata = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Rfq(Base):
    __tablename__ = "rfqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(240), nullable=False)
    summary = Column(Text, nullable=True)
    automation_category = Column(String(120), nullable=True)
    status = Column(String(32), nullable=False, server_default="draft")
    budget_min = Column(Numeric(18, 2), nullable=True)
    budget_max = Column(Numeric(18, 2), nullable=True)
    currency = Column(String(8), nullable=False, server_default="USD")
    due_at = Column(DateTime(timezone=True), nullable=True)
    evaluation_criteria = Column(JSONB, nullable=False, server_default="[]")
    scout_summary = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RfqRequirement(Base):
    __tablename__ = "rfq_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_type = Column(String(64), nullable=False, server_default="general")
    body = Column(Text, nullable=False)
    priority = Column(String(32), nullable=False, server_default="required")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RfqInvitation(Base):
    __tablename__ = "rfq_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), nullable=False, server_default="invited")
    scout_match_score = Column(Numeric(5, 2), nullable=True)
    scout_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("rfq_id", "vendor_team_id", name="uq_rfq_invitations_rfq_vendor"),)


class RfqProposal(Base):
    __tablename__ = "rfq_proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(32), nullable=False, server_default="draft")
    proposal_title = Column(String(240), nullable=True)
    proposal_summary = Column(Text, nullable=True)
    price_estimate = Column(Numeric(18, 2), nullable=True)
    currency = Column(String(8), nullable=False, server_default="USD")
    asset_ids = Column(JSONB, nullable=False, server_default="[]")
    scout_response_plan = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("rfq_id", "vendor_team_id", name="uq_rfq_proposals_rfq_vendor"),)
