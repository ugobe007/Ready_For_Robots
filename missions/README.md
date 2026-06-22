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
python3 scripts/run_mission.py --mission missions/2026-06-22-pipeline-observe-baseline
```

Or use the wrapper: `./scripts/harness python3 scripts/harness_snapshot.py`

1. **Observe** — `python3 scripts/harness_snapshot.py`
2. **Brief** — create `missions/YYYY-MM-DD-<slug>/brief.md`
3. **Run** — `python3 scripts/run_mission.py --mission missions/YYYY-MM-DD-<slug>`
4. **Verify** — gates in `harness/gates.yaml`
5. **Outcome** — write `outcome.md` with metrics delta and follow-ups

## brief.md template

```markdown
# Mission: <title>

**Date:** YYYY-MM-DD
**Agent:** PipelineHealth | LeadQuality | ProductSurface | Deploy
**Status:** planned | in_progress | blocked | done

## Goal

One sentence.

## Acceptance criteria

- [ ] …
- [ ] …

## Context

Link to harness snapshot paths, related issues, user intent.

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
- built_at: …

## Follow-ups

- …
```

## Example missions (backlog)

| Slug | Agent | Notes |
|------|-------|-------|
| `pipeline-observe-baseline` | PipelineHealth | Snapshot only, no code |
| `hero-ticker-swap` | ProductSurface | Replace HeroSpotlightLeads; see `/experiment` |
| `partnership-quarantine-sweep` | LeadQuality | Dry-run then apply quarantine script |
