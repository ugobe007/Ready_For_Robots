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
| Jobs CRM | `/pipeline?src=jobs_activate` | Step 03: collected listing, inspect, quote rental, Place this job. Inbox confirm/release for a held interview slot. |
| Employer evaluate | `/employer/:token` | Accept / Decline (reason code) / propose time / hold a slot. Video résumé when present. No RFR account. |
| OEM hold | `/oem-hold/:token` | Confirm or release a held interview window. |
| Compare | `/compare` | Jobs vs sales-list framing |
| SIGNAL pipeline | `/pipeline` | Buyer queue — **not** the Jobs path |
| Admin | `/admin` | Cal / ops — not Jobs activation |

Canonical frontend: `readyforrobots-new/client/`. API: `https://ready-2-robot.fly.dev`. Marketing domain: `https://readyforrobots.com`.

---

## Nav bars

### Jobs header (`ExperimentHeader`)

Fixed dark bar on Jobs chrome. Wordmark + Kare face → `/?new=1` (empty FIND). While already on `/`, the click resets in place — it must not reload the document or abort an in-flight Start jobs.

| Item | Behavior |
|------|----------|
| Jobs | Selected on `/` and `/jobs/:slug`. Same fresh-home href. |
| About | `/intelligence` |
| Pipeline | **Hidden** on Jobs chrome and Jobs CRM |
| CRM | On Jobs chrome (signed in or out): `/pipeline?src=jobs_activate`. On SIGNAL `/pipeline` or bare `/crm`: `/crm` (signed-in) |
| Admin | Signed-in admin only |
| Sign In / Sign Out | Sign In when anonymous; Sign Out when session |

Jobs chrome paths: `/`, `/jobs…`, About, Compare, vendor design, Jobs CRM (`/pipeline?src=jobs_activate`), Jobs signup/login. Footer and Signal FAB follow: no SIGNAL Pipeline nav.

### Marketing / SIGNAL header (`Header`)

Floating emerald nav used on SIGNAL pages (Pipeline, Signals, Robots, Pricing, …). Includes Pipeline, Signals, More. **Do not assert this header on `/`.** Jobs replaced it with `ExperimentHeader`.

### Workspace sidebar (`AdminNav`)

Collapsible command rail on CRM / pipeline / admin when signed in. Sections: Sell, Outreach, Command, Supply & growth, Account. Default collapsed. This is workspace chrome, **not** the Jobs FIND layout. The Jobs CRM desk on `/pipeline?src=jobs_activate` does not show this sidebar.

---

## Process bar (Jobs workflow chrome)

Not a sidebar. Page-level strip, **top and bottom**, `aria-label="Jobs process"`. The document **scrolls**. Do not lock the workspace at `100vh` + `overflow: hidden`.

| Step | Label | CTA |
|------|-------|-----|
| 01 | Show us your robot | `Start jobs →` |
| 02 | Available jobs | `See jobs →` |
| 03 | CRM | `Open CRM →` |

01 / 02 / 03 stay **links** even while research is running. Next is on the list and process bars, **not** on the Job Card. Step 03 is **CRM**. Place this job (quote the rental) is the money action *inside* CRM.

On `/pipeline?src=jobs_activate` the same process bar renders (unsigned wall and signed desk). Unsigned next is **Sign up to open CRM →**. Signed next leaves the desk: **See jobs →** when they have a submission or collected cards, otherwise **Start jobs →**. Header **About** stays visible on all widths.

---

## Panels (Jobs)

| Panel | Role |
|-------|------|
| FIND form | `aria-label="Find jobs for your robot"`. URL field: `Paste robot product URL`. Optional catalog / known OEM lineup. |
| SKU picker | Several products on the URL → ask which robot. One SKU → jobs on the same click (no second Find jobs). |
| Job list | Up to 5 example jobs before signup. All five start **Keep**-checked. Tag `Job # is for {SKU}`. Collapsed row shows model `list_line` (layer · time · who trains) so QUALIFY happens before the check. |
| Job Card (expanded) | Employer, workplace, work, qualification (usually Conditional), open questions, task models, numbered placement steps, Next is **not** here. |
| Research console | Stage labels while Understanding + match run. Not the result. |
| Live job tape | Ambient listings; not a substitute for named Job Cards. |
| pstack protocol | `JobsPstackProtocol` on `/`, About, Jobs CRM. How / Act / Critic. Jobs still come from `POST /api/robot-job-match`. Not a chatbot. |

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
| CRM unlock | 5 jobs on free after `src=jobs_activate`. Listing first. Place requires pack and a user-entered monthly rental. PoC is preferred, skippable. |

API the UI calls: `POST /api/robot-job-match`. Public reads use `getPublicReadApiBase()` on the marketing domain.

---

## Workflow (user)

```
/?new=1
  → paste robot URL (FIND)
  → optional SKU pick
  → Job Cards (QUALIFY / inspect + check — checking dumps the row into CRM)
  → Open CRM → /signup?next=/pipeline?src=jobs_activate&src=jobs_activate
  → after auth, CRM desk with 5 kept jobs (no robot OEMs)
  → CRM: collect listing (Keep N jobs? + Yes, keep them) → Apply (offer form) → inspect an egg → quote rental → Place this job. Process bar stays 01 / 02 / 03.
  → run the next robot the same way
```

Wordmark / Jobs always returns to empty FIND (`/?new=1`). Bare `/pipeline` without a Jobs `src` is SIGNAL — do not dump Jobs traffic there.

Agent proof of this loop: `python3 scripts/agent_verify.py ci`.

---

## Out of scope for this map

Cal buyer-sales intros, SIGNAL ranking, pipeline junk rules, model dollar indexes on the card.
