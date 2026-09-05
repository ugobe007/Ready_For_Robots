-- Shared L2 cache for pipeline leads, homepage, and admin snapshot (Supabase Postgres).
CREATE TABLE IF NOT EXISTS pipeline_cache_store (
    cache_key   TEXT PRIMARY KEY,
    data        JSONB NOT NULL DEFAULT '{}'::jsonb,
    built_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_cache_store_expires
    ON pipeline_cache_store (expires_at);
