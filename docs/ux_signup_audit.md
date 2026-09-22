# Signup UX Audit

## 2026-09-14

### Summary

Significant architectural shift since the last audit (2026-08-10): `/experiment` is now a legacy redirect stub; the active FIND surface is `RobotJobsWorkspace.tsx` (served at `/` via `Jobs.tsx`). `RobotJobsExperiment.tsx` is dead code — no imports. The biggest new issues are in the upsell gate: blurred-jobs and archive-lock CTAs use hardcoded `/signup?next=/pipeline` hrefs that drop all robot context and land the user in an empty CRM. The `saveJobsHandoffSnapshot` call only fires after CRM activation, not at the gate, so the signup page shows generic "Keep the jobs you picked" copy with no job names. Prior items #1–3 from Aug-10 remain open; no new regressions on those.

### Ranked recommendations

1. **[H/M]** Free-cap blur gate (`src=jobs_free_cap_blur`) uses hardcoded `/signup?next=/pipeline` — user returns to empty CRM, not their robot. Replace with a dynamic href that encodes the robot URL (or job page slug) in `next` so post-auth restore lands them back on their results. — `readyforrobots-new/client/src/components/RobotJobsWorkspace.tsx` (line ~3529)

2. **[H/M]** Archive-lock gate (`src=jobs_archive_lock`) has the same problem — `/signup?next=/pipeline` on a signed-in upsell wall that should be an upgrade wall, not a raw signup CTA. Authenticated free users should see an upgrade path, not re-signup. For anonymous users the `next` should carry the jobs context. — `readyforrobots-new/client/src/components/RobotJobsWorkspace.tsx` (line ~3473)

3. **[H/L]** `saveJobsHandoffSnapshot` is only called from `writeCrmHandoff()`, which fires during CRM activation — not when the blurred-jobs gate appears. So `readJobsHandoffSnapshot()` on `Signup.tsx` returns null at gate time, and `tasteJobs` is empty. The H1 falls back to "Keep the jobs you picked." with no robot or job names. Save a preview handoff snapshot (top 3 jobs + product name) when the free-cap gate is shown, before the user hits signup. — `readyforrobots-new/client/src/components/RobotJobsWorkspace.tsx` + `readyforrobots-new/client/src/lib/jobsHandoffSnapshot.ts`

4. **[H/L]** **Skill file list is stale** — `rfr-signup-ux-audit` skill lists `RobotJobsExperiment.tsx` as the primary file to review, but that component has no callers and is dead code. Future audit cycles reading it waste time and miss real issues. Update the skill to list `RobotJobsWorkspace.tsx` and remove `RobotJobsExperiment.tsx`. — `SKILL.md` (meta-recommendation; no UI change)

5. **[M/M]** Hardcoded gate hrefs carry no `persona`, `src`, or slug — so attribution breaks (we can't connect gate hits to content campaigns) and post-auth restoration can't personalize. Both gate CTAs should receive `src=` (already set), plus any `slug` or `submittedUrl` context carried as a `next` param, so the analytics funnel stays continuous. — `readyforrobots-new/client/src/components/RobotJobsWorkspace.tsx`

6. **[M/L]** `seeAllJobs()` fires `see_all_clicked` and sets `showAllJobs: true` — but for free users, `displayedJobs` is already sliced to 3 and calling `seeAllJobs()` has no visible effect. There is no signup prompt triggered from `seeAllJobs()` for free users. The "See all N jobs" button at line ~3545 is only shown when `hiddenCountForPaid > 0` (paid users). Free users hitting a natural "I want to see more" intent have no pathway except the blur overlay. Consider whether a "See all" CTA for free users should trigger the blur gate scroll or a signup prompt. — `readyforrobots-new/client/src/components/RobotJobsWorkspace.tsx` (~line 3540)

7. **[M/L]** *(Carry-forward from Aug-10 #3)* Magic-link completion leak: `emailInboxLinks()` in `Signup.tsx` generates inbox deep-links but they appear below the fold on the `sent` state. The highest-drop-off moment is after the magic link is sent — no work email ICP should have to scroll to find "Open Gmail / Workspace". Surface the primary inbox link as the first and largest CTA after send. — `readyforrobots-new/client/src/pages/Signup.tsx`

8. **[M/M]** *(Carry-forward from Aug-10 #1)* Pipeline gates: audit whether `pipeline_next_step` build still drops `co` and `resume=save` compared to `signupHrefForLead`. If so, every pipeline-intent signup loses the "Save {company}" personalized H1 — lowest-friction change, highest-continuity win. — `readyforrobots-new/client/src/pages/Pipeline.tsx`

9. **[L/M]** `robotJobsIntent` detection on Signup.tsx (`isJobsHandoffSrc(params.get("src"))` or `nextRaw.startsWith("/crm")`) won't match the blurred-jobs gate src (`jobs_free_cap_blur`) unless `isJobsHandoffSrc` covers that value. Verify the function accepts both `jobs_free_cap_blur` and `jobs_archive_lock` so the `robotJobsIntent` branch fires and shows the jobs-specific signup copy. — `readyforrobots-new/client/src/lib/jobsWorkflow.ts`

10. **[L/L]** `/experiment` redirect stub (`ExperimentIdeas.tsx`) redirects to `/jobs`, which in the router resolves to `Jobs.tsx`. Published content that linked to `/experiment` for the "old" FIND flow now lands on the workspace. Confirm the landing fork correctly detects the visit type (e.g., `?visit=jobs`) so inbound content links don't dump users at the landing fork rather than the FIND input. — `readyforrobots-new/client/src/pages/ExperimentIdeas.tsx` + `readyforrobots-new/client/src/lib/jobsLanding.ts`

### Out of scope this pass

No UI code changes. Volume is still early — do not redesign the gate based on n<50 gate views. Priority is continuity (items 1–3) over visual redesign.

---

## 2026-08-10

### Summary

First-pass read-only audit of `readyforrobots-new` signup conversion. Continuity helpers (`signupHrefForLead`, `co`, `resume=save`, FirstSaveNudge) are strong. Biggest signup leaks are inconsistent `co` personalization on some gates, magic-link completion friction for work emails, and competing CTAs (pricing vs save) near the decision point.

### Ranked recommendations

1. **[H/L]** Ensure every pipeline signup gate uses `signupHrefForLead` (includes `co` + `resume=save`), not a bare `/signup?next=...`. Today `pipeline_next_step` builds next manually and drops `co` personalization. — `readyforrobots-new/client/src/pages/Pipeline.tsx` (~2727)

2. **[H/M]** Surface the `co` buyer name in the primary signup headline when present (already read as `buyerCo`). Confirm the highest-visibility H1/CTA always restates "Save {co}" / unlock that lead — not only a secondary line — so the wall feels continuous. — `readyforrobots-new/client/src/pages/Signup.tsx`

3. **[H/M]** Measure and reduce magic-link drop-off: inbox deep-links exist (`emailInboxLinks`) — add a single primary "Open inbox" CTA above the fold on the `sent` state and track click → return. — `readyforrobots-new/client/src/pages/Signup.tsx`

4. **[M/L]** Unify post-auth activation: FirstSaveNudge is excellent for empty workspaces; ensure returning users with `resume=save` never see a competing pricing banner before the auto-save completes. — `Pipeline.tsx`, `FirstSaveNudge.tsx`

5. **[M/M]** Home / SIGNAL "Find Jobs for Robots" CTA should carry `src` + optional `next=/pipeline` consistently into signup so analytics can attribute SIGNAL → signup → first_save. — home CTA components + `signupHref.ts`

6. **[M/L]** `PipelinePreview` anonymous CTAs: prefer `signupHref`-style next targets with proof context (one lead name if available) over generic `/signup`. — `readyforrobots-new/client/src/components/PipelinePreview.tsx`

7. **[M/M]** OAuth vs magic-link: keep OAuth above the fold for ICP speed; make work-email path secondary but with clearer "use company email" trust copy (OEM/buyer ICP). — `Signup.tsx`

8. **[L/L]** Results FOMO banner already preserves scan URL in `next` — reuse the same pattern for Compare/pricing upgrade walls so users don't land on empty pipeline after auth. — `ResultsFomoBanner.tsx`, `Compare.tsx`

9. **[L/M]** Add a lightweight "why signup" proof strip using live HOT count already fetched on Signup (`liveProof` / `liveBuyer`) — ensure it doesn't push the form below the fold on mobile. — `Signup.tsx`

10. **[L/L]** Document the funnel contract in one place (`next`, `co`, `src`, `resume`, `plan`) for future agents — reduces regressions when new CTAs are added. — `docs/ux_signup_audit.md` / short `docs/signup_funnel_params.md` (optional follow-up)

### Out of scope this pass

No UI code changes (plan decision 2A). Hermes weekly skill `rfr-signup-ux-audit` is **retired** — do not cron it. FIND is `/`.
