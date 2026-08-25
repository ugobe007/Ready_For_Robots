# QUALIFY inspect: model burden on the list, placement steps on the card

**Date:** 2026-08-25  
**Type:** build  
**Status:** done  
**PR:** https://github.com/ugobe007/Ready_For_Robots/pull/140

## Diff

- API `card_contract` adds `list_line` (`Site-adapted · 4–12 weeks · integrator`) and six `steps` (slot → license pack → site adapt → data → workplace qualify → field-data clause)
- Collapsed job rows show `list_line` so checkboxes happen after seeing training burden
- Expanded Job Card walks numbered placement steps. No invented dollars
- Jobs list hint names policy layer and typical time
- CRM unlock + Jobs signup taste rows carry the same model line
- CORS allows Vite fallback `http://127.0.0.1:3001` (port 3000 is often already taken)

## Tests

- pytest `tests/test_robot_task_models.py` — 8 passed
- vitest `robotJobCard.test.ts` + `jobsWorkflow.test.ts` — 33 passed
- Browser: Dexmate Vega FIND on local Vite `:3001` + API `:8000` — collapsed rows show Site-adapted · 4–12 weeks · integrator; expanded CNC card walks steps 1–6 including no automatic rebate

## Follow-ups

- Do not invent pack prices
- Matcher retune still frozen
- Production `list_line` / steps appear after Fly + Vercel deploy this branch
