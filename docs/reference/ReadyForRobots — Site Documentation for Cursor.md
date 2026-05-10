# ReadyForRobots — Site Documentation for Cursor

> **Purpose:** This document describes every page, component, API endpoint, database table, and data flow in the Manus prototype. Use it as the authoritative reference when porting features to your Next.js + FastAPI + Supabase stack in Cursor.

---

## Table of Contents

1. [Overview & Architecture](#1-overview--architecture)
2. [Design System](#2-design-system)
3. [Pages](#3-pages)
4. [Components](#4-components)
5. [API Layer (tRPC Procedures → FastAPI Equivalents)](#5-api-layer)
6. [Database Schema](#6-database-schema)
7. [SCOUT Scoring Engine](#7-scout-scoring-engine)
8. [PDF Generation](#8-pdf-generation)
9. [AI / LLM Flows](#9-ai--llm-flows)
10. [Data Flows End-to-End](#10-data-flows-end-to-end)
11. [Porting Checklist for Cursor](#11-porting-checklist-for-cursor)

---

## 1. Overview & Architecture

ReadyForRobots is an **AI-powered sales development platform** for robotics companies. The core product is **SCOUT** — an AI agent that monitors 150+ signal sources, qualifies prospects using a 6-factor scoring model, drafts personalized outreach, and manages the full pipeline from signal detection to meeting booked.

### Manus Prototype Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + TypeScript + Tailwind CSS 4 |
| Routing | Wouter (client-side SPA) |
| API | tRPC 11 over Express 4 |
| Database | MySQL/TiDB via Drizzle ORM |
| AI | LLM via `invokeLLM()` helper (OpenAI-compatible) |
| PDF | `@react-pdf/renderer` (server-side Node.js) |
| Auth | Manus OAuth (JWT session cookie) |

### Your Production Stack (GitHub repo)

| Layer | Technology |
|---|---|
| Frontend | Next.js (static export) |
| API calls | `fetch()` via `lib/apiBase.js` → Fly.dev |
| Backend | Python FastAPI + Celery |
| Database | Supabase (Postgres) + Alembic migrations |
| Auth | Supabase Auth |
| Deployment | Vercel (frontend) + Fly.dev (backend) |

### Key Difference for Porting

Every `trpc.X.Y.useQuery/useMutation` call in the prototype maps to a `fetch(getApiBase() + "/api/X/Y", ...)` call in your Next.js pages. Every tRPC procedure maps to a FastAPI endpoint.

---

## 2. Design System

### Color Palette

| Token | Hex | Usage |
|---|---|---|
| Background | `#0d0520` | Page background, all sections |
| Brand Purple | `#7c3aed` | Headlines, nav accents, brand elements |
| Teal / CTA | `#03DAC5` | Primary CTA buttons, live indicators, teal accents |
| Amber | `#f59e0b` | SCOUT Score badges, warnings, PDF section headers |
| Red / Hot | `#ef4444` | HOT score band, urgent signals |
| Purple Light | `#a78bfa` | Secondary accents, developing band |
| White | `#ffffff` | Primary text |
| White/50 | `rgba(255,255,255,0.5)` | Secondary text |
| White/25 | `rgba(255,255,255,0.25)` | Tertiary text, placeholders |
| Card BG | `rgba(255,255,255,0.04)` | Card backgrounds |
| Border | `rgba(255,255,255,0.08)` | Card borders, dividers |

### Typography

| Role | Font | Weight | Usage |
|---|---|---|---|
| Display / Hero | Sora | 700–800 | Hero headlines, section titles |
| Body | Inter | 400–600 | All body text, labels, nav |
| Data / Code | JetBrains Mono | 400–600 | Scores, numbers, signal data |

**Google Fonts CDN** (add to `_document.js`):
```html
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
```

### Score Band Colors

| Band | Score Range | Color |
|---|---|---|
| Hot | 80–100 | `#ef4444` (red) |
| Warm | 60–79 | `#FFB000` (amber) |
| Developing | 40–59 | `#a78bfa` (purple) |
| Monitoring | 0–39 | `rgba(255,255,255,0.35)` |

---

## 3. Pages

### `/` — Home (`pages/Home.tsx`)

**Purpose:** Marketing homepage and primary conversion funnel.

**Sections (top to bottom):**

1. **Hero** — "Stop prospecting. Start closing." headline with animated SCOUT Live Pipeline card (right column). The pipeline card shows the Identify → Develop → Connect stage tabs and a live FIT_SCORE breakdown for a sample prospect. CTA: "Activate Pipeline" button + "Talk to SCOUT" inline link.

2. **How It Works** — Three-step grid: (01) We find the signals → (02) We qualify the prospects → (03) We deliver ready actions.

3. **Live Pipeline** — `PipelinePreview` component showing 5 live prospect cards with company name, industry tag, signal description, SCOUT Score badge (HOT/WARM), and timestamp. "Build my pipeline" CTA at the bottom.

4. **Meet SCOUT** — Feature grid (6 capabilities) + SCOUT status widget (150+ sources, 24/7, 14 signal types, <48h signal-to-outreach) + live activity feed (last 3 SCOUT actions).

5. **About / Stats** — 500+ robot deals influenced, 60+ robotics companies served, 12 verticals covered, 150+ signal sources.

6. **Real Signals. Real Deals.** — Two case study cards: Hospitality (15-robot deployment) and Logistics ($2.4M contract), each showing the signal → action → outcome flow.

7. **Before vs. After** — Side-by-side comparison table: cold prospecting vs. SCOUT-powered outreach (7 rows).

8. **Testimonials** — 3 quote cards from VP of Sales, Director of BD, Head of Sales.

9. **CTA Footer** — "Let SCOUT run your pipeline." with "Activate Pipeline" button.

**Key interactions:**
- "Scan URL" button in header → navigates to `/results?url=<encoded-url>`
- "Talk to SCOUT" button → opens the SCOUT chat overlay (`ScoutChat` context)
- Pipeline preview cards are clickable → navigates to `/pipeline`

---

### `/results` — Results (`pages/Results.tsx`)

**Purpose:** Shows AI-generated prospect scan results after a user submits their company URL.

**How it works:**
1. Reads `?url=` query param from the URL
2. Calls `trpc.scout.scanForResults` with the URL → returns 5–8 prospects
3. Each prospect card shows: company name, industry tag, signal description, SCOUT Score (0–100), inferred contact email, outreach angle
4. "Add to Pipeline" button on each card → calls `trpc.pipeline.add` → navigates to `/pipeline`

**Prospect card fields:**
- Company name + industry vertical tag
- Signal description (e.g., "Labor shortage filing + 3 DC expansions")
- SCOUT Score badge (color-coded by band)
- Inferred contact email (e.g., `purchasing@company.com`) with mailto link
- Outreach angle (1-sentence reason to reach out)
- "Add to Pipeline" button

**FastAPI equivalent:** `POST /api/scout/scan-for-results` — accepts `{ url: string }`, returns array of prospects.

---

### `/pipeline` — Pipeline (`pages/Pipeline.tsx`)

**Purpose:** Kanban-style deal management board. The core operational view for sales teams.

**Layout:** Single-column list of deal cards, grouped by outreach stage.

**Deal Card fields:**
- Company name + robot category tag + SCOUT Score badge
- Signal description
- Contact email with mailto link (inferred or user-provided)
- Outreach stage indicator (pending → intro_scheduled → intro_sent → followup_sent → meeting_booked)
- Pipeline mode badge: Assisted (user approves before send) or Autopilot (SCOUT sends automatically)
- Outreach draft (expandable) with "Approve & Send" button
- **Generate Proposal** button (amber) → opens proposal modal
- **Preview PDF** button → opens split-pane editor + iframe PDF preview
- **Download PDF** button → downloads branded PDF

**Proposal Modal:**
- LLM generates a 350–500 word structured proposal with 6 sections: Executive Summary, Opportunity, Solution, Expected Outcomes, Next Steps, About
- Split-pane layout: left = text editor with amber-highlighted section headers, right = live PDF iframe preview
- "Update Preview" button re-renders the PDF from edited text
- "Unsaved changes" badge appears when editor content differs from last render
- "Download PDF" always downloads the most recently rendered version

**Pipeline actions:**
- Advance stage (moves deal to next outreach stage)
- Toggle mode (Assisted ↔ Autopilot)
- Archive deal

**FastAPI equivalents:**
- `GET /api/pipeline` — list all deals for current user
- `POST /api/pipeline` — add new deal
- `POST /api/pipeline/{id}/advance` — advance outreach stage
- `POST /api/pipeline/{id}/toggle-mode` — toggle Assisted/Autopilot
- `POST /api/pipeline/{id}/archive` — archive deal
- `POST /api/pipeline/{id}/generate-proposal` — generate LLM proposal
- `POST /api/proposal/pdf` — generate branded PDF (returns binary PDF)

---

### `/signals` — Signals (`pages/Signals.tsx`)

**Purpose:** Live signal feed showing all buying signals detected across monitored companies.

**Features:**
- Filter by signal type (labor shortage, expansion, CapEx, OSHA, hiring, earnings call, real estate)
- Filter by confidence score (HOT / WARM / Developing)
- Filter by industry vertical
- Each signal card: company name, signal type badge, signal description, detected timestamp, confidence score, "Add to Pipeline" button

**FastAPI equivalent:** `GET /api/signals?type=&band=&vertical=`

---

### `/how-it-works` — How It Works (`pages/HowItWorks.tsx`)

**Purpose:** Detailed explainer page for the SCOUT workflow.

**Sections:**
1. Three-step animated workflow (Find → Qualify → Deliver)
2. Signal source breakdown (150+ sources across 14 categories)
3. Scoring methodology (6-factor SCOUT Score explanation)
4. Autonomy levels (Manual / Co-Pilot / Auto) with `AutonomyDial` component
5. CTA to activate pipeline

---

### `/pricing` — Pricing (`pages/Pricing.tsx`)

**Purpose:** Pricing tiers and waitlist capture.

**Tiers:**
- **Preview** — Free, limited signals, manual only
- **Growth** — $X/month, full signals, Co-Pilot mode, outreach drafts
- **Enterprise** — Custom, full Autopilot, dedicated SCOUT agent

**Waitlist form:** Name + email + tier + robot category → calls `trpc.waitlist.capture` → stores in `waitlistSignups` table + notifies owner.

**FastAPI equivalent:** `POST /api/waitlist` — accepts `{ name, email, tier, robotCategory, companyUrl }`

---

### `/scout-settings` — Scout Settings (`pages/ScoutSettings.tsx`)

**Purpose:** User configuration for SCOUT's behavior.

**Settings sections:**
1. **Robot Category** — what type of robots the user sells (warehouse AMR, service, industrial arm, etc.)
2. **Target Verticals** — which industries to focus on (logistics, hospitality, healthcare, etc.)
3. **Target Geography** — US regions or global
4. **Autonomy Level** — Manual (user does everything), Co-Pilot (SCOUT drafts, user approves), Auto (SCOUT sends automatically)
5. **Outreach Persona** — On Behalf (sends as user) or Independent (sends as SCOUT)
6. **Sender Identity** — Name, title, company name, email for PDF personalisation and outreach attribution

**FastAPI equivalents:**
- `GET /api/settings` — get current user settings
- `PUT /api/settings` — save settings

---

### `/about` — About (`pages/About.tsx`)

**Purpose:** Company story, team background, and mission statement.

---

### `/case-studies` — Case Studies (`pages/CaseStudies.tsx`)

**Purpose:** Detailed deal stories showing signal → action → outcome for real robotics sales.

---

### `/faq` — FAQ (`pages/FAQ.tsx`)

**Purpose:** Answers to common questions about SCOUT, signal sources, and pricing.

---

## 4. Components

### `Header.tsx`
Top navigation bar present on all pages. Contains:
- RFR logo (links to `/`)
- Nav links: Pipeline, Signals, How It Works, Pricing
- "LIVE" indicator badge (animated green pulse)
- "Scan URL" CTA button (teal, opens URL input or navigates to `/results`)
- Hamburger menu for mobile (expands full nav with all links including About, Case Studies, FAQ, SCOUT Settings)

---

### `ScoutChat.tsx`
Global AI chat overlay. Wraps the entire app as a context provider (`ScoutChatProvider`). The "Talk to SCOUT" floating button (bottom-right, teal) opens a full-screen chat modal.

**How it works:**
1. User opens chat → loads or creates a SCOUT session (`trpc.scout.getSession`)
2. User sends message → `trpc.scout.chat` procedure → LLM generates response as SCOUT persona
3. Messages are persisted in `scoutMessages` table
4. SCOUT can reference the user's pipeline and settings in its responses

**SCOUT persona:** Direct, data-driven, slightly dry. Speaks in specifics. Knows the user's robot category and target verticals from their settings.

**FastAPI equivalent:** `POST /api/scout/chat` — accepts `{ sessionId, message }`, returns `{ reply, sessionId }`

---

### `ScoutWorkflowAnimation.tsx`
Animated visualization of the SCOUT pipeline on the homepage. Shows three stages cycling through:
- **IDENTIFY** — signal detection animation (pulsing data points)
- **DEVELOP** — qualification scoring animation (score bar filling)
- **CONNECT** — outreach draft animation (email composing)

Uses CSS keyframes and `requestAnimationFrame` for smooth transitions. No external animation library required.

---

### `PipelinePreview.tsx`
Compact pipeline widget used on the homepage. Shows 5 live prospect rows with:
- Company avatar (initials), name, industry tag
- Signal description (truncated)
- SCOUT Score badge + HOT/WARM label
- Timestamp (e.g., "2m ago")

Data source: `trpc.scout.getSignalUpdate` — returns mock/live signal data.

---

### `ScoutScoreBreakdown.tsx`
Visual breakdown of the 6-factor SCOUT Score. Shows:
- Total score (large number, color-coded by band)
- Six factor bars: Readiness (0–25), Use Case (0–20), ROI (0–15), Deployment Size (0–15), Recognizable Problem (0–15), Customer Value (0–10)
- Each bar animates from 0 to its value on mount
- One-sentence note per factor (from LLM scoring)

---

### `OutreachTimeline.tsx`
Visual timeline of outreach stages for a deal card. Shows:
- Signal Detected → Qualified → Draft Ready → Intro Sent → Follow-up → Meeting Booked
- Current stage highlighted in teal
- Completed stages shown with checkmark
- Pending stages shown as dots

---

### `AutonomyDial.tsx`
Animated dial component for selecting SCOUT autonomy level. Three positions:
- **Manual** — user does all prospecting and outreach
- **Co-Pilot** — SCOUT finds and drafts, user approves before send
- **Auto** — SCOUT runs the full pipeline autonomously

Dial animates smoothly between positions. Used on the How It Works page and Scout Settings page.

---

### `ActivityFeed.tsx`
Real-time feed of SCOUT agent actions. Each item shows:
- Action type icon (signal detected, lead qualified, draft generated, email sent)
- Company name
- Action description
- Timestamp (relative, e.g., "4m ago")

Polls `trpc.scout.getSignalUpdate` every 30 seconds for new items.

---

### `NextBestActions.tsx`
AI-recommended action panel. Shows 3 prioritized actions SCOUT recommends right now, e.g.:
- "Reach out to Silver Peak Hospitality — labor shortage signal detected 2h ago. Score: 94."
- "Follow up with DesertLine Logistics — no reply in 3 days."

Each action has a priority badge (Urgent / High / Medium) and a CTA button.

---

### `WhileYouWereAway.tsx`
Summary card shown on first login or after a period of inactivity:
- "Since your last visit, SCOUT found 12 new signals and qualified 3 leads."
- Lists the top 3 new opportunities with quick "Add to Pipeline" buttons.

---

### `ActionCard.tsx`
Reusable card for displaying a single recommended action. Props:
- `priority`: "urgent" | "high" | "medium"
- `companyName`: string
- `signalContext`: string (the buying signal)
- `score`: number
- `ctaLabel`: string
- `onCta`: () => void

---

### `DashboardLayout.tsx`
Full sidebar dashboard layout. Used for internal/admin views. Contains:
- Collapsible sidebar with nav items
- User profile section at bottom
- Main content area

**Not used in the current RFR site** (which uses a top-nav marketing layout), but available for a future admin panel.

---

### `AIChatBox.tsx`
Generic full-featured chat interface component. Used as the base for `ScoutChat`. Supports:
- Message history with user/assistant bubbles
- Streaming response support
- Markdown rendering via `streamdown`
- Loading states

---

### `SecondaryNav.tsx`
Secondary navigation bar that appears below the main header on some pages. Shows contextual links relevant to the current section.

---

### `ErrorBoundary.tsx`
React error boundary that catches unhandled errors and shows a fallback UI instead of a blank screen.

---

## 5. API Layer

All tRPC procedures in the prototype map to FastAPI endpoints in your production stack. The table below shows the mapping.

### Auth Router (`auth.*`)

| tRPC Procedure | FastAPI Equivalent | Auth | Description |
|---|---|---|---|
| `auth.me` | `GET /api/auth/me` | Public | Returns current user or null |
| `auth.logout` | `POST /api/auth/logout` | Public | Clears session cookie |

### Leads Router (`leads.*`)

| tRPC Procedure | FastAPI Equivalent | Auth | Description |
|---|---|---|---|
| `leads.capture` | `POST /api/leads/capture` | Public | Captures a lead email from homepage |

### Waitlist Router (`waitlist.*`)

| tRPC Procedure | FastAPI Equivalent | Auth | Description |
|---|---|---|---|
| `waitlist.join` | `POST /api/waitlist` | Public | Saves waitlist signup + notifies owner |

### Settings Router (`settings.*`)

| tRPC Procedure | FastAPI Equivalent | Auth | Description |
|---|---|---|---|
| `settings.get` | `GET /api/settings` | Protected | Returns user's SCOUT settings |
| `settings.save` | `PUT /api/settings` | Protected | Saves SCOUT settings |

### Scout Router (`scout.*`)

| tRPC Procedure | FastAPI Equivalent | Auth | Description |
|---|---|---|---|
| `scout.getSession` | `GET /api/scout/session` | Public | Gets or creates a SCOUT chat session |
| `scout.updateSession` | `PUT /api/scout/session` | Public | Updates session metadata |
| `scout.saveMessage` | `POST /api/scout/messages` | Public | Saves a chat message |
| `scout.chat` | `POST /api/scout/chat` | Public | Sends a message to SCOUT, returns LLM reply |
| `scout.scanCompany` | `POST /api/scout/scan-company` | Public | Scans a single company URL for automation readiness |
| `scout.findProspects` | `POST /api/scout/find-prospects` | Public | Finds 5–8 prospects for a given robot category + territory |
| `scout.findPartners` | `POST /api/scout/find-partners` | Public | Finds strategic partners (integrators, distributors) |
| `scout.scanForResults` | `POST /api/scout/scan-for-results` | Public | Full scan: returns prospects with scores + contact emails |
| `scout.getSignalUpdate` | `GET /api/scout/signal-update` | Public | Returns latest signal feed for the pipeline preview |
| `scout.draftOutreach` | `POST /api/scout/draft-outreach` | Public | Generates a personalized outreach email draft |

### Pipeline Router (`pipeline.*`)

| tRPC Procedure | FastAPI Equivalent | Auth | Description |
|---|---|---|---|
| `pipeline.add` | `POST /api/pipeline` | Protected | Adds a prospect to the pipeline |
| `pipeline.list` | `GET /api/pipeline` | Protected | Lists all pipeline deals for current user |
| `pipeline.advanceStage` | `POST /api/pipeline/{id}/advance` | Protected | Advances deal to next outreach stage |
| `pipeline.toggleMode` | `POST /api/pipeline/{id}/toggle-mode` | Protected | Toggles Assisted ↔ Autopilot |
| `pipeline.archive` | `POST /api/pipeline/{id}/archive` | Protected | Archives a deal |
| `pipeline.generateProposal` | `POST /api/pipeline/{id}/generate-proposal` | Protected | Generates LLM proposal document |

### PDF Endpoint (Express route, not tRPC)

| Endpoint | Method | Description |
|---|---|---|
| `/api/proposal/pdf` | `POST` | Generates branded PDF from proposal text. Body: `{ companyName, robotCategory, scoutScore, signalDescription, proposalText }`. Returns `application/pdf` binary. |

**FastAPI equivalent:**
```python
@router.post("/api/proposal/pdf")
async def generate_proposal_pdf(body: ProposalPdfRequest):
    # Use weasyprint or reportlab to generate PDF
    # Return Response(content=pdf_bytes, media_type="application/pdf")
```

---

## 6. Database Schema

### `users`
| Column | Type | Description |
|---|---|---|
| `id` | int PK | Auto-increment |
| `openId` | varchar(256) | Manus OAuth open ID |
| `name` | varchar(256) | Display name |
| `email` | varchar(320) | Email address |
| `role` | enum(admin, user) | Access level |
| `createdAt` | timestamp | |

### `scoutSessions`
| Column | Type | Description |
|---|---|---|
| `id` | int PK | |
| `sessionId` | varchar(64) | Unique session identifier |
| `userId` | int nullable | Linked user (null for anonymous) |
| `robotCategory` | varchar(128) | Robot type context |
| `territory` | varchar(128) | Geographic focus |
| `companyUrl` | varchar(512) | Company URL scanned |
| `createdAt` | timestamp | |

### `scoutMessages`
| Column | Type | Description |
|---|---|---|
| `id` | int PK | |
| `sessionId` | varchar(64) | Links to scoutSessions |
| `role` | enum(user, assistant) | Message author |
| `content` | text | Message text |
| `createdAt` | timestamp | |

### `scoutProfiles`
| Column | Type | Description |
|---|---|---|
| `id` | int PK | |
| `sessionId` | varchar(64) | Links to scoutSessions |
| `companyUrl` | varchar(512) | Scanned company URL |
| `score` | int | Automation readiness score (0–100) |
| `signals` | json | Array of detected signals |
| `summary` | text | LLM-generated summary |
| `recommendation` | text | LLM-generated recommendation |
| `createdAt` | timestamp | |

### `leads`
| Column | Type | Description |
|---|---|---|
| `id` | int PK | |
| `email` | varchar(320) | Captured email |
| `source` | varchar(128) | Where they came from |
| `createdAt` | timestamp | |

### `pipelineOpportunities`
This is the core table. Each row is one deal in the pipeline.

| Column | Type | Description |
|---|---|---|
| `id` | int PK | |
| `userId` | int | Owner (links to users) |
| `companyName` | varchar(256) | Target company |
| `industry` | varchar(128) | Industry vertical |
| `robotCategory` | varchar(128) | Robot type being sold |
| `signalDescription` | text | The buying signal that triggered this |
| `signalSource` | varchar(128) | Where the signal came from |
| `outreachAngle` | text | One-sentence reason to reach out |
| `outreachDraft` | text | Full LLM-generated outreach email |
| `proposalText` | text | LLM-generated proposal document |
| **SCOUT Score fields** | | |
| `scoreTotal` | int | Composite score (0–100) |
| `scoreBand` | enum | Hot / Warm / Developing / Monitoring |
| `scoreReadiness` | int | Readiness factor (0–25) |
| `scoreUseCase` | int | Use case clarity (0–20) |
| `scoreRoi` | int | ROI achievability (0–15) |
| `scoreDeploymentSize` | int | Deployment size (0–15) |
| `scoreRecognizableProblem` | int | Problem recognition (0–15) |
| `scoreCustomerValue` | int | Customer brand/size value (0–10) |
| `scoreNotes` | json | One-sentence note per factor |
| **Pipeline Mode** | | |
| `pipelineMode` | enum(assisted, autopilot) | How SCOUT handles this deal |
| **Outreach Timeline** | | |
| `outreachStage` | enum | pending → intro_scheduled → intro_sent → followup_sent → linkedin_sent → final_sent → meeting_booked → closed → paused |
| `introScheduledAt` | bigint | UTC ms |
| `introSentAt` | bigint | UTC ms |
| `followupSentAt` | bigint | UTC ms |
| `linkedinSentAt` | bigint | UTC ms |
| `finalSentAt` | bigint | UTC ms |
| `meetingBookedAt` | bigint | UTC ms |
| **Contact** | | |
| `contactEmail` | varchar(320) | Inferred or provided contact email |
| **Status** | | |
| `status` | enum(active, paused, archived) | |
| `createdAt` / `updatedAt` | timestamp | |

### `userSettings`
| Column | Type | Description |
|---|---|---|
| `id` | int PK | |
| `userId` | int unique | One row per user |
| `defaultPipelineMode` | enum(assisted, autopilot) | Default for new deals |
| `outreachPersona` | enum(on_behalf, independent) | Who SCOUT sends as |
| `senderCompanyName` | varchar(256) | For PDF footer |
| `senderName` | varchar(128) | For PDF footer |
| `senderEmail` | varchar(320) | Reply-to address |
| `senderTitle` | varchar(128) | For PDF footer |
| `outreachTone` | enum(professional, conversational, direct) | |
| `robotCategories` | json | Array of robot types |
| `targetVerticals` | json | Array of target industries |

### `waitlistSignups`
| Column | Type | Description |
|---|---|---|
| `id` | int PK | |
| `name` | text | |
| `email` | varchar(320) | |
| `tier` | enum(preview, growth, enterprise) | Which pricing tier |
| `robotCategory` | varchar(128) | |
| `companyUrl` | varchar(512) | |
| `createdAt` | timestamp | |

---

## 7. SCOUT Scoring Engine

File: `server/scoring.ts`

The SCOUT Score is a **composite 0–100 score** across 6 weighted factors:

| Factor | Max Points | What it measures |
|---|---|---|
| Readiness | 25 | How urgently ready is this company to buy? |
| Use Case | 20 | How well-defined is the automation use case? |
| ROI | 15 | How achievable is ROI within 24 months? |
| Deployment Size | 15 | How large is the potential deployment? |
| Recognizable Problem | 15 | How well-known is this problem in the industry? |
| Customer Value | 10 | How valuable is this customer (brand, reference value)? |

**Scoring method:** `scoreLeadFromSignal()` calls the LLM with the company name, industry, robot category, and buying signal. The LLM returns normalized scores for each factor (0 to max) plus a one-sentence note explaining each score.

**Score bands:**
- **Hot** (80–100): `#ef4444` — immediate outreach priority
- **Warm** (60–79): `#FFB000` — active pipeline, reach out within 48h
- **Developing** (40–59): `#a78bfa` — monitor and nurture
- **Monitoring** (0–39): `rgba(255,255,255,0.35)` — watch list only

**Python port** (`app/services/scoring.py`):
```python
SCORE_WEIGHTS = {
    "readiness": 25, "use_case": 20, "roi": 15,
    "deployment_size": 15, "recognizable_problem": 15, "customer_value": 10
}

def get_band(total: int) -> str:
    if total >= 80: return "Hot"
    if total >= 60: return "Warm"
    if total >= 40: return "Developing"
    return "Monitoring"
```

---

## 8. PDF Generation

File: `server/proposalPdf.ts`

**Endpoint:** `POST /api/proposal/pdf`

**Request body:**
```json
{
  "companyName": "Apex Logistics",
  "robotCategory": "Warehouse AMR",
  "scoutScore": 91,
  "signalDescription": "3 DC expansions + labor shortage filing",
  "proposalText": "EXECUTIVE SUMMARY\n...\nOPPORTUNITY\n..."
}
```

**PDF structure:**
1. **Header band** — dark background (`#1a0a3e`), RFR logo + "ReadyForRobots" wordmark, "SALES PROPOSAL" label + date
2. **Company block** — company name (large), robot category tag, SCOUT Score badge, "CONFIDENTIAL" label
3. **Signal callout** — teal left-border box with the buying signal description
4. **6 content sections** — each with amber accent bar + uppercase header:
   - EXECUTIVE SUMMARY
   - OPPORTUNITY
   - SOLUTION
   - EXPECTED OUTCOMES
   - NEXT STEPS
   - ABOUT READYFORROBOTS
5. **Footer** — "Prepared by ReadyForRobots SCOUT" + date on every page

**Section parsing:** The proposal text is split on ALL-CAPS headers using this regex:
```js
/^([A-Z][A-Z\s&]+)$/m
```

**Python equivalent using WeasyPrint:**
```python
from weasyprint import HTML
import re

def parse_sections(text: str) -> list[dict]:
    pattern = r'^([A-Z][A-Z\s&]+)$'
    parts = re.split(pattern, text, flags=re.MULTILINE)
    # alternate: [body, header, body, header, body, ...]
    sections = []
    for i in range(1, len(parts), 2):
        sections.append({"header": parts[i].strip(), "body": parts[i+1].strip()})
    return sections
```

---

## 9. AI / LLM Flows

All LLM calls use `invokeLLM()` on the server (never exposed to the frontend). The model uses structured JSON output (`response_format: json_schema`) for all data-extraction tasks.

### SCOUT Chat (`scout.chat`)
- **System prompt:** SCOUT persona — direct, data-driven, robotics sales expert. Knows the user's robot category and target verticals from their session/settings.
- **Input:** Conversation history (last N messages) + new user message
- **Output:** Free-form text reply as SCOUT

### Company Scan (`scout.scanCompany`)
- **Input:** Company URL + robot category
- **Output:** `{ score, signals[], summary, recommendation }` — JSON schema enforced

### Find Prospects (`scout.findProspects`)
- **Input:** Robot category + territory + number of prospects
- **Output:** Array of `{ company, industry, signal, score, outreachAngle }` — JSON schema enforced

### Scan For Results (`scout.scanForResults`)
- **Input:** Company URL (the user's robot company)
- **Output:** Array of prospects + contact email inference per prospect
- **Contact email inference logic:**

| Signal type keywords | Inferred email prefix |
|---|---|
| procurement, supply chain, purchasing | `purchasing@` |
| partnership, bd, business development | `bd@` |
| expansion, real estate, facility | `operations@` |
| hiring, labor, workforce | `hr@` |
| default | `info@` |

### Draft Outreach (`scout.draftOutreach`)
- **Input:** Company name, industry, signal, outreach angle, sender name/company, robot category
- **Output:** Full email with subject line + 5-part body
- **Email structure:**
  1. Subject: `Automation Proposal for [Company] — [Sender Company]`
  2. Opening: Reference the specific buying signal
  3. Value prop: What the robot solves for their exact situation
  4. Social proof: One relevant outcome (e.g., "reduced labor costs 35%")
  5. CTA: Request a 15-minute call
  6. Signature: Sender name + title + company
  - Max 180 words total

### Generate Proposal (`pipeline.generateProposal`)
- **Input:** Company name, robot category, signal description, SCOUT Score, outreach angle
- **Output:** 350–500 word structured proposal with 6 ALL-CAPS sections
- **Sections:** EXECUTIVE SUMMARY, OPPORTUNITY, SOLUTION, EXPECTED OUTCOMES, NEXT STEPS, ABOUT READYFORROBOTS

### SCOUT Score (`scoring.scoreLeadFromSignal`)
- **Input:** Company name, industry, robot category, signal, signal source
- **Output:** 6 factor scores + one-sentence notes per factor — JSON schema enforced

---

## 10. Data Flows End-to-End

### Flow 1: Homepage → Results → Pipeline

```
User enters company URL on homepage
  → navigates to /results?url=<encoded>
  → Results page calls scout.scanForResults({ url })
  → Server: LLM generates 5-8 prospects with scores + contact emails
  → Results page renders prospect cards
  → User clicks "Add to Pipeline" on a card
  → pipeline.add({ companyName, industry, signal, score, contactEmail, ... })
  → Server: stores in pipelineOpportunities table + calls scoreLeadFromSignal
  → navigates to /pipeline
```

### Flow 2: Pipeline → Outreach Draft

```
User views a deal card on /pipeline
  → "Generate Draft" button calls scout.draftOutreach({ companyName, signal, ... })
  → Server: LLM generates email with subject + 5-part body
  → Draft stored in pipelineOpportunities.outreachDraft
  → User reviews draft in expanded card section
  → "Approve & Send" advances outreachStage to intro_sent
    (in Autopilot mode: SCOUT sends automatically without approval)
```

### Flow 3: Pipeline → Proposal → PDF

```
User clicks "Generate Proposal" on a deal card
  → pipeline.generateProposal({ dealId })
  → Server: LLM generates 350-500 word structured proposal
  → Proposal stored in pipelineOpportunities.proposalText
  → Modal opens with proposal text
  → User clicks "Preview PDF"
  → Frontend POSTs to /api/proposal/pdf with proposal data
  → Server: @react-pdf/renderer generates branded PDF binary
  → Frontend creates blob URL → renders in iframe
  → User edits text in left panel → clicks "Update Preview"
  → Frontend re-POSTs to /api/proposal/pdf with edited text
  → iframe refreshes with new PDF
  → User clicks "Download PDF" → browser downloads the blob
```

### Flow 4: SCOUT Chat

```
User clicks "Talk to SCOUT" button
  → ScoutChat context opens overlay
  → scout.getSession() → creates or retrieves session
  → User types message
  → scout.chat({ sessionId, messages }) 
  → Server: builds context (user settings, pipeline summary, persona)
  → LLM generates reply as SCOUT
  → Reply streamed back to chat UI
  → Message saved to scoutMessages table
```

### Flow 5: Waitlist Signup

```
User clicks pricing tier on /pricing
  → Form modal opens (name, email, robot category)
  → waitlist.join({ name, email, tier, robotCategory, companyUrl })
  → Server: stores in waitlistSignups table
  → Server: notifyOwner({ title: "New waitlist signup", content: ... })
  → User sees confirmation message
```

---

## 11. Porting Checklist for Cursor

Use this checklist when porting each feature to your Next.js + FastAPI + Supabase stack.

### Setup

- [ ] Copy `frontend/index.css` → `frontend/nextjs/styles/globals.css`
- [ ] Add Google Fonts CDN to `frontend/nextjs/pages/_document.js`
- [ ] Add Sora, Inter, JetBrains Mono font families

### Design System

- [ ] Set `background: #0d0520` as the default page background in `globals.css`
- [ ] Add brand color CSS variables: `--color-purple: #7c3aed`, `--color-teal: #03DAC5`, `--color-amber: #f59e0b`

### Database (Supabase Migrations)

- [ ] Create `pipeline_opportunities` table (see schema above)
- [ ] Create `user_settings` table
- [ ] Create `scout_sessions` table
- [ ] Create `scout_messages` table
- [ ] Create `waitlist_signups` table
- [ ] Run `alembic upgrade head` on Fly.dev

### Backend (FastAPI — `app/api/`)

- [ ] `scout.py` — `/api/scout/scan-for-results`, `/api/scout/chat`, `/api/scout/draft-outreach`, `/api/scout/find-prospects`
- [ ] `pipeline.py` — CRUD + advance stage + toggle mode + archive + generate proposal
- [ ] `proposal.py` — `/api/proposal/pdf` using WeasyPrint or ReportLab
- [ ] `settings.py` — `GET/PUT /api/settings`
- [ ] `waitlist.py` — `POST /api/waitlist`
- [ ] `scoring.py` — port the 6-factor scoring engine

### Frontend (Next.js — `frontend/nextjs/`)

- [ ] `components/ScoutWorkflowAnimation.jsx` — homepage hero animation
- [ ] `components/ScoutChat.jsx` — global AI chat overlay
- [ ] `components/PipelinePreview.jsx` — homepage pipeline widget
- [ ] `components/ScoutScoreBreakdown.jsx` — 6-factor score bars
- [ ] `components/OutreachTimeline.jsx` — outreach stage tracker
- [ ] `components/AutonomyDial.jsx` — Manual/Co-Pilot/Auto selector
- [ ] `components/ActivityFeed.jsx` — SCOUT activity feed
- [ ] `components/NextBestActions.jsx` — AI recommended actions
- [ ] `components/WhileYouWereAway.jsx` — login summary card
- [ ] `components/ActionCard.jsx` — reusable action card
- [ ] `pages/index.js` — update with all homepage sections
- [ ] `pages/results.js` — prospect scan results page
- [ ] `pages/pipeline-results.js` — full pipeline Kanban with proposal/PDF features
- [ ] `pages/signals.js` — live signal feed with filters
- [ ] `pages/scout-settings.js` — SCOUT configuration page

### TSX → JSX Conversion Notes

When converting TypeScript files to JavaScript:
1. Rename `.tsx` → `.jsx`
2. Remove all `: TypeName` annotations (e.g., `const x: string` → `const x`)
3. Remove `interface` and `type` declarations
4. Replace `trpc.X.Y.useQuery(params)` → `useSWR("/api/X/Y?" + params, fetcher)` or `useEffect + fetch`
5. Replace `trpc.X.Y.useMutation()` → custom `useState + fetch` pattern
6. Replace `useAuth()` → your Supabase auth hook
7. Replace `import { ... } from "@/components/ui/button"` → your existing component imports

### Environment Variables

| Variable | Where to set | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Vercel env vars | FastAPI backend URL (Fly.dev) |
| `RESEND_API_KEY` | Fly.dev secrets | For email delivery |
| `RESEND_FROM_EMAIL` | Fly.dev secrets | Verified sending domain |
| `OPENAI_API_KEY` | Fly.dev secrets | For LLM calls |
| `NEXT_PUBLIC_SUPABASE_URL` | Vercel env vars | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Vercel env vars | Supabase anon key |

---

*Generated from the ReadyForRobots Manus prototype — May 2026*
