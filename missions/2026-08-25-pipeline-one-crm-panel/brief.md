# Mission: One readable CRM panel on Pipeline

**Date:** 2026-08-25
**Agent:** ProductSurface
**Status:** done
**Type:** build

## Goal

`/pipeline` currently shows two CRM how-to rails (command-bar “everything happens on this page” and Search Jobs “your next CRM action”). Keep **one** working CRM surface. Fix light-grey + white-text contrast on the job workspace, and stop clamping that panel so short that Hermes / First 3 actions need an inner scrollbar.

Follow-up: Jobs 02 → 03 was a full document reload (~45s). Bottom process nav did not receive clicks. Outreach draft used light cards (white-on-beige). SIGNAL recommendation / re-run SIGNAL wasted space on the Jobs CRM path.

## Acceptance criteria

- [ ] Signed-in Pipeline does not show two CRM instruction blocks
- [ ] Hermes / First 3 actions use dark navy + light text (readable)
- [ ] Job workspace panel grows with content instead of a short inner scroll
- [ ] Jobs CRM still saves jobs (not SIGNAL buyers)
- [ ] Targeted vitest green
- [ ] Jobs 02 → 03 uses SPA `setLocation` (no full document reload)
- [ ] Top and bottom process nav are always buttons (current step included)
- [ ] Outreach draft / checklist / contact row are dark-native (readable)
- [ ] Pipeline job workspace has no CalLeadDrop SIGNAL recommendation and no Re-run SIGNAL control

## Out of scope

Matcher ranking, HubSpot sync behavior, SIGNAL as core.
