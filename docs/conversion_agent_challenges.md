# Conversion agent challenges

Standing directive for **ProductSurface**, **FrictionMiner**, and **PipelineHealth** agents.

**PMF context:** ReadyForRobots is the **automated sales pipeline for robot companies**. See [product_market_fit.md](product_market_fit.md). Every mission should ask:

> *Does this help a robot OEM/integrator sign up, automate their funnel, and get value in native CRM or HubSpot?*

Funnel question: *Does this reduce friction from casual browse → signup → first saved lead → pipeline motion?*

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
| 1 | **Pricing → signup wiring** — no dead-end toasts; honest free-workspace copy until Stripe | ProductSurface | ✅ Done 2026-06-23 |
| 2 | **Entitlement honesty** — UI tier names match `plan_entitlements.py` | ProductSurface + backend | ✅ Done 2026-06-23 |
| 3 | **Post-auth landing** — default `next` is `/pipeline`, not `/profile` | ProductSurface | ✅ Done 2026-06-23 |
| 4 | **Save-limit upgrade moment** — modal at 5/5 saves with `/pricing?reason=saved_leads` | ProductSurface | ✅ Done 2026-06-23 — AlertDialog on pipeline save |
| 5 | **Locked research teaser** — free signed-in users see blurred Pro research block | ProductSurface | ✅ Done 2026-06-23 |
| 6 | **CTA continuity** — every marketing button does something (`PipelinePreview`, header mobile) | ProductSurface | ✅ Done 2026-06-23 |
| 7 | **Context-preserving signup** — `?next=` on Signals, Results, Pipeline deep links | ProductSurface | ✅ Signals + header; Results already wired |
| 8 | **OAuth-first signup** — peak-intent pages emphasize one-tap Google | ProductSurface | ✅ Copy when `?next=` present |
| 9 | **Profile usage meters** — “3/5 leads saved · Free” + upgrade | ProductSurface | ✅ Done (entitlement-honesty) |
| 10 | **Dynamic social proof** — hero ticker + pipeline preview use live API counts | PipelineHealth | ✅ PipelinePreview summary fetch |

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

- [product_market_fit.md](product_market_fit.md) — canonical PMF statement
- [market_thesis.md](market_thesis.md) — ranked backlog
- [readyforrobots-ux.md](readyforrobots-ux.md) — design system
- `app/services/plan_entitlements.py` — source of truth for gates
