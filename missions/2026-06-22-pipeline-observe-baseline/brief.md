# Mission: Pipeline observe baseline

**Date:** 2026-06-22
**Agent:** PipelineHealth
**Status:** planned

## Goal

Establish a metrics baseline for the public pipeline and homepage feeds without changing production code.

## Acceptance criteria

- [ ] `scripts/harness_snapshot.py` runs successfully
- [ ] `reports/harness_snapshot_latest.json` documents pipeline `built_at`, lead counts, and alerts
- [ ] Brief assessment: is cache fresh? is anonymous feed healthy?
- [ ] Recommend **one** follow-up mission (LeadQuality, ProductSurface, or Deploy) with rationale tied to north star priority

## Context

First mission for the Claude Agent SDK harness (Phase 0 → 1). User chose Python SDK runtime. No deploy or commits in this mission.

## Out of scope

- Code changes
- git commit / push
- fly deploy
- Hero ticker swap (separate ProductSurface mission)
