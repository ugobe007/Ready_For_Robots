# Mission: Drop junk report-download leads

**Date:** 2026-08-25
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Public `/api/leads/report-download` emails the operator on every submit. Spam bots are filling random name / company / robot-category strings (example: `NLexdStETPSyhfSDp`, `info@alohaah.com`, `Qpjgved LLC`). Stop notifying and storing those without blocking real briefing requests.

## Acceptance criteria

- [ ] The operator sample (generated name + mash company + mash category) is ignored: no waitlist row, no owner email, no report email
- [ ] Real OEM-shaped requests (named person, real company, AMR / humanoid / etc.) still capture
- [ ] Hidden honeypot on the About report form
- [ ] Targeted pytest green

## Out of scope

Matcher ranking, Jobs CRM, SIGNAL as core.
