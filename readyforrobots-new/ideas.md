# ReadyForRobots — Design Brainstorm

## Context

Automated sales development workflow for robotics companies. Core concept: "The system moves robot deals forward while the user stays in control." Primary screen is a live pipeline dashboard with autonomy controls, activity feed, and decision panels.

---

<response>
<probability>0.07</probability>
<text>

## Idea A — Industrial Precision / Swiss Grid

**Design Movement:** Swiss International Typographic Style meets industrial SaaS

**Core Principles:**

- Rigid grid with deliberate asymmetry — content bleeds into margins
- Data density without visual noise; every pixel earns its place
- Monospace accents for machine-generated data, humanist sans for editorial copy
- Status and urgency communicated through geometry, not color alone

**Color Philosophy:**

- Background: warm off-white (#F7F6F2) — paper-like, not clinical
- Primary: deep slate-navy (#1A2332) — authority and precision
- Accent 1: emerald (#059669) — live signals, approved actions
- Accent 2: amber (#D97706) — pending, awaiting decision
- Destructive: rust (#B91C1C) — skipped, blocked
- Muted borders, no drop shadows — structure through whitespace

**Layout Paradigm:**

- Left-anchored sidebar with status indicators (not centered nav)
- Main content: 2-column asymmetric split (feed 65% / actions 35%)
- Header is a thin bar — 48px — not a hero
- Cards are flush-edge, not floating — connected to the grid

**Signature Elements:**

- Thin horizontal rule dividers with category labels (like editorial magazines)
- Monospace confidence scores and timestamps
- Status pills: sharp-cornered rectangles, not rounded badges

**Interaction Philosophy:**

- Approve/Skip/Edit actions are keyboard-accessible, feel like command-line efficiency
- Autonomy Dial is a segmented control, not a slider — discrete choices
- Hover reveals secondary metadata without expanding cards

**Animation:**

- Feed items slide in from left on load (staggered 40ms)
- Status changes: instant color swap + subtle scale pulse (0.98 → 1.0)
- Modal: fade + translate-y(-8px) entrance

**Typography System:**

- Display: "DM Sans" 700 for headlines
- Body: "DM Sans" 400/500 for content
- Data/code: "JetBrains Mono" for scores, timestamps, IDs

</text>
</response>

<response>
<probability>0.06</probability>
<text>

## Idea B — Operator Console / Dark Command

**Design Movement:** Mission-critical software (Bloomberg Terminal meets Linear.app)

**Core Principles:**

- Dark background as canvas — reduces eye strain during long sessions
- Color carries semantic meaning exclusively (no decorative color)
- Compact information density — operators scan, not read
- System-generated content visually distinct from human-authored content

**Color Philosophy:**

- Background: #0D1117 (near-black with blue undertone)
- Surface: #161B22
- Primary: #10B981 (emerald) — live, active, approved
- Secondary: #3B82F6 (blue) — system actions, AI-generated
- Warning: #F59E0B (amber) — needs review
- Text: #E6EDF3 primary, #8B949E secondary

**Layout Paradigm:**

- Full-width command bar at top
- Three-panel layout: sidebar nav / main feed / context panel
- No card shadows — borders only, 1px #30363D

**Signature Elements:**

- Blinking cursor on "live" indicators
- Monochrome iconography with color only for status
- Inline expandable details (no modals except WYWA)

**Interaction Philosophy:**

- Every action has a keyboard shortcut shown on hover
- Batch operations via checkbox selection
- Autonomy Dial glows its current mode color

**Animation:**

- Minimal — only functional animations (loading states, status transitions)
- New feed items flash briefly (#10B981 border) then normalize

**Typography System:**

- All: "IBM Plex Mono" — unified terminal aesthetic
- Size hierarchy through weight and size, not font family

</text>
</response>

<response>
<probability>0.08</probability>
<text>

## Idea C — Clean Workflow / Elevated SaaS (CHOSEN)

**Design Movement:** Modern workflow SaaS (Stripe / Linear / Notion aesthetic) — clean, purposeful, premium

**Core Principles:**

- White canvas with structured zones — breathing room between components
- Emerald green as the "live system" color; amber for "needs your attention"
- Typography does the heavy lifting — size and weight create hierarchy
- Cards feel like physical objects: subtle shadow, clear edges, hover lift

**Color Philosophy:**

- Background: pure white (#FFFFFF) with neutral-50 (#FAFAFA) for panels
- Primary action: emerald-600 (#059669) — approved, live, system-active
- Decision needed: amber-500 (#F59E0B) — pending review
- Informational: blue-600 (#2563EB) — system messages, AI suggestions
- Text: neutral-950 (#0A0A0A) primary, neutral-500 (#737373) secondary
- Borders: neutral-200 (#E5E5E5) — light, not heavy

**Layout Paradigm:**

- Top navigation bar (slim, 56px) with logo left, user right
- Below: full-width Autonomy Dial strip (prominent, centered)
- Main: asymmetric 2-column — feed takes 62%, actions panel 38%
- Feed cards stack vertically with 12px gap
- Actions panel is sticky on scroll

**Signature Elements:**

- Autonomy Dial: large segmented toggle with animated indicator pill
- Confidence score: circular arc progress indicator (not a bar)
- Status badges: pill-shaped with colored left border accent
- "While You Were Away" button: fixed bottom-right, pulsing dot

**Interaction Philosophy:**

- Primary actions (Approve) are always green and prominent
- Secondary (Edit) are neutral
- Destructive (Skip) are ghost/muted — require intentionality
- Autonomy mode change triggers a brief system message in feed

**Animation:**

- Cards: staggered fade-in + translateY(12px → 0) on load
- Approve: card collapses with green flash, next card slides up
- Autonomy Dial: smooth sliding pill transition between modes
- WYWA modal: scale(0.95 → 1) + opacity fade

**Typography System:**

- Display/Headlines: "Sora" 700/800 — geometric, modern, distinctive
- Body/UI: "Inter" 400/500 — readable, neutral
- Data: "JetBrains Mono" 500 — scores, timestamps, IDs

</text>
</response>

---

## Selected: Idea C — Clean Workflow / Elevated SaaS

Rationale: Matches the existing brand's emerald/amber palette, aligns with the Stripe/Zapier/Make.com reference sites, and best serves the workflow-oriented use case where users need to scan, decide, and act quickly on a white-canvas interface.
