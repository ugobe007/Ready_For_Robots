-- Create user tables for profile, saved companies, lists, and AI reports
-- Run this in Supabase SQL Editor if migrations fail on Fly
-- Supabase Dashboard → SQL Editor → New query → paste & run

-- user_profiles
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY,
    email VARCHAR,
    display_name VARCHAR,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_user_profiles_email ON user_profiles (email);

-- user_saved_companies
CREATE TABLE IF NOT EXISTS user_saved_companies (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    company_id INTEGER NOT NULL,
    company_name VARCHAR NOT NULL,
    industry VARCHAR,
    tier VARCHAR,
    score FLOAT,
    website VARCHAR,
    notes TEXT,
    saved_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, company_id)
);
CREATE INDEX IF NOT EXISTS ix_user_saved_user_id ON user_saved_companies (user_id);

-- user_lists
CREATE TABLE IF NOT EXISTS user_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_user_lists_user_id ON user_lists (user_id);

-- user_list_companies
CREATE TABLE IF NOT EXISTS user_list_companies (
    list_id UUID NOT NULL,
    company_id INTEGER NOT NULL,
    company_name VARCHAR NOT NULL,
    added_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (list_id, company_id)
);

-- ai_reports
CREATE TABLE IF NOT EXISTS ai_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    company_id INTEGER NOT NULL,
    company_name VARCHAR NOT NULL,
    title VARCHAR,
    report_data JSONB,
    summary_card JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_ai_reports_user_id ON ai_reports (user_id);
