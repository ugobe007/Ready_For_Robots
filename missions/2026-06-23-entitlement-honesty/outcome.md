# Outcome: Entitlement honesty

**Date:** 2026-06-23
**Status:** done

## Backend

- `plan_feature_flags()` — research, HubSpot auto-sync, saves, intel gates
- `user_workspace_entitlements()` — plan, billing slug, display name, saved count/limit
- `/api/user/me` includes `entitlements`
- Pipeline feed `entitlements.features` for UI consistency

## Frontend

- **Pricing** — Free ($0, 50 leads, 5 saves) / Pro / Premium; FAQs updated
- **Profile** — workspace plan card with saved meter and upgrade link

## Truth table (until Stripe)

| Tier | Pipeline | Saves | Research | HubSpot auto-sync |
|------|----------|-------|----------|-------------------|
| Anonymous | 12 preview | 0 | No | No |
| Free | 50 | 5 | No | No |
| Pro/Premium | 50 | Unlimited | Yes | Yes |
