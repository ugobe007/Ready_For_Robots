---
name: rfr-workflow-improve
description: "Propose RFR Hermes loop workflow improvements."
version: 0.1.0
author: Ready For Robots + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Robotics, Meta, ReadyForRobots, Improvement]
    related_skills: [rfr-deployment-evidence, rfr-job-orders, research-cron-watch]
---

# ReadyForRobots Workflow Improve

**RETIRED 2026-08-26.** Hermes is not a Jobs agent. Do not cron this. FIND is `/`. See [`hermes_retired.md`](../hermes_retired.md).

Historical weekly meta-pass: inspect retired Hermes cron outputs + RFR market-graph status. **Do not auto-edit production code** unless the user explicitly asks in-session.

## Operating priority (2026-08-15)

Product lock: `CAPABILITIES → FIND WORK` · traffic on `/experiment` · See All CTR by persona.  
**Traffic vs product:** Propose discovery-content drafts (from scored ledgers), outreach/instrumentation/reporting fixes. Do **not** propose product/channel/scoring changes because early CTR is soft. Do **not** draft generic robotics-trends posts. Low traffic → better discoveries + cohorts, not rewrite the experiment.

**Do not propose:** OEM scrape 11–50, more distributors, Channel Match scoring, distributor/integrator UI, RDD Fly migrate, ontology/capability-layer expansion. Those are frozen until traffic evidence. Prefer proposals that improve **instrumentation, reliability of existing crons, or reading `/experiment` funnel events**.

## When to Use

- Sunday cron / "improve the Hermes↔RFR loop"
- After a failed cron streak
- User asks what to fix next in the intelligence system

## Inputs to read

1. `~/.hermes/cron/output/` recent runs for `rfr-*` jobs
2. `GET {RFR_API_BASE}/api/v1/market-graph/status` (public)
3. Optional: `GET .../deployment-evidence`, `.../vendor-news`, `.../work-units`
4. Bridge doc: `docs/hermes_intelligence_bridge.md`
5. Strategy lock: `docs/CAPABILITY_MODEL.md` · `docs/EXPERIMENT_MODE.md` · `docs/TRAFFIC_SPRINT.md`

## Procedure — Tick

### 1. Diagnose

Note failures (auth, truncated output, empty coverage, drift skips), coverage gaps (e.g. OTTO silent), ingest quality issues (UNKNOWN stages, missing metrics).

### 2. Propose ranked fixes

Each item: problem → proposed change (skill prompt, watch seed, API, cron) → impact → effort → owner hint (`hermes` | `rfr-api` | `frontend`).

### 3. Append log

Prepend a dated section to `docs/agent_improvement_log.md` in the Ready_For_Robots workdir:

```markdown
## YYYY-MM-DD — Hermes workflow review

### Findings
- ...

### Ranked proposals
1. **[impact/effort]** ...
```

Create the file if missing. Do not commit unless asked.

### 4. Digest

Short digest of top 3 proposals. If nothing actionable: `[SILENT]`.

## Pitfalls

- Vague advice ("be better") without a file/endpoint/skill change.
- Secret leakage from cron logs into the markdown file.
- Implementing large refactors unsolicited.

## Verification

- [ ] Log file updated with dated section.
- [ ] Proposals reference concrete paths or endpoints.
