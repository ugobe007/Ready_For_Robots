# Jobs chrome

Jobs chrome is the page frame for FIND → cards → CRM: dark header, process bar, scrolling document. Pipeline is SIGNAL-only and must not appear on `/`.

## Sub-features

- `chrome-header` Jobs / About / CRM; wordmark goes to `/?new=1`.
- `chrome-process` 01 Show us your robot → 02 Available jobs → 03 CRM, as links, top and bottom.
- `chrome-no-pipeline` no Pipeline nav, no SIGNAL FAB on Jobs pages.
- `chrome-scroll` the document scrolls; no `100vh` + `overflow: hidden` trap.
- `chrome-pstack` How / Act / Critic is the **release gate** (`scripts/pstack_release.py`), not a required banner on `/`. Matcher is `POST /api/robot-job-match`. FIND submit is `POST /api/robot-job-search`. Not a chatbot. Do not put JOBS AGENT PROTOCOL on FIND or CRM as merge proof.

## How to get to it (user POV)

- Any Jobs page: `/`, `/jobs/:slug`, About `/intelligence`, Jobs CRM `/pipeline?src=jobs_activate`, Jobs signup/login.
- Not SIGNAL `/pipeline` (no Jobs `src`), `/signals`, or bare `/crm`.

## Driving it with verify-readyforrobots

Preconditions:

- Doctor healthy.

- **Header.** On `/`, nav includes Jobs, About, and CRM. Pipeline is absent. Signed-out Sign In stays. Signed-out CRM href is the signup wall with `next=/pipeline?src=jobs_activate`.
- Process bar. `aria-label="Jobs process"`. Actions: FIND `Find jobs →`, list `Open CRM →`. Step 03 label is CRM.
- **JS canary (CI).** Run `python3 scripts/agent_verify.py drive --feature jobs-chrome --evidence "$EVIDENCE"`. Live `/` bundle: `Find jobs for your robot`, `Show us your robot`, `Available jobs`, `jobs_activate`, and a FIND action (`Find jobs →`, or `Start jobs →` until Vercel ships this copy). Checkout: `FIND_JOBS_CTA = "Find jobs →"`.
- **Proof.** `drive-jobs-chrome.json` hits are all true. Browser: screenshot of `/` with header + FIND, Pipeline not in the header.

## Gotchas

- The marketing `Header.tsx` still lists Pipeline for SIGNAL pages. Jobs uses `ExperimentHeader`. Assert the Jobs header, not the unused marketing nav.
- Footer follows the header: Jobs chrome has no Pipeline / SIGNAL.
- Do not pin Next only under the fold.
