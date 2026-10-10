# ReadyForRobots verification map

This directory is the maintained source for verifying user-facing Jobs behavior. Read the index before driving the app, then use the matching feature file as the recipe.

Product chrome (nav, process bar, panels, results): [`docs/feature_map.md`](../../../../docs/feature_map.md).

## Baseline preconditions

- Prefer production: site `https://readyforrobots.com`, API `https://ready-2-robot.fly.dev`.
- Run `python3 scripts/agent_verify.py doctor` and require `worth_driving: true`.
- Fail immediately on skip-green JS (`/assets/index-bxLpnQiT.js`).
- Do not sign up, send Cal mail, or refresh the pipeline cache during verify.
- Never drive a local Vite instance you did not start. Never `pkill` by name.

## Driving conventions

- Start every recipe from doctor-healthy production unless the feature file says local.
- Prefer ARIA names (`Find jobs for your robot`, `Jobs process`) over CSS.
- Treat commands as literal.
- HTTP drive goes through `python3 scripts/agent_verify.py drive --feature <id>`.
- Browser drive (when available) uses the same handles; still record the match API result.

## Proof and skip reporting

- Capture the user action and the resulting JSON/HTML canary, not only a screenshot of `/`.
- Job Cards need named employers when the matcher is `requirement_v1`.
- Unlocked CRM jobs without a session are `verified-unreachable` with that prerequisite — not a pass via `/login`.
- Record the feature ID with every artifact under the evidence directory the doctor printed.
- Do not report a skipped entry point as verified through SIGNAL `/pipeline`.

## Feature entry contract

Each feature file starts with an H1 and one paragraph, then exactly four H2s:

1. `Sub-features`
2. `How to get to it (user POV)`
3. `Driving it with verify-readyforrobots`
4. `Gotchas`

## Features

- [Find jobs](./find-jobs.md) — paste a robot URL, get Job Cards.
- [Find stay](./find-stay.md) — FIND timeout / 500 / abort stays on `/?visit=jobs`; employer MATCH catalog budget.
- [Job Cards](./job-cards.md) — employer, workplace, work, qualification, task model.
- [Jobs chrome](./jobs-chrome.md) — header, process bar, no Pipeline hop.
- [Jobs CRM](./jobs-crm.md) — Open CRM → `/pipeline?src=jobs_activate`, 5 unlocked jobs, Place this job.
- [About](./about.md) — `/intelligence` is the Jobs loop, not SIGNAL.
