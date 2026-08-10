# V1 Information Architecture And Wireframes

## Experience Rule

The user should always know:

1. which robot is being evaluated;
2. which physical facility and work are under consideration;
3. what is known, inferred, unknown, or incompatible;
4. why this opportunity deserves its priority;
5. the one next action that reduces the most decision uncertainty.

V1 is an intelligence product, not a CRM. The shell contains Robot, Radar, Opportunities, and Notifications. It does not contain Inbox, Calendar, Sequences, Proposals, Social, Marketplace, or generic dashboards.

## Route Map

```mermaid
flowchart LR
    Home[/ Robot Input] --> Review[/robots/:id/review Robot Analysis]
    Review --> Radar[/robots/:id/opportunities Opportunity Radar]
    Radar --> Detail[/opportunities/:id Opportunity Detail]
    Detail --> Qualify[/opportunities/:id/qualify Qualification]
    Detail --> Outcome[/opportunities/:id/outcome Outcome]
    Qualify --> Detail
    Outcome --> Queue[/opportunities My Opportunities]
    Queue --> Detail
```

The browser URL must carry stable robot/opportunity IDs. Analysis tokens may be in session storage or an HttpOnly cookie, never in query parameters.

## Global Shell

Desktop:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ ReadyForRobots   Robot: Atlas AF-1500        Radar  Opportunities  Alerts │
└────────────────────────────────────────────────────────────────────────────┘
```

Mobile uses a compact header with robot selector and bottom navigation for Radar, Opportunities, and Alerts. Primary actions remain sticky at the viewport bottom. No content may be hidden only behind hover.

## Screen 01: Robot Input

**Route:** `/`

**Goal:** Start analysis with one clear action and demonstrate value before registration.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ ReadyForRobots                                                             │
│                                                                            │
│                    Find Companies That Need Your Robots.                   │
│                                                                            │
│  Robot URL                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ https://robotcompany.com/product                                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  [ Find opportunities → ]                                                 │
│                                                                            │
│  Or describe your robot                                                   │
│  [ Payload, movement, environment, and intended work...               ]   │
│                                                                            │
│  Recent supported examples: autonomous forklift · tugger · AMR            │
└────────────────────────────────────────────────────────────────────────────┘
```

Requirements:

- The robot/product is the first viewport signal.
- URL input is primary; description is a disclosure, not a competing card.
- Submit immediately creates an analysis job and routes to review/progress.
- Do not show signup, pricing, CRM, or outreach CTAs before profile value.
- Validate URL inline; preserve entered text on error.

States:

- default;
- invalid URL;
- rate limited with retry time;
- unsupported category with explanation;
- returning analysis with Resume action.

Reuse: URL normalization and current Home submission mechanics. Replace generic company scan language with robot-product analysis.

## Screen 02: Robot Analysis

**Route:** `/robots/:robotId/review`

**Goal:** Establish a trustworthy Robot Capability Profile before searching for work.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ ← Robot input                     Robot Capability Profile   Draft          │
├────────────────────────────────────────────────────────────────────────────┤
│ [Product image]  Autonomous Forklift X                                     │
│                  Autonomous Forklift · Acme Robotics                       │
│                  Source: acmerobotics.com/product/x                        │
├───────────────────────────────┬────────────────────────────────────────────┤
│ Work Envelope                 │ Physical Capability                         │
│ ✓ Pallet acquisition          │ Payload        1,500 kg   Observed [source] │
│ ✓ Pallet transport            │ Lift height    4.5 m      Observed [source] │
│ ✓ Floor placement             │ Runtime        10 h       Inferred [why]    │
│ ✓ Rack placement              │ Trailer entry  Unknown    [Add value]       │
│ ✓ Production replenishment    │ Outdoor        No         Observed [source] │
├───────────────────────────────┴────────────────────────────────────────────┤
│ Critical unknowns: trailer entry · minimum aisle width                    │
│ [ Correct profile ]                         [ Find its jobs → ]             │
└────────────────────────────────────────────────────────────────────────────┘
```

Interaction:

- Inline edit opens a typed control with source and correction note.
- A correction creates OEM-verified evidence and a new profile version.
- Unknown is a valid value and is visually distinct from No.
- Finding jobs requires confirmation of category and at least one Work Envelope capability, not complete specs.

Loading phases use real stage labels: Crawling product page, Extracting capabilities, Checking sources, Preparing profile. Never show fake precision.

Mobile stacks profile sections and keeps `Find its jobs` sticky.

## Screen 03: Opportunity Radar

**Route:** `/robots/:robotId/opportunities`

**Goal:** Rank facility-level decisions by seller effort.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Atlas AF-1500 · Opportunity Radar                       Updated 8 min ago  │
│ 126 facilities match   12 CALL NOW  18 QUALIFY  43 WATCH  9 WRONG ROBOT   │
├────────────────────────────────────────────────────────────────────────────┤
│ Priority [All▾] Location [All▾] Work [All▾] Thesis [All▾] Evidence [All▾] │
├────────────────────────────────────────────────────────────────────────────┤
│ 🔥🔥🔥 CALL NOW                                                            │
│ ABC Foods · Memphis Manufacturing Facility · Memphis, TN                   │
│ Finished Goods → Warehouse / Trailer                                      │
│ Work Match: EXCELLENT        Evidence: STRONG                              │
│ Why now: third-shift forklift hiring · repeated opening · shift premium   │
│ Thesis: REPLACE + PROTECT                            [View opportunity →]   │
├────────────────────────────────────────────────────────────────────────────┤
│ 🔥🔥 QUALIFY ...                                                           │
└────────────────────────────────────────────────────────────────────────────┘
```

Rules:

- Default view surfaces CALL NOW then QUALIFY. WATCH and WRONG ROBOT remain one filter away.
- Cards show facility, not only company.
- No customer-facing composite score.
- Hard blocker cards cannot display CALL NOW.
- Evidence and priority are independent.
- Counts and cards update while the search runs; partial results are labeled.

States:

- staged progress with counts;
- partial results with warnings;
- no credible matches, showing why and profile corrections;
- filters with zero results;
- source freshness warning.

Reuse: card-density and filtering patterns from Pipeline. Do not reuse automated outreach controls or CRM kanban.

## Screen 04: Opportunity Detail

**Route:** `/opportunities/:opportunityId`

**Goal:** Let a seller decide whether to spend time and understand exactly what remains unknown.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ ABC Foods · Memphis Manufacturing Facility                    RFR-OPP-... │
│ 🔥🔥🔥 CALL NOW     PRIORITIZED · ACTIVE                                  │
│ Finished Goods → Warehouse / Trailer                                      │
├──────────────────────────────────────┬─────────────────────────────────────┤
│ Why this opportunity exists          │ Next decision                       │
│ Evidence-specific two sentence case. │ Ask pallet moves per shift          │
│                                      │ High information value              │
│ Work Graph                           │ [ Qualify opportunity → ]            │
│ Production → Pallet → Forklift       │ [ Mark contacted ] [ Reject ▾ ]     │
│                  ↙ Storage ↘ Ship    │                                     │
├──────────────────────────────────────┴─────────────────────────────────────┤
│ Work Match EXCELLENT  Labor HIGH  Exposure HIGH  Buyability MEDIUM        │
│ Deployability UNKNOWN Evidence STRONG Resolvability HIGH                  │
├───────────────────────┬───────────────────────┬────────────────────────────┤
│ What we know ✓        │ What we infer ~       │ What we don't know ?       │
│ Third shift [source]  │ Repetitive flow [why] │ Pallet moves / shift       │
│ Finished pallets [...]│ Throughput exposure   │ Payload · rack height      │
├───────────────────────┴───────────────────────┴────────────────────────────┤
│ Qualification: 62% understood   [████████████░░░░░░░░]                   │
│ 1. Pallet moves / shift — high decision impact                           │
│ 2. Maximum pallet weight — potential hard blocker                        │
│ 3. Operators / shift — economic impact                                   │
├────────────────────────────────────────────────────────────────────────────┤
│ Timeline: prediction frozen · seller actions · answers · outcomes          │
└────────────────────────────────────────────────────────────────────────────┘
```

Requirements:

- Every Known item links to its source excerpt.
- Inferences open a reason drawer showing inputs and model/rules version.
- Unknowns show impact and route to the relevant question.
- Blockers appear above scores and state exactly which requirement conflicts.
- Primary CTA is dynamic: Qualify, Request Site Review, Record Pilot, or Report Outcome.
- `Mark contacted` records action only; it does not send email.
- Reject requires a controlled reason and always includes `RFR prediction wrong`.

Mobile order: priority and next decision, Why, blockers, Work Graph, dimensions, evidence groups, qualification, timeline.

## Screen 05: Qualification

**Route:** `/opportunities/:opportunityId/qualify`

**Goal:** Resolve the minimum high-impact unknowns without a giant form.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ ABC Foods · Qualification                           62% understood         │
│ Question 1 of 5 · High decision impact                                     │
├────────────────────────────────────────────────────────────────────────────┤
│ How many pallet moves occur per shift?                                     │
│ ┌──────────────────────────────┐ [moves / shift ▾]                         │
│ │ 180                          │                                           │
│ └──────────────────────────────┘                                           │
│ Source: [Customer confirmed ▾]  Date: [Today]                              │
│ Why this matters: validates throughput and labor-share assumptions.        │
│ [ Unknown ]                                      [ Save answer → ]          │
├────────────────────────────────────────────────────────────────────────────┤
│ Effect preview                                                             │
│ Work Match       Excellent → Excellent                                     │
│ Confidence       64% → estimated 73%                                       │
│ Qualification    62% → estimated 69%                                       │
└────────────────────────────────────────────────────────────────────────────┘
```

After save:

```text
Answer recorded as CUSTOMER CONFIRMED
Work Match: Excellent · Confidence: 73% · Qualification: 69%
Next question: Maximum loaded pallet weight
```

Rules:

- Show one question at a time and no more than five in a session.
- Support numeric/unit, enum, boolean, short text, range, and Unknown.
- Source/truth state is required for non-unknown answers.
- Hard-blocker answers trigger an immediate decision banner and require seller confirmation before marking WRONG ROBOT/LOST.
- Before/after compares current recalculation to T0 without changing T0.
- Completing critical facts reveals `Request site review`; it does not silently advance.

## Screen 06: My Opportunities

**Route:** `/opportunities`

**Goal:** Provide a minimal working decision queue, not CRM administration.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ My Opportunities       Robot [Atlas AF-1500▾]  State [Active▾]            │
├──────────────────┬────────────────┬─────────┬───────────┬────────┬──────────┤
│ Opportunity      │ Work           │ Priority│ State     │ Qual.  │ Next     │
├──────────────────┼────────────────┼─────────┼───────────┼────────┼──────────┤
│ ABC Foods        │ Pallet move    │ 🔥🔥🔥  │ Contacted │ 48%    │ Moves    │
│ Memphis facility │                │         │           │        │ / shift  │
│ XYZ Manufacturing│ Line supply    │ 🔥🔥    │ Engaged   │ 71%    │ Payload  │
│ DEF Logistics    │ Trailer unload │ Watch   │ Matched   │ 35%    │ Monitor  │
└──────────────────┴────────────────┴─────────┴───────────┴────────┴──────────┘
```

Rules:

- Clicking a row opens Opportunity Detail.
- No drag-and-drop stages.
- Priority, state, and disposition are separate columns/filters.
- The next-action cell is the strongest visual command.
- Mobile uses a dense list with fixed rows, not horizontally clipped tables.

## Screen 07: Outcome

**Route:** `/opportunities/:opportunityId/outcome`

**Goal:** Capture decisive learning in under thirty seconds.

First choice:

```text
What happened?
[ Did not pursue ] [ Pursued, no engagement ] [ Lost ] [ Pilot ] [ Deployed ]
```

Lost path:

```text
Why didn't this become a deployment?
Work          [Wrong workflow] [Low volume] [Too variable]
Robot         [Payload] [Reach] [Speed] [Navigation] [Manipulation]
Economics     [ROI] [Integration cost] [No budget]
Customer      [No interest] [No champion] [Procurement] [IT security]
Timing        [Too early] [Delayed] [Already awarded]
Competition   [Incumbent] [Competitor] [Already automated]
Data          [ReadyForRobots prediction was wrong]
[ Optional note ]                                      [ Save outcome ]
```

Deployment path:

```text
Deployment confirmed
Robots deployed [ 2 ]   Scope [ Pilot / Production ]
Workflow [ Finished pallet transport ▾ ]
Optional details ▸ volume · uptime · labor · throughput · intervention · cost
[ Save outcome ]
```

Rules:

- The controlled reason is required for loss.
- Prediction-wrong is a first-class option.
- Optional metrics never block common-path completion.
- Success confirmation states what was learned, not celebratory CRM copy.

## Notification Surfaces

Notifications are a compact list and optional email, never a dashboard:

- New CALL NOW Opportunity
- Opportunity Heating Up
- New Evidence
- Work Match Changed

Each notification deep-links to the affected evidence or decision. Repeated labor signals at one facility collapse into one update with a time-series summary.

## Component Inventory

| Component | Used on |
| --- | --- |
| `RobotUrlInput` | Robot Input |
| `AnalysisProgress` | Robot Analysis, Radar |
| `ProvenancedField` | Robot Analysis, Detail, Qualification |
| `TruthStateBadge` | all evidence surfaces |
| `RobotWorkEnvelope` | Robot Analysis |
| `PrioritySummary` | Radar |
| `OpportunityCard` | Radar |
| `FacilityIdentity` | Radar, Detail, Queue |
| `WorkGraphSimple` | Detail |
| `DimensionStrip` | Detail, Qualification result |
| `EvidenceTriad` | Detail |
| `QualificationGap` | Detail, Qualification |
| `DynamicQuestion` | Qualification |
| `TransitionCommandBar` | Detail |
| `OutcomeReasonPicker` | Outcome |
| `OpportunityQueue` | My Opportunities |

## Accessibility And Responsive Acceptance

- All status meaning has text in addition to color/flame icons.
- Evidence links and controls are keyboard reachable with visible focus.
- Graph meaning has a text alternative listing nodes and edges.
- Tables become labeled lists below 768 px.
- Sticky action bars do not cover content or browser controls.
- Long company, facility, and workflow names wrap without changing control dimensions.
- Loading states announce progress through an ARIA live region.
- Error states preserve entered data and provide one recovery action.

## Legacy Surface Disposition

| Current route/capability | Decision |
| --- | --- |
| Home URL submit | Reuse mechanics; change semantic target from company scan to robot analysis |
| `/results` | Replace with Robot Analysis and Radar routes |
| `/pipeline` | Reuse dense card/filter patterns only; replace as V1 queue over time |
| `/crm` | Remains outside V1 navigation |
| Save/Copy/Send | Remove from V1 primary loop; intelligence actions are Pursue, Qualify, and Report Outcome |
| Automated outreach and sequences | Not called by V1 endpoints or shown in V1 UI |
| HubSpot | Optional export/sync after intelligence validation; not required for V1 journey |
| Proposal generator | Outside V1 |
