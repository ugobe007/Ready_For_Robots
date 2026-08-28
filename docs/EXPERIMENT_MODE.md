# Product mode — Jobs terminal

**Updated:** 2026-08-21  
**Canonical strategy:** [`CAPABILITY_MODEL.md`](./CAPABILITY_MODEL.md)  
**Product spine / milestones:** [`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md) (M1→M4, then sell/test)  
**While waiting for M1 (20 shadow reviews):** operating loop = acquisition/content only — do not open M2 early ([`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md#current-operating-loop-while-waiting-for-m1)).  
**Understanding foundation:** [`robot_understanding_v1.md`](./robot_understanding_v1.md)

> Historical name: “EXPERIMENT MODE.” The experiment **became the product**. The live surface is **`/`** (Jobs terminal). `/experiment` is obsolete — treat remaining links/events as legacy aliases until cleaned up.

**Hermes is retired.** Do not spawn Hermes for FIND or Jobs. Do not run Mac cron or Fly ingest as the product loop. FIND is `/` via `POST /api/robot-job-match`. Cursor pstack is IDE-only. See [`hermes_retired.md`](hermes_retired.md).

---

## Category & entries

> **Find Jobs for Robots.**

| Who | CTA |
|-----|-----|
| OEM | Find jobs for your robot. |
| Distributor | Find jobs for the robots you sell. |
| Integrator | Find automation jobs your company can solve. |

Home `/` subhead: **We match your robots to specific jobs and models using your URL**.

Not leads. Not SIGNAL. Not three products. One engine: **FIND → QUALIFY → PLACE later**.

---

## The test (current)

```
submit robot URL on /
  → if several SKUs, ask which robot to find jobs for
  → one SKU: picker confirm goes straight to jobs for that product (no profile / second Find jobs)
  → several / all: resolve the search without blocking next steps (type-first, one match per class)
  → 01 robot → 02 jobs → 03 CRM are always navigational links
  → see Robot Jobs (step 2)
       one robot: 5 jobs, each tagged `Job ##### is for {SKU}`
       several robots: 1 sample job per SKU, tagged; run each robot individually for five jobs
       → inspect Robot Job Cards (employer, workplace, work, job description, labeled pay estimate)
  → check the jobs to take forward (all five start checked and dump into CRM)
  → Open CRM → /signup?next=/pipeline?src=jobs_activate&src=jobs_activate
  → after auth, CRM desk with 5 unlocked jobs (free). No robot OEMs.
  → CRM desk shows 5 unlocked job opportunities (free)
  → Place this job: quote the rental you will charge, apply, track follow-up
  → run the next robot the same way
```

Do not hop Jobs traffic onto SIGNAL buyers. Current experiment: Job Cards as employment opportunities — [`robot_employment_model.md`](./robot_employment_model.md) · [`experiments/robco_job_cards.md`](./experiments/robco_job_cards.md).

The picker already decides one vs several. **One robot → jobs for that robot on the same click** — do not open the profile checkpoint and ask Find jobs again. Several/all is slower, so we resolve with a type-level match instead of N SKU scrapes. **Independent of that resolution, every stage keeps process nav** (01 Show us your robot → 02 Available jobs → 03 CRM). Fourier empty portfolio failed because 02/03 were not links. Picking N1 then hitting a second Find jobs with Activate buried below the fold is the same break: the process stops at step 2.

**Do not hop Jobs traffic onto SIGNAL buyers or a Place outreach dump.** Next uses `src=jobs_activate` on `/pipeline` so the destination is the CRM desk with 5 unlocked job opportunities, not a SIGNAL lead feed. Wordmark / Jobs nav is `/?new=1` so a click returns to empty FIND.

Step 2 inspects. Checkboxes dump rows into CRM. **Start jobs →** (FIND) and **Open CRM →** (job list) sit in the process bar, at the top of the job list, and in the page footer — not only under the tape or under the cards. The document scrolls. No Next on the card. No Place buyer screen. No Qualify loop back to jobs.

---

## Jobs page architecture (locked)

Jobs is a **three-step process on a normal web page**. It is not a viewport-locked two-pane dashboard.

```
Site header (Jobs / About / Sign in). Pipeline is SIGNAL-only.
Process bar — 01 robot → 02 jobs → 03 CRM + Start jobs / Open CRM
Content (two columns are layout, not a clipping box)
Process bar repeated at the bottom of the page
```

Jobs chrome and Jobs CRM (`src=jobs_activate` on `/pipeline`) do not show SIGNAL Pipeline nav. Header CRM on those pages is `/pipeline?src=jobs_activate` (visible signed-out too), not bare `/crm`. SIGNAL `/pipeline` and `/crm` without a Jobs `src` still show Pipeline. Jobs footer and the Signal FAB match the header: no SIGNAL on `/`, About, Jobs CRM, or Jobs signup/login. About (`/intelligence`) body is the Jobs loop — Start jobs on `/?new=1`, signup `src=jobs_activate` — not a second product hop.

**Do not** set `100vh` + `overflow: hidden` on the Jobs workspace. Chrome then cannot scroll below the fold, so step 03 sits in a cut-off box. Pinning Activate inside that box is a patch, not a fix.

The document scrolls. Process chrome is page-level (top and bottom). Two columns may remain as layout.

Chrome is **rectilinear**: panels, buttons, cards, and inputs have square corners. Bevel CTAs, inset fields, a faint CRT scan on the Jobs shell, and square LEDs — 1970s control panel, not SaaS pills.

---

## One robot vs several (money-maker)

| Lookup | Jobs shown before signup | Tag |
|--------|--------------------------|-----|
| **One robot** | 5 example jobs | `Job 00001 is for Fourier N1` |
| **Several / all** | 1 sample job per robot | `Job 00002 is for Fourier GR-1` |

The ideal motion is **one robot at a time**: five jobs → Open CRM → quote rental and Place this job → run the next SKU. A lineup preview is a sampler, not a dump of unlabeled work. **Run one robot for 5 jobs →** returns to the picker.

**Retention loop (next, not this surface):** saved CRM jobs are watched. When news or requirements change, email the user and bring them back to respond. Do not build that email loop until this Jobs tagging path is clean.

---

## What is allowed vs frozen

**Product question:**

> Does RFR understand their robot well enough to show credible work — and does that work create enough value that they want more (`rdd_see_all_clicked`) or activate a job list (`rdd_jobs_list_activated`)?

| Pull | Metric |
|------|--------|
| Discovery | See All CTR · `rdd_see_all_clicked` |
| Commercial | Activate job list · `rdd_jobs_list_activated` |

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
| High See All, low Activate | Curious, not ready to keep a list |
| Activate job list | Commercial pull — live 15-job list |
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
| Activate (step 3) | `rdd_jobs_list_activated` |
| Signup | `signup_start` / `signup_complete` (`src=robot_jobs`) |

---

## Schema note

RDD fixtures / universal core: [`product_sim/RDD_UNIVERSAL_CORE.md`](./product_sim/RDD_UNIVERSAL_CORE.md). No Fly migration until Understanding v1 persistence needs it.

Channel Graph fixtures: [`channel_graph/`](./channel_graph/) — do not expand.

---

## Frozen (non-integrity)

Homepage redesigns · Cal · CRM · SIGNAL · premature UX optimization · distributor/integrator UI products · channel research expansion · OEM scrape 11–50 · Phase 4–5 Understanding · new capability families as “quality”
