# Unstick CRM: restore Jobs nav and a next step

**Date:** 2026-08-26  
**Type:** build  
**Agents:** ProductSurface

## Goal

Users were stuck on the CRM page with **no next step** and **no navigation links**. Restore Jobs chrome on the unsigned wall and the signed desk so they can see FIND / Job Cards / CRM, leave the desk, and take a clear next action. Spec: `docs/jobs_crm.md`.

## Acceptance

1. `/pipeline?src=jobs_activate` unsigned still hits the signup wall. The wall shows process chrome (01 / 02 / 03) and **Sign up to open CRM →**. Not a dead “Opening CRM…” page.
2. Signed desk keeps collect-then-act. Process 03 stays **CRM**. After inspect/place, next is Job Cards (`/?restore=1`) when they have a submission or collected jobs, otherwise FIND (`/?new=1`).
3. Header Jobs / About stay visible (About is not hidden on small screens). No SIGNAL hop. `jobsCrmOpenHref` remains the only CRM entry.
4. Vitest covers hrefs/nav helpers. Do not remove the wall.

## Out of scope

Matcher retune. SIGNAL buyer pipeline. Renaming step 03. Hardcoding Fly in `apiBase.ts`.
