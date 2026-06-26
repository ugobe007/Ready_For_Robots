# Mission: Value-first outreach preview

**Date:** 2026-06-25
**Agent:** ProductSurface
**Status:** planned
**Type:** build

## Goal

Users do not buy unless they see value. Anonymous visitors must **read a real Cal outreach draft** on `/pipeline` before signup — not a wall of jargon.

## Acceptance criteria

- [x] Anonymous user sees full outreach subject + body on selected lead (`PipelineOutreachValuePanel`)
- [x] Anonymous value strip explains proof before signup (`AnonymousValueStrip`)
- [x] Signup from pipeline restates save + copy unlock (`Signup.tsx` when `?next=/pipeline`)
- [x] CTA copy: "Sign up free — save & copy" (not "Activate SIGNAL")
- [x] Longer anonymous `pipeline_action` teaser (200 chars in `plan_entitlements.py`)
- [ ] **Next:** First-save nudge for signed-in users with 0 CRM accounts
- [ ] **Next:** URL scan `/results` shows sample draft before signup (parity with pipeline)

## Context

Operator directive: overcome conversion challenges by proving value first.
See `docs/value_first_principle.md`.

## Out of scope

- Stripe billing
- Lead quality sweeps unless junk blocks trust on live pipeline
