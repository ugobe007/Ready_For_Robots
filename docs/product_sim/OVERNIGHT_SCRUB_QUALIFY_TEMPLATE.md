# Overnight Floor Scrub — QUALIFY Template (v0)

**Status:** Locked after three desk experiments (ATL Unifi, Mall of America, Harris Health LBJ).  
**Not yet productized in `/jobs` UI.**  
**CTA meaning:** *ReadyForRobots will investigate the commercial unknowns and tell you whether this job deserves your sales team’s time.* Does **not** promise an introduction.

## Product stack

| Stage | Verb | Output |
|-------|------|--------|
| FIND | Find jobs for your robot | Discovered Robot Job |
| QUALIFY | Qualify This Job | Pursuit Brief → recommendation |
| PLACE | later | Attributed opportunity / intro |

Progression: **DISCOVERED → DESK QUALIFIED → CONTACT QUALIFIED → READY FOR PURSUIT**

## What QUALIFY answers (commercial, not engineering)

1. Does the work still exist?
2. Is there enough of it?
3. Is autonomous hard-floor scrubbing technically plausible?
4. Is this specific work already automated?
5. Who owns the decision?
6. Is there a commercial timing reason to act?

Stop there. Route geometry, docking, network, infection SOPs detail → OEM / channel.

## Pursuit Brief (customer-facing)

```
Overnight Floor Scrub — Qualification

WORK                 Confirmed ✓ | Unconfirmed | Unable to verify
SCALE                Confirmed | Likely sufficient | Unknown
ROBOT FIT            Plausible ✓ | Marginal | Poor
AUTOMATION STATE     Manual | Partial | Incumbent | Unknown
BUYER / DECISION     Identified | Probable | Unresolved
TIMING               Strong | Moderate | Weak | Unknown
COMMERCIAL PATH      Clear | Partially known | Unclear

Recommendation: PURSUE | QUALIFY FURTHER | WATCH | DO NOT PURSUE
Reason: <one sentence>
```

Keep schema % / Desk Qualification Yield **internal**.

## Desk tier (30–90 minutes)

Public sources only:

- Live / recent role posting (machines, shift, employer)
- Who employs operators (in-house vs contractor)
- Facility owner / program owner
- Scale proxies (sq ft, visits, beds, historical contract scope)
- Labor rate if posted
- Public automation / robot claims (flag soft PR)
- Timing proxies (hiring pressure, RFPs, capital projects, renewals)

**Expected ceiling:** ~55–65% of commercial fields resolved.  
**Expected recommendation:** usually `QUALIFY FURTHER` unless buyer + automation + scale are unusually clear.

## Contact tier (canonical four questions)

Ask the appropriate operator (housekeeping / EVS / station ops / facilities):

1. Are these floor-scrubbing routes still being performed manually?
2. Roughly how many operator-hours / how much floor area does the work cover?
3. Are autonomous scrubbers already being used on these routes?
4. Who evaluates changes to the floor-care equipment/process?  
   *(Optional #5 when relevant:)* Is there a near-term contract, capital, or new-facility reason to act?

This is a **bounded** qualification operation — not a consulting engagement.

## Minimum for `PURSUE` (READY FOR PURSUIT)

- Work confirmed
- Scale sufficient (confirmed or strongly evidenced)
- Robot fit plausible
- Decision owner identified (or high-confidence probable + named role)
- No known incumbent blocking *these routes*
- Timing at least moderate

Else stay at `QUALIFY FURTHER`, `WATCH`, or `DO NOT PURSUE`.

## Attribution seed (for future PLACE)

**RFR-Sourced Opportunity** = Company + Worksite + Work first delivered by RFR before the customer has documented active pursuit of that same triple.

Example: `Mall of America · Bloomington · overnight common-area hard-floor scrub`  
Not: “malls” or “MOA” alone.

## Three-case evidence (desk)

| | ATL Unifi | MOA | Harris LBJ |
|--|-----------|-----|------------|
| Ownership shape | Authority / AATC / contractor | In-house property housekeeping | Public system in-house EVS |
| FIND → Desk resolution | 18% → 55% | 20% → 62% | 18% → 58% |
| Research time | ~55m | ~42m | ~50m |
| Contact Qs | 4 | 3 | 4 |
| Eng before pursue | No | No | No |
| Desk rec | QUALIFY FURTHER | QUALIFY FURTHER | QUALIFY FURTHER |

**Desk Qualification Yield:** ~+37 to +42 percentage points of commercial uncertainty removed before contact.

## Who pays (concept only — do not price yet)

Robot seller (OEM / distributor / integrator): FIND access + QUALIFY (credits / per-job / premium). Employer does not pay at this stage.

## `/jobs` copy implication

- Brand: *Robots need jobs. We find the work.*
- Product: *Find jobs for your robot.*
- Next verb: **Qualify This Job** → Request Qualification (desk Pursuit Brief)
- Contact tier: “Additional verification may be required” — not automated
- Do not use Apply / Place until introduction workflow exists

Shipped on `/jobs` (desk QUALIFY CTA). Contact experiment (MOA) is optional and does not block the page.
