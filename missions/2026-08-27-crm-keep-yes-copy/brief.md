# Keep N jobs? — working Yes, live nav, Apply sequence

**Date:** 2026-08-27
**Type:** build
**Agents:** ProductSurface
**Status:** in_progress

## Goal

On Jobs CRM (`/pipeline?src=jobs_activate`) after #156: **Keep N jobs?** is a prompt with a real confirmation button, **Select all N** is gone, process/header nav uses real hrefs, and Apply names the placement sequence. Hold-slot #157 stays.

## Acceptance

1. Prompt is `Keep ${n} jobs?` (N from selected count, not a hardcoded 5). Confirmation is a button/submit (e.g. **Yes, keep them**) that POSTs keep / signed-in upsert and then surfaces Apply. Unsigned still walls. Not `href="#"`.
2. **Select all N** is removed. It asked the same keep question twice.
3. Process chrome 01 FIND / 02 Available jobs / 03 CRM and header Jobs / About are real hrefs (`/`, job-cards restore, `/pipeline?src=jobs_activate`, `/intelligence`). `onJobsFreshHomeClick` only intercepts on Jobs home.
4. Apply CTA carries the sequence: apply to the job → we help schedule interviews with the customer → they close. No invented rental dollars.
5. Vitest covers confirm control, nav hrefs, and Apply sequence. Grep: no `Keep these`, no `Select all 5`, no `href="#"` on Yes.

## Out of scope

Fly deploy. SIGNAL hop. Matcher retune. Reverting #157 hold.
