# Outcome: pipeline-actionable-crm

**Status:** complete
**Type:** build

## What shipped

- Non-Pro `/pipeline` shows **15 customer opportunities**; Pro keeps the full live market (90).
- Company names are high-contrast (near-white, larger) in the list and the buyer workspace.
- Removed the duplicate “You’re activated — finish setup” panel. Search pipeline next steps remain.
- Signed-in users no longer see empty CRM columns (New Signal / Discovered) or a fake “Draft Ready” board before CRM is on.
- Primary next step for a signed-in workspace with 0 saves: **Activate CRM — save this buyer**.
- Right panel is “Work this buyer” with a large company name and the same CRM activation card.

## Tests

- `npx vitest run client/src/lib/pipelineVisibility.test.ts` — 3 passed
- `npx tsc --noEmit` — passed
- `tests/test_plan_entitlements.py::test_pipeline_limits` — passed (free/anonymous = 15, paid = 90)
- Remaining Python trim tests need project venv deps (sqlalchemy/jwt) in this environment; they import the existing filter stack, not new logic.

## Conversion hypothesis

A ranked 15-buyer list plus one obvious CRM save beats a classified-style board with empty stages and a second setup checklist.
