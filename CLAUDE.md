# Ready For Robots — Agent SDK project context

Read **AGENTS.md** for the full harness constitution. This file is loaded on every Agent SDK session via `settingSources: ["project"]`.

## Summary for every turn

1. **North star order:** names/events → scores → rank → robot specs. Fix junk before ranking tweaks.
2. **One mission per cycle.** Write `missions/YYYY-MM-DD-<slug>/brief.md` before coding.
3. **Observe first:** `python3 scripts/harness_snapshot.py` → read `reports/harness_snapshot.json`.
4. **Verify:** run targeted pytest; never deploy without human approval.
5. **Frontend:** `readyforrobots-new/` (Vite + wouter). API: `https://ready-2-robot.fly.dev`.
6. **Do not commit** `reports/` artifacts.

## Compaction — always preserve

When summarizing conversation history, keep:

- Current mission objective and acceptance criteria
- Files modified and test results
- Metrics before/after from harness snapshot
- Decisions made and open blockers

## Subagent delegation

| Task | Delegate to |
|------|-------------|
| Pipeline cache / API feed | PipelineHealth |
| Junk rules / quarantine | LeadQuality |
| Home / experiment UI | ProductSurface |
| git / fly / smoke | Deploy (human approves deploy) |
