# Vercel production secrets (the three GitHub secrets)

`readyforrobots.com` is a Vercel static site. Fly is the API. GitHub workflow **Deploy frontend to Vercel** (`.github/workflows/deploy-frontend.yml`) is the only path that promotes `main` to that domain **unless** you click Promote on a Preview in the Vercel UI.

Until these three **repository secrets** exist, that workflow cannot call `vercel deploy --prebuilt --prod`. It used to skip-green in ~7 seconds. It now **fails** so the lie is visible.

---

## The three secrets

| GitHub secret | What it is | Where to copy it |
|---------------|------------|------------------|
| **`VERCEL_TOKEN`** | Personal (or team) access token that can deploy | Vercel → Account Settings → **Tokens** → Create. Scope: the `ugobe07-gmailcoms-projects` team / `ready-for-robots` project |
| **`VERCEL_ORG_ID`** | Team/org id (`team_…`) | Vercel → team **Settings** → General → **Team ID**. Or from a linked checkout: `.vercel/project.json` → `orgId` |
| **`VERCEL_PROJECT_ID`** | Project id (`prj_…`) | Vercel → project **ready-for-robots** → Settings → General → **Project ID**. Or `.vercel/project.json` → `projectId` |

Paste them in GitHub: **ugobe007/Ready_For_Robots** → Settings → Secrets and variables → Actions → New repository secret. Names must match **exactly** (case-sensitive).

**Paste rules for `VERCEL_TOKEN`:** one token string, nothing else. No trailing space, no newline, no quotes, no `Bearer ` prefix. Vercel CLI 59+ errors with `Must not contain: " "` if any space is present. A GitHub Actions env dump that shows `VERCEL_TOKEN: *** ` (space after the mask) while `VERCEL_ORG_ID: ***` has none means the token secret itself has a trailing space. The deploy workflow now trims that; still re-paste the secret so later jobs do not depend on trim.

These are **not** `DATABASE_URL`, `FLY_API_TOKEN`, or `ANTHROPIC_API_KEY`. Those are other systems.

---

## After the secrets are set

1. Actions → **Deploy frontend to Vercel** → Run workflow on `main`  
   **or** push an empty commit / re-run the failed job on the latest `main` push.
2. A real run is **minutes** (`vercel pull` → `vercel build` → `vercel deploy --prebuilt --prod`), not 7 seconds.
3. Confirm `https://readyforrobots.com` HTML bundle hash changed and Jobs header has no Pipeline.

Alternatively: Vercel dashboard → a Preview for the merge SHA → **Promote to Production**. Git still will not stay in sync until the CLI secrets exist for the next merge.

---

## How to tell skip-green from a real deploy

| | Skip (broken) | Real |
|--|---------------|------|
| Duration | 6–11s | minutes |
| Log | `VERCEL_TOKEN:` empty; warning/error about secrets | `vercel deploy --prebuilt --prod` |
| Token paste | `Must not contain: " "` (CLI 59+) | `vercel pull` then a minutes-long build |
| GitHub Deployments | Fly `production` only | Vercel Production or a new `readyforrobots.com` alias |
| Live JS | Same `index-….js` as yesterday | New hashed bundle |

`python3 scripts/harness_compile_memory.py` labels skip-green `skipped_missing_secrets` and sets `next_mission` to `vercel-production-cli-secrets`.
