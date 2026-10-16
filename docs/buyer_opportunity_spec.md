# RFR Build Spec: Buyer Opportunities v1

**Owner:** Bob Christopher · **Status:** approved for build · **Version:** 1.6 (2026-10-14: lexicon §0, 9th group auto dealerships, restaurants include bars, signal dedupe by workflow; v1.5 taxonomy v1.2 industries in pilot groups; v1.4 product-not-company rule and maker catalog discovery; v1.3 form-fits-work matching rule; earlier: "robot job" definition, automation-intent signals, stage mapping, Phase 0.5)
**Location in repo:** `docs/buyer_opportunity_spec.md`

This document is the source of truth for what the agent builds next. If code, older docs, or `AGENTS.md` disagree with it, this document wins. If something here is unclear or seems wrong, **stop and ask Bob**; do not decide product meaning yourself. Changes to this spec require Bob's approval.

---

## 0. Words we use (Bob's lexicon)

| Word | Meaning |
|---|---|
| **Robot** | A **classification**: what kind of robot it is (form, primary class, functions, industries from the taxonomy). "A cleaning AMR," "a stationary drink-making arm." |
| **Product** | A specific named item a maker sells, and its **description** (its product page). ADAM, Titan, DUST-E S. Each product is classified as a robot. |
| **Maker** (OEM) | The company that makes products. One maker usually has many products of different robot classes. Supply, never a buyer. |
| **Robot job** | Work a robot can perform at a company that is moving to automate it. |
| **Workflow** | The kind of work (taxonomy `functions`) at a buyer, e.g., cleaning, drink-making. |
| **Buyer** | A company that could buy robots for its workflows. |
| **Signal** | Sourced evidence that a buyer is moving to automate a workflow. |

In code and files: entries describing specific items are **products** (e.g., the RichTech set uses `products`); the benchmark runner reads `products` and still accepts the older `robots` key.

**Addendum:** [Robot profile lifecycle](robot_profile_lifecycle.md). It extends this spec. Where they disagree, this document wins until Bob approves a change.

## 1. What we are building

Ready For Robots finds companies that are ready to buy or pilot robots, and tells robot sellers **which company, which workflow, and why now**.

- **A "job" in RFR is work a robot can perform.** A person may do that work today; what makes it a robot job is that the company is moving to **automate** it. Companies looking for automation are looking for robots, not people. "Robot Job Cards" stays as the product term, with this meaning only.
- A **robot job** (buyer opportunity) = **company × workflow × readiness signals.**
- Companies rarely say "we want robots." They describe **automation intent** in their own words ("streamline our production line," "improve operational efficiency," "reduce workflow friction"). Recognizing that language and tying it to a workflow is core to the product (§5a).
- A **workflow** is a kind of work at a company that a robot could be hired to do (cleaning, delivery, food prep…). Workflows use the same values as the robot taxonomy's `functions`, so robots and buyers join directly.
- A company that already deployed robots in a workflow is **committed in that workflow**, not as a company. Other workflows at that company can still be open.
- The sales window is **before** a company commits: budgeting, modernizing, labor pressure, exploring, piloting. **A published RFP means budget is confirmed, which makes it the strongest signal.**
- Job postings for people are never the product. At most they are a weak labor-pressure signal on a company's workflow.
- Robot makers are supply. They are classified, never treated as buyers.

**The end-to-end flow:**

```
Robot URL ──► classify robot (taxonomy extractor, prompt v4)
                 │  primary_function, industries
                 ▼
          join on workflow (= function) and industry
                 ▼
Buyers ──► workflows (status: open/exploring/piloting/committed)
                 ▼
          rank by readiness signals, drop committed workflows
                 ▼
          Buyer cards: company · workflow · why now · matching robots
```

---

## 2. Scope for v1

- **Pilot industries** (config: `rfr_config.pilot_industries`), **confirmed by Bob**, in priority order. Each group maps to taxonomy industry values:

  | Priority | Group | Taxonomy industries |
  |---|---|---|
  | 1 | Warehouse, logistics, 3PL | `warehouse_distribution`, `3pl`, `logistics_parcel` |
  | 2 | Factories | `manufacturing`, `food_manufacturing` |
  | 3 | Hotels and casinos | `hotel`, `casino` |
  | 4 | Hospitals | `hospital`, `surgery_center` |
  | 5 | Retail | `retail_store`, `grocery`, `shopping_mall` |
  | 6 | Restaurants and bars | `restaurant`, `qsr_fast_food`, `bar_nightclub` |
  | 7 | Airports | `airport` |
  | 8 | Office buildings | `office_building`, `commercial_building`, `corporate_campus` |
  | 9 | Auto dealerships | `automotive_dealership` (sales, service and parts departments) |

  Matching and the UI show only buyers in these industries until Bob expands the list. **Priority order sets build order:** when a phase can't cover every group at once (sources, seed import checks, signal classifiers), do group 1 first and work down. Other taxonomy industries (construction, energy, government, defense, schools, transit, etc.) stay in the data model but are hidden. `residential_consumer` is never a buyer. Taxonomy is v1.2 (adds bars/nightclubs, surgery centers, automotive dealerships, K-12 schools, transit, residential); `industry_parents` in the taxonomy says which new industries also count as an older one.

  **Restaurants include their bars** (Bob: almost all restaurants have bars). `restaurant` covers the restaurant and its bar; `bar_nightclub` is for standalone bars, lounges and nightclubs, and counts as `restaurant` through `industry_parents`. So a drink robot like ADAM matches restaurants as well as standalone bars. The extractor prompt includes each industry's **description**, not just its name, so the model sees these definitions (rule change: measured on the next fresh test set).
- **Geography:** United States. Las Vegas metro is a priority view (filter), not a limit.
- **Robots:** any robot the extractor classifies. Buyers are shown only for robots whose industries overlap the pilot industries.

---

## 3. Rules that apply to every phase

1. **Additive only.** New tables via new Alembic migrations. **No deletes, drops, renames, or bulk updates of existing tables** (`companies`, `signals`, `robot_jobs`, etc.). Existing tables are read-only inputs and stay as an archive.
2. **Feature flag.** Everything user-facing sits behind `RFR_BUYER_OPPORTUNITIES_V1` (default off). The old flow keeps working until Bob switches.
3. **One phase = one draft PR.** Each PR states what it does, shows its acceptance evidence, and stops. Bob merges and deploys.
4. **Explainable over clever.** Every score and match must be explainable in one sentence on the card. No opaque models for ranking in v1.
5. **Evidence or nothing.** Every industry, workflow status, and signal row carries a source URL or `source = bob_seed`. No invented facts.
6. **Report honestly.** Say what was run and verified. Estimates are labeled as estimates.

---

## 4. Data model (new tables, prefix `rfr_`)

All IDs are integers unless stated. `taxonomy` refers to `tests/fixtures/taxonomy.v1.json` (v1.2); enum values come from that file, never hard-coded.

### 4.1 `rfr_robot_products`
One row per robot product classified by the extractor.

| Column | Notes |
|---|---|
| id | PK |
| source_url | page the product was extracted from |
| company_name | robot maker |
| product_name | |
| page_type | from extractor (only `manufacturer_product_page` rows are matchable) |
| offering_type, form, primary_class, primary_function | taxonomy values; null if unsupported |
| secondary_functions | JSON list |
| industries | JSON list of taxonomy industries (supported facts only) |
| evidence | JSON: field → quote |
| unsupported_facts | JSON |
| prompt_version, taxonomy_version | |
| extracted_at | |

Re-classifying a URL creates new rows; the newest per (source_url, product_name) is current.

### 4.2 `rfr_buyers`
A company that could buy robots. Links to the existing `companies` row when one exists; never modifies it.

| Column | Notes |
|---|---|
| id | PK |
| company_id | FK `companies.id`, nullable |
| name, website_domain | |
| hq_city, hq_state, hq_country | |
| priority | `A`/`B`/`C` from Bob's seed, else null |
| source | `bob_seed`, `backfill_companies`, `sam_gov`, `news`, … |
| is_robot_maker | bool. If true, never shown as a buyer. |
| created_at, updated_at | |

Unique on `website_domain` when present; otherwise on normalized name.

### 4.3 `rfr_buyer_industries`
| Column | Notes |
|---|---|
| buyer_id | FK |
| industry | taxonomy industry |
| confidence | 0–1 |
| source, source_url | |

Industry means the industry of the buyer itself (the organization that would buy and operate the robot), same definition as the extractor.

### 4.4 `rfr_workflows`
One row per buyer × workflow that matters.

| Column | Notes |
|---|---|
| buyer_id | FK |
| workflow | taxonomy `functions` value |
| status | `unknown` · `open` · `exploring` · `piloting` · `committed` |
| status_source_url, status_note | evidence for the status |
| committed_vendor | if committed: who (e.g., robot maker) |
| updated_at | |

### 4.5 `rfr_signals`
| Column | Notes |
|---|---|
| id | PK |
| buyer_id | FK |
| workflow | taxonomy function, nullable (company-wide signal) |
| signal_type | see §5 |
| tier | `A`–`E` (derived from type) |
| intent_strength | `explicit` or `implicit` (§5a); null for signal types where it doesn't apply |
| title | short, human-readable |
| evidence_text | quote from the source |
| source_url | required (except `bob_seed`) |
| source_feed | e.g., `sam_gov`, `news_rss`, `ats_board`, `bob_seed` |
| observed_at | when the source says it happened |
| expires_at | e.g., RFP response deadline |
| created_at | |

Dedupe on (buyer_id, signal_type, workflow, source_url), since one source can give one signal per workflow (§5a). The unique index must treat a null `workflow` as one value (`UNIQUE NULLS NOT DISTINCT`, or index `COALESCE(workflow, '')`), so a company-wide signal from one source stays one row on re-import.

### 4.6 `rfr_opportunities`
Computed by the matcher (Phase 4). Rebuilt on a schedule; safe to truncate and recompute **this table only**.

| Column | Notes |
|---|---|
| buyer_id, workflow | the opportunity |
| score | see §6 |
| top_tier | best signal tier present |
| reasons | JSON list of one-line explanations (from signals) |
| matched_robot_product_ids | JSON list |
| computed_at | |

---

## 5. Signal types and tiers

| Tier | signal_type | What it is | Example | Default life |
|---|---|---|---|---|
| **A** | `rfp_open` | Published RFP/RFQ/bid for robots or automation in a workflow | SAM.gov notice for hospital delivery robots | until `expires_at` |
| **A** | `procurement_award` | Award/contract just made for automation in a related workflow (expansion likely) | contract award notice | 365 days |
| **B** | `pilot_or_budget` | Announced pilot, budget line, or stated plan to automate a workflow | earnings call: "piloting cleaning robots" | 365 days |
| **B** | `modernization_plan` | Stated modernization program covering the workflow | press release on property modernization | 365 days |
| **C** | `robotics_hiring` | Buyer (not robot maker) hiring robotics/automation roles | "Robotics Program Manager" at a hospital system | 120 days |
| **D** | `expansion` | New building, property, DC, or major renovation | new resort tower, new fulfillment center | 365 days |
| **E** | `labor_pressure` | Repeated/high-volume postings for people in the workflow, or reported labor shortage | many custodial openings at one property | 60 days |
| — | `deployment` | Robot deployed in a workflow. **Sets workflow status; adds no score.** | resort deploys floor scrubbers | n/a |

Rules:
- `labor_pressure` alone never creates an opportunity card. It can only add to a card that has another signal, or to a buyer in Bob's seed list.
- `robotics_hiring` requires the hiring company to be a buyer (`is_robot_maker = false`).
- A signal must name or clearly imply a workflow to attach to it; otherwise `workflow = null` (company-wide, counts for all of that buyer's workflows at half weight).

---

## 5a. Automation intent: reading how companies say it

Companies signal robot jobs in business language, not robot language. The classifier must recognize the **meaning**, the same way the robot extractor reads "physical AI for the construction workforce" as a construction robot.

**Do not build this as keyword or regex matching.** Use the same approach as the robot extractor: an LLM reads the source, chooses from closed values (signal type, workflow, intent strength), and quotes its evidence, which must pass the evidence check. The lexicon file below is a set of **examples and test cases**, not a list of patterns.

**Intent strength**

| Strength | What it sounds like | Examples | Treatment |
|---|---|---|---|
| **explicit** | Names automation, robots, or a specific automation technology | "automate our fulfillment centers", "deploying AMRs", "robotic palletizing pilot", "automation engineer" | Full weight for its signal type |
| **implicit** | Business goals that, **tied to a physical workflow**, mean automation | "streamline our production line" (Clorox-style), "improve operational efficiencies" or "reduce workflow friction" in distribution (Sysco-style), "increase throughput", "reduce manual handling", "modernize our warehouses", "labor productivity initiatives", "capex for supply chain transformation" | `modernization_plan` at **0.6 × weight**. Must name or clearly imply a workflow; otherwise company-wide |
| **generic** | Corporate language with no physical workflow | "operational excellence", "digital transformation", "efficiency across the enterprise" | **Not a signal.** Not stored. |

**Rules**
- Implicit intent counts only when the text ties it to physical work the taxonomy covers (production line, warehouse, kitchen, housekeeping, patient transport, cleaning…). "Efficiency" about software, finance, or staffing alone is generic.
- One source can produce several signals (e.g., a 10-K mentioning both warehouse automation and store modernization). Each gets its own workflow and evidence quote.
- The industry rule still applies: the buyer is the company doing the work (Clorox = `manufacturing`; Sysco = `warehouse_distribution` / `logistics_parcel`).

**Lexicon file:** `data/seed/automation_intent_lexicon.csv`. Each row is an example phrase with its intent strength, workflows, industries, and signal type. Bob adds rows as he spots new phrasing. Used in the classifier prompt as examples **and** as a test set: every row must classify as labeled before a classifier change merges. Hold-out discipline applies: new rows are added before a run, never in response to that run's results.

**Best sources for this language:** public filings (SEC EDGAR 10-K, 10-Q, 8-K), earnings call transcripts, investor-day presentations, capex announcements, and press releases. These are where companies like Clorox and Sysco describe operational plans.

---

## 6. Workflow status and scoring

**Status rules**
- A `deployment` signal sets that workflow to `committed`.
- Existing `deployment_events.deployment_stage` maps as follows. **Confirmed by Bob:** `PILOT` and `PROOF_OF_CONCEPT` → `piloting`. **Proposed (Bob to confirm):** `EVALUATION` → `exploring`; `LIVE_DEPLOYMENT` and `COMMERCIAL_DEPLOYMENT` → `committed`; any other stage → no status change, listed in a report. The mapping lives in config.
- `pilot_or_budget` sets `piloting` or `exploring` per the evidence.
- `rfp_open` sets `exploring` unless already `committed`.
- Otherwise `open` if any signal exists, else `unknown`.

**Committed workflows are never shown as opportunities.** The card for that buyer can mention them ("already using cleaning robots"), which also tells the seller about adjacent workflows.

**Score (explainable, v1)**

```
weight:  A=100, B=60, C=40, D=25, E=10
decay:   1.0 until half of the signal's life has passed, then linear to 0 at end of life
company-wide signals count at 0.5 × weight
score = Σ (weight × decay) over the opportunity's live signals, capped at 200
top_tier = best tier present
```

Sort cards by `top_tier`, then `score`, then most recent signal. Weights live in config, not code.

---

## 7. Matching

For a robot product R (current row, `page_type = manufacturer_product_page`):

1. Candidate workflows = `R.primary_function` (required) plus `R.secondary_functions` (shown as secondary matches, lower in the list).
2. Candidate buyers = buyers with an industry in `R.industries` ∩ pilot industries **and** a workflow row in the candidate workflows whose status is not `committed`.
3. If R has no industries, use the industries most common for its `primary_class` (config map), and label the card "industry inferred".
4. Exclude `is_robot_maker` buyers.
5. **Form must fit the work.** Workflows that move through a building (`delivery_transport`, `serving_hospitality` table-running and bussing, `cleaning`, `security_patrol`) require a mobile form (AMR, mobile manipulator, legged, humanoid, autonomous vehicle, drone). A fixed or stationary robot (`robotic_arm_cobot`, `fixed_gantry_system`, `portable_stationary_unit`) never matches them, even if the industry fits. Example: RichTech ADAM is a stationary drink-making and drink-serving station for restaurants, hotels and bars; it matches `food_beverage_prep` (drink stations, bars, cafés), never bussing, room service, or food running. The compatibility table lives in config.
6. Rank per §6.

Reverse view (for the home page): opportunities sorted by §6, each listing the robot products that match its workflow and industry.

---

## 8. Buyer card (UI)

Each card shows:
- **Company** (name, location, industry)
- **Workflow** (e.g., "Room-service delivery") and its status
- **Why now:** top 3 reasons, each one line with source link and date (e.g., "RFP open until Nov 30 — SAM.gov")
- **Top tier badge** (A–E) and score
- **Matching robots** (from `rfr_robot_products`), primary matches first
- **Already committed elsewhere** (if any): "Uses cleaning robots (Vendor X)"

No contact data, outreach, or upgrade prompts on the card in v1. Value first.

API: `GET /api/v1/rfr/opportunities?robot_url=…` and `GET /api/v1/rfr/opportunities?industry=…&city=…`. Both behind the feature flag.

---

## 9. Data sources

| Source | Feeds | Notes |
|---|---|---|
| **Bob's seed list** (`data/seed/rfr_seed_accounts.csv`) | buyers, industries, workflows, known deployments | Highest trust. Import script is idempotent and only inserts/updates `rfr_*` rows. |
| **Backfill from `companies`** | buyers, industries | Map free-text `companies.industry` to taxonomy via `data/seed/industry_synonyms.csv`. Unmapped companies go in a review report, not guessed. Skip companies whose only source was job-posting feeds unless Bob approves. |
| **SAM.gov** (running) | `rfp_open`, `procurement_award` | Buyer = the agency or facility. Tag `government`/`defense` **and** the industry of the facility doing the work (VA medical center → `hospital`, distribution depot → `warehouse_distribution`, airport authority → `airport`), so government RFPs show up in pilot industries. Keyword list in config. Respect `SAM_GOV_DAILY_REQUEST_LIMIT`. |
| **SEC filings + earnings calls** (new) | `modernization_plan`, `pilot_or_budget`, `expansion`, `deployment` | SEC EDGAR (free API) for 10-K/10-Q/8-K; earnings transcripts where licensed. Classified per §5a. Start with public companies in Bob's seed list. |
| **RFP marketplace scraper** (idle) | `rfp_open` | Revive outside Celery (Fly scheduled machine or GitHub Action). Separate PR. |
| **News / RSS** (existing) | `pilot_or_budget`, `modernization_plan`, `expansion`, `deployment` | Classify each article into a signal type with an evidence quote; same evidence check as the extractor. |
| **deployment_events** (existing) | workflow status | Read-only. Map `work_type` / `workflow` to taxonomy functions. |
| **ATS / job boards** (paused by #315) | `robotics_hiring`; `labor_pressure` | Only after Bob approves re-enabling, and only through §5 rules. Never creates buyers on its own. |

---

## 10. Build phases (one draft PR each)

**Phase 0: Baseline (no code)**
List what the live site does today, end to end, for 3 robot URLs, with screenshots or API output. Confirms what "broken" means.
*Accept:* Bob agrees the list is accurate. **Done 2026-10-14 (PR #318).** Finding: today's cards come from a bundled file of 134 seed/demo entries with no sources, and several card details are generated.

**Phase 0.5: Honesty patch on the current site (small, ships first)**
The new pipeline takes several phases; until then the live site must not present made-up details as fact. Changes to the **current** flow only:
- Remove hash-generated deadlines, "spots open," and "applicants" values.
- Remove hard-coded "30–90 day buying window," "$60–90k/yr public budget," "Operations Director," and "verified buyer" text.
- Stop returning generated contact emails (`operations@<name>.com`) from any API.
- Label every bundled seed/demo card clearly as **"Example"** on the card.
- Never show a robot maker as a buyer (e.g., Intuitive Surgical); filter them out of the bundled cards.
- Fix the Relay bug: the site's request adds two fields that turn a valid result into "no jobs." The site and API must return the same result for the same robot.
*Accept:* for Locus Origin, ADAM, and Relay, every field on every card is either sourced or labeled Example; no generated emails anywhere in API responses; Relay shows its hospital results.

**Phase 1: Tables + seed import**
Migrations for §4 tables. Seed CSV import script. Industry synonym map plus backfill **report** (dry run; writes nothing).
*Accept:* migration runs on a copy; importing Bob's seed list twice gives identical rows; backfill report lists mapped/unmapped counts by industry.

**Phase 2: Robot side wired**
The taxonomy extractor (prompt v4) writes `rfr_robot_products` for any submitted robot URL, behind the flag.
**Robot makers make many robots.** A maker is not one robot: RichTech makes a drink station (ADAM), a bartender arm (Scorpion), a restaurant server (Matradee Plus), heavy delivery (Titan), pallet moving (Pallet Jack), two floor cleaners (DUST-E MX, DUST-E S) and an industrial humanoid (Dex), each for different work and buyers. So:
- The unit is the **product**, never the company. Each product gets its own `rfr_robot_products` row and its own matches.
- If the submitted URL is a maker's homepage or catalog, discover its product pages (e.g., `/solutions/*`, `/products/*`) and classify each one. Show the user the list of products found and let them pick, rather than merging them into one robot.
- If the submitted URL is a product page, classify that product only.

*Accept:* the 5 acceptance robots (§11) produce product rows with sensible fields; one row per product on multi-product pages. **Plus the RichTech set** (`tests/fixtures/robot_oem_richtech_set.v1.json`): each of the 8 product URLs classifies per its answer key, and submitting `richtechrobotics.com` finds all 8 products as separate records.

**Phase 3: Signals**
SAM.gov → `rfr_signals`; news classifier → signals; `deployment_events` → workflow status. Bob confirms pilot industries before this phase.
*Accept:* for 10 random signals, source URL, quote, type, and buyer are correct by inspection (Bob spot-checks).

**Phase 4: Matcher + scoring**
Computes `rfr_opportunities` per §6–7. Config for weights and decay.
*Accept:* the 5 acceptance robots each return ranked buyers with reasons; no committed workflows; no robot makers; no card based only on labor pressure.

**Phase 5: Cards + switch**
API and UI per §8 behind the flag; preview deploy.
*Accept:* Bob reviews the 5 robots on preview. Bob flips the flag.

**Phase 6: Backfill (only with approval)**
Apply the backfill from Phase 1 after Bob reviews the report.

---

## 11. Acceptance test (end to end)

Run on preview after Phase 4 and again after Phase 5. Bob picks the final 5; suggested (covering the top pilot groups):

1. **A warehouse robot** (e.g., Locus): warehouses/3PLs, ranked with RFP or pilot signals first.
2. **A factory robot** (e.g., OTTO Motors or a Universal Robots cobot): manufacturers, not warehouses, as buyers for in-plant work.
3. **RichTech ADAM** (drink-making and serving: cocktails, coffee): bars and nightclubs (`bar_nightclub`), restaurants, hotels. Workflow must be `food_beverage_prep`, not bussing, room service, or food running. Las Vegas filter shows local buyers.
4. **Relay or Aethon** (hospital delivery): hospitals with delivery workflows; committed hospitals excluded for delivery.
5. **A cleaning robot** (e.g., Avidbots): airports, retail, office buildings, hotels; excluding any already committed to cleaning robots.

For each: list the top 10 cards with reasons. Bob marks each card right / wrong / unsure. Target for switching the flag on: **at least 7 of 10 right for each robot, and zero cards that show a robot maker, a committed workflow, or a labor-only signal.**

---

## 12. Out of scope for v1 (do not build)

- Contacts, outreach, sequences, CRM features. (Later: an opportunity usually has **several decision makers**, e.g., operations, facilities, F&B, IT, procurement, finance. Design for many-per-opportunity when contacts are added.)
- Pricing, upgrade, or signup prompts on cards
- Ingesting postings for people as leads
- Supply-side hiring (robot makers) as a buyer source
- Industries outside the pilot list in the UI
- Any change to existing tables' data

---

## 13. Open decisions for Bob

1. ~~Confirm pilot industries (§2).~~ Confirmed 2026-10-14: 8 groups in priority order.
2. Provide the seed list (`rfr_seed_accounts.csv`), even 50–100 rows to start.
3. Confirm the rest of the stage mapping (§6): EVALUATION → exploring; LIVE and COMMERCIAL deployment → committed.
4. Whether companies created only by job-posting feeds are kept in the backfill (§9).
5. When to re-enable ATS feeds for `robotics_hiring` only (§9).
6. Final 5 acceptance robots (§11).
7. Keep adding automation-intent phrasing to the lexicon (§5a).
