# ReadyForRobots — Autonomous Deal Flow UX

## Core principle

> Users don’t want leads.  
> They want robot deals moving forward without doing the work.

ReadyForRobots is not a dashboard.  
It is a **control surface for an autonomous deal engine**.

---

## Product definition

**ReadyForRobots = Detect → Qualify → Engage → Advance**

The system:

- Detects companies with robot intent
- Decides the highest-leverage action
- Executes (or prepares execution)
- Reports progress to the user

---

## Primary UX model

### Home = “What Happened”

Replace traditional dashboards with a **live activity feed**.

### Layout (wireframe)

Top bar: **Logo · Autonomy Dial · Profile**

```
┌─────────────────────────────────────────────────────────────────┐
│  Logo          [ Autonomy Dial ]                    Profile        │
├──────────────────────────────────┬──────────────────────────────┤
│  Activity Feed (~70%)            │  Next Actions (~30%)          │
│                                  │                               │
│  [ Card ]                        │  1. Action                    │
│  [ Card ]                        │  2. Action                    │
│  [ Card ]                        │  3. Action                    │
│  …                               │                               │
└──────────────────────────────────┴──────────────────────────────┘
```

---

## 1. Activity feed (core UI)

### Purpose

Show **real progress**, not data.

### Format

Each item represents a **state change or action taken**.

### Example items

**[New Signal Detected]**  
Company: Regional Logistics Co.  
Signal: Hiring automation engineers  
→ Suggested action: Engage with warehouse robotics solution

**[Outreach Drafted]**  
Company: Hotel Group (Las Vegas)  
Use case: Service robots  
→ Draft ready for approval

**[Follow-up Sent]**  
Company: Manufacturing Plant  
Status: No response after 3 days  
→ Re-engaged with new angle

**[Opportunity Qualified]**  
Company: Airport Services Operator  
→ Likely pilot opportunity (cleaning robots)

---

## 2. Action cards

Each feed item expands into a **decision card**.

### Card structure

**Header**

- Company name
- Industry
- Signal type

**System insight**

- Why this company matters
- Likely robot use case

**Action taken or suggested**

- Draft outreach message **or**
- Engagement step

### User controls

- Approve and send
- Edit message
- Skip
- Prioritize

---

## 3. Autonomy dial (global control)

### UI element

`Manual` ——— `Assisted` ——— `Auto`

### Behavior

| Mode      | Behavior |
|-----------|----------|
| Manual    | User approves all actions |
| Assisted  | System drafts; user confirms |
| Auto      | System executes; user reviews |

### Purpose

Build **trust and control** into automation.

---

## 4. Next best actions panel

### Location

Right side of screen.

### Content (examples)

- Follow up with Hotel Group (2 days idle)
- Contact Logistics Co. (new signal)
- Review 3 qualified opportunities

### Function

Expose system decision-making.

---

## 5. “While you were away” view

### Trigger

Button or daily auto-display.

### Shows

- Signals detected
- Outreach generated or sent
- Follow-ups executed
- Opportunities advanced

### Example

**While you were away**

- 5 companies flagged for robot needs
- 3 outreach drafts created
- 2 follow-ups sent
- 1 pilot opportunity identified

---

## 6. Daily report (retention engine)

Delivered via:

- In-app
- Email

### Format

**Today’s progress**

- 6 signals detected
- 4 companies qualified
- 2 outreach messages sent
- 1 opportunity progressing

### Goal

Create habit and dependency.

---

## 7. Deep dive view (on click)

### Displays

- Full signal breakdown
- Why this company was selected
- Robot category recommendation
- Outreach history
- Suggested next steps

### Purpose

Transparency → trust.

---

## 8. Visual design system

### Style

- Clean, minimal (Supabase-inspired)
- White or light background
- Stroke-based UI (no heavy fills)
- Square edges (no excessive rounding)
- Helvetica or similar sans-serif

### Avoid

- Cluttered dashboards
- Overuse of charts
- Decorative graphics

---

## 9. Core product loop

1. Detect signal  
2. Generate insight  
3. Suggest or execute action  
4. Capture response  
5. Recommend next step  
6. Repeat  

---

## 10. Key UX differentiator

| Most platforms | ReadyForRobots |
|----------------|----------------|
| Show data      | **Move deals forward** |

---

## 11. Core messaging

### Internal

“Advance the state of the deal.”

### External

“Robot deals, initiated for you.”

---

## 12. MVP scope (build first)

- Activity feed  
- Action cards  
- Autonomy dial (basic)  
- Outreach draft generator  
- Daily report  

---

## 13. Future enhancements

- Auto-follow-ups  
- CRM memory layer  
- Multi-agent pipeline (qualification → engagement → deal)  
- Vendor matching automation  
- Pilot / POC tracking  

---

## Final thought

> This is not a tool.  
> This is a system that moves robot deals forward without waiting for humans.
