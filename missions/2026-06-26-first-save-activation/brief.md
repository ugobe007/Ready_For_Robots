# Mission: First-save activation trio

**Date:** 2026-06-26
**Agent:** ProductSurface
**Status:** complete
**Type:** build

## Goal

Close the post-signup activation gap: first save, URL scan value parity, and CRM path fork.

## Acceptance criteria

- [x] Signed-in user with 0 saves sees `FirstSaveNudge` on `/pipeline` with one-click save
- [x] After first save, `CrmPathFork` offers native CRM vs HubSpot (pipeline + `/crm`)
- [x] Anonymous `/results` shows value strip + full outreach draft (top lead + per card)
- [x] Signup from results preserves `?next=/results?url=…`

## Context

Operator picked ranks 1–3 from activation backlog after rep-voice outreach shipped.
See `docs/value_first_principle.md` rung 2 (Capture).

## Out of scope

- Stripe billing
- Lead quality sweeps
