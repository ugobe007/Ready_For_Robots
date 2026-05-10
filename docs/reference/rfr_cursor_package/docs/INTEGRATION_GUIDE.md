# ReadyForRobots — Manus Prototype → Cursor Integration Guide

This package contains all the new features, components, pages, and server logic built in the Manus prototype that are **not yet in your GitHub repo**. Use this as a reference to port each piece into your Next.js + FastAPI + Supabase stack in Cursor.

---

## What's in This Package

```
frontend/
  pages/            ← 12 full page components (React/TSX)
  components/       ← 18 custom components including animations and AI chat
  hooks/            ← Custom React hooks
  contexts/         ← ThemeContext
  types/            ← TypeScript types for RFR domain models
  data/             ← Mock data and seed structures
  lib/              ← tRPC client binding (reference only — you use fetch/apiBase.js)
  App.tsx           ← Route definitions and layout wiring
  index.css         ← Full design system: dark theme, brand tokens, typography
  const.ts          ← App constants

server/
  routers.ts        ← All tRPC procedures (reference for API logic to port to FastAPI)
  db.ts             ← Database query helpers
  scoring.ts        ← SCOUT scoring engine (signal scoring, qualification logic)
  proposalPdf.ts    ← PDF generation with @react-pdf/renderer
  scoutDb.ts        ← SCOUT AI agent database helpers
  storage.ts        ← S3 file storage helpers
  index.ts          ← Express server with PDF endpoint registered
  schema/
    schema.ts       ← Full Drizzle ORM schema (reference for Supabase table design)
    relations.ts    ← Drizzle relations

shared/
  types.ts          ← Shared TypeScript types
  const.ts          ← Shared constants

docs/
  INTEGRATION_GUIDE.md  ← This file
```

---

## Key Features to Port

### 1. SCOUT Workflow Animation (`ScoutWorkflowAnimation.tsx`)
A multi-step animated pipeline visualization showing signal detection → qualification → outreach. Uses CSS keyframes and Framer Motion. Drop into your homepage or how-it-works page.

**Port to**: `frontend/nextjs/components/ScoutWorkflowAnimation.jsx`

### 2. SCOUT Chat (`ScoutChat.tsx`)
Full AI chat interface with streaming support, message history, and markdown rendering. Powered by the `trpc.scout.chat` procedure on the server. The FastAPI equivalent is `POST /api/agent/chat`.

**Port to**: `frontend/nextjs/components/ScoutChat.jsx`

**Backend**: The chat logic in `server/routers.ts` under `scout.chat` shows the LLM prompt structure. Port to `app/api/agent.py`.

### 3. Pipeline Page (`pages/Pipeline.tsx`)
Full Kanban-style pipeline with:
- Deal cards with SCOUT Score, signal tags, contact email (mailto link)
- Outreach draft display with "Approve & Send" button
- **Generate Proposal** button → LLM-generated structured proposal
- **Preview PDF** button → split-pane editor + iframe PDF preview
- **Download PDF** button → branded PDF with logo, section headers

**Port to**: `frontend/nextjs/pages/pipeline-results.js` (extend existing)

**Backend**: `POST /api/proposal/pdf` endpoint in `server/index.ts` + `server/proposalPdf.ts`

### 4. Results Page (`pages/Results.tsx`)
Signal scan results with:
- Prospect cards showing company, signal type, SCOUT Score
- Inferred contact email per prospect
- "Add to Pipeline" button

**Port to**: `frontend/nextjs/pages/pipeline-results.js` or new `results.js`

### 5. Signals Page (`pages/Signals.tsx`)
Live signal feed with filtering by signal type, confidence score, and industry vertical.

**Port to**: `frontend/nextjs/pages/dashboard.js` (extend existing signals section)

### 6. Scout Settings Page (`pages/ScoutSettings.tsx`)
User configuration for:
- Robot category / vertical
- Target company size and geography
- Autonomy level (Manual / Co-Pilot / Auto)
- Sender name, title, company for PDF personalisation

**Port to**: `frontend/nextjs/pages/profile.js` (extend existing)

### 7. SCOUT Score Breakdown (`ScoutScoreBreakdown.tsx`)
Visual breakdown of the 4-factor SCOUT Score: labor pain, expansion stage, automation fit, timing. Animated progress bars with color coding.

**Port to**: `frontend/nextjs/components/ScoutScoreBreakdown.jsx`

### 8. Outreach Timeline (`OutreachTimeline.tsx`)
Visual timeline of outreach stages: Signal Detected → Qualified → Draft Ready → Intro Sent → Meeting Booked.

**Port to**: `frontend/nextjs/components/OutreachTimeline.jsx`

### 9. Pipeline Preview (`PipelinePreview.tsx`)
Compact pipeline summary widget for the homepage showing live deal counts by stage.

**Port to**: `frontend/nextjs/components/PipelinePreview.jsx`

### 10. Autonomy Dial (`AutonomyDial.tsx`)
Animated dial component for selecting SCOUT autonomy level (Manual / Co-Pilot / Auto).

**Port to**: `frontend/nextjs/components/AutonomyDial.jsx`

### 11. Activity Feed (`ActivityFeed.tsx`)
Real-time feed of SCOUT actions: signals detected, leads qualified, drafts generated, emails sent.

**Port to**: `frontend/nextjs/components/ActivityFeed.jsx`

### 12. Next Best Actions (`NextBestActions.tsx`)
AI-recommended next actions panel: "Reach out to Acme Corp — labor shortage signal detected 2h ago."

**Port to**: `frontend/nextjs/components/NextBestActions.jsx`

### 13. While You Were Away (`WhileYouWereAway.tsx`)
Summary card shown on login: "Since your last visit, SCOUT found 12 new signals and qualified 3 leads."

**Port to**: `frontend/nextjs/components/WhileYouWereAway.jsx`

### 14. Action Card (`ActionCard.tsx`)
Reusable card component for displaying a recommended action with priority badge, company name, signal context, and CTA button.

**Port to**: `frontend/nextjs/components/ActionCard.jsx`

---

## SCOUT Scoring Engine (`server/scoring.ts`)

This is the core signal qualification logic. It scores each prospect on 4 dimensions:

| Dimension | Weight | Signal sources |
|---|---|---|
| Labor Pain | 30% | Job postings, OSHA filings, turnover signals |
| Expansion Stage | 25% | Real estate permits, earnings calls, press releases |
| Automation Fit | 25% | Industry vertical, company size, existing tech stack |
| Timing | 20% | Signal recency, budget cycle, RFP proximity |

**Port to**: `app/services/scoring.py` in your FastAPI backend.

---

## Contact Email Inference Logic

In `server/routers.ts`, the `skillScanForResults` procedure infers contact emails by signal type:

| Signal Type | Inferred Email Prefix |
|---|---|
| procurement / supply chain | `purchasing@` |
| partnership / BD | `bd@` |
| expansion / real estate | `operations@` |
| hiring / labor | `hr@` |
| default | `info@` |

**Port to**: `app/services/contact_inference.py`

---

## PDF Generation (`server/proposalPdf.ts`)

Uses `@react-pdf/renderer` (Node.js) to generate a branded PDF with:
- Dark header band with RFR logo
- "SALES PROPOSAL" label + date
- Company name, SCOUT Score, signal tags
- Teal-bordered buying signal callout box
- 6 sections with amber accent bars: Executive Summary, Opportunity, Solution, Expected Outcomes, Next Steps, About
- Branded footer on every page

**Python equivalent**: Use `reportlab` or `weasyprint` in FastAPI. The section parsing logic (splitting proposal text on ALL-CAPS headers) is in `proposalPdf.ts` — port the regex to Python.

---

## Design System (`frontend/index.css`)

The full design system is in `index.css`. Key tokens:

| Token | Value | Usage |
|---|---|---|
| Background | `#0d0520` | Page background |
| Brand purple | `#7c3aed` | Headlines, brand accents |
| Teal / CTA | `#03DAC5` | Action buttons, live indicators |
| Amber | `#f59e0b` | SCOUT Score, warnings, PDF accents |
| Font: Display | Sora | Hero headlines |
| Font: Body | Inter | All body text |
| Font: Data | JetBrains Mono | Scores, numbers, code |

Copy `index.css` into your Next.js `styles/globals.css` and add the Google Fonts CDN links to `_document.js`:

```html
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
```

---

## Conversion Notes: TSX → JSX

All files in this package are TypeScript (`.tsx`). To use in your Next.js JSX project:

1. Rename `.tsx` → `.jsx`
2. Remove all `: TypeName` type annotations
3. Remove `interface` and `type` declarations (or move to a `.d.ts` file)
4. Replace `trpc.*` calls with `fetch()` calls to your FastAPI endpoints via `getApiBase()`
5. Replace `useAuth()` with your Supabase auth hook

---

## Deployment Checklist

- [ ] Copy `index.css` tokens into `styles/globals.css`
- [ ] Add Google Fonts CDN to `_document.js`
- [ ] Port `ScoutWorkflowAnimation` to JSX and add to homepage
- [ ] Port `ScoutChat` to JSX and wire to `POST /api/agent/chat`
- [ ] Port `Pipeline.tsx` to JSX and wire to CRM/pipeline API endpoints
- [ ] Port `scoring.ts` to `app/services/scoring.py`
- [ ] Port contact email inference to `app/services/contact_inference.py`
- [ ] Add PDF generation endpoint to FastAPI using `weasyprint` or `reportlab`
- [ ] Add `RESEND_API_KEY` to Fly.dev secrets and wire send-outreach endpoint
- [ ] Run Alembic migrations for proposals, user_settings, outreach fields
