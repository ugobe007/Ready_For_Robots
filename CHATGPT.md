# ReadyForRobots — Product / Architecture Contract

Purpose: Shared operating context between Bob, ChatGPT, and
implementation agents working in Cursor.

Role of this file: Read this before making material ReadyForRobots
product, architecture, workflow, matching, or UX changes. This is a
coordination contract, not a replacement for the canonical documents
under docs/.

## 1. Product promise

ReadyForRobots finds jobs for robots.

A user gives ReadyForRobots a robot URL. ReadyForRobots understands the
robot accurately enough to find credible work it can do, explains why
each job matches and what remains unknown, and lets the user qualify
jobs worth pursuing.

```
ROBOT URL
  → UNDERSTAND
  → REVIEW ROBOT PROFILE
  → FIND WORK
  → EXPLAIN THE MATCH
  → QUALIFY
  → PURSUIT
```

Company thesis:

Robots need jobs.

Category:

Find Jobs for Robots.

Product primitive:

CAPABILITIES → FIND WORK

Commercial stack:

FIND → QUALIFY → PLACE later

## 2. Current product workflow

The homepage / is the ReadyForRobots work terminal.

The intended interaction is:

```
FIND
  → RESEARCH
  → SELECT robot(s), when needed
  → REVIEW PROFILE
  → FIND JOBS
  → REVIEW MATCHES
  → QUALIFY
```

Workspace model

Narrow rail = robot/context/navigation.

Large panel = workspace.

Before submission, the large panel may show the public live Robot Job
board.

After submission, the large panel becomes the user's workspace. Do not
push important research, evidence, product selection, or match reasoning
into a cramped side panel.

Multi-product / portfolio behavior

A company URL may represent more than one robot.

The user may select:

one robot;

several robots; or

all robots.

Do not assume every URL maps to one product.

Portfolio mode is part of the same engine, not a separate product.

## 3. Trust sequence

The Robot Profile is a real checkpoint.

Do not show a personalized job count before matching has actually run.

The sequence is:

```
research robot
  → show what we understood
  → confirmed facts / unknowns / sources
  → user requests jobs
  → run matching
  → show matched work
```

Primary profile presentation should emphasize:

product identity;

profile tier;

confirmed facts;

still unknown;

evidence/sources.

Internal calibration details such as grounding %, coverage %, and
source-quality % should not dominate the customer-facing profile. They
may live behind Profile details.

For Tier B/C profiles, be explicit that the profile is credible but
incomplete.

## 4. Robot Job match contract

Matching is not:

robot type → category/family → generic jobs

Matching is:

```
GROUNDED ROBOT FACTS
  → DERIVED CAPABILITIES
  → WORKFLOW
  → ROBOT JOB REQUIREMENTS
  → MATCHED / UNMET / UNKNOWN / LIKELY
```

Unknowns remain unknown. Never silently promote missing evidence into a
match.

A positive match must explain why.

A rejection must identify a real unmet requirement when possible.

Customer-facing match shape

```
JOB 01 · POSSIBLE MATCH

<physical work>
<company / worksite>

WHY <ROBOT>
✓ matched requirement
✓ matched requirement

STILL UNKNOWN
? unresolved constraint
? unresolved constraint

NO CONFIRMED BLOCKER
(or explicit blocker)

QUALIFY THIS JOB →
```

No opaque percentage is required.

Ranking may prefer jobs that exercise more of the robot's distinctive
grounded capabilities, after requirement truth has been established.

Do not manufacture differentiation. If portfolio results cannot honestly
support differentiated counts, omit the counts.

## 5. Product objects

Use these concepts consistently:

Robot Profile

What ReadyForRobots currently knows about a specific robot, with
grounded facts, unknowns, contradictions, and evidence.

Robot Job

A bounded piece of physical work potentially compatible with robotic
capabilities.

Match

The relationship between a Robot Profile and Robot Job requirements.

Pursuit Brief

The output of QUALIFY: enough commercial information to decide whether a
seller should spend sales resources pursuing the job.

Placement

Later-stage attributed introduction/deployment opportunity. Not V1's
primary promise.

## 6. One engine, three capability envelopes

ReadyForRobots is not three products.

Level 1 --- Robot

Find jobs for your robot.

Level 2 --- Portfolio

Find jobs for the robots you sell.

Level 3 --- Solution provider

Find automation jobs your company can solve.

All three use the same primitive:

CAPABILITIES → FIND WORK

Do not create separate product architectures unless explicitly approved.

## 7. Understanding v1.0 --- frozen

Robot Understanding Phases 1--3 are frozen at v1.0 calibration.

The pipeline is:

```
IDENTITY
  → TYPED SOURCES
  → ATOMIC FACTS
  → DERIVED CAPABILITIES
```

Understanding is credible but incomplete.

Do not reopen extractors, source discovery, resolve logic, Blind 20
tuning, or ontology merely because one robot profile looks imperfect.

Production shadow review is the decision instrument for reopening
Understanding.

A future Understanding change must cite a repeated, generalized
production failure that justifies a narrow reopen.

Individual WRONG/INCOMPLETE profiles are observations, not automatic
permission to retune.

Canonical freeze documents under docs/calibration/ govern details.

## 8. Shadow mode

Understanding shadow is observe-only.

It may:

log real submitted profiles;

record GOOD / INCOMPLETE / WRONG / UNVERIFIABLE reviews;

aggregate repeated failure themes.

It must not:

silently repair profiles;

modify matching;

retune Understanding automatically;

become an open-ended research project.

The first 20 reviewed real profiles form the finite M1 Understanding
checkpoint.

Shadow does not block matcher/product work.

## 9. Finite V1 milestones

M1 --- Understand

Robot profiles are professionally usable, with honest uncertainty.

M2 --- Match

Capability → requirement matching produces defensible, differentiated
work with explanations.

M3 --- Product

URL → profile → jobs → See All works end-to-end.

M4 --- Commercial

Qualify This Job produces a Pursuit Brief customers request.

After M4:

Stop building and sell/test.

Channel routing and PLACE come later, after FIND + QUALIFY demonstrate
demand.

## 10. Current release discipline

Do not equate:

logic works locally

with:

production gate passed.

Every meaningful release should distinguish:

logic/unit PASS;

production deploy;

production verification;

customer-facing gate PASS.

Traffic and discovery-content publishing should remain paused whenever
the canonical pre-traffic document says the product is not ready.

Use docs/V1_PRETRAFFIC_TEST.md as the release authority.

## 11. Submit workflow contract

Submitting a URL should feel like one transaction.

```
IDLE
  → RESEARCHING
  → PRODUCT_SELECTION (optional)
  → REVIEW_PROFILE
  → MATCHING
  → RESULTS
```

During research:

keep geometry stable;

do not flash personalized jobs;

do not show partial/reordered result boards;

use completed stages rather than fake percentage progress.

Cached profiles may skip a visible research beat when sufficiently fast.

The system may research progressively internally, but the UI should
reveal customer-facing states deliberately.

## 12. Design language

Do not design a generic retro website.

Design:

the operating system for robot employment.

Internal design sentence:

ReadyForRobots is a job terminal that somehow existed before robots
were ready for it.

Early-computing / Susan-Kare-inspired language should provide:

simplicity;

recognizable symbols;

operational clarity;

restrained personality;

a slightly human quality.

Avoid decorative retro effects such as:

CRT scanlines;

fake screen curvature;

glitch effects;

chromatic aberration;

excessive blinking;

neon/cyberpunk gradients;

decorative terminal noise.

The interface should feel like a serious employment system for machines,
not a retro-computing costume.

Visual vocabulary

Prefer authored product symbols for:

Robot

Job

Search

Worksite

Employer

Match

Unknown

Evidence

New

Qualified

Route

Pursuit

Task-family symbols (transport, manipulation, cleaning, inspection,
palletizing, etc.) are a secondary icon family.

Do not destabilize product workflow merely to add visual character.

## 13. Product language

Preferred vocabulary:

ROBOT PROFILE

JOBS / JOBS FOUND

JOB <number>

WORKSITE

EMPLOYER

ROUTE

POSSIBLE MATCH

WHY <ROBOT>

STILL UNKNOWN

EVIDENCE

QUALIFY THIS JOB

QUALIFIED

READY FOR PURSUIT

Avoid generic CRM/sales language when the Robot Job vocabulary is more
accurate.

Avoid implying PLACE, APPLY, or introduction until those workflows
actually exist.

## 14. Acquisition principle

ReadyForRobots should not rely primarily on self-promotion.

Acquisition is discovery-led.

Content should make people ask:

Could my robot do this job?

Editorial territory:

Robot Work

Good content starts with discovered physical work, not ReadyForRobots
marketing.

Examples:

Today's Job for a Robot

We Went Looking for Work for...

Human Work → Robot Work

Content success is measured by:

```
content source
  → visit
  → robot submitted
  → jobs reviewed
  → See All
  → Qualify
```

not likes alone.

## 15. What is currently out of scope

Unless explicitly reopened by Bob:

new Understanding heuristics;

Blind-eval score chasing;

ontology churn;

channel expansion;

distributor directory building;

Channel Match scoring;

PLACE workflow;

new product surfaces for distributors/integrators;

generic CRM/SIGNAL resurrection;

broad visual redesign;

speculative product expansion.

Protect the current product spine.

## 16. Decision hierarchy

When implementation choices conflict, use this order:

1. Truth --- is the claim supported?

2. Product promise --- does this help find credible jobs for the
   robot?

3. User comprehension --- can a robotics professional understand
   why?

4. Workflow integrity --- is the state stable and coherent?

5. Measurement --- can we observe what happened?

6. Aesthetics --- does it express ReadyForRobots clearly?

Never sacrifice 1--4 merely to improve appearance or apparent
conversion.

## 17. Cursor / implementation-agent role

Cursor agents are implementation engineers.

They should:

read this file before material ReadyForRobots work;

read the canonical document relevant to the mission;

preserve frozen boundaries;

implement the smallest change that satisfies the mission;

test locally;

distinguish local PASS from production PASS;

report uncertainty and defects rather than hiding them;

avoid opportunistic architecture/product expansion.

They should not reinterpret product strategy because an implementation
would be easier another way.

If strategy appears contradictory, stop and surface the
contradiction rather than choosing silently.

## 18. Canonical documents

Before material work, consult the relevant files:

docs/readyforrobots_v1_milestones.md

docs/CAPABILITY_MODEL.md

docs/V1_PRETRAFFIC_TEST.md

docs/robot_understanding_v1.md

docs/calibration/understanding_blind_20/V1_0_FREEZE.md

docs/calibration/understanding_shadow_v1.md

docs/DISCOVERY_CONTENT.md

docs/CONTENT_SPRINT.md

docs/TRAFFIC_SPRINT.md

If this file conflicts with a newer explicit decision from Bob, Bob's
decision wins and the canonical docs should be updated.

## 19. Agent handoff protocol

After a meaningful mission, update:

docs/agent_handoff.md

Keep it short.

Required structure:

```
# Agent Handoff

MISSION
<what was requested>

STATUS
PASS | FAIL | BLOCKED | PARTIAL

CHANGED
- material files / behavior changed

VERIFIED
- tests
- browser/API checks
- production checks, if any

PRODUCTION
- deployed commit/release
- or NOT DEPLOYED

OPEN DEFECTS
- real remaining issues only

DECISION NEEDED
- only decisions requiring Bob / product review

DO NOT TOUCH
- frozen layers relevant to the next agent
```

Do not paste a full development diary. The handoff exists so another
agent can understand the state in under two minutes.

## 20. Operating principle

Make the product true, then make it clear, then measure whether
people want it.

Do not confuse more code with progress.

Do not confuse a green test with product truth.

Do not confuse infrastructure with the product.

ReadyForRobots V1 ends when a robotics company can submit its robot,
understand what ReadyForRobots believes about it, see credible work
matched for defensible reasons, and ask ReadyForRobots to qualify work
worth pursuing.
