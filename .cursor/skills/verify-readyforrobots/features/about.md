# About

About (`/intelligence`) explains the Jobs loop and sends the user back to FIND. It is not a second product and not SIGNAL intelligence as the core CTA.

## Sub-features

- `about-loop` shows 01 robot → 02 jobs → 03 CRM.
- `about-cta` Find jobs → goes to `/?new=1`.
- `about-chrome` Jobs header (no Pipeline).
- `about-signup` signup carries `src=jobs_activate`.
- `about-pstack` optional protocol explainer (`#jobs-protocol`). Merge proof is `scripts/pstack_release.py`, not this module.

## How to get to it (user POV)

- Click About in the Jobs header.
- Open `https://readyforrobots.com/intelligence`.
- Legacy `/how-it-works` redirects here.

## Driving it with verify-readyforrobots

Preconditions:

- Doctor healthy.

- **Open.** `GET /intelligence` 200.
- **JS.** Bundle includes `/intelligence`.
- **CI.** `python3 scripts/agent_verify.py drive --feature about --evidence "$EVIDENCE"`.
- **Browser.** Jobs header visible, Find jobs → present, Pipeline absent. CTA does not go to `/pipeline`.

## Gotchas

- `/intelligence` used to read as market-signals. Body copy must stay the Jobs loop.
- A 200 on an empty SPA shell is not enough without the JS route canary.
