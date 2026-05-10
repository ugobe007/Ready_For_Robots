-- SCOUT chat persistence (Postgres)
-- Equivalent to Alembic revision e2f3a4b5c6d7 (migrations/versions/e2f3a4b5c6d7_add_scout_chat_tables.py)
--
-- WHERE TO RUN THIS:
--   Supabase: Dashboard → SQL Editor → paste → Run
--   psql:     psql "$DATABASE_URL" -f migrations/sql/e2f3a4b5c6d7_scout_chat_tables.sql
--
-- PREREQUISITE: table `user_profiles` must already exist (it is referenced by user_id).
--
-- IMPORTANT (Vercel vs database):
--   Vercel deploys your frontend; it does NOT run Alembic or this SQL. Migrations apply
--   only to the Postgres database your FastAPI backend uses (e.g. Supabase SQL Editor,
--   GitHub Action, or wherever you run `alembic upgrade head`).
--
--   This script uses CREATE TABLE IF NOT EXISTS (safe to re-run in Supabase).
--   The Python Alembic migration uses plain CREATE TABLE. If you run this SQL first AND
--   later something else runs the same Alembic revision on the same DB, you can get
--   "relation already exists". Then stamp Alembic once on that same database:
--
--     INSERT INTO alembic_version (version_num)
--     SELECT 'e2f3a4b5c6d7' WHERE NOT EXISTS (
--       SELECT 1 FROM alembic_version WHERE version_num = 'e2f3a4b5c6d7'
--     );
--
--   If your API host runs `alembic upgrade head` on every deploy, you usually do not
--   need this .sql file—only run it when you want to apply schema directly in Supabase.

BEGIN;

CREATE TABLE IF NOT EXISTS scout_sessions (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(80) NOT NULL,
    user_id UUID REFERENCES user_profiles (id) ON DELETE SET NULL,
    robot_category VARCHAR(32),
    vertical TEXT,
    territory VARCHAR(128),
    company_name VARCHAR(256),
    company_url VARCHAR(512),
    conversation_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_scout_sessions_fingerprint UNIQUE (fingerprint)
);

CREATE INDEX IF NOT EXISTS ix_scout_sessions_user_id ON scout_sessions (user_id);

CREATE TABLE IF NOT EXISTS scout_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES scout_sessions (id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    skill_invoked VARCHAR(64),
    skill_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_scout_messages_session_id ON scout_messages (session_id);

CREATE TABLE IF NOT EXISTS scout_profiles (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES scout_sessions (id) ON DELETE CASCADE,
    companies_viewed JSONB NOT NULL DEFAULT '[]'::jsonb,
    drafts_approved JSONB NOT NULL DEFAULT '[]'::jsonb,
    signals_seen JSONB NOT NULL DEFAULT '[]'::jsonb,
    inferred_needs TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_scout_profiles_session_id UNIQUE (session_id)
);

COMMIT;
