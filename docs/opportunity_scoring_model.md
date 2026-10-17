# Opportunity scoring model

**Owner:** Bob Christopher · **Status:** approved direction, v0.4 (2026-10-17)
**Location in repo:** `docs/opportunity_scoring_model.md`
**Replaces:** any logic where a signal creates, gates or deletes a buyer opportunity (including the "a signal must name the work" rule in #356/#359/#360).

---

## 1. The principle

**Signals inform decisions; they do not make them.**

1. **Discover** automation opportunities from what a company *is*: its industry, its facilities and the workflows those facilities run.
2. **Score** every opportunity on a fixed set of variables (the **opportunity score**).
3. **Score each robot against each opportunity** (the **match score**): can *this* robot win and run *this* job?
4. **Signals** are evidence that moves a variable up or down. A signal never creates an opportunity and never deletes one.

An opportunity is **company × workflow** (per site where we know sites). "No workflow, no robot job" still holds; the workflow comes from the model, not from a signal.

Two layers, because most deployment challenges belong to the robot, not the buyer. A hospital's pharmacy delivery is the same opportunity whichever robot shows up; whether a given robot can do it there is a property of that robot at that buyer.

## 2. Discovery

For each buyer company:

- Industry (taxonomy `industries`, same list robots use) and facility types.
- Look up the workflows that industry/facility type runs (industry → workflow map, built from `workflow_ontology.v1.json` and the taxonomy functions). Example: hospital → pharmacy delivery, specimen/lab transport, linen and waste transport, floor cleaning, disinfection, food tray delivery.
- Each (company, workflow) pair is an opportunity, whether or not any signal mentions it.

Start with the 102 seed accounts.

Starting list of workflows to include in the map (humanoid and industrial), for Bob's review:

| Setting | Workflows |
|---|---|
| Factory | light assembly (fasteners, connectors, cable routing), machine tending (CNC, presses, injection molding), quality checks, overhead or awkward-posture work, line-side replenishment, component transport |
| Warehouse | shelf picking, tote and case moving, truck loading/unloading, pallet moves, cycle counting |
| Plants and facilities | gauge, valve and thermal inspection; valve and switch operation; predictive-maintenance rounds; floor cleaning |
| Hazardous sites | nuclear (radiation zones, decommissioning), chemical (leaks, confined spaces), mining (tunnels, remote inspection), disaster response |

Each must map to a taxonomy function and industry. Industries the taxonomy lacks (likely mining, chemical) are **proposed** to Bob, not added.

## 3. Layer 1: opportunity score (buyer × workflow)

Answers: **is this company worth pursuing for this work?** Same for every seller.

| # | Variable | Question | Evidence |
|---|---|---|---|
| 1 | **Workflow fit** | Do they run this work, and how much of it? | Industry, facility type, sites, stated operations |
| 2 | **Scale** | How many robots, running how many hours? | Sites, square footage, beds, volume, headcount, **operating hours / shifts per day** (a 24/7 operation is worth more than one shift with the same headcount) |
| 3 | **Labor economics** | Is this work expensive or hard to staff? | Regional wages, turnover, people job postings for this work (`robot_jobs`) |
| 4 | **Peer adoption** | Have similar companies deployed robots for this work? | Deployments at peers in the same industry |
| 5 | **Timing** | Is there budget or intent now? | RFP, funded pilot, robotics hire, capex/modernization plan, new site; lowered by evidence of workforce resistance |
| 6 | **Decision-maker access** | Can a seller reach the person who decides? | Named role, public contact, existing relationship |
| 7 | **Adoption path** | Is this workflow the logical next step, given the robots and systems they already run? | Their deployments by workflow and site, connected systems (WMS, MES), facility digitization |

Weights: equal (1/7 each).

### Adoption sequence (drives Adoption path)

What a company has already deployed predicts what it is ready for next. Starting sequence for industrial sites, to be drafted as a table and reviewed by Bob (not hard-coded from one source):

1. Inspection and cleaning robots (mapped, stable, sensor-rich facility)
2. AMRs for material transport (connected to WMS/MES)
3. Humanoid pilots: tote handling, simple assembly, component transport
4. Service robots: parts and tool delivery, technician support
5. Humanoids in production: machine tending, pick-and-place, light assembly
6. Mixed-fleet orchestration

A workflow scores high on Adoption path when the company has the earlier stages at that site; it scores at the baseline (estimated) when we don't know what they run. Other industries (hospitals, hotels, retail) get their own sequences later.

## 4. Layer 2: match score (robot × opportunity)

Answers: **can this robot win and run this job, here?** Computed when a seller searches with a robot.

| # | Factor | Question | Evidence |
|---|---|---|---|
| a | **Task capability** | Does the robot do this work, with the handling it needs (payload, dexterity, grippers)? | Robot profile facts (function, secondary functions, form), maker specs, deployments of this robot in this workflow |
| b | **Runtime vs operating hours** | Can it cover the buyer's shifts (battery runtime, charge time, swap)? | Robot specs vs the opportunity's operating hours |
| c | **Work setting** | Can it work in this environment? Open floor among people or a fenced cell; structured and predictable or variable; the safety certification that setting needs | Robot certifications and stated settings vs the facility type |
| d | **Proven reliability** | Has it run reliably in similar deployments? | Deployments of this robot (or its class) in this workflow; stated uptime from credible sources only |
| e | **Integration and service** | Can it connect to the buyer's systems (WMS, MES, elevators, doors) and be maintained in the buyer's region? | Robot integration claims, seller/partner service coverage |

Weights: equal (1/5 each). Missing robot evidence uses the class baseline, marked **estimated**.

### Buyer constraints (filter, not a score)

Some buyers can't use some robots at all. A robot that fails is left off that opportunity; the opportunity itself stays.

- **Country of origin / supplier rules**: e.g. federal buyers (SAM.gov) may be restricted from robots made by, or sourced from, certain countries or companies. The current rules must be checked and cited before this filter is built; do not guess them.
- **Compliance the buyer states**: certifications, security or data requirements named in an RFP or policy.

Each exclusion shows its reason and source to the seller ("Not eligible for this buyer: …").

## 5. Ranking

- **Browsing opportunities** (no robot chosen): rank by opportunity score.
- **FIND with a robot**: rank by the average of opportunity score and match score (equal weight). Show both, so a seller can see "strong opportunity, weak fit for your robot."

Rules for both layers:

- **Never blocking:** no variable gates an opportunity. A low score ranks low; it does not disappear. Decision-maker access in particular is scored, never required. The only exclusions are buyer constraints (section 4) and commitment (section 6).
- **Missing evidence** uses the baseline and is marked **estimated**. Missing evidence is not zero.
- **Weights start equal.** They are tuned later from outcomes (saved, contacted, meeting, won), not by hand.
- **Not a variable: robot price.** Most buyers rent; the fee depends on the robot's capabilities and the task's complexity, so price can't be measured per opportunity.
- **Source quality:** numbers used as baselines (ROI periods, uptime, unit costs) need a credible, cited source. Marketing blogs and AI summaries are not baselines.

## 6. Commitment is a status, not a score (confirmed by Bob)

A known deployment of robots for this workflow at this company/site marks that opportunity **committed** (outside the sales window). It moves to a committed list (kept, not deleted). Other workflows at the same company stay open.

A deployment is also a buyer signal:

- it raises **Adoption path** for the next workflows in the sequence at the same site;
- it raises **Peer adoption** for similar companies;
- it raises **Proven reliability** for the deployed robot.

## 7. How signals move variables

| Signal | Moves |
|---|---|
| RFP / solicitation (open) | Timing → top until the response deadline |
| Funded pilot | Timing up |
| Robotics / automation hire | Timing up (in the workflow the role points to, if stated) |
| Capex / modernization plan, new site | Timing up; Scale up |
| WMS / MES rollout, facility digitization | Adoption path up |
| New shift, extended hours, 24/7 operation | Scale up |
| Labor shortage, wage pressure, turnover | Labor economics up |
| Workforce resistance, union dispute over automation | Timing down |
| Named buyer contact | Decision-maker access up |
| Deployment at this company | Status → committed (that workflow only); Adoption path up for the next workflows at that site |
| Deployment at a peer | Peer adoption up for similar companies; Proven reliability up for that robot |
| Robot safety certification, new skill, longer runtime (maker side) | Match factors up for that robot (work setting, task capability, runtime) |

Each signal's effect is scaled by the measured precision of its source/type (the 100-sample audit). A low-precision signal moves a score a little; it can never move it much. Every effect keeps its source and date, and decays with the signal's life (RFP until deadline; others per the existing tier lives).

## 8. What a seller sees

The card stays: **company, workflow, why now, matching robots**, plus:

- opportunity score and, in FIND, match score for the seller's robot, and the rank;
- each variable and factor with its value, its evidence, and *estimated* where it came from a baseline;
- any buyer constraint that excludes a robot, with its reason;
- the signals behind it, with source links and dates.

## 9. Build order

1. Industry → workflow map, including the starting list in section 2, and the adoption sequence table (both drafts for Bob's review).
2. Generate opportunities for the 102 seed accounts.
3. Opportunity-score baselines per industry; fill company-specific evidence where we have it.
4. Map existing signals to variables (section 7), scaled by precision.
5. Score, rank, and show the top 20 opportunities to Bob before anything is public.
6. Match score: robot profile facts → factors a–e, class baselines, buyer constraints (after the origin rules are researched and cited).
7. FIND reads scored opportunities plus match score (behind a flag).

Storage: `rfr_opportunities` and `rfr_signals` exist. Any new columns or tables are a schema change: propose the migration, Bob approves, backup first.

## 10. Acceptance

- Every seed account has opportunities for each workflow its industry runs.
- Every opportunity has all seven variables, each with evidence or marked estimated.
- Every robot × opportunity match has all five factors, each with evidence or marked estimated.
- No signal creates or deletes an opportunity (test).
- Same inputs give the same scores (test).
- Diligent's Moxi returns real seed hospitals, ranked, each with both scores and their reasons.
- Bob reviews the top 20 before the flag is turned on.
