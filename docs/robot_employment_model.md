# ReadyForRobots — Robot Employment Model

**Status:** Canonical operating model (2026-08-22)  
**Surface today:** `/` Jobs terminal — FIND → QUALIFY → PLACE later  
**Do not:** treat this as permission to expand SIGNAL, Cal, or a two-sided marketplace UI

---

## What we are

ReadyForRobots is **recruitment and placement infrastructure for robotic labor**.

Companies have work. Robots need jobs. ReadyForRobots brings them together.

Not a robot catalog. Not a lead-generation platform. Not an SDR copilot.

The central object is the **Robot Job**.

The transaction is:

> We found work your robot is qualified to perform.

A sale is an **outcome of a successful placement**, not the object we optimize.

---

## The employment loop

```
DISCOVER WORK
        ↓
DEFINE THE JOB
        ↓
QUALIFY THE JOB
        ↓
FIND ROBOT CANDIDATES
        ↓
QUALIFY THE ROBOTS
        ↓
MATCH
        ↓
INTERVIEW / SITE ASSESSMENT
        ↓
PILOT
        ↓
HIRE / PLACE
        ↓
ROBOT WORKS
        ↓
MEASURE PERFORMANCE
        ↓
EXPAND EMPLOYMENT  →  DISCOVER MORE WORK
```

Product today implements the top of the loop: **show us the robot → confirm capabilities → find work**. PLACE, pilots, and employment history come after FIND is trusted.

Supply-side candidate roster (who can be placed): [robot_employment_universe.md](./robot_employment_universe.md).

---

## Objects

| Object | Meaning | Not |
|--------|---------|-----|
| **Employer** | Organization with physical work | Prospect, lead, buyer |
| **Workplace** | The facility where work happens | Account |
| **Work** | Observable physical activity (robot-neutral) | A robot use-case we invented |
| **Robot Job** | Work defined well enough to recruit against | A SIGNAL row |
| **Job requirements** | What a robot must do / tolerate | Keywords, industry labels |
| **Robot candidate** | A specific product/configuration | A vendor name |
| **Robot résumé** | Capabilities + morphology + integrations + cost + history | Category (“AMR”, “humanoid”) |
| **Qualification** | Explainable requirements ↔ capabilities | A match percentage |
| **Interview** | Site assessment + practical demo | A sales demo |
| **Pilot** | Working interview | Closed-won trial |
| **Placement** | Robot hired into the job | Robot sold |
| **Employment** | The robot is working | Deployment as an end state |
| **Open position** | Additional work at an employer after a placement | Upsell |

Work is discovered **before** we ask which robot could do it. Otherwise the system invents jobs to fit machines.

```
Employer → Workplace → Work → Robot Job → Job requirements
                                              ↕
Robot → Capabilities → Qualifications → Experience
                                              ↕
                         Match → Candidate → Assessment
                         → Pilot → Placement → Employment
                         → Performance → Work history → Expansion
```

This extends, it does not replace, the capability spine:

`COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS → WORKFLOWS → JOB REQUIREMENTS → MATCH`

Never: `company → category → jobs`.

---

## Language (do not let sales terms creep back)

| Never | Use |
|-------|-----|
| Lead | Robot Job |
| Prospect / buyer (Jobs path) | Employer |
| Lead qualification | Job qualification |
| Product fit | Robot qualification |
| Demo | Interview / site assessment |
| POC | Pilot (working interview) |
| Closed-won / robot sold | Placed / hired / deployed |
| Upsell | Open robot positions / expanded employment |
| MQL / pipeline | Jobs discovered, qualified, matched, placed |

**Available for work** is the robot-side status: this robot is registered; find it jobs.

---

## Two sides of the labor market

| Employers (work) | Robot workforce (candidates) |
|------------------|------------------------------|
| Factories, warehouses, hospitals, restaurants, hotels, airports, retail, cleaning, construction, agriculture | OEMs, distributors, integrators, RaaS, fleet operators |

ReadyForRobots sits **between** them. GTM today still starts on the robot side: an OEM submits a URL and we return jobs. We do not wait for employers to post. We observe evidence of work and say: **we think you have a Robot Job.**

That is how we avoid marketplace cold-start. It is not a license to pitch “buy this robot” to the employer, or “here are leads” to the OEM.

---

## Job Card (unit of value)

A Robot Job Card is what we show and what we send.

```
EMPLOYER
WORKPLACE
JOB
WORK BEING PERFORMED
JOB REQUIREMENTS
WORK VOLUME          ← Unknown unless evidenced
CURRENT LABOR        ← Unknown unless evidenced
WHY THIS IS WORK     (not why to buy)
EVIDENCE
ROBOT QUALIFICATION  (explainable ✓ / △ / ✕ — never a %)
OPEN QUESTIONS
NEXT STEP            (site assessment, not outreach)
```

Do **not** invent FTE, loaded labor cost, payback, or route meters. Unknown is a valid field. Fake economics destroy the model.

Qualification is explainable:

- **Qualified** — you or the employer confirmed the work (not a matcher score)
- **Conditional** — physically plausible; pending your review and a site assessment
- **Not qualified** — a required capability is unmet
- **Pending robot** — the job is real; this robot has no résumé in R4R yet

No 87% match.

---

## Metrics that matter (later dashboard)

Jobs discovered · Jobs qualified · Open positions · Robots available for work · Qualified matches · Site assessments · Pilots · Robots placed · Robot hours worked · Annualized work placed · Retention · Expansion jobs

Not: leads, MQLs, pipeline coverage.

---

## What is live vs later

| Now (Jobs terminal) | Later (do not build this cycle) |
|---------------------|----------------------------------|
| Discover work from evidence | Employer job posting |
| Define the job on the card | Interview / site-assessment product |
| Qualify the job (work is real enough) | Pilot workflow |
| Match from submitted robot URL | Placement CRM as HRIS |
| Unlock jobs in CRM | Employment-rate dashboard |
| | Robot career / work history graph |

Matcher (M2) stays frozen. Understanding v1 Phases 1–3 stay frozen. This model changes **what the objects mean**, not match scoring.

---

## Current experiment

**Sentence to test:** “We found jobs for your robots.”

Pack: [`docs/experiments/robco_job_cards.md`](./experiments/robco_job_cards.md)

Rules for that pack:

1. Every card is named work from the manipulation ledger / match corpus.
2. Do not pad to a round number with invented employers.
3. Do not score RobCo as Qualified until a RobCo URL produces a résumé.
4. Economics stay Unknown until evidenced.
