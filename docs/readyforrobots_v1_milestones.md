# ReadyForRobots v1 — Product spine & finite milestones

**Status:** Canonical product path (2026-08-17) — profile path live (P0-A); **M2 unlocked** against frozen Understanding; traffic paused until MATCH TRUTH  
**Not:** Open-ended Understanding research. Not Blind retune.  
**Related:** [`CAPABILITY_MODEL.md`](./CAPABILITY_MODEL.md) · [`EXPERIMENT_MODE.md`](./EXPERIMENT_MODE.md) · [`robot_understanding_v1.md`](./robot_understanding_v1.md) · shadow [`calibration/understanding_shadow_v1.md`](./calibration/understanding_shadow_v1.md) · pre-traffic [`V1_PRETRAFFIC_TEST.md`](./V1_PRETRAFFIC_TEST.md)

---

## Product promise (canonical)

A user gives ReadyForRobots a **robot URL**. We understand the robot accurately enough to **find credible jobs** it can do, **show why** each job matches, and let the user **qualify** the ones worth pursuing.

```
ROBOT URL
  → UNDERSTAND (Company → Product → Facts → Capabilities)
  → FIND WORK (Capabilities → Workflows → Robot Jobs)
  → EXPLAIN THE MATCH (why fits / unknowns)
  → QUALIFY
  → PURSUIT
```

**Infrastructure ≠ product.** Shadow mode, Blind 20, and ontology exist to support this path. They are not the thing users buy.

---

## Current state (accurate)

| Layer | State |
|-------|--------|
| **FIND WORK** | Substantially proven |
| **QUALIFY** | First pattern proven |
| **ROBOT UNDERSTANDING** | Trustworthy but incomplete (v1.0 freeze) |
| **CAPABILITY → JOB MATCHING** | M2 requirement matcher prototyped (Novolex + 4-physics gold + corpus templates) |
| **CHANNEL / PLACE** | Later — after FIND + QUALIFY demand evidence |

Homepage stays simple:

```
URL → profile → capabilities (light) → jobs with why / evidence / unknowns
  → See All → Qualify
```

---

## Four finite milestones

Build in order. Clear each gate before the next. **Do not** reopen Understanding forever between them.

| Milestone | Done when |
|-----------|-----------|
| **M1 — Understand** | Real robot profiles are professionally usable; shadow confirms acceptable behavior (honest B/C unknowns OK) |
| **M2 — Match** | Capability → requirement matching produces **defensible, differentiated** top jobs |
| **M3 — Product** | URL → profile → 5 jobs → See All works end-to-end |
| **M4 — Commercial** | Qualify This Job produces a **Pursuit Brief** people request |

After M4: **stop building and sell/test.** Channel / PLACE only after FIND + QUALIFY show demand evidence.

### Crucial correction

Do **not** allow an open-ended loop:

> improve Understanding → measure → improve Understanding forever

Shadow answers **whether to reopen Understanding (M1 calibration)**. It does **not** block **M2**. The real next build is **Phase 4 matcher work** (M2) against frozen Understanding output — not more Understanding polish.

---

## Shadow checkpoint (M1 calibration — not an M2 blocker)

Full ops contract: [`calibration/understanding_shadow_v1.md`](./calibration/understanding_shadow_v1.md).

Shadow is a **decision instrument for Understanding reopen / M1 accept**, not a permanent research program, and **not** a gate that blocks M2 prototyping.

1. Collect and human-review the **first 20 real** robot profiles (not hundreds).
2. Until 20 reviewed: individual WRONG / INCOMPLETE cases are **observations only** — not reopen permission for Understanding extractors.
3. At 20 reviewed, make **ONE** decision about Understanding:

| Pattern | Decision |
|---------|----------|
| Repeated **general** failure (e.g. 8/20 miss PDFs) | Reopen Understanding **only** for that mechanism |
| Scattered failures + most profiles professionally useful | Accept B/C unknowns as product behavior — M1 “good enough” |

**Question to answer:**  
“Is Understanding good enough to support the product, with honest unknowns?”  

**Not:** “Is Understanding perfect?”  
**Not:** “May we start M2?” — M2 may begin now (see below).

---

## M2 unlock (decoupled from 20-shadow)

**New rule (2026-08-17):** Understanding Phases 1–3 remain **frozen**. **M2 may begin** using grounded profiles (Tier A/B/C) and must **propagate unknowns**. The 20-shadow gate is for **M1 calibration / reopen-Understanding decisions only** — not a blocker on prototyping M2.

**Rationale (circular dependency):** can’t invite traffic until match is credible; can’t collect 20 organic shadows without traffic; match can’t become credible without M2. So: freeze Understanding, allow M2 against its output.

| Layer | Status |
|-------|--------|
| Understanding extractors / Blind retune | **FROZEN** |
| Production profile path (`/api/robot-profile`) | **LIVE** (P0-A) |
| M2 requirements matcher | **ALLOWED to prototype** (next mission) |
| Traffic / C04 publish | **Still paused** until MATCH TRUTH + funnel gates |

### Current operating loop

```
Keep Understanding frozen
  → M2: capability → requirement match on A/B/C profiles (propagate unknowns)
  → Clear MATCH TRUTH pre-traffic gate
  → Then invite traffic / content (shadow accrues organically)
  → At 20 reviewed shadows: one M1 Understanding decision (narrow reopen or accept)
```

### Active work queue

| Priority | Work | Notes |
|----------|------|-------|
| **Now (engineering)** | **M2 Match** — requirement satisfaction (MATCHED / UNMET / UNKNOWN / LIKELY); Novolex + four-physics gold | In progress this mission |
| Paused | Content / C04 / invite traffic | Until MATCH TRUTH clears Digit distinctive review — see [`V1_PRETRAFFIC_TEST.md`](./V1_PRETRAFFIC_TEST.md) |
| Ongoing | Review shadow rows as they arrive | Observations only until 20; does not block M2 |

Canonical content slate (when traffic resumes): [`CONTENT_SPRINT.md`](./CONTENT_SPRINT.md) · [`DISCOVERY_CONTENT.md`](./DISCOVERY_CONTENT.md) · [`TRAFFIC_SPRINT.md`](./TRAFFIC_SPRINT.md).

---

## Phase 4 / M2 target shape (next mission — prototyping allowed)

M2’s engine: professional **capability → requirement** matching with explained fit. Understanding stays frozen; matcher consumes Tier A/B/C profiles and surfaces unknowns.

**Reject:** keyword “mobile manipulator → therefore 12 vague jobs.” · Do **not** patch the old heuristic matcher to fake differentiation.

**Target card shape (example):** Vega → CNC load/unload · **Novolex-shaped** plant workflows as a concrete next-mission fixture

| Surface | Content |
|---------|---------|
| Verdict | **GOOD MATCH** (or weaker / no-match with same honesty) |
| Why | Matched requirements (grounded in capabilities / facts) |
| Still unknown | Unmet or unknown requirements — shown, not hidden |
| Evidence | Trace to profile facts / sources where available |

Jobs terminal should surface a small set of **differentiated** top jobs, each with Why / Still unknown — not a laundry list of category keywords.

Spec depth: [`robot_understanding_v1.md`](./robot_understanding_v1.md) Phase 4 sections. Extractor reopen still requires the shadow narrow-reopen rule.

---

## Operating rules

| Do | Do not |
|----|--------|
| Keep Understanding frozen; prototype M2 against A/B/C profiles | Treat Blind 20 or 20-shadow as a blocker on M2 |
| Use shadow for a finite M1 Understanding decision | Chase Understanding perfection / Blind retune |
| Propagate unknowns in match explanations | Patch old keyword matcher to fake board differentiation |
| Pause traffic until MATCH TRUTH | Publish C04 / invite traffic on profile-path alone |
| Accept honest B/C profiles as M2 inputs | Expand Channel / PLACE before FIND+QUALIFY demand |

Freeze line for Understanding code: [`calibration/understanding_blind_20/V1_0_FREEZE.md`](./calibration/understanding_blind_20/V1_0_FREEZE.md).
