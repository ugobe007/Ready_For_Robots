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

    -- ── Computed benchmark scores (0-100 each) ────────────────────────────
    score_mobility          FLOAT,   -- speed, terrain, stair
    score_manipulation      FLOAT,   -- payload, fingers, precision
    score_autonomy          FLOAT,   -- AI level, commercial deployments
    score_safety            FLOAT,   -- collision force, e-stop, certifications
    score_endurance         FLOAT,   -- battery life, charge time
    score_market_readiness  FLOAT,   -- commercial status, price, SDK
    score_total             FLOAT,   -- weighted composite

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
  'Humanoid robot specs and 6-dimension benchmark scores. Populated by scraper + scoring engine.';
