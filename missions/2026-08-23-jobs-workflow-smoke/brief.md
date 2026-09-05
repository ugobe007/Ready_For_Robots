# Jobs workflow smoke + honest Vercel gate

**Date:** 2026-08-23  
**Type:** build  
**Agents:** ProductManager + Deploy

## Goal

Production Vercel is on the Jobs bundle (`index-CoF0C_UB.js`). GHA still goes red because smoke `curl -f`s the `*.vercel.app` URL (404) under `set -e` and never polls `readyforrobots.com`. Make the gate match production truth, then smoke FIND → Job Cards → CRM.

## Acceptance

1. Smoke does not treat a `*.vercel.app` 404 as deploy failure.
2. Gate is `https://readyforrobots.com`: JS ≠ `index-bxLpnQiT.js`, JS > 100k, canary `Jobs for`.
3. Pytest covers the #105 404 abort.
4. Production: `/` header has no Pipeline; Fourier URL yields Conditional Job Cards; Next goes to `/crm?src=jobs_activate`.

## Out of scope

SIGNAL ranking, inventing jobs, matcher retune, Vercel token changes.
