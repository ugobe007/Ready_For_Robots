# 70s UI source is missing from the clone

**Date:** 2026-09-01
**Type:** blocked (no port)
**Branch:** `cursor/rfr-70s-ui-port-009b` from `origin/main` @ `b2e58e25` (#210 merged)
**Did not** port anything into `readyforrobots-new/`. **Did not** invent a 70s UI. **Did not** copy the Manus URL from #209. **Did not** Fly-deploy. **Did not** merge #195.

## Verdict

**Missing.** Cloud workspace `/workspace` does not have `docs/rfr-70s-ui-source`. It was never committed and never pushed. `.gitignore` is not the reason.

Operator pointed at local Desktop:

`/Users/robertchristopher/Desktop/Ready_For_Robots/docs/rfr-70s-ui-source`

That path is the operator machine. This clone is `/workspace`. Desktop is not here.

## What I searched

| Check | Result |
|---|---|
| Filesystem `docs/rfr-70s-ui-source` | Directory does not exist |
| `git ls-files` for `70s` / `rfr-70` | No tracked files |
| `git log --all` for that path | Empty |
| Sparse checkout | Off |
| `todo.md` anywhere in the repo | None |

Operator listed `client/`, `server/`, `shared/`, `vite.config.ts`, `ideas.md`, `todo.md` under that folder. None of those sit at `docs/rfr-70s-ui-source` in this clone.

Close cousin, **not** the 70s source: `docs/reference/readyforrobots_new_web/` (has `client/`, `server/`, `shared/`, `vite.config.ts`, `ideas.md`). That package is the older Manus SIGNAL/marketing redesign (emerald/white SaaS). It has no `todo.md`. Do not treat it as the 70s UI.

## `.gitignore` is not hiding it

Root `.gitignore` has **no** `rfr-70s-ui-source` and **no** `docs/rfr-70s*` rule. No `docs/` ignore at all.

`git check-ignore -v docs/rfr-70s-ui-source` prints nothing. If the folder existed on disk, `git add docs/rfr-70s-ui-source` would stage it. No `-f` needed unless someone adds an ignore later.

Also not ignored by:

- `readyforrobots-new/.gitignore`
- `.git/info/exclude` (empty of real rules)
- `core.excludesfile` (unset)
- `.cursorignore` (none)

So: **never added, never pushed**, not gitignored.

## Do not substitute

#209 already ported **mockup A** from https://rfr70sui-wipjpxme.manus.space into `JobsLanding`. Operator then replaced headline A with **Put your robot to work.** (#210, on `main`).

This mission asked for the **local source tree** as the source of truth (layout, components, tokens). I did not scrape Manus again. I did not restyle `/` from memory or from `docs/EXPERIMENT_MODE.md` CRT notes.

## What is already on `main` (keep this when the source lands)

- **#208** routing: `/` fork, `/?visit=jobs`, `/?visit=candidates`
- **#210** copy:
  - Headline: **Put your robot to work.**
  - Sub: Jobs for a robot you already have, or robots for work you need done. Paste a product URL — we match it to real jobs, then keep them in our CRM.
  - Two doors with explainers
- Cal off landing. No invented SKUs.
- Landing lives in `readyforrobots-new/client/src/components/JobsLanding.tsx` + `readyforrobots-new/client/src/lib/jobsLanding.ts`

**#211** FIND timeout must not bounce home (`cursor/find-timeout-no-home-a883`, still open). Next port should rebase onto `main` plus #211 if still unmerged. This docs-only branch does **not** include #211 so the PR stays a missing-source report.

## How the operator adds the source

On the Desktop clone, from repo root:

```bash
ls docs/rfr-70s-ui-source
# expect client/ server/ shared/ vite.config.ts ideas.md todo.md

# Only if git status says ignored:
# git check-ignore -v docs/rfr-70s-ui-source
# git add -f docs/rfr-70s-ui-source

git add docs/rfr-70s-ui-source
git status   # confirm node_modules / dist are still ignored
git commit -m "Add rfr-70s-ui-source as the landing visual source."
git push
```

Then tell the next agent the folder is on `main` (or a PR). Cloud agents cannot see Desktop.

Skip `node_modules/`, `dist/`, `.env`, `client/public/__manus__/version.json`. Those belong in gitignore, not in the source tree commit.

## Next agent: port after the folder exists

1. Branch from latest `origin/main`. Include #211 if unmerged.
2. Confirm `docs/rfr-70s-ui-source` is in the clone. If still missing, stop.
3. Port layout, components, and tokens into `readyforrobots-new/` landing `/`. That tree is the visual source of truth. Product routing and copy stay as above.
4. FIND must not bounce home on timeout.
5. Cal off landing. No invented SKUs. No Fly. Do not merge #195.
6. `python3 scripts/pstack_release.py` + verify-readyforrobots. After UI copy, unslop.
7. Draft PR on `cursor/rfr-70s-ui-port-009b` or a fresh `cursor/rfr-70s-ui-port-*` if this branch is already used for the report.

## Files in this commit

- `missions/2026-09-01-rfr-70s-ui/REVIEW.md` — this file only
