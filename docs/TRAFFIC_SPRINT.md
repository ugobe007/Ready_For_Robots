# Traffic sprint — capability → find work

**Status:** Primary product test · channel research **stopped**  
**Surface:** `/experiment` (one UI)  
**Strategic model:** [`CAPABILITY_MODEL.md`](./CAPABILITY_MODEL.md)  
**Unknown:** When we show someone work matched to what they sell or can solve, do they want more?

Not a product sprint. Not another channel / ontology session.

---

## Category vs CTA

**Category:** Find Jobs for Robots.

Outreach personalizes (same landing page):

| Persona | Outreach prompt | Still lands on |
|---------|-----------------|----------------|
| A — OEM | Find jobs for your robot. | `/experiment` |
| B — Distributor | Find jobs for the robots you sell. | `/experiment` |
| C — Integrator | Find automation jobs your company can solve. | `/experiment` |

Do **not** ship three UIs for Cohort 1–3. Track **persona + source** so we learn which segment pulls.

---

## Message patterns (use these)

### OEM

> I gave ReadyForRobots a warehouse robot and it found 67 places where that robot could work.  
> Give us your robot. We'll find jobs it can do.  
> [Try it → `/experiment?persona=oem&src=…`]

### Distributor

> We matched jobs across robots a channel partner already sells.  
> Find jobs for the robots you sell.  
> [Try it → `/experiment?persona=distributor&src=…`]

### Integrator

> For a Southeast integrator (cobot / industrial arms), we went from 0 → ~19 automation jobs their team can solve.  
> Find automation jobs your company can solve.  
> [Try it → `/experiment?persona=integrator&src=…`]

**Outreach principle:** Send them to `/experiment`. Don't ask for a meeting. Don't explain the research.

---

## Mixed audience (required)

Do **not** send the first 100 only to OEMs. Intentionally mix:

### Cohort A — Robot OEM

CEO · VP Sales · BD · Product / commercialization  
Prompt: *Find jobs for your robot.*

### Cohort B — Distributor

Owner · President · Sales leader · Robotics business leader  
Prompt: *Find jobs for the robots you sell.*

### Cohort C — Integrator

President · Automation sales · BD · Application engineering leader  
Prompt: *Find automation jobs your company can solve.*

Rough mix target across 100: **~40% OEM · ~30% distributor · ~30% integrator** (directional, not rigid).

If See All CTR by persona looks like OEM 18% / distributor 41% / integrator 57%, that changes GTM. Aggregate CTR alone is not enough.

---

## Instrumentation (persona + source)

Append to every outreach link:

```
/experiment?persona=oem|distributor|integrator&src=<channel_or_campaign>
```

Events attach `persona` and `src` on `rdd_*` funnel steps (see experiment page). Segment:

| Slice | Why |
|-------|-----|
| `persona` | Which entry-point pulls |
| `src` | Which outreach channel |
| `profile_key` / family | Which robot envelope |
| `job_key` / company | Which job kinds feel compelling |

Primary metric still: **See All CTR** — but **by persona**.

### First useful read (Cohort 1–3)

Not aggregate CTR alone. Read in this order:

1. **Persona pull** — OEM vs distributor vs integrator See All CTR (and job engagement before gate)  
2. **Within persona** — which submitted capability family / `profile_key` drives the strongest job engagement (`job_viewed`, 3+, See All)

That answers the **first customer segment** question:

| If strongest… | Initial wedge |
|---------------|---------------|
| OEM | Robot OEMs needing applications |
| Distributor | Distributors needing pipeline across portfolio |
| Integrator | Integrators needing automation work they can solve |

If distributors or integrators **materially** outperform OEMs, that is **not** a messaging tweak — it changes who we sell to first. Still one engine; different first wedge.

Until Cohort 1–3: **traffic, segmentation, behavior. No more expansion.** No new capability layers.

---

## Pre-traffic QA gate (required)

Test 10 deliberately different robot URLs. **Never** silently map a palletizer onto Origin tote jobs.

| Kind | Expect |
|------|--------|
| AMR | → Origin jobs |
| Floor cleaning | → Neo jobs |
| Inspection / cobot / palletizer / humanoid / ag / delivery / construction / food service | → **unsupported** (honest refuse + try AMR/scrub demos) |

Results: [`qa_robot_url_matrix.md`](./product_sim/qa_robot_url_matrix.md)

---

## Cohorts (volume)

### Cohort 1 — 20 (instrumentation + integrity + persona tags)

Verify: land → submit → capabilities → jobs → 3+ → See All → signup start.  
Confirm `persona` / `src` land on events. Watch `rdd_unsupported_robot`.  
Touch only if something is **literally broken**.

### Cohort 2 — +30 (freeze)

No product changes unless Cohort 1 exposed a real bug. At ~50, look for **large** directional signals by persona — not statistical significance.

### Cohort 3 — to 100

No product changes 50→100 unless broken. Then first real conversion review **segmented by persona**.

---

## How to read results

**Before See All** = product. **After See All** = conversion mechanics.

| If… | Then… |
|-----|--------|
| Don't submit | Proposition / input |
| Submit, don't engage jobs | Matching / job quality |
| Engage, no See All | Value / gating |
| See All, won't register | Signup friction |
| Register and ask “how do I contact these companies?” | Earned next layer |
| One persona dominates See All CTR | GTM wedge — still one engine |

Do **not** decide post-100 architecture now. The funnel decides.

---

## Explicitly frozen (adjacent research)

| Frozen | Why |
|--------|-----|
| OEM scrape 11–50 | Premature scale |
| More distributors | Question already answered |
| Channel Match scoring | Premature |
| Distributor / integrator UI | Validate pull first |
| Channel Graph expansion | Fixtures enough; stop here |

Keep fixtures: [`channel_graph/`](./channel_graph/) · Manipulation 25 results. Return to traffic.

---

## Sequence

```
QA 10 robots (pass)
  → mixed outreach (OEM / distributor / integrator) with persona= + src=
  → send 20 qualified
  → verify instrumentation + persona tags
  → +30 (freeze)
  → reach 100
  → read the funnel by persona
```
