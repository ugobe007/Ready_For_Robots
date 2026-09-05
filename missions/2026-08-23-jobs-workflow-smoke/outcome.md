# Outcome — Jobs workflow smoke + honest Vercel gate

**Date:** 2026-08-23  
**Type:** build  
**Status:** shipped (PR)

## Diff

- `scripts/vercel_production_smoke.py` — gate only on `https://readyforrobots.com` (JS ≠ `index-bxLpnQiT.js`, >100kB, canary `Jobs for`). A `*.vercel.app` 404 is advisory.
- `.github/workflows/deploy-frontend.yml` — replace `curl -f` + `set -e` bash with that script; parse deploy URL from the CLI log without making it a hard gate.
- `tests/test_vercel_production_smoke.py` — reproduces the #105 abort (deploy URL 404 must not skip the domain poll).
- `docs/vercel_production_secrets.md` — document the 404 / protection race.

## Production smoke (FIND → cards → CRM)

| Check | Result |
|-------|--------|
| Bundle | `index-CoF0C_UB.js` 1,831,787 bytes, canary `Jobs for` |
| Fly `/health` | 200 `{"status":"ok"}` |
| Header `/` | JOBS / ABOUT / SIGN IN — **no Pipeline** |
| Fourier `https://www.fftai.com/en` | picker 5 robots in 2 groups |
| Fourier N1 | 5 Job Cards, all **Conditional**, tagged `Job 00001 is for Fourier N1` |
| Next → | `/signup?next=/crm?src=jobs_activate&submission=14&src=jobs_activate` |
| Signup | 3 job opportunities for Fourier N1; no HOT buyers; no Back to pipeline |

API: `POST /api/robot-job-search` for Fourier N1 returned 5 `POSSIBLE_MATCH` jobs (Fulcrum, groninger, Industrial Metal Supply, Siemens Energy, TransTech).

GHA #105 (`32610689880`): Vite build + pack + `vercel deploy --prebuilt --prod` **succeeded**; smoke `curl -f` of `ready-for-robots-87igrkw5w-….vercel.app` returned **404** and aborted. Custom domain was already the new bundle.

## Metrics

Not a pipeline-cache mission. Pytest: `tests/test_vercel_production_smoke.py` 8 passed.

## Follow-ups

- Jobs signup **footer** still lists Pipeline / SIGNAL (header is clean).
- Fourier hub research is still ~45s; do not retune matcher to fake speed.
