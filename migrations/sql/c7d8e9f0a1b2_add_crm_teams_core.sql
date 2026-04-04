-- Migration c7d8e9f0a1b2 — CRM teams core (PostgreSQL / Supabase SQL editor)
-- Mirrors: migrations/versions/c7d8e9f0a1b2_add_crm_teams_core.py
--
-- Prerequisites (must exist before running):
--   - public.user_profiles (id uuid PK)
--   - public.companies (id integer PK)
--
-- Idempotent: uses IF NOT EXISTS so re-runs skip objects that already exist (no 42P07).
-- Do not paste the Python Alembic file into the SQL editor.

BEGIN;

CREATE TABLE IF NOT EXISTS public.teams (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_teams_slug ON public.teams (slug);

CREATE TABLE IF NOT EXISTS public.team_members (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id uuid NOT NULL REFERENCES public.teams (id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES public.user_profiles (id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'member',
  created_at timestamptz DEFAULT now(),
  CONSTRAINT uq_team_members_team_user UNIQUE (team_id, user_id)
);

CREATE INDEX IF NOT EXISTS ix_team_members_team_id ON public.team_members (team_id);
CREATE INDEX IF NOT EXISTS ix_team_members_user_id ON public.team_members (user_id);

CREATE TABLE IF NOT EXISTS public.crm_accounts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id uuid NOT NULL REFERENCES public.teams (id) ON DELETE CASCADE,
  company_id integer REFERENCES public.companies (id) ON DELETE SET NULL,
  name text NOT NULL,
  website text,
  industry text,
  owner_user_id uuid,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_crm_accounts_team_id ON public.crm_accounts (team_id);
CREATE INDEX IF NOT EXISTS ix_crm_accounts_company_id ON public.crm_accounts (company_id);
CREATE INDEX IF NOT EXISTS ix_crm_accounts_owner_user_id ON public.crm_accounts (owner_user_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_crm_accounts_team_company
  ON public.crm_accounts (team_id, company_id)
  WHERE company_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.crm_engagements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id uuid NOT NULL REFERENCES public.teams (id) ON DELETE CASCADE,
  crm_account_id uuid NOT NULL REFERENCES public.crm_accounts (id) ON DELETE CASCADE,
  name text NOT NULL,
  stage text NOT NULL DEFAULT 'qualification',
  value_amount numeric(18, 2),
  currency text DEFAULT 'USD',
  owner_user_id uuid,
  status text NOT NULL DEFAULT 'open',
  opened_at timestamptz DEFAULT now(),
  closed_at timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_crm_engagements_team_id ON public.crm_engagements (team_id);
CREATE INDEX IF NOT EXISTS ix_crm_engagements_crm_account_id ON public.crm_engagements (crm_account_id);
CREATE INDEX IF NOT EXISTS ix_crm_engagements_owner_user_id ON public.crm_engagements (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_crm_engagements_status ON public.crm_engagements (status);

CREATE TABLE IF NOT EXISTS public.crm_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id uuid NOT NULL REFERENCES public.teams (id) ON DELETE CASCADE,
  crm_account_id uuid NOT NULL REFERENCES public.crm_accounts (id) ON DELETE CASCADE,
  engagement_id uuid REFERENCES public.crm_engagements (id) ON DELETE SET NULL,
  title text NOT NULL,
  body text,
  status text NOT NULL DEFAULT 'todo',
  priority text DEFAULT 'normal',
  due_at timestamptz,
  assignee_user_id uuid,
  source text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_crm_tasks_team_id ON public.crm_tasks (team_id);
CREATE INDEX IF NOT EXISTS ix_crm_tasks_crm_account_id ON public.crm_tasks (crm_account_id);
CREATE INDEX IF NOT EXISTS ix_crm_tasks_engagement_id ON public.crm_tasks (engagement_id);
CREATE INDEX IF NOT EXISTS ix_crm_tasks_assignee_user_id ON public.crm_tasks (assignee_user_id);
CREATE INDEX IF NOT EXISTS ix_crm_tasks_due_at ON public.crm_tasks (due_at);

CREATE TABLE IF NOT EXISTS public.crm_notes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id uuid NOT NULL REFERENCES public.teams (id) ON DELETE CASCADE,
  crm_account_id uuid NOT NULL REFERENCES public.crm_accounts (id) ON DELETE CASCADE,
  engagement_id uuid REFERENCES public.crm_engagements (id) ON DELETE SET NULL,
  author_user_id uuid NOT NULL,
  body text NOT NULL,
  source text DEFAULT 'user',
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_crm_notes_team_id ON public.crm_notes (team_id);
CREATE INDEX IF NOT EXISTS ix_crm_notes_crm_account_id ON public.crm_notes (crm_account_id);

CREATE TABLE IF NOT EXISTS public.agent_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id uuid NOT NULL REFERENCES public.teams (id) ON DELETE CASCADE,
  user_id uuid NOT NULL,
  crm_account_id uuid NOT NULL REFERENCES public.crm_accounts (id) ON DELETE CASCADE,
  engagement_id uuid REFERENCES public.crm_engagements (id) ON DELETE SET NULL,
  model text,
  prompt_version text,
  input_json jsonb,
  output_json jsonb,
  tokens_in integer,
  tokens_out integer,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_agent_runs_team_id ON public.agent_runs (team_id);
CREATE INDEX IF NOT EXISTS ix_agent_runs_user_id ON public.agent_runs (user_id);
CREATE INDEX IF NOT EXISTS ix_agent_runs_crm_account_id ON public.agent_runs (crm_account_id);
CREATE INDEX IF NOT EXISTS ix_agent_runs_created_at ON public.agent_runs (created_at);

CREATE TABLE IF NOT EXISTS public.crm_playbook_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id uuid REFERENCES public.teams (id) ON DELETE CASCADE,
  name text NOT NULL,
  slug text,
  definition jsonb NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_crm_playbook_templates_team_id ON public.crm_playbook_templates (team_id);
CREATE INDEX IF NOT EXISTS ix_crm_playbook_templates_slug ON public.crm_playbook_templates (slug);

COMMIT;
