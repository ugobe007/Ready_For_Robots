# About page is Jobs, not SIGNAL

**Date:** 2026-08-23  
**Type:** build  
**Agents:** ProductSurface

## Goal

`/intelligence` is the Jobs **About** tab. Header and footer already hide Pipeline / SIGNAL. The body still hops to `/signals` and “Activate SIGNAL.” Reframe copy and CTAs to FIND → jobs → CRM. Do not expand SIGNAL as a second product on this page.

## Acceptance

1. No `Activate SIGNAL`, no `/signals` links, no product-name `SIGNAL` on `/intelligence`.
2. Primary CTA is `Start jobs →` to `/?new=1`. Signup stays `src=jobs_activate`.
3. Process copy is the Jobs loop (robot URL → job cards → CRM), not lead scoring / HOT buyers.
4. Newsletter and report forms stay; their copy is work/jobs, not buying signals.
5. Vitest file-read on `Intelligence.tsx` locks the contract.

## Out of scope

Matcher / ranking. CRM “Pipeline lead #” hop. Rewriting `/signals` itself.
