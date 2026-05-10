# `rfr_cursor_package` → production port checklist

**Source:** `Ready_For_Robots/rfr_cursor_package/`  
**Target SPA:** `readyforrobots-new/client/src/`  
**Target API:** `app/` (FastAPI), `worker/` as needed  

**Legend:** `[x]` done or present in repo · `[ ]` not done / needs work · **(ref)** reference-only — do not copy verbatim into production tree

---

## Where we are now (review snapshot)

**Shipping frontend:** Vite app in **`readyforrobots-new/`** (not legacy `frontend/nextjs/`). Docker/Fly build copies **`dist/public` → `static/`** and serves it from FastAPI.

**Done recently**

- [x] Core marketing routes: Home, How It Works, Pipeline, Signals, Results, Pricing, NotFound
- [x] Auth: Login, Profile, Supabase session, CRM + Admin stubs, `AuthProvider`, header nav
- [x] Pipeline list loads from **`GET /api/leads`**; hero spotlight uses **`GET /api/leads/homepage`**
- [x] **`ScoutWorkflowAnimation`** ported and shown on **Home** (after pipeline preview) and **How It Works**
- [x] Public assets: **`client/public/logo-r.png`**, favicons (copied from Next `public/`)
- [x] **`docs/rfr_cursor_package_port_checklist.md`** (this file) — port tracking

**In progress / gaps**

- [x] **SCOUT chat API (v1):** `POST /api/scout/chat`, `POST /api/scout/session`, `PATCH /api/scout/session/context`, `GET /api/scout/session/{fingerprint}/history` — persistence tables `scout_sessions`, `scout_messages`, `scout_profiles` (migration `e2f3a4b5c6d7`). Uses **`OPENAI_API_KEY`** + optional **`SCOUT_CHAT_MODEL`** (default `gpt-4o-mini`).
- [ ] **`ScoutChat`** UI in `readyforrobots-new`: replace tRPC with **`fetch(\`${getApiBase()}/api/scout/...\`)`** (streaming optional next)
- [ ] **Scout settings parity:** dedicated **`ScoutSettings`** page or full merge into Profile + **`PUT /api/user/settings`** for autonomy / PDF sender fields
- [ ] **Results page:** inferred contact email + “Add to pipeline” per prototype **`Results.tsx`**
- [ ] **Pipeline depth:** Kanban + proposal generate / PDF preview / send — align with package **`Pipeline.tsx`** + verify **`app/api/proposals.py`** PDF matches **`proposalPdf.ts`** branding/sections
- [ ] **Support pages:** About, Case Studies, FAQ (or keep FAQ on Home only)
- [ ] **Hooks/data:** `useFadeUp`, `readyForRobotsMockData` not ported
- [ ] **Activity feed / Next best / While you were away:** components exist as stubs — need real API or events

---

## Shared (`rfr_cursor_package/shared/`)

- [ ] Merge or diff `shared/types.ts` → `readyforrobots-new/shared/` + `client/src/types/readyForRobots.ts`
- [ ] Compare `shared/const.ts` with `readyforrobots-new/shared/const.ts` and `client/src/const.ts`

---

## Frontend — pages (`rfr_cursor_package/frontend/pages/`)

- [x] `Home.tsx` → `client/src/pages/Home.tsx` (evolved; includes `HeroLivePipeline`, `ScoutWorkflowAnimation`, SCOUT copy)
- [x] `HowItWorks.tsx` → `client/src/pages/HowItWorks.tsx` (includes `ScoutWorkflowAnimation`)
- [x] `Pipeline.tsx` → `client/src/pages/Pipeline.tsx` (API-backed; extend for Kanban / PDF / outreach from package)
- [x] `Signals.tsx` → `client/src/pages/Signals.tsx`
- [x] `Results.tsx` → `client/src/pages/Results.tsx` (exists — [ ] feature parity: emails, add-to-pipeline)
- [x] `Pricing.tsx` → `client/src/pages/Pricing.tsx`
- [x] `NotFound.tsx` → `client/src/pages/NotFound.tsx`
- [ ] `ScoutSettings.tsx` → new `ScoutSettings.tsx` **or** extend `Profile.tsx` + settings API
- [ ] `About.tsx` → new route or fold into Home
- [ ] `CaseStudies.tsx` → new route if needed
- [ ] `FAQ.tsx` → new route (Home already has FAQ section)
- [ ] `ComponentShowcase.tsx` → optional dev-only route

**Extra routes in app (not in Manus package list):** `[x]` Login, Profile, CRM, Admin — wired in `App.tsx`.

**Routing reminder:** any new page above needs `App.tsx` + `Header.tsx` / nav updates.

---

## Frontend — components (`rfr_cursor_package/frontend/components/`)

- [x] `ScoutWorkflowAnimation.tsx` → `client/src/components/ScoutWorkflowAnimation.tsx` (Home + How It Works)
- [ ] `ScoutChat.tsx` → port; replace tRPC with `fetch(\`${getApiBase()}/api/agent/chat\`)` once route exists
- [ ] `ScoutScoreBreakdown.tsx` → port or mount existing file if added; use on Pipeline / Results with score payload
- [ ] `OutreachTimeline.tsx` → port; CRM / deal detail
- [x] `PipelinePreview.tsx` → present — keep in sync with package if design changes
- [x] `AutonomyDial.tsx` → file present — [ ] wire to settings / `PUT /api/user/settings`
- [x] `ActivityFeed.tsx` → stub — [ ] real events (API or websocket)
- [x] `NextBestActions.tsx` → stub — [ ] backend suggestions
- [x] `WhileYouWereAway.tsx` → stub — [ ] “since last visit” summary endpoint + UI
- [x] `ActionCard.tsx` → present
- [ ] `AIChatBox.tsx` → merge with ScoutChat or drop
- [x] `Header.tsx` → present (`/logo-r.png`, not `/manus-storage/…`)
- [x] `SecondaryNav.tsx` → present
- [ ] `DashboardLayout.tsx` / `DashboardLayoutSkeleton.tsx` → optional logged-in shell
- [x] `ErrorBoundary.tsx` → present
- [ ] `ManusDialog.tsx` → audit usage; remove if dead
- [ ] `Map.tsx` → gate Forge URL on env; production-safe defaults

---

## Frontend — hooks, contexts, data, lib, types

- [x] `hooks/useComposition.ts`
- [ ] `hooks/useFadeUp.ts` → not in `readyforrobots-new` yet
- [x] `hooks/useMobile.tsx`
- [x] `hooks/usePersistFn.ts`
- [x] `contexts/ThemeContext.tsx`
- [ ] `data/readyForRobotsMockData.ts` → optional `client/src/data/` or tests-only
- [ ] **(ref)** `lib/trpc.ts` — do not port; use `getApiBase`, `liveFetchInit`, `fetch`
- [x] `lib/utils.ts` (`cn`, etc.)
- [x] `types/readyForRobots.ts` — present — [ ] diff field-by-field with package
- [ ] `frontend/index.css` vs `client/src/index.css` — token pass (e.g. teal `#03DAC5` from prototype; partial use in `ScoutWorkflowAnimation`)
- [ ] `frontend/const.ts` vs `client/src/const.ts` — compare
- [x] `App.tsx` / routing + `main.tsx` entry

---

## Frontend — assets

- [x] Use `readyforrobots-new/client/public/` for logos and favicons (package has no `public/`; avoid `/manus-storage/…`)
- [ ] Optional: mirror CloudFront marketing WebPs into `public/` if CDN URLs ever break

---

## Server (`rfr_cursor_package/server/`) → FastAPI

- [ ] **(ref)** `routers.ts` — map each tRPC procedure to `app/api/*.py`; fill gaps (notably **SCOUT chat**)
- [ ] **(ref)** `scoring.ts` — overlap with `app/services/lead_filter.py`, `scoring_public.py`; avoid duplicating rules
- [x] PDF / proposals — `app/api/proposals.py` has `proposal_pdf` — [ ] parity with `proposalPdf.ts` (layout, regex sections, logo)
- [ ] **(ref)** `scoutDb.ts`, `db.ts`, `schema/*`, `storage.ts` — align with SQLAlchemy models + existing storage patterns
- [ ] **(ref)** `server/index.ts` (Express) — PDF registration reference only; HTTP stays FastAPI

---

## Docs in package

- [ ] Cross-check `rfr_cursor_package/docs/BACKEND_IMPLEMENTATION.md` with implemented FastAPI modules

---

## Suggested port order (unchanged)

1. High visibility: ~~ScoutWorkflowAnimation~~ done; next **`ScoutScoreBreakdown`**, **`OutreachTimeline`** on Pipeline / Results  
2. Revenue path: **`ScoutChat`** + **`POST /api/agent/chat`**, proposal PDF visual parity  
3. Settings: **`ScoutSettings`** + persisted **`user_settings`**  
4. Results: contact inference + CTA  
5. Optional: **`DashboardLayout`** for unified logged-in shell  

---

*Update checkboxes here as work lands. Last expanded: status snapshot + GitHub-style tasks.*
