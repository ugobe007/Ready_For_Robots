# Robot Understanding v1

**Status:** Phase 1–3 v1.0 calibration — regex extractors CLOSED, but a **narrow reopen (2026-08-18)** adds a deterministic **Robot Inference Engine** (`evidence → inference → capability`, the Pythh forward-chaining pattern) alongside them. Reopen reason: *manufacturer capability narrative + structured product data present → material robot capabilities absent* (1X NEO returned `capabilities=[]`). See [`V1_0_FREEZE.md` § Narrow reopen](./calibration/understanding_blind_20/V1_0_FREEZE.md) and `app/services/robot_inference_engine.py`. Not an LLM profile generator; regex retune / Blind 20 remain closed; matcher unchanged. **M2 matcher prototyping allowed** against frozen A/B/C profiles.  
**Updated:** 2026-08-18 (Robot Inference Engine — narrow M1 reopen)  
**Calibration outcome:** [`docs/calibration/understanding_blind_20/outcome.md`](./calibration/understanding_blind_20/outcome.md) · freeze note [`V1_0_FREEZE.md`](./calibration/understanding_blind_20/V1_0_FREEZE.md)  
**Product spine / finite milestones:** [`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md) — Understanding is M1 infrastructure, not an open-ended research loop.  
**Next ops path:** **M2 Match** next mission; production shadow remains **M1 Understanding decision instrument** (first **20 real reviewed** → accept / narrow-reopen) — not Blind 20 retune, not forever polish. Spec: [`calibration/understanding_shadow_v1.md`](./calibration/understanding_shadow_v1.md).  
**Role in product:** Intelligence foundation under FIND in [`CAPABILITY_MODEL.md`](./CAPABILITY_MODEL.md) (`FIND → QUALIFY → PLACE later`).

**Governing standard:**

> ReadyForRobots must be able to explain *why* it believes a robot can do a job — not merely return a plausible list.

That sentence governs implementation. Knowing Phase 4–5 shape is **permission to prototype the matcher (M2)** against frozen Understanding output — **not** permission to reopen extractors or chase Blind 20.

---

## Place in the stack

```
FIND (this doc)
  URL → Identity → Typed sources → Atomic facts
  → (Phase 4) Derived capabilities → Workflows
  → (Phase 5) Job requirements match
       ↓
ROBOT JOBS → QUALIFY → PURSUIT BRIEF → PLACE later
```

This is **product-integrity work**, not hypothesis expansion. **Phases 1–3 only, then stop and evaluate.**

The first deliverable is a trustworthy **Robot Profile** — not a better job list.

---

## Full conceptual hierarchy (hard separations)

Two separations that must never collapse:

**Evidence chain**

```
SOURCE → FACT → CAPABILITY
```

**Work chain** (Phase 4+, conceptual now — no extra table required in Phase 1–3)

```
CAPABILITY → WORKFLOW → ROBOT JOB
```

Example:

| Layer | Example |
|-------|---------|
| Capability | `carry_load`, `autonomous_indoor_mobility`, `tote_handling` |
| Workflow | `move_tote_between_workstations` |
| Robot Job | CuraScript Newark — return empty totes from packing to operating area |

**Phase 4 must not jump from `carry_load` to arbitrary jobs.** Capabilities compose into workflows; workflows satisfy job requirements. Do not invent a `robot_workflow` table in Phase 1 unless needed — keep the distinction in the model so later phases stay honest.

Full chain:

```
SOURCE
  ↓
FACT
  ↓
CAPABILITY
  ↓
WORKFLOW
  ↓
ROBOT JOB
```

---

## What we copy from Pythh (and what we do not)

**Copy the discipline:** identity first → evidence second → structured profile third → matching last.

**Do not copy:** investor GOD ontology, sector→investor scoring, or keyword shortcuts as the understanding layer.

Pythh reference spine (pattern only): `~/Desktop/hot-honey` — submit resolve → scrape/enrich → score → match. See canvas `pythh-vs-rfr-url-architecture`.

---

## Five design rules (non-negotiable)

### 1. Product identity is durable (and version-aware when evidence requires it)

`agilityrobotics.com` → **Agility Robotics** → product(s) such as **Digit**.

- **Vendor URL lookup (seed):** if the submitted host matches `app/data/vendor_robots_index.json` (humanoids from `/robots`) or `app/data/vendor_robots_commercial_seed.json` (commercial SKUs such as Richtech), return that vendor's stored SKUs instead of guessing from a thin homepage. Homepage crawl may **add** extra SKUs; it must not replace the index. Press hosts (Morningstar, TMCnet, Yahoo, …) are never lookup keys. A bot-challenged OEM host must not fan out to Wayback copies of every product hub. Industrial lists can append `vendor_robots_industrial_seed.json`. Rebuild humanoids: `PYTHONPATH=. python3 scripts/backfill_vendor_robots_from_index.py`.
- The **robot product** is the match subject, not the company hostname.
- Multi-product → user choice (or clear default with audit trail).
- Identity is persisted; do not re-derive a company label from the hostname every request.
- Conceptually: **Company → Product → Product version / generation** when evidence conflicts across generations (Digit 2024 ≠ Digit 2026; same for Spot, Neo, Origin, UR models, etc.). Do **not** merge conflicting generations into one timeless robot. A version table is optional in Phase 1 — only add when evidence forces it; until then, keep version/generation on facts or as product aliases, never silently collapse.

### 2. Everything important has provenance

If RFR claims “Digit carries 35 lb,” there is a `robot_source` (and a `robot_fact`) behind it.

Epistemic states on claims: **explicit** · **strongly inferred** · **weakly inferred** · **unknown** · **contradicted**.

### 3. Capabilities are derived objects, not scraped strings

| Layer | Role |
|-------|------|
| Source | Typed evidence (URL, type, date, confidence) |
| Fact | Concrete claim supported by a source |
| Capability | Primitive (+ constraints) derived from facts |
| Workflow | Composition of capabilities into a work pattern (Phase 4+) |
| Robot Job | Localized instance of work (Phase 5) |

Never collapse “page said X” into “capability X” or “job Y” in one step.

### 4. Robot Jobs carry requirements, not only categories

Match inspects requirement satisfaction (matched / unmet / unknown / likely). Not: `Humanoid family score: 0.82`.

### 5. Unknown is a legitimate result

Enough evidence to recommend investigating a job, while stating what is not yet established, beats manufactured certainty.

---

## Target pipeline

```
URL
  → company / product identity (+ version when required)
  → typed source pack
  → atomic facts (with provenance; contradictions preserved)
  → [STOP — Robot Profile]
  → derived capabilities (+ constraints)
  → workflows
  → job requirements match
```

**Forbidden shortcut:** `URL → keywords → capability family → jobs`

Live `/` path stays until blind eval wins. Feature-flag / shadow the new spine.

---

## Jobs FIND lookup (what actually runs)

`POST /api/robot-profile` (Jobs URL submit) is **catalog-first**, then a bounded live crawl. It is not “scrape every OEM site and guess SKUs.”

```
submitted URL
  → vendor index lookup (domain)
        humanoid JSON  (readyforrobots.com/robots → app/data/vendor_robots_index.json)
      + commercial seed (app/data/vendor_robots_commercial_seed.json)
      + optional industrial seed
  → fetch the submitted page once (no Wayback if the host is already in the index)
  → identity: index SKUs for the picker (homepage nav is not a robot)
  → several SKUs, no product=  → picker, stop (no source pack)
  → one SKU / product= selected
        indexed vendor → facts from stored specs + catalog claims
                         (homepage HTML kept; no /adam, sitemap, or Wayback fan-out)
        unknown host, live HTML → typed source pack (≤6 pages, 12s budget, no archive)
        unknown host, 429/empty → identity from domain only, Profile C, stop
  → regex extractors (frozen) + inference engine (narrow M1 reopen)
  → coverage checklist → Profile A/B/C
```

| Host class | Identity | Specs / facts | Live crawl |
|------------|----------|---------------|------------|
| Indexed humanoid OEM (Unitree, EngineAI, Figure, …) | Stored SKUs only (no nav extras) | Index specs mapped to checklist predicates | Homepage only |
| Indexed commercial OEM (Richtech, Bear, Pudu, Locus, …) | Stored SKUs | Curated class / environment / payload when known | Homepage only |
| Same domain, extra SKUs in commercial seed (Boston Dynamics Spot/Stretch on top of Atlas) | Merged list | Per-SKU claims | Homepage only |
| Press host (Morningstar, Yahoo, …) | Never a lookup key | — | Rejected as vendor key |
| Unknown OEM, live site | Guessed from homepage links/prose | Regex + inference on a small typed pack | Yes, no Wayback |
| Unknown OEM, bot-challenge | Domain label only | Almost none → Profile C | No fan-out |

**How coverage grows:** add vendors to the JSON index (or `--apply` into `manufacturers` / `robot_models`). Do not reopen Blind 20 extractors or live-crawl 129 OEM sites. Industrial lists later use `app/data/vendor_robots_industrial_seed.json` with the same shape.

**Not in this loop:** job matching (`POST /api/robot-job-search`) runs after identity. Picker confirm for one SKU (or a single product URL) goes straight to jobs; the profile checkpoint is optional via process nav 01.

---

## Persistent objects (v1 spine — Phases 1–3)

Thin schema. No grand ontology. No workflow/job tables in this phase.

### `robot_company`

OEM identity (canonical name, primary domain, aliases).

### `robot_product`

Digit, Vega, Origin, Neo, etc. — FK to company. Optional generation/version label when needed. Display class is descriptive only.

### `robot_source`

| Field | Notes |
|-------|--------|
| url | Canonical |
| source_type | Typed pack below |
| fetched_at | |
| published_at / document_date | When known — critical for contradiction resolution |
| title | Optional |
| publisher_role | manufacturer \| third_party |
| confidence | Evidence quality for this source |

### `robot_fact`

```
subject | predicate | value | units | epistemic | source_id | confidence
[+ optional product_version / observed_at]
```

Example: `Digit | carrying_capacity | 35 | lb | explicit | source_123 | 0.98`

**Good facts:** concrete claims (`has_mobile_base`, `arm_count`, `carrying_capacity`, `supports_tote_handling`, `battery_runtime`, `deployed_in_warehouse`, `supports_hard_floor_scrubbing`).

**Bad facts:** interpretation (`good_for_machine_tending = true`) — that is capability/workflow, Phase 4+.

### Contradiction handling (Phase 3 — mandatory)

**Do not silently pick a winner during extraction.**

If older press says payload = 20 kg and current spec says 16 kg, store **both** facts with source, date, and type:

| value | source | date |
|-------|--------|------|
| 20 kg | manufacturer press release | 2024 |
| 16 kg | manufacturer specification | 2026 |

Current profile resolution (which value is “active”) is a **later, auditable authority rule** (prefer newer manufacturer spec over older press) — not extraction-time collapse. Robotics specs change by generation and software release; preserving contradiction is part of being professional.

### `robot_capability` / workflow (Phase 4 — define only; build after M1)

Target product shape (when earned): GOOD MATCH cards with **Why** (matched requirements) / **Still unknown** (unmet/unknown) — e.g. Vega → CNC load/unload. **Reject** keyword “mobile manipulator → 12 vague jobs.” Full milestones: [`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md).

```
carry_load
  max_payload = 35 lb
  derivation = explicit | inferred
  derived_from = [fact_…]
```

Then capabilities → workflow (e.g. `move_tote_between_workstations`) → job. **Not in Phases 1–3. Not building yet.**

---

## Typed source pack (Phase 2)

Deliberate typed acquisition — not a generic same-domain crawl:

| source_type | Role |
|-------------|------|
| product | Identity and claimed work |
| specifications | Hard limits — highest weight for constraints |
| solutions / use_cases | Workflow *claims* (still facts about claims, not derived workflows) |
| documentation | Technical detail |
| case_study | Deployment evidence |
| press_release | Soft claims; weak for hard limits |
| support / manual | Operational constraints |

**Rank:** manufacturer spec ≫ manufacturer product ≫ case study ≫ solutions ≫ press ≫ SEO/blog.

**Reject / demote from primary pack:** 404/error pages, contact, leadership/about (unless identity fallback), privacy/legal/cookies, bare blog/news indexes.

---

## Profile confidence tiers

Tier is **derived** from three separate dimensions — not from grounding alone:

| Dimension | Question |
|-----------|----------|
| **Grounding** | Are material claims sourced? (~100% required for A/B) |
| **Coverage** | Did we fill the morphology research checklist? |
| **Source quality** | Are sources PRODUCT / SPECS / DOCS / SOLUTIONS / CASE — not contact/legal/404? |

| Tier | Meaning |
|------|---------|
| **A** | Strong identity; authoritative sources; high checklist coverage |
| **B** | Identity known; medium coverage; usable but incomplete |
| **C** | Sparse coverage and/or weak sources — even if grounding is 100% |

One perfectly sourced fact is still **C**. Unknown checklist slots are emitted as `epistemic=unknown`, not invented.

Research checklists are **descriptive only** (have we researched enough to describe the robot?). They do **not** select jobs.

---

## Phase 1–3 deliverable: Robot Profile (not jobs)

After Phases 1–3, `agilityrobotics.com` must produce something like:

```
COMPANY
  Agility Robotics

PRODUCTS FOUND
  Digit

PROFILE CONFIDENCE
  A | B | C

SOURCES
  Product page — manufacturer — url — fetched_at
  Specifications — manufacturer — …
  Solutions — manufacturer — …
  Case study — manufacturer — …

FACTS
  product_class = humanoid          ← source…
  carrying_capacity = 35 lb         ← source…
  battery_runtime = 4 hr            ← source…
  tote_handling = explicitly demonstrated  ← source…
  warehouse_deployment = true       ← source…
```

Every fact is auditable back to evidence (clickable source in UI or API).

**Stop there.** Do **not** emit in this phase:

- “37 jobs for Digit”
- “Digit can palletize” (unless that exact claim is a sourced fact — still a fact, not a job match)
- “92% match”

If the Robot Profile is not excellent, there is no reason to build downstream inference.

Smoke after Agility: Dexmate → Locus → Avidbots → then blind 20.

---

## Implementation order (locked)

| Phase | Scope | Exit gate |
|-------|--------|-----------|
| **1 — Resolve** | Company + product (+ version awareness when needed) | Identity accuracy |
| **2 — Research** | Typed source pack | Sources typed, ranked, persisted |
| **3 — Facts** | Atomic claims; contradictions preserved | Fact metrics + **Source Grounding Rate** |
| **STOP** | Robot Profile eval | Blind Understanding scores |
| **4 — Capabilities → Workflows** | Primitives + composition | Capability precision; no job leap |
| **5 — Job requirements match** | matched / unmet / unknown | Top-10 precision; differentiation |

**FROZEN (v1.0 calibration):** Phases 1–3 implemented and Blind-20-evaluated — gate failed honestly; leave failed. Extractors / Blind retune stay closed.  
**M2 / Phase 4–5 matcher:** **ALLOWED to prototype** against grounded Tier A/B/C profiles; must propagate unknowns. Do **not** wait on 20-shadow for permission — that gate is Understanding-only ([`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md)).  
**Still forbidden:** Blind 20 retune; open-ended Understanding polish; new capability families; channel research; OEM scrape scale; more corpora; heuristic patches that fake match differentiation.

**Production:** Live `/` uses `POST /api/robot-profile` then job match (P0-A). Shadow accrues on profile submits. **M2 requirement matcher** (`requirement_v1`) runs when the Jobs UI passes the frozen profile into `POST /api/robot-job-match`. Chip recovery still uses the legacy keyword matcher. Do not retune Understanding to compensate.

---

## Extraction prompt contract (Phase 3)

This is an **implementation contract**, not documentation color.

**Ask:**

> What concrete claims about this robot are supported by this source?

**Do not ask:**

> What can this robot do?

Rules for any extractor (LLM or rules):

1. Emit only atomic facts with predicate/value/units when present.  
2. Attach `source_id` and epistemic = `explicit` when the source states it.  
3. Do not invent capabilities, workflows, or jobs.  
4. Do not resolve contradictions — emit multiple facts.  
5. Prefer quote/span or stable locator when available.  
6. If the source does not support a claim, omit it (unknown is fine).

---

## Blind evaluation (release gate)

Hand-tuned fidelity fixtures are **not** the Understanding release gate.

### Cohort (~20 robots not used to author rules)

4 AMRs · 4 humanoid/mobile manipulators · 3 cleaning · 3 cobots/arms · 2 inspection · 2 service · 2 unusual/ambiguous.

Human ground truth independent of implementation.

### Score separately

**A. Robot Understanding (Phases 1–3 gate)**

| Metric | Target |
|--------|--------|
| Company / product resolution accuracy | High |
| Fact precision / recall | High |
| Constraint extraction accuracy | High |
| **Source Grounding Rate** | **~100%** — every material profile fact has a valid supporting source |
| Unsupported invented facts | ~0 on presented profile |

If RFR presents a fact as factual, it needs evidence. Source Grounding Rate failing is a Phase 3 fail even if jobs would look plausible.

**B. Job Matching** (only after A passes and Phases 4–5 exist)

Top-10 precision · requirement satisfaction · useful unknowns · differentiation.

### Smoke before blind eval

Agility → Digit · Dexmate · Locus · Avidbots — profile quality only (used to author rules; **out of blind cohort**).

### Blind 5 (stage 1 — current gate)

See [`docs/calibration/understanding_blind_5/`](./calibration/understanding_blind_5/README.md).

Five fresh robots across AMR / humanoid / cobot arm / inspection / service. Implementation frozen. Human GT authored independently. No job matching. No QUALIFY influence.

```bash
python3 scripts/run_understanding_blind5.py
python3 scripts/score_understanding_blind5.py
```

If Blind 5 shows a **general** failure → one generalized fix → **rerun the same five**. Then Blind 20.

### Blind 20 (full holdout — completed; gate FAIL frozen)

See [`docs/calibration/understanding_blind_20/`](./calibration/understanding_blind_20/README.md).

20 fresh robots (locked physics mix). Implementation frozen. Human GT authored independently. Aggregate + by-class metrics. No job matching. No QUALIFY influence. **Gate FAIL left open — do not retune to clear 80%.** Understanding extractors remain closed; M2 Phase 4–5 matcher prototyping is allowed against frozen profiles.

```bash
python3 scripts/run_understanding_blind20.py
python3 scripts/score_understanding_blind20.py
```

Outcome + v1.0 decision: [`docs/calibration/understanding_blind_20/outcome.md`](./calibration/understanding_blind_20/outcome.md).

---

## Success standard (full stack — after Phase 5)

1. Which product (and version, if relevant) was resolved  
2. Which sources were used  
3. Which facts were extracted (incl. contradictions retained)  
4. Which capabilities / workflows were derived (explicit vs inferred)  
5. Which job requirements are matched, unmet, or unknown  

Phases 1–3 only need 1–3 with Source Grounding Rate ≈ 100%.

---

**Canonical submit workflow (product UX):**

```
URL → Research Agent → Company → Products → Sources → Facts → Robot Profile → Results
```

The Robot Profile is the first visible proof of intelligence. Jobs come after.

Loading stages (user-facing): Identifying company → Finding products → Reviewing sources → Building profile → Profile ready → Searching work.

Multi-product: pause for “Which robot needs jobs?” before full research.

API: `POST /api/robot-profile` · UI: `/` Jobs terminal left rail = profile, right = jobs.

## Architecture closed

No further conceptual docs on Robot Understanding until Phases 1–3 are implemented and evaluated.

**Implementation (shadow spine — does not replace live `/` matcher):**

| Path | Role |
|------|------|
| `app/services/robot_understanding_v1/` | Phases 1–3 pipeline |
| `scripts/build_robot_profile.py` | CLI → markdown/JSON Robot Profile |
| `POST /api/robot-profile` | Shadow API (same payload; no jobs) |
| `readyforrobots-new/.../RobotProfileCard.tsx` | Results left-rail profile |
| `tests/test_robot_understanding_v1.py` | Unit tests |

```bash
python3 scripts/build_robot_profile.py https://www.agilityrobotics.com/
```

**v1.0 calibration locked:** Blind 20 holdout **FAIL** (critical 78%) — see [`outcome.md`](./calibration/understanding_blind_20/outcome.md). Gate left failed on purpose; do **not** chase 80% on this cohort. Understanding extractors remain **CLOSED**.

**M2 unlock:** Phase 4–5 **matcher** work may proceed against frozen profile output (A/B/C + unknowns). Circular dependency: traffic needs credible match; 20 organic shadows need traffic; match needs M2 — so freeze Understanding, allow M2.

**Shadow path:** production shadow as **M1 Understanding decision instrument** — first **20 real reviewed** profiles, then one accept / narrow-reopen — see [`calibration/understanding_shadow_v1.md`](./calibration/understanding_shadow_v1.md) · [`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md). Fail-open logging; taxonomy GOOD/INCOMPLETE/WRONG/UNVERIFIABLE. Do **not** improve Understanding forever. Fresh Blind 20 later only after a **narrow** reopen justified by **repeated production failures** (cite in mission brief).

**Next build:** M2 requirements matching (*What jobs can this robot do?* with Why / Still unknown) — not more Understanding research.

---

## Related docs

- [`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md) — product spine + finite M1–M4  
- [`CAPABILITY_MODEL.md`](./CAPABILITY_MODEL.md) — canonical product strategy  
- [`EXPERIMENT_MODE.md`](./EXPERIMENT_MODE.md) — `/` Jobs terminal operating mode  
- [`calibration/understanding_shadow_v1.md`](./calibration/understanding_shadow_v1.md) — M1 shadow checkpoint  
- Legacy path (frozen for understanding quality): `app/services/robot_ready_profile.py`, `app/services/robot_job_capability_match.py`
