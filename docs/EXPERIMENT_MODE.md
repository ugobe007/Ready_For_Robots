# Product mode — Jobs terminal

**Updated:** 2026-08-17  
**Canonical strategy:** [`CAPABILITY_MODEL.md`](./CAPABILITY_MODEL.md)  
**Product spine / milestones:** [`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md) (M1→M4, then sell/test)  
**While waiting for M1 (20 shadow reviews):** operating loop = acquisition/content only — do not open M2 early ([`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md#current-operating-loop-while-waiting-for-m1)).  
**Understanding foundation:** [`robot_understanding_v1.md`](./robot_understanding_v1.md)

> Historical name: “EXPERIMENT MODE.” The experiment **became the product**. The live surface is **`/`** (Jobs terminal). `/experiment` is obsolete — treat remaining links/events as legacy aliases until cleaned up.

---

## Category & entries

> **Find Jobs for Robots.**

| Who | CTA |
|-----|-----|
| OEM | Find jobs for your robot. |
| Distributor | Find jobs for the robots you sell. |
| Integrator | Find automation jobs your company can solve. |

Not leads. Not SIGNAL. Not three products. One engine: **FIND → QUALIFY → PLACE later**.

---

## The test (current)

```
submit robot URL on /
  → see understood capabilities (must be credible)
  → see Robot Jobs
  → inspect cards
  → discovery pull: See All Jobs
  → and/or commercial pull: Qualify This Job
  → signup / pursuit when ready
```

**Product question:**

> Does RFR understand their robot well enough to show credible work — and does that work create enough value that they want more (`rdd_see_all_clicked`) or ask us to qualify it (`rdd_qualify_requested`)?

| Pull | Metric |
|------|--------|
| Discovery | See All CTR · `rdd_see_all_clicked` |
| Commercial | Qualify requested · `rdd_qualify_requested` (stronger when present) |

Segment by `persona` and robot product / family.

---

## What is allowed vs frozen

| Allowed now | Frozen / do not expand |
|-------------|-------------------------|
| Robot Understanding v1 Phases 1–3 frozen at v1.0 calibration; shadow through **first 20 reviewed** for M1 | Product-hypothesis expansion; open-ended Understanding polish |
| Production shadow / honest profile UI (decision instrument — then move on) | Phase 4–5 until M1 clears (CLOSED — do not retune Blind 20) |
| Traffic / discovery content / funnel reports | Channel Match scoring, OEM scrape scale |
| Integrity fixes that make FIND trustworthy | New UI products, more corpora, capability-family churn |

**Rule:** Do not expand the product hypothesis while traffic runs. Product-integrity work required for `CAPABILITIES → FIND WORK` is allowed. Keyword-heuristic patches are not that work — see Understanding v1. Shadow answers M1 once; then Phase 4 / M2 — not Understanding forever.

Legacy matcher stays live until Understanding v1 wins blind eval. No Fly migrate of RDD schema until Understanding spine needs it.

---

## Funnel interpretation

| Pattern | Likely cause |
|---------|----------------|
| Low submit → capabilities | Input / trust |
| Capabilities shown, jobs feel wrong | **Understanding integrity** (fix Phases 1–3) |
| High job views, low See All | Weak discovery pull |
| High See All, low qualify | Curious but not commercially hooked |
| Qualify requested | Strong commercial pull on that job |
| High unlock, low signup | Auth / gating friction |
| One persona dominates | GTM wedge (still one engine) |

Do not rewrite UX or expand channels from tiny traffic noise. Do fix understanding when Agility/Dexmate-class failures show the promise is false.

---

## Instrumentation

`trackRobotJobsFunnel` → `/event/rdd_*`

Prefer outreach to `/` (or current Jobs entry) with `?persona=oem|distributor|integrator&src=…`. Legacy `/experiment?…` may still fire events — migrate links to `/`.

| Step | Event |
|------|--------|
| Land | `rdd_experiment_view` (legacy name) · prefer land-on-`/` |
| Submit | `rdd_robot_submitted` |
| Capabilities | `rdd_capabilities_viewed` |
| Search beat | `rdd_discovery_started` / `rdd_discovery_complete` |
| Jobs | `rdd_first_job_viewed` · `rdd_job_viewed` · `rdd_jobs_3plus_viewed` |
| Discovery unlock | `rdd_see_all_clicked` |
| Commercial pull | `rdd_qualify_requested` |
| Signup | `signup_start` / `signup_complete` (`src=robot_jobs`) |

---

## Schema note

RDD fixtures / universal core: [`product_sim/RDD_UNIVERSAL_CORE.md`](./product_sim/RDD_UNIVERSAL_CORE.md). No Fly migration until Understanding v1 persistence needs it.

Channel Graph fixtures: [`channel_graph/`](./channel_graph/) — do not expand.

---

## Frozen (non-integrity)

Homepage redesigns · Cal · CRM · SIGNAL · premature UX optimization · distributor/integrator UI products · channel research expansion · OEM scrape 11–50 · Phase 4–5 Understanding · new capability families as “quality”
