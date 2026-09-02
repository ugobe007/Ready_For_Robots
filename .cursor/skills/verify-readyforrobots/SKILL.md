---
name: verify-readyforrobots
description: Drive ReadyForRobots Jobs the way a user does — FIND on `/`, Job Cards, Jobs chrome, Jobs CRM, About. Use when proving a code change or PR, before auto-merge, or when a Jobs-path mission needs production evidence (not a skip-green Vercel badge).
---

# Verify ReadyForRobots

Primary surface: **Jobs web UI** on `https://readyforrobots.com` (`readyforrobots-new/`, Vite + wouter). API: `https://ready-2-robot.fly.dev`. Other routes (SIGNAL `/pipeline`, Cal admin) exist; they are not the product. Do not hop Jobs traffic onto HOT buyers.

**Hermes is retired.** Do not smoke `/experiment` as FIND. `/` is the landing fork. FIND is `/?visit=jobs` after Jobs for Robots (same `/` document). Jobs proof is this skill plus `POST /api/robot-job-search` (submit) and `POST /api/robot-job-match` (cards). **Critic is pstack.** How / Act / Critic live in `pstack/`, `scripts/pstack_release.py`, `pstackSite.ts`, and `pstack_protocol.py`. pstack is the **release gate**, not a customer chatbot and not protocol chrome on `/` or Jobs CRM.

**No Jobs product PR without pstack release checks.** Draft PRs must still run `.github/workflows/pstack-release.yml` and the `pstack-release` job in `agent-verify.yml`. Critic `healthcare_class` fails if Diligent FIND is `robot_class=humanoid` or shows `No humanoid jobs for this robot yet.`

You are reading this cold. Production is the honest instance. A local Vite shell is optional chrome. A 7-second “Deploy frontend” skip is not proof.

## Launch

Production (default — doctor and drive this unless the mission is purely local CSS):

- Site: `https://readyforrobots.com`
- API: `https://ready-2-robot.fly.dev`
- Ready: `GET /health` on Fly is 200 and `GET /` returns an `/assets/index-*.js` that is **not** `index-bxLpnQiT.js`.

Local Jobs UI (optional, does not replace Fly):

```bash
cd readyforrobots-new && pnpm exec vite --host --port 3000
```

Ready when `http://127.0.0.1:3000/` returns 200. `strictPort` is false — if 3000 is taken, Vite moves; record the actual port. Teardown: kill **that PID** only. Never `pkill -f vite`.

Two local instances can share nothing if they use different ports. Do not double-drive a shared production session with writes (CRM opt-in, signup). Match `POST /api/robot-job-match` is the Jobs FIND path and does not write CRM.

Print the launch command without daemonizing:

```bash
python3 scripts/agent_verify.py launch
```

## Doctor

Run first whenever anything looks off, before the first drive, and after a failed drive:

```bash
python3 scripts/agent_verify.py doctor --evidence "$EVIDENCE"
```

Worth driving only if **all** are true:

- Fly `/health` 200
- Fly `/api/leads/pipeline` JSON has `built_at` and a `leads` list
- Homepage HTML points at `/assets/index-*.js` and it is not the skip-green stale hash
- That JS contains `Find jobs for your robot`, `Jobs for`, and `jobs_activate`

If `skip_green` is true, **fail**. Do not auto-merge. The next mission is Vercel production, not another UI tweak.

Helpers (same doctor): `.cursor/skills/verify-readyforrobots/scripts/doctor`

## Drive

Recipe: HTTP the user path the Jobs terminal already uses. Prefer ARIA when a browser is available; CI uses the match API + JS canaries because `/` is an SPA shell.

```bash
python3 scripts/agent_verify.py drive --feature find-jobs --evidence "$EVIDENCE"
python3 scripts/agent_verify.py drive --feature find-url --evidence "$EVIDENCE"
python3 scripts/agent_verify.py drive --feature find-stay --evidence "$EVIDENCE"
python3 scripts/agent_verify.py drive --feature employer-match --evidence "$EVIDENCE"
python3 scripts/agent_verify.py pstack --evidence "$EVIDENCE"
python3 scripts/agent_verify.py ci --evidence "$EVIDENCE"
```

| Feature | Handle | Observable end state |
|---------|--------|----------------------|
| find-jobs | `POST /api/robot-job-match` (Vega profile or chip) | `state=matches`, `job_count>0`, job titles; requirement matcher has named `company_name` |
| find-url | `POST /api/robot-job-search` (Dexmate + Greenfield) | not Research failed / Failed to fetch; identity is that URL’s company; Greenfield is not strawberry/Agrobot |
| find-stay | FIND catch + `Jobs.tsx` visit guard | timeout / 500 / abort stay on `/?visit=jobs`; never `/` or `/?new=1` landing. Skip-green is a fail. |
| employer-match | `POST /api/employer-robot-match` | catalog snapshot only; when `catalog_only` is live, elapsed < 3s; no OEM scrape |
| job-cards | same payload | cards exist (title + employer); expand in UI shows employer / workplace / work / Conditional |
| jobs-chrome | homepage JS | process labels + `jobs_activate`; checkout CTA `Find jobs →` |
| jobs-crm | `/pipeline?src=jobs_activate` | bundle has activate src; unlocked 5 jobs need a snapshot/session — do not call login a pass |
| about | `/intelligence` | 200 and JS has the route; body is the Jobs loop, not SIGNAL |

Stable UI handles (browser):

- FIND form: `aria-label="Find jobs for your robot"`; url input placeholder `Paste robot product URL`
- Process bar: `aria-label="Jobs process"`; steps 01 / 02 / 03
- Jobs header: wordmark → `/?new=1`; nav **Jobs** / **About**; **no Pipeline** on `/`
- Next: `Open CRM →` on the list, not on the card
- Activate: `/pipeline?src=jobs_activate`

Helpers: `.cursor/skills/verify-readyforrobots/scripts/drive`

## Evidence

Directory: `$RFR_VERIFY_EVIDENCE` or `/opt/cursor/artifacts/verify-<utc>/` or `/tmp/rfr-verify/verify-<utc>/`.

Proof standards:

- Exercise the real Jobs path (URL/profile → match API → cards), not a test-only endpoint.
- Capture the action and the result (`doctor.json`, `drive-<feature>.json`, `summary.json`).
- Side effects: match must not create CRM rows. Do not POST signup during verify.
- Skip-green Vercel is a failed proof even if Fly is healthy. A 7-second “Deploy frontend” skip is not proof. Doctor `skip_green` fails the run.
- FIND lookup failure must remain on `/?visit=jobs`. Landing (`/` / `/?new=1`) after timeout, 500, abort, or Failed to fetch is a failed proof.
- After cleanup, JSON evidence must still exist at the named path.

## Cleanup

Remove Vite PIDs **this run started**. Do not kill Fly, Vercel, or leftover user servers. Do not delete evidence files.

## Helpers

```bash
python3 scripts/agent_verify.py doctor
python3 scripts/agent_verify.py drive --feature find-jobs
python3 scripts/pstack_release.py
python3 scripts/agent_verify.py ci
python3 scripts/agent_verify.py map
python3 scripts/agent_verify.py launch
```

Skill wrappers (executable):

```bash
.cursor/skills/verify-readyforrobots/scripts/doctor
.cursor/skills/verify-readyforrobots/scripts/drive --feature find-jobs
```

Feature map: [features/README.md](features/README.md). Product chrome: [docs/feature_map.md](../../../docs/feature_map.md).

Upkeep: `/maintain-verification-skill` (pstack). Edit only this skill directory on a maintain pass; product bugs stay product bugs.

## Auto-merge (PRs)

GitHub Action `.github/workflows/agent-verify.yml` runs job **pstack How / Act / Critic** (including drafts) then `ci` + targeted vitest/pytest. `.github/workflows/pstack-release.yml` is the same gate on every PR, including drafts. If **both** pstack-release and verify are green **and** the branch is `cursor/*` (or label `automerge-after-verify`) **and** skip-green is false **and** the PR is not a draft, the workflow enables squash auto-merge. Hourly observe does not open or merge PRs. Label `do-not-merge` blocks it. Draft-skip on this gate is forbidden.
