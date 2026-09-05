# CRM recruiter flow — keep → apply → employer evaluate

**Type:** build  
**Date:** 2026-08-27  
**Agents:** ProductSurface, LeadQuality (Jobs CRM), Deploy  

## Goal

Clean the Jobs CRM workflow so an OEM can keep jobs, apply with specs, and recruit like a placement desk — without SIGNAL, invented employer emails, Cal sales autonomy, or a Hermes hop.

## Acceptance

1. Next steps on `/pipeline?src=jobs_activate` is a working control (`next=offer` + `#jobs-next-steps`) that opens the offer/apply form.
2. One keep prompt: **Keep these N jobs?** (N = selected count). Yes persists selected/visible cards. Then status bar + **Apply** (offer form; price + catalogued model still required).
3. Signed-in OEM can upload PDF/image brochures/specs (size-capped, account-private). Selected docs attach to the application snapshot and appear in outreach as hosted token URLs (Resend attachments when small).
4. Employer outreach (only with a real email) includes token **Accept** and **Set up interview**. Landing page needs no RFR account. Tokens write `application_messages` + status.
5. Recruiter emails go to the signed-in OEM account email on apply / accept / interview / outcome. Interview time is stored and shown in the CRM thread. v1 scheduling is a token form + emails — not Cal.

## Hard no

Signup wall stays. Process 03 stays CRM. No SIGNAL hop. No invented contacts or rental dollars. Catalogued SKUs only. Hermes stays retired. Do not revert Cal digest (#155).
