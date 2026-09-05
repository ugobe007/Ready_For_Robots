-- Optional Supabase RLS sketch for CRM tables (apply AFTER Alembic migration c7d8e9f0a1b2).
-- Adjust if your auth model differs. FastAPI + service role often bypasses RLS.
--
-- Prereq: auth.uid() matches user_profiles.id / team_members.user_id (UUID).

-- Helper: user belongs to team
-- CREATE OR REPLACE FUNCTION public.is_team_member(tid uuid)
-- RETURNS boolean AS $$
--   SELECT EXISTS (
--     SELECT 1 FROM public.team_members tm
--     WHERE tm.team_id = tid AND tm.user_id = auth.uid()
--   );
-- $$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Example policy pattern (uncomment and tailor):

-- ALTER TABLE public.crm_accounts ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY crm_accounts_select ON public.crm_accounts
--   FOR SELECT USING (
--     EXISTS (SELECT 1 FROM public.team_members tm WHERE tm.team_id = crm_accounts.team_id AND tm.user_id = auth.uid())
--   );
-- CREATE POLICY crm_accounts_insert ON public.crm_accounts
--   FOR INSERT WITH CHECK (
--     EXISTS (SELECT 1 FROM public.team_members tm WHERE tm.team_id = crm_accounts.team_id AND tm.user_id = auth.uid())
--   );
-- CREATE POLICY crm_accounts_update ON public.crm_accounts
--   FOR UPDATE USING (
--     EXISTS (SELECT 1 FROM public.team_members tm WHERE tm.team_id = crm_accounts.team_id AND tm.user_id = auth.uid())
--   );

-- Repeat for crm_engagements, crm_tasks, crm_notes, agent_runs (same team_id gate).
-- teams / team_members: restrict to members (select own membership; owners may invite — app logic).
