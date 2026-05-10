# ReadyForRobots Cursor Doc — Implementation Checklist

Source: `ReadyForRobots — Site Documentation for Cursor.md`
Checked against current repo on May 9, 2026.

## Current Repo Snapshot

- Frontend is already `Next.js 14` in `frontend/nextjs`.
- Backend is already `FastAPI` in `app/`, mounted through `app/main.py`.
- Auth/user settings are partially present via Supabase-style user profile routes in `app/api/user.py`.
- Database migrations already exist under `migrations/versions`.
- The product currently leans toward a lead-intelligence dashboard/CRM rather than the exact Manus SCOUT pipeline workflow.

## Design System

- [x] Dark product baseline exists in `frontend/nextjs/styles/globals.css`.
- [~] Update palette to match Cursor doc exactly:
  - Background: `#0d0520`
  - Purple: `#7c3aed`
  - Teal CTA: `#03DAC5`
  - Amber: `#f59e0b` / warm score accent `#FFB000`
  - Card background: `rgba(255,255,255,0.04)`
  - Border: `rgba(255,255,255,0.08)`
- [ ] Add Sora and JetBrains Mono alongside Inter.
- [ ] Replace old emerald/cyan utility styling with named SCOUT palette classes.

## Pages

| Documented Page | Current Status | Current Closest File | Action |
| --- | ---: | --- | --- |
| `/` Home | Partial | `frontend/nextjs/pages/index.js` | Keep existing live-data homepage, but align story to SCOUT: Identify → Develop → Connect, pipeline preview, SCOUT CTA. |
| `/results` | Missing | none | Add `pages/results.js` for URL scan results. |
| `/pipeline` | Partial / renamed | `pages/pipeline-results.js`, `pages/crm.js` | Decide canonical route: either add `/pipeline` alias or rename/reshape current CRM pipeline. |
| `/signals` | Missing / partial | `pages/search.js`, `pages/dashboard.js`, API lead signals | Add dedicated signal feed with filters. |
| `/how-it-works` | Missing | none | Add explainer page. |
| `/pricing` | Missing | none | Add tiers + waitlist capture. |
| `/scout-settings` | Partial | `pages/profile.js`, `app/api/user.py` | Add SCOUT-specific settings page or extend profile. |
| `/about` | Present | `pages/about.js` | Review copy against doc. |
| `/case-studies` | Missing | none | Add case studies page or defer. |
| `/faq` | Missing | none | Add FAQ or defer. |

## Components

| Documented Component | Current Status | Action |
| --- | ---: | --- |
| `Header` | Partial | Current nav uses `SiteTopNav`, `RrSiteLayout`; align labels/CTA to SCOUT. |
| `ScoutChat` | Backend partial, frontend missing | Add global chat overlay component using existing `/api/scout/chat`. |
| `ScoutWorkflowAnimation` | Missing | Add homepage hero animation. |
| `PipelinePreview` | Partial inline | Extract homepage preview into reusable component. |
| `ScoutScoreBreakdown` | Missing / partial scoring UI | Add 6-factor score bars. |
| `OutreachTimeline` | Missing / partial CRM stage | Add timeline for account/deal cards. |
| `AutonomyDial` | Missing | Add settings/how-it-works autonomy selector. |
| `ActivityFeed` | Partial via live homepage data | Extract reusable SCOUT activity feed. |
| `NextBestActions` | Missing | Add prioritized action panel. |
| `WhileYouWereAway` | Missing | Defer unless login dashboard becomes priority. |
| `ActionCard` | Missing | Add once next-best-actions is implemented. |

## Backend API Alignment

### Already Present / Partial

- [x] `GET /api/user/me` and `PUT /api/user/me` exist.
- [x] `GET /api/user/settings` and `PUT /api/user/settings` exist.
- [x] `POST /api/scout/session`, `PATCH /api/scout/session/context`, `GET /api/scout/session/{fingerprint}/history`, `POST /api/scout/chat` exist.
- [x] CRM account routes exist at `/api/crm/accounts` with outreach fields and send route.
- [x] Proposal save/list/pdf routes exist at `/api/proposals` and `/api/proposals/pdf`.
- [x] Lead/signal/dashboard APIs exist under `/api/leads`, `/api/search`, `/api/trending`, `/api/agent`, and related routers.

### Missing from Cursor Spec

- [ ] `POST /api/scout/scan-for-results`
- [ ] `POST /api/scout/scan-company`
- [ ] `POST /api/scout/find-prospects`
- [ ] `POST /api/scout/find-partners`
- [ ] `GET /api/scout/signal-update`
- [ ] `POST /api/scout/draft-outreach`
- [ ] `GET /api/pipeline`
- [ ] `POST /api/pipeline`
- [ ] `POST /api/pipeline/{id}/advance`
- [ ] `POST /api/pipeline/{id}/toggle-mode`
- [ ] `POST /api/pipeline/{id}/archive`
- [ ] `POST /api/pipeline/{id}/generate-proposal`
- [ ] `POST /api/waitlist`

### Route Decision Needed

Current backend uses `CRM` + `proposals` routes. The Cursor doc expects a dedicated `pipeline` API. Choose one:

1. **Compatibility wrapper:** add `/api/pipeline/*` routes that call the existing CRM/proposal logic.
2. **Rename/refactor:** migrate CRM account workflow into a new first-class pipeline module.

Recommendation: start with compatibility wrappers to avoid breaking existing dashboard/CRM behavior.

## Database / Migrations

### Present / Partial

- [x] `scout_sessions`, `scout_messages`, and `scout_profiles` models exist in `app/models/scout_chat.py`.
- [x] `user_settings` migration exists.
- [x] CRM tables exist: `teams`, `team_members`, `crm_accounts`, `crm_engagements`.
- [x] `pipeline_proposals` migration/API exists.

### Missing / Needs Mapping

- [ ] `pipeline_opportunities` exact table from Cursor doc is not present by name.
- [ ] `waitlist_signups` is not present.
- [~] Current `crm_accounts` can likely serve as the first pipeline-opportunity backing table if wrappers are added.
- [~] SCOUT score fields exist in current lead/scoring systems, but not in the exact `scoreReadiness`, `scoreUseCase`, `scoreRoi`, etc. shape.

## SCOUT Scoring

- [x] Current scoring APIs/models exist.
- [~] Implement documented 6-factor SCOUT score as an adapter/service:
  - Readiness: 25
  - Use Case: 20
  - ROI: 15
  - Deployment Size: 15
  - Recognizable Problem: 15
  - Customer Value: 10
- [ ] Add `get_band(total)` mapping: Hot / Warm / Developing / Monitoring.
- [ ] Add API response fields compatible with `ScoutScoreBreakdown`.

## PDF / Proposal

- [x] PDF export exists with ReportLab at `/api/proposals/pdf`.
- [~] Align output with Cursor doc branded structure:
  - Dark header band
  - RFR wordmark
  - SCOUT score badge
  - Teal signal callout
  - Amber section headers
  - Footer on every page
- [ ] Add section parsing for ALL-CAPS proposal headers.
- [ ] Add frontend split-pane editor + iframe PDF preview if not retained elsewhere.

## Recommended Implementation Order

1. **Design alignment**
   - Update global palette/classes and fonts.
   - Keep existing pages functional.

2. **SCOUT chat frontend**
   - Add `ScoutChat` overlay using existing `/api/scout/chat` and session endpoints.
   - Add global provider/button in `_app.js` or layout.

3. **Pipeline compatibility layer**
   - Add `/api/pipeline` wrappers over CRM/proposals.
   - Add `/pipeline` page route or redirect to `pipeline-results` after UI decision.

4. **Scan results flow**
   - Add `/results?url=` page.
   - Implement `/api/scout/scan-for-results`.
   - Add `Add to Pipeline` action.

5. **SCOUT skill endpoints**
   - Implement `scan-company`, `find-prospects`, `draft-outreach`, and `signal-update`.
   - Reuse existing intelligence/lead data where possible before adding new scraping.

6. **Scoring adapter**
   - Add the documented 6-factor score output and UI breakdown.
   - Keep old scoring fields as internal/provenance data.

7. **Proposal/PDF polish**
   - Upgrade PDF branding and section parsing.
   - Add live preview/editor only after pipeline route is stable.

8. **Pricing/waitlist**
   - Add `/pricing` and `POST /api/waitlist`.
   - Add `waitlist_signups` migration.

## Short Verdict

The repo is not starting from scratch. It already has the correct production stack and a substantial lead-intelligence/CRM foundation. The main gap is product-shape compatibility with the Cursor doc: exact SCOUT pages, exact `/api/scout/*` skill endpoints, `/api/pipeline/*` route naming, waitlist, and polished proposal/PDF workflow.
