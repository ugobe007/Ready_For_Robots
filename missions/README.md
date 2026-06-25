# Missions

Autonomous work units for the Ready For Robots agent harness. One folder per mission; the Orchestrator creates the brief before execution and fills the outcome when done.

## Lifecycle

**Run all harness commands from the repo root** (`Ready_For_Robots/`), not `readyforrobots-new/`:

```bash
cd /path/to/Ready_For_Robots
python3 scripts/harness_snapshot.py
python3 -m venv .venv-harness && source .venv-harness/bin/activate
pip install -r requirements-harness.txt
export ANTHROPIC_API_KEY=...
python3 scripts/run_mission.py --mission missions/2026-06-23-friction-baseline
python3 scripts/harness_notify.py --mission missions/2026-06-23-friction-baseline
```

Or use the wrapper: `./scripts/harness python3 scripts/harness_snapshot.py`

### Daily automation

```bash
# Full loop once (creates missions/YYYY-MM-DD-daily-cycle/ if needed)
python3 scripts/harness_daily.py

# GitHub Actions: .github/workflows/harness-daily.yml (14:00 UTC daily)
# macOS: ./scripts/install_harness_launchd.sh
```

Required secrets for CI: `ANTHROPIC_API_KEY`, `DATABASE_URL`, `ADMIN_KEY`.

### Intelligence loop (start here)

1. **Orient on PMF** — read `docs/product_market_fit.md` (automated sales pipeline for robot companies)
2. **Observe** — `python3 scripts/harness_snapshot.py` (includes `intelligence` slice)
3. **Orient** — read `docs/market_thesis.md` + snapshot deltas
4. **Research mission** — FrictionMiner / MarketIntel → update thesis + backlog
5. **Build mission** — LeadQuality / ProductSurface / Deploy → code + deploy (prefer conversion/activation unless P0 junk)
6. **Notify** — `harness_notify.py` (email if Resend configured)

## Mission types

| Type | Deploy? | Example |
|------|---------|---------|
| `research` | No (docs only) | `2026-06-23-friction-baseline` |
| `build` | Yes when brief says so | `hero-ticker-swap`, `partnership-quarantine-sweep` |

Add `**Type:** research | build` to `brief.md`.

## brief.md template

```markdown
# Mission: <title>

**Date:** YYYY-MM-DD
**Agent:** FrictionMiner | MarketIntel | LeadQuality | ProductSurface | Deploy
**Status:** planned | in_progress | blocked | done
**Type:** research | build

## Goal

One sentence.

## Acceptance criteria

- [ ] …
- [ ] …

## Context

Link to harness snapshot paths, market thesis, user intent.

## Out of scope

What this mission must not touch.
```

## outcome.md template

```markdown
# Outcome: <title>

**Result:** success | partial | blocked
**Commit:** <sha or none>

## Changes

- …

## Metrics (before → after)

- pipeline leads: …
- intelligence.gap_frequency: …
- built_at: …

## Follow-ups

- …
```

## Example missions

| Slug | Agent | Type | Notes |
|------|-------|------|-------|
| `2026-06-16-pmf-conversion-focus` | Orchestrator → ProductSurface | build | **Directive** — PMF docs + next conversion/activation build |
| `2026-06-23-friction-baseline` | FrictionMiner | research | **Done** — thesis + backlog from sweep reports |
| `2026-06-23-snapshot-db-telemetry` | PipelineHealth | build | **Done** — `harness_env.py`, DB telemetry in snapshot |
| `buyer-intent-gate-triage` | LeadQuality | build | **Done** — assess/stamp/triage; dry-run ~55% no-intent |
| `rss-html-strip-and-report-filter` | LeadQuality | build | **Next** — Unknown industry HTML noise |
| `pipeline-observe-baseline` | PipelineHealth | research | Snapshot only, no code |
| `hero-ticker-swap` | ProductSurface | build | Live ticker on home hero |
| `partnership-quarantine-sweep` | LeadQuality | build | Dry-run then apply quarantine script |

Backlog ranks live in `docs/market_thesis.md`.
