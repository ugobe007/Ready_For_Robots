-- Marketplace + SCOUT supply tracking + sales-agent persistence (Postgres)
-- Equivalent coverage for Alembic revisions:
--   f2a3b4c5d6e7_add_supply_outreach_tracking.py
--   f6a7b8c9d0e1_expand_marketplace_procurement.py
--   f7a8b9c0d1e2_add_sales_agent_opportunities.py
--
-- WHERE TO RUN THIS:
--   Supabase: Dashboard -> SQL Editor -> paste -> Run
--   psql:     psql "$DATABASE_URL" -f migrations/sql/f2_to_f7_marketplace_scout_sales.sql
--
-- This script is idempotent for direct SQL upgrades. If your backend deploy runs
-- `alembic upgrade head`, use Alembic instead of this direct SQL file.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- f2a3b4c5d6e7: supply-side outreach tracking
CREATE TABLE IF NOT EXISTS supply_outreach_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    robot_company_id INTEGER NOT NULL REFERENCES robot_companies (id) ON DELETE CASCADE,
    to_emails JSONB NOT NULL,
    from_email VARCHAR(320),
    reply_to VARCHAR(320),
    reply_token VARCHAR(80) NOT NULL UNIQUE,
    subject VARCHAR(512) NOT NULL,
    body_text TEXT NOT NULL,
    template_type VARCHAR(80) NOT NULL DEFAULT 'supply_pipeline',
    resend_id VARCHAR(128),
    status VARCHAR(32) NOT NULL DEFAULT 'draft_approved',
    is_test BOOLEAN NOT NULL DEFAULT false,
    payload JSONB,
    approved_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_supply_outreach_messages_robot_company_id ON supply_outreach_messages (robot_company_id);
CREATE INDEX IF NOT EXISTS ix_supply_outreach_messages_reply_to ON supply_outreach_messages (reply_to);
CREATE INDEX IF NOT EXISTS ix_supply_outreach_messages_reply_token ON supply_outreach_messages (reply_token);
CREATE INDEX IF NOT EXISTS ix_supply_outreach_messages_resend_id ON supply_outreach_messages (resend_id);
CREATE INDEX IF NOT EXISTS ix_supply_outreach_messages_status ON supply_outreach_messages (status);
CREATE INDEX IF NOT EXISTS ix_supply_outreach_messages_is_test ON supply_outreach_messages (is_test);
CREATE INDEX IF NOT EXISTS ix_supply_outreach_messages_approved_at ON supply_outreach_messages (approved_at);
CREATE INDEX IF NOT EXISTS ix_supply_outreach_messages_sent_at ON supply_outreach_messages (sent_at);

CREATE TABLE IF NOT EXISTS supply_outreach_replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supply_outreach_message_id UUID NOT NULL REFERENCES supply_outreach_messages (id) ON DELETE CASCADE,
    robot_company_id INTEGER NOT NULL REFERENCES robot_companies (id) ON DELETE CASCADE,
    from_email VARCHAR(320),
    to_email VARCHAR(320),
    subject VARCHAR(512),
    body_text TEXT,
    raw_payload JSONB,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_supply_outreach_replies_supply_outreach_message_id ON supply_outreach_replies (supply_outreach_message_id);
CREATE INDEX IF NOT EXISTS ix_supply_outreach_replies_robot_company_id ON supply_outreach_replies (robot_company_id);
CREATE INDEX IF NOT EXISTS ix_supply_outreach_replies_from_email ON supply_outreach_replies (from_email);
CREATE INDEX IF NOT EXISTS ix_supply_outreach_replies_received_at ON supply_outreach_replies (received_at);

-- f6a7b8c9d0e1: marketplace procurement expansion
ALTER TABLE buyer_profiles ADD COLUMN IF NOT EXISTS decision_makers JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE buyer_profiles ADD COLUMN IF NOT EXISTS procurement_workflow JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE buyer_profiles ADD COLUMN IF NOT EXISTS po_preferences JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE rfqs ADD COLUMN IF NOT EXISTS project_description TEXT;
ALTER TABLE rfqs ADD COLUMN IF NOT EXISTS timeline_summary TEXT;
ALTER TABLE rfqs ADD COLUMN IF NOT EXISTS decision_makers JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE rfqs ADD COLUMN IF NOT EXISTS workflow_process JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE rfqs ADD COLUMN IF NOT EXISTS technical_specs JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE rfqs ADD COLUMN IF NOT EXISTS schedule JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS marketplace_commercial_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfq_id UUID REFERENCES rfqs (id) ON DELETE CASCADE,
    proposal_id UUID REFERENCES rfq_proposals (id) ON DELETE SET NULL,
    buyer_team_id UUID NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    vendor_team_id UUID NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    created_by_user_id UUID REFERENCES user_profiles (id) ON DELETE SET NULL,
    document_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    document_number VARCHAR(120),
    title VARCHAR(240),
    amount NUMERIC(18, 2),
    currency VARCHAR(8) NOT NULL DEFAULT 'USD',
    due_at TIMESTAMPTZ,
    issued_at TIMESTAMPTZ,
    asset_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_marketplace_commercial_documents_rfq_id ON marketplace_commercial_documents (rfq_id);
CREATE INDEX IF NOT EXISTS ix_marketplace_commercial_documents_proposal_id ON marketplace_commercial_documents (proposal_id);
CREATE INDEX IF NOT EXISTS ix_marketplace_commercial_documents_buyer_team_id ON marketplace_commercial_documents (buyer_team_id);
CREATE INDEX IF NOT EXISTS ix_marketplace_commercial_documents_vendor_team_id ON marketplace_commercial_documents (vendor_team_id);
CREATE INDEX IF NOT EXISTS ix_marketplace_commercial_documents_created_by_user_id ON marketplace_commercial_documents (created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_marketplace_commercial_documents_document_type ON marketplace_commercial_documents (document_type);
CREATE INDEX IF NOT EXISTS ix_marketplace_commercial_documents_status ON marketplace_commercial_documents (status);
CREATE INDEX IF NOT EXISTS ix_marketplace_commercial_documents_document_number ON marketplace_commercial_documents (document_number);
CREATE INDEX IF NOT EXISTS ix_marketplace_commercial_documents_due_at ON marketplace_commercial_documents (due_at);
CREATE INDEX IF NOT EXISTS ix_marketplace_commercial_documents_issued_at ON marketplace_commercial_documents (issued_at);

CREATE TABLE IF NOT EXISTS marketplace_integration_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    created_by_user_id UUID REFERENCES user_profiles (id) ON DELETE SET NULL,
    connection_type VARCHAR(32) NOT NULL,
    name VARCHAR(180) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    base_url VARCHAR(1024),
    mcp_server_url VARCHAR(1024),
    auth_type VARCHAR(64),
    secret_ref VARCHAR(240),
    allowed_scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_checked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_marketplace_integration_connections_team_id ON marketplace_integration_connections (team_id);
CREATE INDEX IF NOT EXISTS ix_marketplace_integration_connections_created_by_user_id ON marketplace_integration_connections (created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_marketplace_integration_connections_connection_type ON marketplace_integration_connections (connection_type);
CREATE INDEX IF NOT EXISTS ix_marketplace_integration_connections_status ON marketplace_integration_connections (status);

CREATE TABLE IF NOT EXISTS rfq_schedule_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfq_id UUID NOT NULL REFERENCES rfqs (id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    title VARCHAR(240) NOT NULL,
    description TEXT,
    due_at TIMESTAMPTZ NOT NULL,
    reminder_offsets JSONB NOT NULL DEFAULT '[]'::jsonb,
    email_recipients JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'scheduled',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_rfq_schedule_events_rfq_id ON rfq_schedule_events (rfq_id);
CREATE INDEX IF NOT EXISTS ix_rfq_schedule_events_event_type ON rfq_schedule_events (event_type);
CREATE INDEX IF NOT EXISTS ix_rfq_schedule_events_due_at ON rfq_schedule_events (due_at);
CREATE INDEX IF NOT EXISTS ix_rfq_schedule_events_status ON rfq_schedule_events (status);

-- f7a8b9c0d1e2: SCOUT sales-agent opportunities
CREATE TABLE IF NOT EXISTS sales_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_type VARCHAR(32) NOT NULL,
    team_id UUID REFERENCES teams (id) ON DELETE CASCADE,
    crm_account_id UUID REFERENCES crm_accounts (id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies (id) ON DELETE SET NULL,
    robot_company_id INTEGER REFERENCES robot_companies (id) ON DELETE CASCADE,
    owner_user_id UUID REFERENCES user_profiles (id) ON DELETE SET NULL,
    title VARCHAR(240) NOT NULL,
    current_stage VARCHAR(64) NOT NULL DEFAULT 'new',
    status VARCHAR(32) NOT NULL DEFAULT 'open',
    automation_level VARCHAR(32) NOT NULL DEFAULT 'first_reply_auto',
    next_best_action JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_inbound_at TIMESTAMPTZ,
    last_outbound_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_sales_opportunity_type_crm_account UNIQUE (opportunity_type, crm_account_id),
    CONSTRAINT uq_sales_opportunity_type_robot_company UNIQUE (opportunity_type, robot_company_id)
);

CREATE INDEX IF NOT EXISTS ix_sales_opportunities_opportunity_type ON sales_opportunities (opportunity_type);
CREATE INDEX IF NOT EXISTS ix_sales_opportunities_team_id ON sales_opportunities (team_id);
CREATE INDEX IF NOT EXISTS ix_sales_opportunities_crm_account_id ON sales_opportunities (crm_account_id);
CREATE INDEX IF NOT EXISTS ix_sales_opportunities_company_id ON sales_opportunities (company_id);
CREATE INDEX IF NOT EXISTS ix_sales_opportunities_robot_company_id ON sales_opportunities (robot_company_id);
CREATE INDEX IF NOT EXISTS ix_sales_opportunities_owner_user_id ON sales_opportunities (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_sales_opportunities_current_stage ON sales_opportunities (current_stage);
CREATE INDEX IF NOT EXISTS ix_sales_opportunities_status ON sales_opportunities (status);
CREATE INDEX IF NOT EXISTS ix_sales_opportunities_last_inbound_at ON sales_opportunities (last_inbound_at);
CREATE INDEX IF NOT EXISTS ix_sales_opportunities_last_outbound_at ON sales_opportunities (last_outbound_at);

CREATE TABLE IF NOT EXISTS sales_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sales_opportunity_id UUID NOT NULL REFERENCES sales_opportunities (id) ON DELETE CASCADE,
    direction VARCHAR(16) NOT NULL,
    channel VARCHAR(32) NOT NULL DEFAULT 'email',
    source_type VARCHAR(64),
    source_id VARCHAR(80),
    from_email VARCHAR(320),
    to_email VARCHAR(320),
    subject VARCHAR(512),
    body_text TEXT,
    detected_intent VARCHAR(64),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_sales_messages_sales_opportunity_id ON sales_messages (sales_opportunity_id);
CREATE INDEX IF NOT EXISTS ix_sales_messages_direction ON sales_messages (direction);
CREATE INDEX IF NOT EXISTS ix_sales_messages_source_type ON sales_messages (source_type);
CREATE INDEX IF NOT EXISTS ix_sales_messages_source_id ON sales_messages (source_id);
CREATE INDEX IF NOT EXISTS ix_sales_messages_from_email ON sales_messages (from_email);
CREATE INDEX IF NOT EXISTS ix_sales_messages_detected_intent ON sales_messages (detected_intent);
CREATE INDEX IF NOT EXISTS ix_sales_messages_created_at ON sales_messages (created_at);

CREATE TABLE IF NOT EXISTS sales_agent_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sales_opportunity_id UUID NOT NULL REFERENCES sales_opportunities (id) ON DELETE CASCADE,
    action_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'planned',
    risk_level VARCHAR(32) NOT NULL DEFAULT 'low',
    requires_approval BOOLEAN NOT NULL DEFAULT false,
    stage_before VARCHAR(64),
    stage_after VARCHAR(64),
    detected_intent VARCHAR(64),
    recommendation TEXT,
    draft_subject VARCHAR(512),
    draft_body TEXT,
    resend_id VARCHAR(128),
    error TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_sales_agent_actions_sales_opportunity_id ON sales_agent_actions (sales_opportunity_id);
CREATE INDEX IF NOT EXISTS ix_sales_agent_actions_action_type ON sales_agent_actions (action_type);
CREATE INDEX IF NOT EXISTS ix_sales_agent_actions_status ON sales_agent_actions (status);
CREATE INDEX IF NOT EXISTS ix_sales_agent_actions_requires_approval ON sales_agent_actions (requires_approval);
CREATE INDEX IF NOT EXISTS ix_sales_agent_actions_detected_intent ON sales_agent_actions (detected_intent);
CREATE INDEX IF NOT EXISTS ix_sales_agent_actions_resend_id ON sales_agent_actions (resend_id);
CREATE INDEX IF NOT EXISTS ix_sales_agent_actions_sent_at ON sales_agent_actions (sent_at);

COMMIT;
