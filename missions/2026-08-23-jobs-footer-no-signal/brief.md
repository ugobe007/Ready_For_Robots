# Jobs footer matches header (no Pipeline / SIGNAL)

**Date:** 2026-08-23  
**Type:** build  
**Agents:** ProductSurface

## Goal

Jobs-path pages that still render `SiteFooter` (signup, login, About) must not list Pipeline or SIGNAL. The floating Signal FAB must not appear on those pages either. Header already hid Pipeline; footer was the leftover leak after square chrome.

## Acceptance

1. `showJobsSiteChrome` is true on `/`, `/jobs…`, `/intelligence`, Jobs CRM (`src=jobs_activate`), and Jobs signup/login (`src` or `next` continues Jobs).
2. False on `/pipeline`, `/signals`, bare `/crm`, and `/signup?next=/pipeline`.
3. Jobs footer kicker is JOBS; product links are Jobs / CRM / About — no Pipeline, no Signals.
4. `ScoutChat` hides the Signal FAB when `showJobsSiteChrome` is true.
5. Vitest covers the helper plus file-read contracts on `SiteFooter` and `ScoutChat`.

## Out of scope

Intelligence page body copy (still SIGNAL). Matcher / ranking. CRM “Pipeline lead #” hop.
