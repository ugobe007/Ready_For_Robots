# Conversion agent challenges

Standing directive for **ProductSurface**, **FrictionMiner**, and **PipelineHealth** agents: every mission should ask *“Does this reduce friction from casual browse → signup → first saved lead?”*

## North-star funnel

```
Home / Signals / Robots (browse)
  → URL scan (/results) OR pipeline preview (/pipeline, 12 anon leads)
  → Intent peak (save lead, activate SIGNAL, research panel)
  → Signup (/signup?next=…) with OAuth or magic link
  → First value (/pipeline save, CRM account, HubSpot connect)
  → Upgrade (/pricing) at save limit or locked research
```

Measure weekly: anonymous pipeline views, signup starts, signup completes, first save, pricing clicks, upgrade attempts.

---

## Agent challenge board (ranked)

| Rank | Challenge | Agent | Acceptance test |
|------|-----------|-------|-----------------|
| 1 | **Pricing → signup wiring** — no dead-end toasts; honest free-workspace copy until Stripe | ProductSurface | Every tier CTA lands on `/signup?next=/pipeline` or sales mailto |
| 2 | **Entitlement honesty** — UI tier names match `plan_entitlements.py` | ProductSurface + backend | `/api/user/me` exposes plan + limits; Pricing FAQ matches gates |
| 3 | **Post-auth landing** — default `next` is `/pipeline`, not `/profile` | ProductSurface | New OAuth user sees pipeline + first-run checklist |
| 4 | **Save-limit upgrade moment** — modal at 5/5 saves with `/pricing?reason=saved_leads` | ProductSurface | Free user hitting 403 gets upgrade CTA, not toast-only |
| 5 | **Locked research teaser** — free signed-in users see blurred Pro research block | ProductSurface | `panelPlan === "free"` shows upsell, not empty panel |
| 6 | **CTA continuity** — every marketing button does something (`PipelinePreview`, header mobile) | ProductSurface | No inert buttons on Home; mobile header has signup path |
| 7 | **Context-preserving signup** — `?next=` on Signals, Results, Pipeline deep links | ProductSurface | Auth return resumes exact route |
| 8 | **OAuth-first signup** — peak-intent pages emphasize one-tap Google | ProductSurface | Results/Pipeline signup puts OAuth above magic link |
| 9 | **Profile usage meters** — “3/5 leads saved · Free” + upgrade | ProductSurface | Profile fetches entitlements |
| 10 | **Dynamic social proof** — hero ticker + pipeline preview use live API counts | PipelineHealth | No stale “247 opportunities” when feed is 35 |

---

## Friction themes (browse → signup)

| Theme | Symptom | Fix pattern |
|-------|---------|-------------|
| Dead-end CTAs | Pricing toasts, Approve button inert | Link to signup or pipeline |
| Wrong door after auth | Lands on Profile settings | Default `/pipeline` + `?next=` |
| Invisible paywall | Free users hit limit with no upgrade path | Intercept API codes; surface `/pricing` |
| Trust gap | Paid features promised but not gated consistently | Align copy + `plan_entitlements` |
| Mobile leakage | Signup hidden on small screens | Drawer CTAs mirror desktop |

---

## Mission template (copy for new missions)

```markdown
# Mission: <slug>
**Agent:** ProductSurface
**Type:** build
**Conversion hypothesis:** <one sentence>
**Primary metric:** signup completion rate from <entry page>
**Acceptance:** <measurable UI/API change>
**Out of scope:** Stripe unless explicitly scoped
```

---

## Related

- [market_thesis.md](market_thesis.md) — ranked backlog
- [readyforrobots-ux.md](readyforrobots-ux.md) — design system
- `app/services/plan_entitlements.py` — source of truth for gates
