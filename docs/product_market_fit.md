# Product / Market Fit — ReadyForRobots

**Canonical PMF statement for all harness agents, Cursor sessions, and mission briefs.**

**Last updated:** 2026-06-16

---

## What we are

**ReadyForRobots is the automated sales pipeline for robot companies.**

Robot OEMs, integrators, and distributors sign up to **automate their sales funnel** — from verified buyer intent through outreach and deal advance — without building their own lead-ops stack.

---

## Who buys

| Segment | Job to be done |
|---------|----------------|
| **Robot OEMs** | Find qualified buyer ops (warehouses, retail, hospitality, healthcare) and pitch the right robot SKU |
| **Integrators / VARs** | Turn SIGNAL-ranked leads into meetings faster than manual prospecting |
| **Sales leaders at robotics vendors** | Replace spreadsheet + RSS chaos with a pipeline that moves deals forward |

We do **not** sell to end-user operators as the primary ICP. We sell **to the companies that sell robots**.

---

## Core product promise

1. **Detect** — verified buyer intent (not vendor PR, not headline junk)
2. **Qualify** — SIGNAL-ranked leads with industry, robot types, and pipeline actions
3. **Engage** — outreach templates, social amplify, autonomous next actions
4. **Advance** — kanban pipeline, CRM accounts, stage progression

Hero copy and home narrative: **“Automate Your Sales Pipeline.”**

---

## CRM choice (customer-facing)

Customers run their funnel in **either**:

| Path | Routes / integration | When to prefer |
|------|----------------------|----------------|
| **Native CRM** | `/pipeline`, `/crm`, in-app save + kanban | Default for new signups; fastest time-to-value |
| **HubSpot** | HubSpot connect + sync (Growth tier) | Teams already on HubSpot; keep reps in familiar CRM |

**Agent rule:** ProductSurface and backend work should support **both paths equally** in copy, onboarding, and feature parity where feasible. Do not over-index on dashboards or generic robotics content — index on **signup → first saved lead → pipeline motion → CRM or HubSpot**.

Salesforce and other CRMs are future; HubSpot is the external CRM bet today.

---

## Success metrics (PMF)

Measure weekly and report in mission `outcome.md`:

| Stage | Metric |
|-------|--------|
| Awareness | Anonymous `/pipeline` views, hero live-panel engagement |
| Intent | Signup starts, OAuth/magic-link completes |
| Activation | First lead saved, first CRM account, HubSpot connected |
| Value | Deals advanced, outreach sent, social shares from pipeline |
| Revenue | Upgrade attempts, `/pricing` clicks at save limit |

**North star for product missions:** increase **activated robot-company workspaces** (signed up + first pipeline value), not raw page views or news volume.

---

## How this relates to lead quality

Lead quality (`docs/lead_quality_north_star.md`) is **infrastructure for PMF**, not the product itself:

- Clean **names/events** → reps trust the pipeline
- Defensible **scores** → SIGNAL activation converts
- **Robot types + pipeline_action** → OEMs know what to pitch

**Never** ship UX that showcases junk leads to win demos. **Always** ship UX that makes a signed-up robot company feel their funnel is running on autopilot.

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
