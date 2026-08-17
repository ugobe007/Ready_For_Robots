# Understanding v1.0 — observe-only production shadow

**Status:** ops path after v1.0 calibration freeze — **finite decision instrument for M1 Understanding**, not a permanent research program, **not an M2 blocker**  
**Product dual track:** `/` Find Jobs → profile → Qualify stays the product path; this doc covers the **intelligence shadow** only.  
**Product spine:** [`docs/readyforrobots_v1_milestones.md`](../readyforrobots_v1_milestones.md) (M2 unlocked; 20-shadow = Understanding-only)  
**Freeze:** [`understanding_blind_20/V1_0_FREEZE.md`](./understanding_blind_20/V1_0_FREEZE.md) remains the line in the sand for extractors.

## Purpose (hard end)

Shadow answers one product question:

> **Is Understanding good enough to support the product, with honest unknowns?**

Not: “Is Understanding perfect?” Not: open-ended improve → measure → improve forever.  
Not: “May we start M2?” — M2 may begin against frozen A/B/C profiles now.

| Checkpoint | Rule |
|------------|------|
| **First 20 real reviewed** robot profiles | Hard sample for the **M1 Understanding** decision (not hundreds) |
| Until 20 reviewed | Individual WRONG / INCOMPLETE rows are **observations only** — **not** reopen permission for extractors |
| At 20 reviewed | Make **ONE** Understanding decision (below) — narrow reopen **or** accept B/C |
| **M2 Match** | **Not blocked** by this checkpoint |

### One decision at 20 reviewed

| Pattern | Decision |
|---------|----------|
| Repeated **general** failure (e.g. 8/20 miss PDFs) | Reopen Understanding **only** for that mechanism |
| Scattered failures + most profiles professionally useful | Accept B/C unknowns; do not keep polishing Understanding |

Do **not** treat shadow as a permanent research program after that checkpoint.  
Do **not** treat “waiting for 20” as permission to delay M2.

### Team work while shadow accumulates

| Do | Do not |
|----|--------|
| Prototype **M2** requirements matching on A/B/C profiles | Reopen Understanding extractors / Blind retune |
| Review shadow rows as they arrive | Invent Understanding polish “while waiting for 20” |
| Keep traffic paused until MATCH TRUTH | Publish C04 / invite traffic on profile path alone |

See operating loop in [`readyforrobots_v1_milestones.md`](../readyforrobots_v1_milestones.md).

## Contract (observe-only)

1. Shadow **logs** real URL → Robot Profile builds. It does **not** silently repair, retune, or replace extractors/sources/resolve.
2. Shadow write is **fail-open**: if persistence fails, `POST /api/robot-profile` still returns the profile to the user.
3. Shadow does **not** change job-match results by itself. The Jobs terminal calls `/api/robot-profile` for the left-rail profile (P0-A) — that product path stays; shadow is additive logging beside it. M2 matcher work is separate and may consume the same profiles.
4. Understanding extractors, Blind 20 retune, and ontology expansion remain **CLOSED** until the M1 decision above says otherwise (narrow reopen). **M2 / Phase 4 matcher prototyping is allowed now** without waiting for 20 reviews.

## Dual tracks

| Track | Surface | Role |
|-------|---------|------|
| **Product** | `/` Jobs terminal | Find Jobs → See All / Qualify (existing path) |
| **Intelligence shadow** | DB + admin API | Persist profiles for real submitted URLs; measure professional trustworthiness via human review — **through the first 20 reviewed**, then decide |

## Capture fields (every real submission)

Persisted on `understanding_shadow_observations` after a successful `build_robot_profile` in the API path:

| Field | Notes |
|-------|--------|
| `submitted_url`, `submitted_at` | Request URL + timestamp |
| `correlation_id` | Optional body/`X-Correlation-Id`, else generated UUID |
| `company_name`, `company_domain` | Identity |
| `selected_product`, `products_found` | Selection + catalog from resolve |
| `profile_tier` | A / B / C |
| `source_pack` | urls, types, titles (compact) |
| `grounded_facts` | Non-unknown, non-contradicted material facts |
| `unknowns`, `contradictions` | Research gaps + conflicts |
| `coverage_rate` / `coverage_level` | Honest coverage dimensions |
| `source_quality_rate` / `source_quality_level` | Source pack quality |
| `research_morphology` | Checklist morphology |
| `source_grounding_rate` | Grounding |
| `research_duration_ms` | Wall time of profile build |
| `notes` | Includes fetch/degraded notes when present |
| `research_stages` | If available on the profile |
| `profile_snapshot` | Full `to_dict()` for audit |

## Review taxonomy

Label each shadow row (admin):

| Label | Meaning |
|-------|---------|
| **GOOD** | I'd trust this profile (comfortable to show a robotics professional) |
| **INCOMPLETE** | Correct but materially missing facts |
| **WRONG** | Identity or facts are wrong |
| **UNVERIFIABLE** | Public evidence insufficient |

Optional `failure_themes` tags (for later aggregation): `pdf`, `js_page`, `cn_oem`, `multi_product`, `sparse_startup`, `fetch_failure`, `identity`, `other`.

## Primary metric

**Comfortable %** = `GOOD / reviewed_total`  
where `reviewed_total = GOOD + INCOMPLETE + WRONG + UNVERIFIABLE`.

- Treat **GOOD** as “comfortable showing a robotics professional.” **GOOD is demanding** — correct-but-thin = **INCOMPLETE**, not GOOD.
- Report **INCOMPLETE** separately (`incomplete_pct_of_reviewed`) — correct-but-thin is not a pass.
- Unreviewed rows are excluded from the percentage (surfaced as `unreviewed_total`).
- Professionally useful profiles with honest B/C unknowns can still support **M1** — perfection is not the bar.

Admin: `GET /api/admin/understanding-shadow/metrics` (auth: `X-Admin-Key` or admin JWT).

### Sample size before the M1 decision

- **Hard checkpoint: first 20 reviewed** real submissions — then ONE decision (see Purpose).
- Do **not** wait for 30–50 or hundreds before deciding; that recreates open-ended research.
- Until 20 reviewed: individual **WRONG** / **INCOMPLETE** rows are **observations only** — they are **not** permission to reopen Understanding extractors, sources, resolve, or Blind 20.

## How to review

```bash
# List recent / unreviewed
curl -sS -H "X-Admin-Key: $ADMIN_KEY" \
  'https://ready-2-robot.fly.dev/api/admin/understanding-shadow?unreviewed_only=true&limit=20'

# Label one
curl -sS -X POST -H "X-Admin-Key: $ADMIN_KEY" -H 'Content-Type: application/json' \
  -d '{"review_label":"GOOD","review_notes":"Solid Digit profile"}' \
  "https://ready-2-robot.fly.dev/api/admin/understanding-shadow/<id>/review"

# Metrics
curl -sS -H "X-Admin-Key: $ADMIN_KEY" \
  "https://ready-2-robot.fly.dev/api/admin/understanding-shadow/metrics"
```

## Trigger

`POST /api/robot-profile` (also mounted under `/api/v1`) builds the profile, then calls `record_shadow_observation` (fail-open). No separate product submit required — Jobs UI already hits this endpoint.

## First shadow report template

Use at the **20 reviewed** checkpoint. Keep it short; do not expand scope from a thin sample.

```text
Shadow report — YYYY-MM-DD
Reviewed: 20 (M1 checkpoint)
GOOD%: XX%  (GOOD / reviewed)
INCOMPLETE%: XX%
WRONG%: XX%
UNVERIFIABLE%: XX%
Themes (failure_themes counts): …
Notable WRONG/INCOMPLETE examples (ids only): …

M1 question (answer explicitly):
“Is Understanding good enough to support the product, with honest unknowns?”
→ REOPEN (narrow): only if repeated general failure — cite theme + ≥N examples + proposed mechanism
→ ACCEPT Understanding (default when scattered / most profiles useful): accept B/C unknowns; do not reopen extractors  
→ M2 is already allowed; this checkpoint does not unlock or lock matcher work
→ NOT: keep collecting forever / chase perfection
```

## Reopen rule (freeze)

**Do not reopen** Understanding extractors / sources / resolve / Blind 20 bars for cohort chasing or open-ended polish.

Any future Understanding change must cite **which repeated production failure** (from the first ~20 reviewed shadow rows + failure themes) justified a **narrow** reopen — not Blind 20 score polishing. Document that justification in the mission brief / outcome before touching `app/services/robot_understanding_v1/`.

Until 20 reviewed: treat WRONG/INCOMPLETE as logged observations — **not** a reopen ticket.

After an ACCEPT Understanding decision: do not restart Understanding research. M2 matcher work does not wait on this checkpoint (see [`readyforrobots_v1_milestones.md`](../readyforrobots_v1_milestones.md)).

## Implementation map

| Path | Role |
|------|------|
| `app/models/understanding_shadow.py` | ORM + label constants |
| `app/services/understanding_shadow.py` | Persist, review, metrics |
| `app/api/robot_profile.py` | Product build + fail-open shadow hook |
| `app/api/admin_understanding_shadow.py` | List / get / review / metrics |
| `migrations/versions/ush0a1b2c3d4_*.py` | Table |
| `tests/test_understanding_shadow.py` | Fail-open + review enum |
