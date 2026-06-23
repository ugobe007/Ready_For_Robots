# Mission: Entitlement honesty

**Date:** 2026-06-23
**Agent:** ProductSurface
**Status:** done
**Type:** build

## Goal

Align pricing page and profile with `plan_entitlements.py` — no tier promises the backend does not enforce.

## Acceptance criteria

- [x] `user_workspace_entitlements()` + `plan_feature_flags()` in plan entitlements service
- [x] `GET /api/user/me` returns `entitlements` block
- [x] Pricing reframed as Free / Pro / Premium matching gates
- [x] Profile shows plan label, saved usage, upgrade CTA
