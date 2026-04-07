-- Optional manual DDL (Alembic migration f1a2b3c4d5e6 also performs this on upgrade).
-- Supabase SQL editor: safe to run if the column does not exist yet.

ALTER TABLE companies ADD COLUMN IF NOT EXISTS automation_profile JSONB;

-- Backfill is NOT done in SQL: rules_v1 logic lives in Python
-- (`build_automation_profile_dict_from_company`). After the column exists, run:
--   alembic upgrade head
-- or deploy so `alembic upgrade head` runs in release.
