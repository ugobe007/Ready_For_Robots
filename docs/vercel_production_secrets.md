# Vercel production secrets

`readyforrobots.com` is a Vercel static site. Fly is the API. GitHub workflow **Deploy frontend to Vercel** (`.github/workflows/deploy-frontend.yml`) is the path that promotes `main` to that domain **unless** you click Promote on a Preview in the Vercel UI.

The production Vercel project is **`ready-for-robots`**. Root Directory is the **repository root** (`.`), using root `vercel.json` — not `readyforrobots-new/`.

---

## Required GitHub secret

| GitHub secret | What it is |
|---------------|------------|
| **`VERCEL_TOKEN`** | Access token from [Account Tokens](https://vercel.com/account/tokens) |

**Paste rules:** one token string. No trailing space, no newline, no quotes, no `Bearer ` prefix.

Project-scoped tokens (`vcp_…` created by picking a single project) are **valid**. Do not recreate as Full Account unless you want to.

**Revoke any token that was pasted into chat, email, or a ticket.** GitHub secret scanning and this conversation both count as exposure. Create a new token, put it in the GitHub secret, delete the old one.

Optional (the workflow fills these from the token if it can see `ready-for-robots`):

| GitHub secret | Value for this project |
|---------------|------------------------|
| **`VERCEL_ORG_ID`** | `team_i9wBQr2ur295OmAB8COX5Q0r` (team slug `ugobe07-gmailcoms-projects`) |
| **`VERCEL_PROJECT_ID`** | `prj_VHdUEY8x5jC9O2dnUdYxbDHWeTqn` (project name `ready-for-robots`) |

Copy **Team ID** / **Project ID** from Vercel Settings → General. Not the project name, not the dashboard URL.

These are **not** `DATABASE_URL`, `FLY_API_TOKEN`, or `ANTHROPIC_API_KEY`.

---

## Why `#100` re-runs fail with `.vercel` / Project Settings

That log:

```
Retrieving project…
Error: Could not retrieve Project Settings. To link your Project, remove the `.vercel` directory
```

is **not** a missing `.vercel` folder and **not** a space in the token. Vercel CLI 59 `vercel pull` also calls `GET /v2/user` and `GET /teams/{orgId}`. A **project-scoped** token returns user **404** and team **403** even when `GET /v9/projects/{id}` is **200**. Upstream: [vercel/vercel#17506](https://github.com/vercel/vercel/issues/17506).

The workflow no longer runs `vercel pull`. It runs `vercel deploy --prod` from the repo root, which works with a project-scoped token.

**Do not re-run the #100 job** after this lands. That job still contains `vercel pull`. Merge the workflow change (or Run workflow on `main` once the new YAML is on `main`).

---

## After the token is set

1. Actions → **Deploy frontend to Vercel** → Run workflow on `main` (workflow file must already include `vercel deploy --prod`, not `vercel pull`).
2. A real run is **minutes** (upload + Vercel cloud build), not 7–30 seconds.
3. Confirm `https://readyforrobots.com` HTML bundle hash changed.

The GitHub job **builds Vite in Actions**, packs `.vercel/output`, and runs `vercel deploy --prebuilt --prod`. Cloud `vercel deploy` was returning Ready while Vite was still transforming and aliasing `index-bxLpnQiT.js`. After alias, the custom domain can still serve that hash for a few seconds (edge HIT). Smoke checks the deployment URL first, then polls `readyforrobots.com`.

`setup-flyctl@1.5` fails on Node 24 GitHub runners (`flyctl: command not found`). Deploy.yml uses `setup-flyctl@master`. The **Fly.io** GitHub check is Fly’s own Git integration and can go red even when `https://ready-2-robot.fly.dev/health` is 200.

Framework Settings: leave **Other** and keep Override toggles **off**. Do not Save the `npm run build` / `public` placeholders.

Alternatively: Vercel dashboard → a Preview for the merge SHA → **Promote to Production**.

---

## How to tell skip-green / pull-fail from a real deploy

| | Skip (broken) | Pull fail (project-scoped token) | Real |
|--|---------------|----------------------------------|------|
| Duration | 6–11s | ~30s | minutes |
| Log | `VERCEL_TOKEN` empty | `Could not retrieve Project Settings` | `vercel deploy --prod` then a Production URL |
| Live JS | Same `index-….js` | Unchanged (or a bad promote) | New hashed bundle |

`python3 scripts/harness_compile_memory.py` labels skip-green `skipped_missing_secrets`.
