# Signup UX Audit

## 2026-08-10

### Summary

First-pass read-only audit of `readyforrobots-new` signup conversion. Continuity helpers (`signupHrefForLead`, `co`, `resume=save`, FirstSaveNudge) are strong. Biggest signup leaks are inconsistent `co` personalization on some gates, magic-link completion friction for work emails, and competing CTAs (pricing vs save) near the decision point.

### Ranked recommendations

1. **[H/L]** Ensure every pipeline signup gate uses `signupHrefForLead` (includes `co` + `resume=save`), not a bare `/signup?next=...`. Today `pipeline_next_step` builds next manually and drops `co` personalization. — `readyforrobots-new/client/src/pages/Pipeline.tsx` (~2727)

2. **[H/M]** Surface the `co` buyer name in the primary signup headline when present (already read as `buyerCo`). Confirm the highest-visibility H1/CTA always restates “Save {co}” / unlock that lead — not only a secondary line — so the wall feels continuous. — `readyforrobots-new/client/src/pages/Signup.tsx`

3. **[H/M]** Measure and reduce magic-link drop-off: inbox deep-links exist (`emailInboxLinks`) — add a single primary “Open inbox” CTA above the fold on the `sent` state and track click → return. — `readyforrobots-new/client/src/pages/Signup.tsx`

4. **[M/L]** Unify post-auth activation: FirstSaveNudge is excellent for empty workspaces; ensure returning users with `resume=save` never see a competing pricing banner before the auto-save completes. — `Pipeline.tsx`, `FirstSaveNudge.tsx`

5. **[M/M]** Home / SIGNAL “Find Jobs for Robots” CTA should carry `src` + optional `next=/pipeline` consistently into signup so analytics can attribute SIGNAL → signup → first_save. — home CTA components + `signupHref.ts`

6. **[M/L]** `PipelinePreview` anonymous CTAs: prefer `signupHref`-style next targets with proof context (one lead name if available) over generic `/signup`. — `readyforrobots-new/client/src/components/PipelinePreview.tsx`

7. **[M/M]** OAuth vs magic-link: keep OAuth above the fold for ICP speed; make work-email path secondary but with clearer “use company email” trust copy (OEM/buyer ICP). — `Signup.tsx`

8. **[L/L]** Results FOMO banner already preserves scan URL in `next` — reuse the same pattern for Compare/pricing upgrade walls so users don’t land on empty pipeline after auth. — `ResultsFomoBanner.tsx`, `Compare.tsx`

9. **[L/M]** Add a lightweight “why signup” proof strip using live HOT count already fetched on Signup (`liveProof` / `liveBuyer`) — ensure it doesn’t push the form below the fold on mobile. — `Signup.tsx`

10. **[L/L]** Document the funnel contract in one place (`next`, `co`, `src`, `resume`, `plan`) for future agents — reduces regressions when new CTAs are added. — `docs/ux_signup_audit.md` / short `docs/signup_funnel_params.md` (optional follow-up)

### Out of scope this pass

No UI code changes (plan decision 2A). Hermes weekly skill `rfr-signup-ux-audit` should refresh this file each Monday.
