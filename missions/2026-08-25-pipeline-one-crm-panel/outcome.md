# Outcome: One readable CRM panel on Pipeline

**Date:** 2026-08-25
**Status:** done
**Type:** build

## Diff

- `WorkspaceQuickLinks` is Activity / Replies / HubSpot only — no CRM how-to strip.
- Signed-in Search Jobs no longer repeats “your next CRM action.” Unsigned visitors still get one start-workspace box.
- Hermes + First 3 actions use navy + light text (`.pipeline-hermes`).
- Job workspace grows with the page (`items-start`, overflow visible) instead of a `100vh` inner-scroll clamp.
- Jobs 02 → 03 uses wouter `setLocation` instead of a full document reload.
- Top and bottom process nav are always `<button>`s (current step included); footer sits above the scanline overlay.
- Outreach draft / checklist / contact / proposal are dark-native. CalLeadDrop SIGNAL recommendation and Re-run SIGNAL are gone from Pipeline.

## Tests

- `pnpm exec vitest run client/src/lib/jobsWorkflow.test.ts` — 28 passed

## Follow-ups

Signed-in First 3 actions still needs a logged-in pass. Jobs CRM activate stays in `PipelineCrmMotion` + the selected job workspace.
