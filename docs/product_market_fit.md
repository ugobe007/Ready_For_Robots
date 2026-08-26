# Product / Market Fit — ReadyForRobots

**Canonical PMF statement for all harness agents, Cursor sessions, and mission briefs.**

**Last updated:** 2026-08-26

**Hermes is retired.** Do not run Hermes as the Jobs agent. The product loop is robot URL → Job Cards (`POST /api/robot-job-match`). See [`hermes_retired.md`](hermes_retired.md).

**Operating model:** [`robot_employment_model.md`](./robot_employment_model.md)

---

## What we are

**ReadyForRobots is the employment layer for robots** — recruitment and placement infrastructure for robotic labor.

Companies have work. Robots need jobs. We find the match.

The unit of value is the **Robot Job**, not a lead. The robot is the candidate. The company with work is the employer. A sale is what happens after a robot gets the job.

GTM still starts with robot companies (OEMs, distributors, integrators, RaaS): they register a robot as **available for work**. We do not sell “SDR productivity.” We show up with jobs.

**Deeper thesis:** Matching supply and demand *is* the product. Commercial maturity still matters at placement — see [commercial_maturity_models.md](./commercial_maturity_models.md) — but it is not the category.

**Brand dual meaning:** Is the work ready for a robot? Is the robot ready for the work?

---

## Who buys

| Segment | Job to be done |
|---------|----------------|
| **Robot OEMs** | Find Robot Jobs their machines are qualified to perform |
| **Integrators / VARs** | Place their robots (or the robots they install) into qualified work |
| **Distributors / RaaS / fleet operators** | Keep carried robots employed |

Primary ICP remains the **robot workforce side**. Employers (factories, hospitals, warehouses) are the other side of the labor market — we discover their work; we do not pitch them “buy a robot” as the product.

---

## Core product promise

1. **Discover work** — observable physical jobs, robot-neutral
2. **Define the Robot Job** — employer, workplace, requirements, evidence
3. **Qualify the robot** — hardware capabilities **and task models** ↔ job requirements (explainable, never a %)
4. **Place later** — site assessment → pilot → employment

**The channel hole:** a robot can be sold into a warehouse or a hospital and still fail the work. The physical task is performed by a **task model** (internal nickname: “certificate”) — a trained policy for that job. Distributors and integrators often resell platforms and skip this cost. Qualification stays **conditional** until we know which model covers the work and where it is published.

Hero copy: **Find jobs for your robot.** Subhead: **We match your robots to specific jobs and models using your URL.**

---

## CRM choice (customer-facing)

Customers run their funnel in **either**:

| Path | Routes / integration | When to prefer |
|------|----------------------|----------------|
| **Native CRM** | `/pipeline`, `/crm`, in-app save + kanban | Default for new signups; fastest time-to-value |
| **HubSpot** | HubSpot connect + sync (Growth tier) | Teams already on HubSpot; keep reps in familiar CRM |

**Agent rule:** ProductSurface work indexes on **submit robot URL → credible Robot Job Cards → unlock jobs in CRM**. Native CRM and HubSpot keep the job list; they are not a SIGNAL buyer workspace on the Jobs path.

Salesforce and other CRMs are future; HubSpot is the external CRM bet today.

---

## Success metrics (PMF)

Measure weekly and report in mission `outcome.md`:

| Stage | Metric |
|-------|--------|
| Awareness | Anonymous `/` Jobs submits, Job Cards inspected |
| Intent | Signup starts after jobs (`src=jobs_activate`) |
| Activation | Jobs unlocked in CRM, watch opt-in |
| Value | Jobs qualified, robots submitted as available for work |
| Later | Placements, robot hours, expansion jobs |

**North star for product missions:** increase **robots that have jobs** (URL → credible Job Cards → kept in CRM), not leads or news volume.

---

## How this relates to lead quality

Lead quality (`docs/lead_quality_north_star.md`) is **SIGNAL infrastructure**, not the product. Jobs copy must not hop onto HOT buyers. Never showcase junk work to win a demo. Always ship UX that makes a robot company feel we found **work their robot can do**.

---

## Agent priorities (ranked)

When choosing or executing a mission, prefer work in this order:

1. **Value proof (anonymous)** — live lead + pipeline_action + outreach draft before signup ([value_first_principle.md](value_first_principle.md))
2. **Conversion to signup** — CTA continuity, post-auth landing on `/pipeline`, friction removal ([conversion_agent_challenges.md](conversion_agent_challenges.md))
3. **Activation** — first save, copy draft, CRM account, HubSpot connect flow
4. **Pipeline motion** — rotate/preview leads, kanban, next actions, share/amplify
5. **Earned upgrade** — paywall only after free value consumed (save limit, research teaser)
6. **Lead quality** — only when snapshot shows junk blocking trust (names/events first)
7. **Market intel / catalog** — supports pitch specificity, not primary PMF

**Anti-patterns:** robotics news aggregator, OEM-as-buyer pipeline, dashboard parity with Salesforce, volume over quality, **horizontal GTM data parity** (Explee/Apollo-style “105M companies” — see [competitive_positioning.md](competitive_positioning.md)).

---

## Competitive frame (vs Explee and data tools)

Users will compare us to [Explee](https://explee.com/landing-search) and similar GTM data providers. **Do not compete on database size.** Compete on:

| We lose if judged on… | We win when judged on… |
|------------------------|-------------------------|
| Company/people count | **Robot buyer intent** with HOT/WARM timing |
| Search filters & lookalikes | **`pipeline_action`** + **`robot_types_needed`** |
| CSV export & API runs | **Automated funnel** — save, outreach, kanban, HubSpot |
| Generic deep research | **SIGNAL** cited research on qualified robot buyers |

**Positioning line:** Explee helps you find accounts. ReadyForRobots helps robot companies **close** them.

Full comparison: [competitive_positioning.md](competitive_positioning.md).

---

## Related docs

- [value_first_principle.md](value_first_principle.md) — show value before signup/pay
- [competitive_positioning.md](competitive_positioning.md) — vs Explee, Apollo, Clay
- [market_thesis.md](market_thesis.md) — ranked backlog and puck bets
- [conversion_agent_challenges.md](conversion_agent_challenges.md) — funnel challenges for ProductSurface
- [readyforrobots-ux.md](readyforrobots-ux.md) — Detect → Qualify → Engage → Advance
- [AGENTS.md](../AGENTS.md) — harness constitution
- [hermes_retired.md](hermes_retired.md) — Hermes is not the Jobs agent
- [pstack_jobs.md](pstack_jobs.md) — Cursor pstack is IDE-only
