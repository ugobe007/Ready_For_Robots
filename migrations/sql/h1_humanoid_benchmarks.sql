-- Migration: humanoid robot benchmark table
-- Stores scraped specs + computed 6-dimension benchmark scores

CREATE TABLE IF NOT EXISTS humanoid_benchmarks (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,              -- e.g. "Unitree G1"
    vendor          TEXT NOT NULL,              -- e.g. "Unitree"
    model_slug      TEXT NOT NULL UNIQUE,       -- e.g. "unitree-g1"
    product_url     TEXT,
    image_url       TEXT,
    status          TEXT NOT NULL DEFAULT 'available'
                    CHECK (status IN ('available','pilot','research','discontinued')),

    -- ── Raw specs (populated by scraper or manual seed) ───────────────────
    specs           JSONB NOT NULL DEFAULT '{}',
    -- Keys used by scorer:
    --   top_speed_mps, payload_kg, battery_life_h, charge_time_h,
    --   has_dexterous_hands, finger_count, can_climb_stairs, can_navigate_rough_terrain,
    --   autonomy_level (full|semi|teleoperated|research),
    --   has_estop, collision_force_n, safety_certified,
    --   price_usd, has_sdk, commercial_deployments (int),
    --   height_cm, weight_kg

    -- ── HEIF scores (0–4, HEIR 2026 framework) ───────────────────────────────
    heif_mobility          FLOAT,
    heif_manipulation      FLOAT,
    heif_cognition         FLOAT,
    heif_safety            FLOAT,
    heif_data_pipeline     FLOAT,
    heif_production        FLOAT,
    heif_total             FLOAT,

    -- ── Computed benchmark scores (0-100 each, HEIF × 25) ───────────────────
    score_mobility          FLOAT,   -- mobility
    score_manipulation      FLOAT,   -- manipulation
    score_autonomy          FLOAT,   -- cognition (legacy column name)
    score_safety            FLOAT,   -- safety
    score_endurance         FLOAT,   -- data pipeline (legacy column name)
    score_market_readiness  FLOAT,   -- production (legacy column name)
    score_total             FLOAT,   -- HEIF composite × 25

    -- ── Provenance ────────────────────────────────────────────────────────
    sources         JSONB DEFAULT '[]',         -- [{url, title, scraped_at}]
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_humanoid_benchmarks_vendor  ON humanoid_benchmarks (vendor);
CREATE INDEX IF NOT EXISTS idx_humanoid_benchmarks_status  ON humanoid_benchmarks (status);
CREATE INDEX IF NOT EXISTS idx_humanoid_benchmarks_score   ON humanoid_benchmarks (score_total DESC NULLS LAST);

COMMENT ON TABLE humanoid_benchmarks IS
  'Humanoid robot specs, HEIF scores (0–4), and HEIF-aligned 0–100 index. Populated by scraper + HEIR research overrides.';
