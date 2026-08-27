# Jobs CRM — hold an interview slot

**Date:** 2026-08-27  
**Type:** build  
**Agents:** ProductSurface, LeadQuality (Jobs CRM recruiter)

## Goal

After #156 (Accept / propose time / connect us), add **hold a slot** as a first-class interview option on `/employer/:token`. Persist the window on the application. Email employer + OEM. OEM confirms or releases from CRM and from a token link. Do not re-enable Cal sales autonomy.

## Acceptance

1. Employer token page offers **Propose time + confirm** and **Hold this slot** (concrete window).
2. Hold writes `interview_held`, stores `held_at` / `hold_expires_at` / `slot_start` / `slot_end`.
3. Recruiter email to OEM: slot held for {employer} {job} {time}, plus confirm/release link. Both-sides email only when a real employer email exists.
4. OEM CRM inbox shows the held slot and Confirm hold / Release hold.
5. Success/fail stay on the application. Process 03 stays CRM. No SIGNAL hop. `CAL_AUTONOMY_ENABLED` stays 0. Hermes stays retired.
6. Tests cover hold vs propose, mocked Resend, no employer send without an employer email.

## Out of scope

Cal `/calendar` send queue. Invented employer emails. HOT-buyer outreach.
