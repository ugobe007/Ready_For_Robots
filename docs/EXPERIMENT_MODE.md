# EXPERIMENT MODE — Active

**Updated:** 2026-08-15 (traffic = the product test · channel research stopped)

## Category

> **Find Jobs for Robots.**

Entry prompts (same engine — see [`CAPABILITY_MODEL.md`](./CAPABILITY_MODEL.md)):

| Who | CTA |
|-----|-----|
| OEM | Find jobs for your robot. |
| Distributor | Find jobs for the robots you sell. |
| Integrator | Find automation jobs your company can solve. |

Not leads. Not SIGNAL. Not sales intelligence. Not three products.

## Schema: FROZEN

Architecture stays alone. Fixtures support `/experiment`. **No Fly migration yet.**

See [`product_sim/RDD_UNIVERSAL_CORE.md`](./product_sim/RDD_UNIVERSAL_CORE.md).

## The test

> When we show someone work matched to what they sell or can solve, do they want more?

```
submit robot
  → see capabilities
  → see jobs
  → inspect multiple cards
  → click See All
  → start signup
```

- **Before See All** = product (does the job create pull?)  
- **After See All** = conversion mechanics (CTA / auth / onboarding)

Primary metric: **See All CTR** — **segment by `persona`** (oem / distributor / integrator) and by robot family / `profile_key` within persona.

First useful read = **which audience pulls** and **which capability families engage** — that picks the first customer segment, not a tagline. See [`TRAFFIC_SPRINT.md`](./TRAFFIC_SPRINT.md).

Until traffic evidence: **no more capability layers · no channel expansion · no UI forks.**

## Funnel interpretation (do not tweak from tiny traffic)

| Pattern | Likely cause |
|---------|----------------|
| Low submit → capabilities | Input / trust problem |
| High capabilities, low job engagement | Weak or implausible matching |
| High card engagement, low See All CTR | Insufficient perceived value, or too many free results |
| High See All CTR, low signup start | Gating / CTA friction |
| High signup start, low completion | Auth / onboarding friction |
| One persona >> others on See All | GTM wedge (still one engine) |

**Also watch:** which `job_key` / company appears in `rdd_job_viewed`.

**Rule:** Let a meaningful traffic batch accumulate. Judge the funnel as a whole. Do not optimize from noise. Do not add architecture, scoring, scraping, ontology, channel scoring, or UI variables before that.

## Stopping point (2026-08-15)

Architecture frozen. Product frozen. Channel research **stopped** (fixtures kept). Instrumentation running.  
**Next:** mixed-audience traffic sprint — [`TRAFFIC_SPRINT.md`](./TRAFFIC_SPRINT.md).  
Integrity QA (10 URLs) must pass before Cohort 1 — [`product_sim/qa_robot_url_matrix.md`](./product_sim/qa_robot_url_matrix.md).

## Instrumentation

`trackRobotJobsFunnel` → `/event/rdd_*`

Outreach links: `/experiment?persona=oem|distributor|integrator&src=…`

| Step | Event |
|------|--------|
| Land | `rdd_experiment_view` (+ persona, src) |
| Submit | `rdd_robot_submitted` |
| Capabilities | `rdd_capabilities_viewed` |
| Search beat | `rdd_discovery_started` / `rdd_discovery_complete` |
| Jobs | `rdd_first_job_viewed` · `rdd_job_viewed` (+ `job_key`, company) · `rdd_jobs_3plus_viewed` |
| Unlock | `rdd_see_all_clicked` |
| Signup | `signup_start` / `signup_complete` (`src=robot_jobs`) |

## Capability entry points (research done · no UI yet)

```
CAPABILITIES → FIND WORK
```

| Level | Prompt | Status |
|-------|--------|--------|
| Robot | Find jobs for your robot | `/experiment` traffic |
| Portfolio | Find jobs for the robots you sell | Fixtures · **no UI** |
| Solution | Find automation jobs your company can solve | Cross 0→~19 · fixture only |

Channel Graph fixtures: [`channel_graph/`](./channel_graph/). Do not expand OEM 11–50, more distributors, or Channel Match scoring.

## Frozen

Schema churn (RDD) · Fly migrate · homepage · Cal · CRM · SIGNAL · premature UX optimization · distributor/integrator UI · channel research expansion · OEM scrape scale
