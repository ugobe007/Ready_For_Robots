# ReadyForRobots Capability Model

**Status:** Canonical strategy (updated 2026-08-21)  
**Not:** Three products. One engine. Three entry points.  
**Surface:** `/` is the Jobs terminal. `/experiment` is obsolete.  
**Finite milestones (M1–M4):** [`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md) · **MATCH TRUTH — PRODUCTION PASS** · M2 frozen · submit workflow merged / production smoke PASS · traffic paused

---

## Category

> **Find Jobs for Robots.**

## Company thesis

> Robots need jobs.

## Company definition

> ReadyForRobots is recruitment and placement infrastructure for robotic labor.

The primitive remains:

```
CAPABILITIES → FIND WORK
```

Employment-model expansion (PLACE later) is specified in [`robot_employment_model.md`](./robot_employment_model.md). Do not build marketplace posting, pilots, or employment-rate dashboards this cycle.

In product language:

```
FIND → QUALIFY → PLACE later
```

---

## Product stack

```
ROBOT / PORTFOLIO / SOLUTION CAPABILITIES
                  ↓
                FIND
                  ↓
             ROBOT JOBS
                  ↓
               QUALIFY
                  ↓
            PURSUIT BRIEF
                  ↓
              PLACE
               later
```

### Commercial objects

| Object | Meaning |
|--------|---------|
| **Robot Job** | Work defined well enough to recruit a robot against |
| **Job Card** | Employer · workplace · work · requirements · qualification · open questions |
| **Placement** | Later: robot hired into the job |

### UX (keep primitive)

```
Show us your robot.
Available jobs.
Open CRM — 5 unlocked Job Cards (free). Place this job is the money action.
```

Step 2 is the jobs list: expand/inspect (why / unknowns / blockers). **One robot → five jobs, each tagged `Job ##### is for {SKU}`.** Several robots → one tagged sample each, plus **Run one robot for 5 jobs**. Checkboxes dump into CRM; **Open CRM →** in the process bar. FIND is **Find jobs →**. Open CRM hits the signup wall; after auth the desk on `/pipeline?src=jobs_activate` shows 5 unlocked jobs (free). The document scrolls. Do not put the list CTA on the card. Do not insert a Place buyer/outreach screen. Do not mix unlabeled jobs across a lineup.

Everything underneath exists to make those interactions trustworthy.

---

## Three entry points (same engine)

| Entry | Prompt |
|-------|--------|
| OEM | Find jobs for your robot. |
| Distributor | Find jobs for the robots you sell. |
| Integrator | Find automation jobs your company can solve. |

Same system. Same graph. Same engine. Different capability envelope.

```
Level 1 — Robot
  What can this robot do?
  Digit · Vega · Origin · Neo · Spot
       ↓
Level 2 — Portfolio
  What can the robots this company sells do?
       ↓
Level 3 — Solution provider
  What automation problems can this company solve?
       ↓
ReadyForRobots
  Find → Qualify → (Place later)
```

| Level | Envelope source | Live surface |
|-------|-----------------|--------------|
| 1 Robot | Single SKU / URL | `/` Jobs terminal |
| 2 Portfolio | Brands carried | Fixtures · no separate UI product |
| 3 Solution | Aggregate solution capability | Fixtures · no separate UI product |

Economic shape (distributors / integrators):

```
value ∝ portfolio breadth × capability breadth × territory coverage
```

---

## Intelligence foundation

**Canonical:** [`robot_understanding_v1.md`](./robot_understanding_v1.md)

Under FIND:

```
URL
 ↓
IDENTITY
 ↓
TYPED SOURCES
 ↓
ATOMIC FACTS
 ↓
DERIVED CAPABILITIES
 ↓
TASK MODELS
 ↓
JOB REQUIREMENTS MATCH
```

Agility / Dexmate exposed a **product-integrity** defect on the capability side of `CAPABILITIES → FIND WORK`. Fixing Robot Understanding is not expansion or premature optimization — it is required for the existing homepage promise to be true.

---

## Moat (long-term graph)

Asset is not a lead DB, SIGNAL, or distributor directory. It is accumulating:

> What physical work exists, which machines can perform it, and who can commercially deliver those machines.

With **evidence** between WORK and ROBOT:

```
WORK
 ↕
EVIDENCE
 ↕
CAPABILITY
 ↕
ROBOT
 ↕
CHANNEL
 ↕
CUSTOMER
 ↕
DEPLOYMENT
```

Deployment evidence feeds back into **capability truth** and **work truth**.

Channel routing concept (research frozen — do not score yet):

```
Robot Job → Robot Match → Channel → Pursuit
```

---

## Acquisition

Discovery creates content → content creates curiosity → people submit robots → jobs create pull.

See [`DISCOVERY_CONTENT.md`](./DISCOVERY_CONTENT.md) · [`TRAFFIC_SPRINT.md`](./TRAFFIC_SPRINT.md).

---

## Current product question

Not merely: *Do people click See All?*

Now:

> Does ReadyForRobots understand their robot well enough to show credible work — and does that work create enough value that they activate a job list?

### Pull metrics

| Manifestation | Signal | Event |
|---------------|--------|--------|
| **Discovery pull** | Want to see more jobs | See All Jobs · `rdd_see_all_clicked` |
| **Commercial pull** | Keep this work in a live list | Activate job list · `rdd_jobs_list_activated` |

Keep See All CTR. Activate is one page-level CTA, not a button on the job card.

Segment by `persona` (oem / distributor / integrator) and by robot product / family within persona.

---

## Stop / Continue

### CONTINUE NOW

**M2 — Match:** **FROZEN** after **MATCH TRUTH — PRODUCTION PASS** (2026-08-17, #15 live). No fifth robot, no ranking tweaks, no new scoring ideas.

Phases 1–3 remain **frozen** at v1.0 calibration ([`robot_understanding_v1.md`](./robot_understanding_v1.md)). Production `/` uses `POST /api/robot-job-search` (profile + match in one transaction; P0-A profile path still exists).

**M1 shadow** (first **20 real reviewed** profiles → one Understanding decision) continues in parallel as a **calibration instrument**.

Traffic / C04 stay **paused** ([`V1_PRETRAFFIC_TEST.md`](./V1_PRETRAFFIC_TEST.md)):

- **MATCH TRUTH** — **PRODUCTION PASS**
- **SUBMIT WORKFLOW** — merged / production smoke PASS
- **TRAFFIC** — paused

### DO NOT CONTINUE YET

- Understanding extractor / Blind 20 retune / open-ended polish  
- Patching the old heuristic matcher to fake differentiation  
- New capability families / channel research / OEM scrape scale  
- More UI concepts / distributor–integrator product surfaces  
- Expanding the product hypothesis / inviting traffic before the pre-traffic gate  

### Operating rule (replaces the Aug 15 freeze)

> **Do not expand the product hypothesis while traffic runs.**  
> **Product-integrity work required to make `CAPABILITIES → FIND WORK` accurate is allowed.**

That is the critical distinction. Heuristic keyword patches are not integrity work — Phases 1–3 of Understanding v1 are.

| Locked | |
|--------|--|
| Category | Find Jobs for Robots |
| Thesis | Robots need jobs |
| Primitive | `CAPABILITIES → FIND WORK` |
| Stack | FIND → QUALIFY → PLACE later |
| Surface | `/` Jobs terminal |
| Intelligence | Identity → Sources → Facts → Capabilities → Requirements Match |
| Discovery metric | See All CTR |
| Commercial metric | Job list activated |
| First segmentation | OEM vs distributor vs integrator |

**Decision rule:** Expansion and GTM wedges come from **behavior**. Understanding accuracy comes from **evidence + blind eval**, not from fixture echo.

See [`readyforrobots_v1_milestones.md`](./readyforrobots_v1_milestones.md) · [`robot_understanding_v1.md`](./robot_understanding_v1.md) · [`EXPERIMENT_MODE.md`](./EXPERIMENT_MODE.md) · [`TRAFFIC_SPRINT.md`](./TRAFFIC_SPRINT.md) · [`hermes_retired.md`](./hermes_retired.md) (Hermes bridge is retired)
