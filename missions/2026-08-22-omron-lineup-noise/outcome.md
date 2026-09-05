# Outcome — Filter OEM hub noise; cap product searches; navy CRM

**Date:** 2026-08-22  
**Mission:** `missions/2026-08-22-omron-lineup-noise`  
**Type:** build

## Diff

- `app/services/robot_understanding_v1/resolve.py` — hub/nav/locale/discontinued labels are not products; hyphenated category slugs (`mobile-robots`) are not SKUs.
- `app/services/robot_profile_cache.py` — cache namespace `robot_profile_v10`.
- `app/services/plan_entitlements.py` — `jobs_product_limit` 3 free/anonymous, 5 paid.
- Jobs picker filters noise, lists up to 10 real SKUs, **searches** 3 (5 if paid). Profile lookup aborts at 22s.
- `JobsHandoffBoard` is Save-to-CRM confirmation — not a repeat of the step-2 card list.
- CRM table, outreach, and account cards use navy (`#0b162f`) in JSX; `.sb-surface` is navy; `bg-white` remaps no longer use zero-specificity `:where()`.

## Metrics

Not a pipeline-cache mission. Omron hub nav (About Us, Deutsch, Industries, …) no longer enters the picker.

## Follow-ups

Segment large OEM catalogs later: type-first buckets, family vs SKU, pages of 5. Not in this change.
