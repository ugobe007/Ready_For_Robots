# ReadyForRobots Capability Model

**Status:** Locked strategic model (2026-08-15)  
**Not:** Three products. One discovery engine. Three entry points.

---

## Category statement

> **ReadyForRobots — Find Jobs for Robots.**

That is the market / category line. Personalize the CTA by who is supplying capabilities:

| Entry | Prompt |
|-------|--------|
| OEM | Find jobs for your robot. |
| Distributor | Find jobs for the robots you sell. |
| Integrator | Find automation jobs your company can solve. |

Same system. Same graph. Same engine. Different capability envelope.

---

## Primitive

```
CAPABILITIES → FIND WORK
```

Addressable user (broadened):

> Companies that need to find commercial applications for robotic capabilities.

Includes: robot OEMs · distributors · VARs · system integrators · automation companies  
(and possibly later: automation-component manufacturers).

Common problem:

> We know what our technology can do. Where is the work?

---

## Three levels (do not rebuild as separate products)

```
Level 1 — Robot
  What can this robot do?
  Origin · Neo · Spot
       ↓
Level 2 — Portfolio
  What can the robots this company sells do?
  RG Group · XCube · RobotShop
       ↓
Level 3 — Solution provider
  What automation problems can this company solve?
  Cross
       ↓
ReadyForRobots
  Find work matching those capabilities.
```

| Level | Envelope source | Evidence |
|-------|-----------------|----------|
| 1 Robot | Single SKU / URL | Origin / Neo / Spot · `/experiment` |
| 2 Portfolio | Brands carried | Reverse-five · distributor fixtures |
| 3 Solution | Aggregate solution capability | Cross · Manipulation 25 · 0→~19 |

Economic shape (distributors / integrators):

```
value ∝ portfolio breadth × capability breadth × territory coverage
```

The more robots / solution types they sell or can deliver, the more valuable discovery becomes.

---

## Eventual loop (moat — do not build now)

```
WORK → ROBOT → CHANNEL → CUSTOMER → DEPLOYMENT
  → evidence that this robot can perform this work
  → better DISCOVERY + MATCHING
```

Asset is not the lead DB, SIGNAL, or a distributor directory. It is accumulating knowledge of:

> What physical work exists, which machines can perform it, and who can commercially deliver those machines.

Channel routing concept (frozen research):

```
Robot Job → Robot Match → Channel → Pursuit
```

**Routable Job** = capability × territory × channel capability (sell / integrate / deploy / service). Concept only — no scoring yet.

---

## Stop / continue

| Stop (for now) | Continue |
|----------------|----------|
| OEM scrape 11–50 | Traffic sprint on `/experiment` |
| Another 50 distributors | Mixed-audience outreach (OEM / distributor / integrator) |
| Channel Match scoring | Persona / source tracking |
| Distributor / integrator UI | Fixtures already written |
| Adjacent research expansion | Read See All CTR **by persona** |

The next evidence question:

> When we show someone work matched to what they sell or can solve, do they want more?

**First useful read:** persona pull (OEM vs distributor vs integrator), then capability-family engagement within persona. That names the first customer segment — not a messaging tweak if channel/integrator wins.

Until Cohort 1–3: traffic, segmentation, behavior. **No more expansion.**

**Decision rule:** The next ReadyForRobots decision comes from **behavior**, not another hypothesis.

| Locked | |
|--------|--|
| Product hypothesis | `CAPABILITIES → FIND WORK` |
| Experiment | matched work → desire to see more |
| Primary metric | See All CTR (`rdd_see_all_clicked`) |
| First segmentation | OEM vs distributor vs integrator |
| Second segmentation | capability-family engagement within persona |
| Operating activity | Get qualified people into `/experiment` · observe · accumulate |
| First real question (after evidence) | Who wants this most — and what kind of work makes them want more? |

**Traffic vs product:** generating traffic via **discovery content** / cohorts / funnel reports is allowed. Changing the experiment because early numbers look weak is not. See [`DISCOVERY_CONTENT.md`](./DISCOVERY_CONTENT.md).

No additional product, channel, ontology, or discovery work until traffic gives evidence.

See [`TRAFFIC_SPRINT.md`](./TRAFFIC_SPRINT.md) · [`EXPERIMENT_MODE.md`](./EXPERIMENT_MODE.md) · [`hermes_intelligence_bridge.md`](./hermes_intelligence_bridge.md)
