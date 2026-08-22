# Job Cards stay Conditional; battle-test FIND → CRM

**Date:** 2026-08-22  
**Type:** build  
**Agents:** ProductSurface

## Goal

Matcher possible-match is not Qualified. Cards stay Conditional until user or employer feedback. Battle-test FIND → Job Cards → Next → CRM so the employment loop does not hop onto SIGNAL or claim a hire.

## Acceptance

1. POSSIBLE_MATCH / INSUFFICIENT render Conditional (pending review + site assessment).
2. Qualified is not assigned from the matcher alone.
3. Fourier (or equivalent) FIND → expand card → Next → `/crm?src=jobs_activate` still works: 3 jobs, no pipeline chrome.
4. Vitest covers the Conditional mapping.

## Out of scope

Marketplace, pilots, M2 retune, header Pipeline removal, invented economics.
