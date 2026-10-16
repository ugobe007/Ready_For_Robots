# Ready For Robots: site redesign build guide for copilot

**Owner:** Bob Christopher · **Date:** 2026-10-15 · **Repo:** github.com/ugobe007/Ready_For_Robots (main at `1ca3464a`, PR #329)
**Package:** this file sits in `rfr-site-design/` next to the design sources (`design/`), static renders (`static/`) and screenshots (`shots/`).

Read `CLAUDE.md` and `AGENTS.md` first. This guide doesn't override them.

---

## 0. What you are building

Ready For Robots finds **companies ready to buy or pilot robots** and tells robot sellers *which company, which workflow, and why now*.

- A **robot job** is work a robot can do at a company that is moving to automate it. It never means a job posting for a person.
- The unit of the product is **company × workflow × readiness signals**.
- Robot makers are **supply**. They are classified, never shown as buyers.

The redesign replaces the current home, results, buyer detail, CRM and pricing screens with six pages in one look ("Industrial Editorial"). Build to the designs in this package. Copy comes from `docs/website_copy_v1.md`; where the design and that doc differ, the design wins.

---

## 1. Package contents

| Folder | What it is | How to use it |
|---|---|---|
| `static/*.html` | Each page rendered to plain HTML in its first state. Open `static/Home.html` in a browser and click through. | Visual reference: layout, spacing, copy. Interactions (tabs, rotation, checkboxes) are frozen in their first state. |
| `design/*.dc.html` | Design sources. Markup plus a `renderVals()` class with the sample data and interaction logic. | Read the `renderVals()` blocks for the data each page needs and how its controls behave. Don't ship this format; rebuild in React. |
| `shots/*.png` | Full-page screenshots at 1440px wide. | Quick reference and for PR comparison. |

The live canvas (Bob's "RFR Home Redesign" artifact) has the same six pages with the interactions working.

---

## 2. Sitemap and what happens to today's pages

### New public pages

| Page | Route | Design file |
|---|---|---|
| Home | `/` | `Home` |
| Results: buyers for a robot | `/results?robot=<url>` (keep `/results`) | `Results` |
| Buyer detail | `/buyers/:buyerId?workflow=<w>` (new) | `Buyer` |
| Product picker (maker homepage pasted) | `/results` in "catalog" state | `Picker` |
| Pricing: early access | `/pricing` | `Pricing` |
| How it works | `/how-it-works` | Home section 4 (anchor or short page) |

### Signed-in pages

| Page | Route | Design file |
|---|---|---|
| My desk: Pipeline (tabs: Pipeline, New signals, My robots, Alerts) | `/desk` (redirect `/crm`, `/pipeline` here) | `Saved` |

### Today's routes (from `readyforrobots-new/client/src/App.tsx`)

| Today | Becomes |
|---|---|
| `/crm`, `/pipeline` (Lead Pipeline) | **My desk → Pipeline.** Redirect both to `/desk`. Keep `/api/jobs-crm/*` underneath for now. |
| `/signals` | **Buyer detail** "Why now" timeline and **My desk → New signals**. |
| `/my-robots` | **My desk → My robots** tab. |
| `/newsletter`, `/intelligence`, `/market-insights` | **Explore → The robot jobs brief.** One route `/newsletter`; others redirect. |
| `/robot-ready`, `/robots`, `/robots/report` | **Explore → Robot index.** |
| `/roi-calculator`, `/roi`, `/benchmark` | **Explore → RaaS ROI calculator.** |
| `/reports/benchmarking[/:industry]` | **Explore → Industry reports.** |
| `/about` (currently renders `Intelligence`) | **About**, linked from the footer. Copy: `website_copy_v1.md` §7. Not designed yet; use the same header/footer and type scale. |
| `/integrations/hubspot` | Behind "Sync to HubSpot" on My desk. |
| `/employer/:token`, employer match/draft | **Hold.** Returns after Phase 2 as "Post a robot job": a buyer describes the work, and that becomes a tier-A `direct_request` signal (proposal; needs Bob's sign-off and a spec change). |
| `/compare`, `/social`, `/marketplace`, `/sales-console`, `/sales-workflow`, `/supply-pipeline`, `/vendor/design` | Behind sign-in or admin. No public links. |
| `/icons`, `/icon-review`, `/experiment` | Remove from production builds. |
| `/login`, `/signup`, `/privacy`, `/terms`, `/support` | Keep; restyle to the new look. |

**Not designed yet** (build with the shared header/footer, and ask Bob before inventing layout): About, the four Explore pages, sign-in, the results empty state, Post a robot job.

---

## 3. User workflow

1. **Home.** Seller pastes a robot product page URL → **Find buyers**. No sign-in.
2. **Classify.**
   - Product page → classified robot (form, work, industries, "never matched to") → **Results**.
   - Maker homepage → **Picker**: "We found N robots. Pick the one to sell." Seller picks one or more → Results.
   - Not recognized → honest message plus "Try a product page". Never fall back to a sibling robot (fixed in #329; keep it that way).
3. **Results.** Ranked buyer list for that robot. Filters by industry, near (city), sort (strongest signal). Every card is marked **Example** until it comes from `rfr_opportunities` with sources. Whole list visible without sign-in.
4. **Buyer detail.** Tier, top signal, work, status; **Why now** timeline (date, tier chip, quote, source link); **Every workflow at this company** (exploring/committed/open/unknown); robots that fit; who usually decides.
5. **Save.** "Save buyers" or "Save buyer" → sign-in prompt only now (value first) → card lands in **My desk → Pipeline → Saved**.
6. **Work the deal.** Stages: Saved → Contacted → Meeting → Site assessment → Pilot → Won. Lost deals go under a filter, never deleted. A new signal on a saved buyer bumps the card and shows in **New signals**. Optional HubSpot sync.
7. **Pricing / early access.** Email, company, robot page → `POST /api/waitlist/founding-customer`.

---

## 4. Design system

### Tokens (put these in CSS variables or Tailwind theme)

| Token | Value | Use |
|---|---|---|
| `--ground` | `#EEF0EC` | Page background |
| `--ink` | `#111418` | Text, 2px rules, dark buttons, black band |
| `--rule` | `#C9CCC6` | 1px rules, borders |
| `--rule-soft` | `#E1E3DE` | Inner dividers |
| `--muted` | `#4A4F57` | Labels, secondary text |
| `--body-2` | `#30353C` | Long-form secondary text |
| `--faint` | `#6B7078` | Placeholders, tier E |
| `--accent` | `#C2410C` | Primary buttons, tier A, active nav, links in sources |
| `--example-fg` / `--example-bg` | `#7A3E00` / `#FFE3C2` | **Example** and **Sample data** badges |
| `--late` | `#B42318` | Overdue dates |
| `--surface` | `#FFFFFF` | Inputs, cards on desk |

### Type (Google Fonts)

- **Display:** Archivo 800/900, tight tracking (`-0.03em` to `-0.04em`), line-height 0.9–0.95. H1 `clamp(52px, 7vw, 104px)`.
- **Body:** IBM Plex Sans 400/500/600, 15–20px.
- **Labels:** IBM Plex Mono 500/600, 11–13px, uppercase, letter-spacing `0.12em`.

### Rules of the look

- No rounded corners, no shadows, no gradients. Structure comes from 2px ink rules and 1px gray rules.
- Max width 1296px (marketing) / 1392px (desk), 24px gutters.
- Tier letters are big Archivo 900; A is accent, B–D ink, E faint.
- Buttons: primary = accent fill, white Archivo 800; secondary = 2px ink border, transparent.
- Every page must work at 375px wide with no horizontal scroll (the desk's board may scroll inside its own container).

### Shared components

`SiteHeader` (public nav: Find buyers, How it works, Explore ▾, Pricing, Sign in, Get early access; signed-in nav: Find buyers, My desk, Explore, avatar) · `SiteFooter` (About, Newsletter, Privacy, Terms, Support) · `Eyebrow` (mono label row with bottom rule) · `ExampleBadge` · `TierLetter` · `TierChip` ("A · RFP") · `SignalRow` (tier chip, title, source line) · `StatusChip` (exploring = accent, committed = gray, open = ink, unknown = white) · `UrlInput` + button · `BuyerRow` · `PipelineCard`.

---

## 5. Page specs and the data each needs

### 5.1 Home (`design/Home.dc.html`)

Sections in order:
1. Hero: headline, subhead, URL input. Below: **Example case files** rotating every 6s across ADAM, Relay, Locus Origin, Neo, UR cobot. Tabs pick one and pause; a Pause button toggles. Left panel: the robot classified (form, main work, buyers, never). Right panel: one buyer with three "why now" lines. Both badged **Example**.
2. **Every buyer comes with evidence**: tiers A–E.
3. **One maker. Eight robots.**: the RichTech lineup, click a row to see form, work, buyers, never matched to, and "Find buyers for X". Data should come from `rfr_robot_products` (real classifications), not hardcoded, once Phase 2 persists them.
4. How it works, three steps (copy in the design is final).
5. Nine industries in rollout order.
6. Explore cards.
7. Early-access band (`[FOUNDING PRICE]` is Bob's decision; hide the line until set).

### 5.2 Results (`design/Results.dc.html`)

Data: classified robot (`product_name`, `company_name`, `form`, `primary_function`, `industries`, never-matched list) + list of opportunities: `buyer name`, `hq_city/state`, `industry`, `workflow`, `workflow status`, `top_tier`, up to 3 `reasons` (title, tier, source type, url, date), `is_example`.
Aside: "How we matched", "Left out" (committed workflows), "Also from {maker}" (siblings with their work, linking to their results; never auto-substituted).
Early-access banner shows while any card is Example.

### 5.3 Buyer detail (`design/Buyer.dc.html`)

Data: `rfr_buyers` row; all `rfr_signals` for the buyer (newest first, with tier, `evidence_text` quote, `source_url`, `observed_at`); all `rfr_workflows` for the buyer with `status` and `status_note`; matching robot products per workflow; decision roles (static by industry for now). "Response due" only when an RFP signal carries a due date.

### 5.4 Picker (`design/Picker.dc.html`)

Data: output of catalog discovery (`discover_product_pages` → classify each). Columns: pick, product, form, work, likely buyers, Find buyers. Button reads "Find buyers for N robots". "Wrong? Open a product and tell us" goes to a feedback form (stub is fine).

### 5.5 My desk (`design/Saved.dc.html`)

Six stage columns, cards with company, tier, work · robot, NEXT action, due (red when overdue), robot filter, Sync to HubSpot, + Find buyers. Tabs: Pipeline, New signals (count badge), My robots, Alerts. Drag to move cards. Mark everything **Sample data** until real saved buyers exist.
Backend: reuse `/api/jobs-crm/*` (keep, jobs, cal/desk) for storage now. Stage names must be the six above; the stage mapping from the old CRM stages is pending Bob's confirmation.

### 5.6 Pricing (`design/Pricing.dc.html`)

$0 founding customer, five features, form (work email, company, robot product page) → `POST /api/waitlist/founding-customer`. Three FAQs. "Need a hand?" services block. Remove the Basic/Pro/Premium tiers.

---

## 6. API

**Base URL (production):** `https://ready-2-robot.fly.dev` (Fly app `ready-2-robot`, region `iad`)
**Interactive docs:** `https://ready-2-robot.fly.dev/api/docs`
Frontend reads the base from `VITE_PUBLIC_API_URL`.

| Method | Path | File | Used by |
|---|---|---|---|
| GET | `/health`, `/health/db` | `app/main.py` | Smoke checks |
| POST | `/api/robot-job-search` (also `/api/v1/…`) | `app/api/robot_job_search.py` | Home → Results / Picker. Calls `try_phase2_search` when the flag is on. |
| POST | `/api/robot-job-match` (also `/api/v1/…`) | `app/api/robot_job_match.py` | Results list |
| GET | `/api/robot-job-card/{job_key}` (also `/api/v1/…`) | `app/api/robot_job_match.py` | Buyer detail (until the opportunities API ships) |
| GET | `/api/robot-jobs/preview` | `app/api/robot_jobs_preview.py` | Home examples |
| POST | `/api/robot-profile` · GET `/api/oem-listing` | `app/api/robot_profile.py` | Robot classification, My robots |
| GET | `/api/leads/match-url` | `app/api/leads.py` | Legacy URL match |
| * | `/api/jobs-crm/keep`, `/jobs`, `/jobs/task-model`, `/cal/desk`, `/skus`, `/apply-prep`, `/apply`, `/apply-selected`, `/applications/{id}/send` | `app/api/jobs_crm.py` | My desk |
| GET/POST | `/api/newsletter/edition`, `/subscribe`, `/generate` | newsletter router | Explore → brief |
| * | `/api/robot-ready/*` | `app/api/robot_ready.py` | Explore → robot index submissions |
| * | `/api/humanoid/*`, `/api/robot-companies/*` | `humanoid_benchmark.py`, `robot_companies.py` | Explore → robot index |
| POST | `/api/vendor-design/compute-roi` | `app/api/vendor_design.py` | Explore → ROI calculator |
| POST | `/api/waitlist`, `/api/waitlist/founding-customer` | `app/api/waitlist.py` | Pricing form, early-access band |
| * | `/api/integrations` (HubSpot), `/api/billing`, `/api/companies`, `/api/crm` | various | Desk sync, account |
| POST | `/api/employer-robot-match`, `/api/employer-job-draft` | `app/api/employer_jobs.py` | **On hold** (see §2) |

**Planned (spec Phase 5, not built yet):**
- `GET /api/v1/rfr/opportunities?robot_url=<url>` → classified robot + ranked opportunities (feeds Results).
- `GET /api/v1/rfr/opportunities?industry=<slug>&city=<city>` → opportunities by place (feeds filters and Explore).
- Buyer detail will need `GET /api/v1/rfr/buyers/{id}` (signals + workflows). Propose its shape in the PR; don't build without the spec update.

---

## 7. Database

- **Supabase Postgres.** Dashboard: `https://supabase.com/dashboard/project/lmoyydlhlgdyqbxkmkuz` (the project ref used across the repo's backup and deploy docs; confirm with Bob that it's production before touching anything).
- **Migrations:** Alembic, files in `migrations/versions/`. Single head: `rfr0a1b2c3d4` (`add_rfr_buyer_opportunity_tables`). Check production with `fly ssh console -a ready-2-robot -C "alembic current"`.
- **Connection:** `DATABASE_URL` (use the Supabase pooler on Fly). Agents get a **read-only** database user, never the production `DATABASE_URL`.

### RFR tables (from `rfr0a1b2c3d4`)

| Table | Key columns |
|---|---|
| `rfr_robot_products` | `source_url`, `company_name`, `product_name`, `page_type`, `offering_type`, `form`, `primary_class`, `primary_function`, `secondary_functions` (json), `industries` (json), `evidence` (json), `unsupported_facts` (json), `prompt_version`, `taxonomy_version`, `extracted_at` |
| `rfr_buyers` | `company_id` → `companies.id`, `name`, `name_normalized`, `website_domain`, `hq_city`, `hq_state`, `hq_country`, `priority`, `source`, `is_robot_maker` |
| `rfr_buyer_industries` | `buyer_id`, `industry`, `confidence`, `source`, `source_url` |
| `rfr_workflows` | `buyer_id`, `workflow`, `status` (default `unknown`), `status_source_url`, `status_note`, `committed_vendor` |
| `rfr_signals` | `buyer_id`, `workflow`, `signal_type`, `tier`, `intent_strength`, `title`, `evidence_text`, `source_url`, `source_feed`, `observed_at`, `expires_at` |
| `rfr_opportunities` | `buyer_id`, `workflow`, `score`, `top_tier`, `reasons` (json), `matched_robot_product_ids` (json), `computed_at` |

Legacy tables (`companies`, leads, jobs-crm, etc.) stay. Don't migrate or drop them in this work.

### Environment variable names (values live in Fly / Vercel secrets, never in files)

- **Backend (Fly):** `DATABASE_URL`, `SUPABASE_URL`, `ANTHROPIC_API_KEY`, `SAM_GOV_API_KEY`, `SAM_GOV_DAILY_REQUEST_LIMIT`, `PAUSE_JOB_POSTING_INGEST`, `RFR_BUYER_OPPORTUNITIES_V1`, `RFR_ALLOW_PAID_LLM`, `RFR_SENDER_DOMAINS`, `ADMIN_KEY` (alias `RFR_ADMIN_KEY`), `RFR_FLY_API`
- **Frontend (Vercel):** `VITE_PUBLIC_API_URL`, `VITE_SITE_URL`, `VITE_PUBLIC_SUPABASE_URL`, `VITE_PUBLIC_SUPABASE_ANON_KEY`, `VITE_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- Templates: `.env.example`, `readyforrobots-new/.env.example`. Vercel notes: `docs/vercel_production_secrets.md`, `docs/vercel_agent_spend.md`.

---

## 8. Tools and scripts

| Command | What it does |
|---|---|
| `python3 scripts/harness_snapshot.py` then `python3 scripts/harness_compile_memory.py` | Observe first; read `reports/compiled_memory_latest.json` |
| `python3 scripts/pstack_release.py --local --fly --evidence` | Release check (How / Act / Critic). Release authority. |
| `python3 scripts/snapshot_pages.py --benchmark <fixture> --out <dir> [--render] [--ids …] [--url ID=URL]` | Save robot pages for offline tests |
| `python3 scripts/test_understanding_v2_benchmark.py --robot <id> --hint on\|off --benchmark <fixture> --fixtures <dir> --output <file>` | Run the classifier benchmark (scorer and answer key are frozen) |
| `python3 scripts/rfr_import_seed.py [--apply]` | Seed buyers. Dry run unless `--apply`; `--apply` needs Bob's OK. |
| `python3 scripts/rfr_backfill_report.py --database-url <ro-url> --out <file>` | Read-only backfill report |
| `python3 scripts/rfr_industry_company_check.py` | Industry ↔ company sanity check |
| `python3 scripts/report_rows_by_source.py --json` | Row counts by source |
| `python3 scripts/harness_notify.py --mission <path>` | Notify when a mission is done |
| `pytest -q tests/…` | Targeted tests (137 passing on last run) |
| `cd readyforrobots-new && pnpm install && pnpm dev` | Frontend dev server (Vite + wouter) |
| `fly deploy -a ready-2-robot`, `fly logs -a ready-2-robot` | Backend deploy and logs (Bob or Deploy role) |

Fixtures: `tests/fixtures/taxonomy.v1.json` (v1.3), `robot_benchmark_set.v2.json`, `robot_holdout_set.v1.json`, `robot_holdout_set.v2.json`, `robot_oem_richtech_set.v1.json`; snapshots in `robot_pages`, `robot_pages_holdout`, `robot_pages_holdout_v2`, `robot_pages_richtech`.

---

## 9. Special functions you must respect

| Function / file | What it does | Rule for the UI |
|---|---|---|
| **Taxonomy** `tests/fixtures/taxonomy.v1.json` | Closed lists: 35 industries + `facility_services`, functions, 11 forms, 13 primary classes, 6 offering types; `industry_parents` (bar_nightclub→restaurant, surgery_center→hospital, k12_school→college_university); `industries._definition` (the buyer-operator rule) | Labels on screen come from the taxonomy. Never invent values. Show plain-English names (map slugs → labels in one place). |
| **Extractor** `app/services/robot_understanding_v1/taxonomy_extraction.py` (prompt v6) + `extraction_config.json` | Page type first; evidence check v2; unsupported facts excluded (cap 0.3); max 5 records/page; max_output_tokens 8192 | "Never matched to" and buyer industries come from this output. |
| **Record selection** | Picks the record matching the target product name or `target_aliases`; reports `target_not_extracted` / `target_not_on_page` | If the target isn't found, show "not recognized", not another product. |
| **Phase 2** `app/services/buyer_opportunity/phase2_match.py` | `buyer_opportunities_enabled()` reads `RFR_BUYER_OPPORTUNITIES_V1` (`1/true/yes`); `try_phase2_search`, `classified_match_payload`, `catalog_payload`, `unrecognized_payload`, `discover_product_pages`, `pick_product_record`, `merge_market_variants`, `industries_join`, `industries_for_match`, `jobs_for_classification`, `persist_classified_product` | The three payloads map to Results, Picker and the not-recognized state. |
| **Form fit** `app/services/form_fit.py` (`jobs_fit_form`, `indexed_sku`) | Stationary robots never match mobile work (ADAM never gets bussing or room service) | Drives "Never matched to". |
| **Provenance** `app/services/job_card_provenance.py` (`is_example_job`, `job_source_url`, `public_employer_email`) | Marks example cards; no minted emails | Every card with `is_example_job` shows the **Example** badge. No source link → no "verified/live" wording. |
| **Signal tiers** | A: `rfp_open`, `procurement_award` · B: `pilot_or_budget`, `modernization_plan` · C: `robotics_hiring` · D: `expansion` · E: `labor_pressure` (never creates a card alone) · `deployment` sets the workflow to **committed** | Tier letter/chip colors per §4. Committed workflows are left out of Results and listed on Buyer detail. |
| **Score** | A=100, B=60, C=40, D=25, E=10, with time decay; company-wide signals ×0.5; cap 200 | Sort "Strongest signal" uses `score`; show the tier, not the number. |
| **Robot makers** `rfr_buyers.is_robot_maker` | Supply side | Never shown as buyers. |

Pilot industries, in rollout order: warehouse/logistics/3PL · factories · hotels and casinos · hospitals (+ surgery centers) · retail · restaurants and bars · airports · offices (+ facility services) · auto dealerships.

---

## 10. Copy rules

1. One audience on public pages: robot sellers.
2. Plain words. Never on public pages: SIGNAL (as a label), HEIR, HEIF, FIND, Cal, "Profile A/B/C", "SKU", raw field names.
3. No number unless it comes from the database at render time; hide it if the query fails.
4. Nothing called "verified", "live" or "active" without a source link.
5. Value before sign-up: no wall before results.

---

## 11. Guardrails and how to ship

- **Database:** no deletes, bulk updates or schema changes without Bob's explicit approval and a confirmed backup. (In Oct 2026 an agent erased ~14,500 records.) This redesign needs **no schema change**.
- **PRs:** branch → **draft PR** → stop. Bob merges. Base every PR on `main`; never stack on another PR's branch (that's how #322 and #327 missed main).
- **Benchmarks:** answer key and scorer are frozen.
- **Secrets:** never in files, PR text or logs.
- **Hermes is retired.** Don't spawn it.
- **Don't commit** `reports/`.
- **Verify:** targeted pytest; real Vercel production build; Fly `/health`; screenshot each page at 1440 and 375 and attach them to the PR next to `shots/*.png`.

### Suggested PR order (each a separate draft PR)

1. **Design tokens + shared components** (header, footer, badges, tier letter/chip, signal row, status chip). No page changes.
2. **Home** to `Home` design, with the rotating examples and RichTech index (example data where the API isn't ready, badged).
3. **Results + Picker + not-recognized state** on today's `robot-job-search` / `robot-job-match` payloads.
4. **Buyer detail** at `/buyers/:id`, using `robot-job-card` until the opportunities API exists.
5. **Pricing** + founding-customer form wired to `/api/waitlist/founding-customer`.
6. **My desk** at `/desk`, redirects from `/crm` and `/pipeline`, Sample data badge.
7. **Route cleanup**: Explore menu, redirects in §2, remove dev routes, footer About.

**Done when:** a first-time visitor on phone and desktop can paste a robot URL without signing in, see all results, open a buyer, and only then be asked to sign in to save; every example card is badged; no banned words on public pages; and `pstack_release.py` passes.

### Open decisions for Bob (don't guess)

- Founding price.
- Mapping of old CRM stages to the six new stages.
- Format of the NEXT step on pipeline cards.
- Seed buyer list.
- "Post a robot job" (employer side) scope and timing.
