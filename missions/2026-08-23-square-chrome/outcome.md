# Outcome — Square chrome + 1970s control panel

**Date:** 2026-08-23  
**Type:** build  
**Status:** shipped (PR)

## Diff

- `index.css` — `--radius: 0`; global `border-radius: 0` (glow orbs excluded); bevel/inset/LED/scanline; square native checkboxes; emerald caret + selection.
- Jobs CTAs and process-bar action use `rfr-bevel`. Jobs shell has a faint CRT scan. Header Jobs tab has a square LED when active.
- Shadcn button/card/input/textarea/checkbox/badge drop `rounded-*`.
- Signup, login, CRM cards/buttons/inputs drop leftover pills.
- `docs/EXPERIMENT_MODE.md` — rectilinear chrome is locked.

## Verify

`pnpm exec vitest run client/src/lib/jobsWorkflow.test.ts` — 27 passed.

Local `/?new=1` and `/signup?src=jobs_activate`: square URL field, square Start jobs, square OAuth + email, header Jobs LED, no Pipeline in the header.

## Follow-ups

Jobs signup **footer** still lists Pipeline / SIGNAL. Browser autocomplete dropdowns are OS chrome (not ours).
