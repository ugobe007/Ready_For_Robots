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

### Intelligence loop (start here)

1. **Observe** — `python3 scripts/harness_snapshot.py` (includes `intelligence` slice)
2. **Orient** — read `docs/market_thesis.md` + snapshot deltas
3. **Research mission** — FrictionMiner / MarketIntel → update thesis + backlog
4. **Build mission** — LeadQuality / ProductSurface / Deploy → code + deploy
5. **Notify** — `harness_notify.py` (email if Resend configured)

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
| `2026-06-23-friction-baseline` | FrictionMiner | research | **Start here** — thesis + backlog from snapshot |
| `pipeline-observe-baseline` | PipelineHealth | research | Snapshot only, no code |
| `hero-ticker-swap` | ProductSurface | build | Live ticker on home hero |
| `partnership-quarantine-sweep` | LeadQuality | build | Dry-run then apply quarantine script |

Backlog ranks live in `docs/market_thesis.md`.
