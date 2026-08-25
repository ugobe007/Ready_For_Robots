# ReadyForRobots feature map

**Audience:** agents and operators driving or changing the Jobs product  
**Verification recipes:** [`.cursor/skills/verify-readyforrobots/features/`](../.cursor/skills/verify-readyforrobots/features/README.md)  
**Product loop:** FIND → QUALIFY (Job Cards) → PLACE later (CRM). `/` is Jobs. SIGNAL/Cal are frozen as core.

This file names **chrome** — nav, process bar, panels, surfaced results — and how they work. It is not a screenshot gallery and not a SIGNAL playbook.

---

## Surfaces

| Surface | Route | What the user is doing |
|---------|-------|------------------------|
| Jobs terminal | `/` (`/jobs/:slug` same workspace) | Paste robot URL, inspect Job Cards |
| About | `/intelligence` | Jobs loop explainer; Start jobs → `/?new=1` |
| Jobs CRM | `/crm?src=jobs_activate` | Keep 3 unlocked jobs (free) |
| Compare | `/compare` | Jobs vs sales-list framing |
| SIGNAL pipeline | `/pipeline` | Buyer queue — **not** the Jobs path |
| Admin | `/admin` | Cal / ops — not Jobs activation |

Canonical frontend: `readyforrobots-new/client/`. API: `https://ready-2-robot.fly.dev`. Marketing domain: `https://readyforrobots.com`.

---

## Nav bars

### Jobs header (`ExperimentHeader`)

Fixed dark bar on Jobs chrome. Wordmark + Kare face → `/?new=1` (empty FIND).

| Item | Behavior |
|------|----------|
| Jobs | Selected on `/` and `/jobs/:slug`. Same fresh-home href. |
| About | `/intelligence` |
| Pipeline | **Hidden** on Jobs chrome and Jobs CRM |
| CRM | Signed-in only. On Jobs chrome: `/crm?src=jobs_activate`. On SIGNAL `/pipeline` or bare `/crm`: `/crm` |
| Admin | Signed-in admin only |
| Sign In / Sign Out | Sign In when anonymous; Sign Out when session |

Jobs chrome paths: `/`, `/jobs…`, About, Compare, vendor design, Jobs CRM (`src=jobs_activate`), Jobs signup/login. Footer and Signal FAB follow: no Pipeline / SIGNAL.

### Marketing / SIGNAL header (`Header`)

Floating emerald nav used on SIGNAL pages (Pipeline, Signals, Robots, Pricing, …). Includes Pipeline, Signals, More. **Do not assert this header on `/`.** Jobs replaced it with `ExperimentHeader`.

### Workspace sidebar (`AdminNav`)

Collapsible command rail on CRM / pipeline / admin when signed in. Sections: Sell, Outreach, Command, Supply & growth, Account. Default collapsed. This is workspace chrome, **not** the Jobs FIND layout. Jobs CRM may show it after activate; FIND itself has no left sidebar.

---

## Process bar (Jobs workflow chrome)

Not a sidebar. Page-level strip, **top and bottom**, `aria-label="Jobs process"`. The document **scrolls**. Do not lock the workspace at `100vh` + `overflow: hidden`.

| Step | Label | CTA |
|------|-------|-----|
| 01 | Show us your robot | `Start jobs →` |
| 02 | Here are its jobs | `See jobs →` |
| 03 | CRM | `Next →` |

01 / 02 / 03 stay **links** even while research is running. Next is on the list and process bars, **not** on the Job Card. No Place-buyer screen.

---

## Panels (Jobs)

| Panel | Role |
|-------|------|
| FIND form | `aria-label="Find jobs for your robot"`. URL field: `Paste robot product URL`. Optional catalog / known OEM lineup. |
| SKU picker | Several products on the URL → ask which robot. One SKU → jobs on the same click (no second Find jobs). |
| Job list | Up to 5 example jobs before signup. Checkboxes select. Tag `Job # is for {SKU}`. Collapsed row shows model `list_line` (layer · time · who trains) so QUALIFY happens before the check. |
| Job Card (expanded) | Employer, workplace, work, qualification (usually Conditional), open questions, task models, numbered placement steps, Next is **not** here. |
| Research console | Stage labels while Understanding + match run. Not the result. |
| Live job tape | Ambient listings; not a substitute for named Job Cards. |

SIGNAL-only panels (activity feed, next actions, Cal queue, lead share) stay off the Jobs path.

---

## Surfaced results

| Result | Honest rule |
|--------|-------------|
| Job Card | Named employer + real work. No invented FTE/payback. |
| Qualification | Conditional until site assessment + task model evidence. Hardware in the room is not enough. |
| Task model | Slot + unknown/present/absent. List line names layer / typical time / who trains. Expanded card walks placement steps. Lookups, not fake “this SKU has GR00T”. |
| Lineup | One robot → 5 jobs. Several → sample per SKU / type; run each robot for five. |
| Empty / thin | Tell the truth (`could_not_understand`, `thin_corpus`). Do not pad with SIGNAL HOT buyers. |
| CRM unlock | 3 jobs on free after `src=jobs_activate`. |

API the UI calls: `POST /api/robot-job-match`. Public reads use `getPublicReadApiBase()` on the marketing domain.

---

## Workflow (user)

```
/?new=1
  → paste robot URL (FIND)
  → optional SKU pick
  → Job Cards (QUALIFY / inspect + check)
  → Next → /crm?src=jobs_activate  (signup first if signed out)
  → 3 unlocked jobs in CRM
  → run the next robot the same way
```

Wordmark / Jobs always returns to empty FIND (`/?new=1`). Do not dump Jobs traffic on `/pipeline`.

Agent proof of this loop: `python3 scripts/agent_verify.py ci`.

---

## Out of scope for this map

Cal buyer-sales intros, SIGNAL ranking, pipeline junk rules, model dollar indexes on the card.
