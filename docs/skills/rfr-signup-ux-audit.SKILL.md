---
name: rfr-signup-ux-audit
description: "Audit RFR signup UX; recommendations only."
version: 0.1.0
author: Ready For Robots + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Product, UX, Signup, ReadyForRobots]
    related_skills: [rfr-workflow-improve, research-cron-watch]
---

# ReadyForRobots Signup UX Audit

Weekly **read-only** audit of signup conversion paths in `readyforrobots-new`. Write ranked recommendations to `docs/ux_signup_audit.md`. **No UI code changes** in this skill.

## Operating priority (2026-08-15)

Primary conversion surface under test: **`/experiment`** (robot → jobs).  
Read `docs/EXPERIMENT_MODE.md` · `docs/TRAFFIC_SPRINT.md` · `docs/CAPABILITY_MODEL.md`.

Prioritize continuity: land → submit → capabilities → jobs → **See All** → signup (`src=robot_jobs`, preserve `persona` / `src`).  
Do **not** recommend Cal/SIGNAL/CRM/distributor-UI expansions while the traffic sprint is the decision source. Next product decision comes from **behavior** (See All CTR by persona), not new hypotheses.

## When to Use

- Monday cron / "audit signup UX"
- User asks how to drive more signups without implementing yet

## Files to review (read-only)

**First (experiment funnel):**
- `readyforrobots-new/client/src/pages/ExperimentIdeas.tsx`
- `readyforrobots-new/client/src/components/RobotJobsExperiment.tsx`
- `readyforrobots-new/client/src/lib/robotJobsEnvelopeMap.ts`
- `readyforrobots-new/client/src/lib/siteAnalytics.ts` (`trackRobotJobsFunnel` / `rdd_*`)

**Also:**
- `readyforrobots-new/client/src/pages/Signup.tsx`
- `readyforrobots-new/client/src/pages/Login.tsx`
- `readyforrobots-new/client/src/lib/signupHref.ts`
- `readyforrobots-new/client/src/lib/authNext.ts`
- `readyforrobots-new/client/src/pages/Pipeline.tsx` (signup gates, save resume)
- `readyforrobots-new/client/src/components/pipeline/FirstSaveNudge.tsx`
- `readyforrobots-new/client/src/components/pipeline/CalLeadDrop.tsx`
- `readyforrobots-new/client/src/components/PipelinePreview.tsx`
- `readyforrobots-new/client/src/components/results/ResultsFomoBanner.tsx`
- Home / SIGNAL CTA paths that deep-link to signup

## Rubric

Score each finding: **impact** (H/M/L) × **effort** (H/M/L). Prefer continuity of value (`next=`, `persona=`, `src=`, resume save), friction (fields, OAuth clarity), trust (copy, proof before wall), mobile, and post-signup activation (first save).

Segment recommendations by whether they help **OEM / distributor / integrator** outreach (`persona` query param) — do not invent three UIs.

## Procedure — Tick

### 1. Read current funnel code

Skim the files above; note broken continuity, premature walls, weak CTAs, dead ends after signup.

### 2. Rank recommendations

Top 10 max. Each: finding → why it hurts signups → proposed change → impact/effort → primary file path.

### 3. Write report

Overwrite or prepend dated section in Ready_For_Robots `docs/ux_signup_audit.md`:

```markdown
# Signup UX Audit

## YYYY-MM-DD

### Summary
...

### Ranked recommendations
1. **[H/L]** ... — `path/to/file.tsx`
```

**Do not edit** `.tsx` / CSS / routes in this skill.

### 4. Digest

Top 5 recommendations in chat. If no material change since last audit: `[SILENT]` (still refresh date note optionally).

## Pitfalls

- Implementing UI "while you're here."
- Generic advice unrelated to RFR's value-first pipeline signup.
- Ignoring existing `signupHref` / resume-save patterns.

## Verification

- [ ] `docs/ux_signup_audit.md` updated.
- [ ] No frontend files modified.
- [ ] Each rec cites a file path.
