# Mission: Signup acceleration sprint

**Date:** 2026-06-30
**Agent:** ProductSurface (Orchestrator may delegate)
**Status:** in_progress
**Type:** build

## Goal

Increase **signup completions** this week. Every change must move an anonymous visitor closer to creating a free account and saving their first lead. Ship at least one measurable UX improvement today and deploy it.

## North star

> ReadyForRobots wins when robot OEM reps **sign up**, see value on `/pipeline`, and **save their first lead** within the first session.

## Acceptance criteria

- [ ] Read `docs/conversion_agent_challenges.md` and pick the **highest-open** signup friction item (or a new hypothesis documented in outcome)
- [ ] Implement **one** user-visible improvement on signup, pipeline, home, or results (UI/UX/copy/workflow)
- [ ] Verify on production paths: anonymous `/pipeline` → signup CTA → `/signup?next=` → OAuth or magic link → `/pipeline` with save nudge
- [ ] `npm run build` in `readyforrobots-new/` passes
- [ ] **Autonomous mode:** commit, push to `main` (Vercel + Fly deploy). Do not wait for operator approval.
- [ ] Write `outcome.md` with before/after, conversion hypothesis, and next signup experiment
- [ ] Run `python3 scripts/harness_notify.py --mission missions/2026-06-30-signup-acceleration`

## Agent permissions (explicit)

You **may and should**:

- Edit frontend (`readyforrobots-new/`), backend entitlements/API, and harness docs
- Run tests and build locally in CI-style commands
- `git commit` + `git push` to `main` when gates pass
- Deploy via push (Vercel/Fly CI) — no manual operator step required

## Priority backlog (pick one)

1. Live social proof on `/signup` (hot lead count, companies tracked)
2. Stronger Google OAuth prominence when `?next=/pipeline`
3. Post-signup first-save modal or guided tour on pipeline
4. Mobile signup drawer parity with desktop CTAs
5. Reduce pipeline load time / empty states that kill signup intent

## Out of scope

- Force push, committing `reports/`, `.env` commits
- Lead-quality quarantine unless junk blocks trust on live pipeline slice
- Stripe billing unless signup blocker is explicitly paywall copy
