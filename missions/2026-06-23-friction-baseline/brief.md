# Mission: Friction baseline (intelligence)

**Date:** 2026-06-23
**Agent:** FrictionMiner (+ ProductThesis for synthesis)
**Status:** planned
**Type:** research

## Goal

Establish a measurable friction baseline and update `docs/market_thesis.md` with evidence-backed backlog ranks — no production code unless a trivial doc-only fix is required.

## Acceptance criteria

- [ ] Run `python3 scripts/harness_snapshot.py` and read `intelligence` slice in `reports/harness_snapshot_latest.json`
- [ ] Sample quarantine / rectification failure patterns (DB or recent secondary-pass reports in `reports/`)
- [ ] Update **Friction themes** and **Ranked build backlog** in `docs/market_thesis.md`
- [ ] Write `outcome.md` with: top 5 friction themes, top 5 ranked build missions, metrics cited
- [ ] Commit doc + mission outcome; push; notify via `python3 scripts/harness_notify.py --mission missions/2026-06-23-friction-baseline`
- [ ] Do **not** deploy unless a code change was made

## Context

Phase 1 intelligence loop. Prior work: partnership compound rule, hero ticker, secondary pass on pipeline surface. Snapshot now includes junk reasons, gap frequency, industry distribution, and vertical deltas.

Read first:

- `docs/market_thesis.md`
- `docs/lead_quality_north_star.md`
- `reports/harness_snapshot_latest.json` → `intelligence`

## Out of scope

- Schema migrations
- `--apply` quarantine scripts without dry-run summary in outcome
- Fly deploy (research mission)

## Autonomous policy

You may commit, push, and notify without asking. Follow red lines in `AGENTS.md` (no force push, no `reports/` in git, no parallel cache refresh).
