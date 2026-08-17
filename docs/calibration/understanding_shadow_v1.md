# Understanding v1.0 — observe-only production shadow

**Status:** ops path after v1.0 calibration freeze  
**Product dual track:** `/` Find Jobs → Qualify stays the product path; this doc covers the **intelligence shadow** only.  
**Freeze:** [`understanding_blind_20/V1_0_FREEZE.md`](./understanding_blind_20/V1_0_FREEZE.md) remains the line in the sand.

## Contract (observe-only)

1. Shadow **logs** real URL → Robot Profile builds. It does **not** silently repair, retune, or replace extractors/sources/resolve.
2. Shadow write is **fail-open**: if persistence fails, `POST /api/robot-profile` still returns the profile to the user.
3. Shadow does **not** change job-match results. The Jobs terminal may already call `/api/robot-profile` for the left-rail profile — that product path stays as-is; shadow is additive logging beside it.
4. Phase 4 (capabilities / workflows / jobs from Understanding), Blind 20 retune, and ontology expansion remain **CLOSED**.

## Dual tracks

| Track | Surface | Role |
|-------|---------|------|
| **Product** | `/` Jobs terminal | Find Jobs → See All / Qualify (existing path) |
| **Intelligence shadow** | DB + admin API | Persist profiles for real submitted URLs; measure professional trustworthiness via human review |

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

Admin: `GET /api/admin/understanding-shadow/metrics` (auth: `X-Admin-Key` or admin JWT).

### Sample size before interpreting Comfortable %

- **Minimum 20 reviewed** real submissions before treating Comfortable % as a signal.
- **30–50 reviewed** is preferable before any freeze / reopen discussion.
- Until that bar: individual **WRONG** / **INCOMPLETE** rows are **observations only** — they are **not** permission to reopen Understanding extractors, sources, resolve, or Blind 20.

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
  'https://ready-2-robot.fly.dev/api/admin/understanding-shadow/metrics'
```

## Trigger

`POST /api/robot-profile` (also mounted under `/api/v1`) builds the profile, then calls `record_shadow_observation` (fail-open). No separate product submit required — Jobs UI already hits this endpoint.

## First shadow report template

Use after enough reviewed rows (see sample size above). Keep it short; do not expand scope from a thin sample.

```text
Shadow report — YYYY-MM-DD
Reviewed: N (target ≥20; prefer 30–50)
GOOD%: XX%  (GOOD / reviewed)
INCOMPLETE%: XX%
WRONG%: XX%
UNVERIFIABLE%: XX%
Themes (failure_themes counts): …
Notable WRONG/INCOMPLETE examples (ids only): …

Reopen question (answer explicitly):
“Is there a repeated generalized failure important enough to reopen V1_0_FREEZE?”
→ YES only with cited theme + ≥N examples + proposed mechanism
→ NO (default): continue observe-only; do not retune Blind / Phase 4
```

## Reopen rule (freeze)

**Do not reopen** Understanding extractors / sources / resolve / Blind 20 bars for cohort chasing.

Any future Understanding change must cite **which repeated production failure** (from reviewed shadow rows + failure themes) justified reopening — not Blind 20 score polishing. Document that justification in the mission brief / outcome before touching `app/services/robot_understanding_v1/`.

Until ≥20 reviewed (prefer 30–50): treat WRONG/INCOMPLETE as logged observations — **not** a reopen ticket.

Phase 4 stays closed until a later holdout passes without regressing trust (see `docs/robot_understanding_v1.md`).

## Implementation map

| Path | Role |
|------|------|
| `app/models/understanding_shadow.py` | ORM + label constants |
| `app/services/understanding_shadow.py` | Persist, review, metrics |
| `app/api/robot_profile.py` | Product build + fail-open shadow hook |
| `app/api/admin_understanding_shadow.py` | List / get / review / metrics |
| `migrations/versions/ush0a1b2c3d4_*.py` | Table |
| `tests/test_understanding_shadow.py` | Fail-open + review enum |
