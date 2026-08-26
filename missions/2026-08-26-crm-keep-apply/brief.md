# Keep jobs, apply, and employer inbox on the account

**Date:** 2026-08-26  
**Type:** build  
**Agents:** ProductSurface

## Goal

Jobs CRM keeps selected Job Cards on the user account, then next-steps → apply → employer outreach, with a desk inbox for replies. Spec: `docs/jobs_crm.md`.

## Acceptance

1. Authenticated Keep jobs upserts Job Cards onto the user (Postgres). Status bar shows “N jobs saved”. CRM link only when the user is not already on the desk.
2. Unsigned users still hit the signup wall. After signup, kept jobs restore.
3. Next steps form: robot name, catalogued OEM SKUs, skippable PoC, proposed monthly price (user offer, not a site rate). Apply gated on price + model.
4. Apply persists `job_applications`. Outreach sends only when a real employer email exists. No invented contacts. No invented rental dollars.
5. Employer replies live in `application_messages`. CRM desk shows thread + Reply + paste-inbound.
6. Process chrome stays 01 / 02 / 03 CRM. No SIGNAL hop. Wall stays.

## Out of scope

Fly deploy. Resend inbound MX/DNS. HubSpot export. Matcher retune.
