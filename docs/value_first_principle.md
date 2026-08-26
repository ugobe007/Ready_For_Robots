# Value-First Principle — ReadyForRobots

**Users do not buy unless they see value.** Every agent mission and product change must prove outcomes before asking for signup, save, or upgrade.

**Last updated:** 2026-08-22

---

## Core rule

> **Show → Believe → Act → Pay**

Never lead with account creation or pricing when the user has not seen a Robot Job Card.
The signup wall belongs **after** Job Cards, **in front of** the CRM desk. See [jobs_crm.md](jobs_crm.md).

---

## What "value" means

| Moment | User thinks | We must show |
|--------|-------------|--------------|
| **Anonymous Jobs** | "Is this real work?" | A Robot Job Card: employer, workplace, work being performed |
| **Card expanded** | "Would I send a robot here?" | Requirements, open questions, site assessment as next step |
| **URL scan** | "Does this fit my machine?" | Explainable qualification (✓ / △ / ✕), never a % |
| **Free signup** | "Did signing up change anything?" | 5 unlocked jobs in CRM |
| **Upgrade ask** | "Is Pro worth it?" | Watching more SKUs / more jobs — after they have kept 3 |

Proof is **jobs for the robot**, not a HOT buyer or outreach draft.

---

## Value ladder (do not skip rungs)

```
1. PROOF (anonymous, no account)
   Live pipeline · pitch action · robot SKU · sample outreach draft

2. CAPTURE (free account)
   Save lead · copy draft · 50-lead workspace · HubSpot connect option

3. AUTOMATION (Pro)
   Cited research · unlimited saves · HubSpot auto-sync · kanban motion

4. TEAM (Premium)
   Priority coverage · strategy prompts · support
```

**Agent rule:** Optimize rung 1–2 before rung 3–4. Paid conversion without activation is churn.

---

## Anti-patterns (kill these)

| Anti-pattern | Why it fails |
|--------------|--------------|
| Signup wall before any lead detail | User cannot judge lead quality |
| "Activate SIGNAL" with no preview | Jargon; no demonstrated output |
| Pricing page as first CTA | No proof of pipeline motion |
| Truncated pipeline_action so short it looks generic | Destroys differentiation vs Explee |
| Empty pipeline / junk leads in demo | One bad row kills trust permanently |
| Upgrade modal before first save | User never felt free tier value |

---

## ProductSurface acceptance tests

Every build mission should pass at least one:

- [ ] Anonymous user can read a **full outreach draft** for a selected lead without signing up
- [ ] Copy/send/save gates signup with **`?next=`** back to the same lead
- [ ] Signup page restates **what they unlock** (not generic "create account")
- [ ] First signed-in session shows **save + copy** within two clicks of landing
- [ ] Upgrade prompts appear **after** a completed free-tier action (save, research teaser click)

---

## Metrics (value before revenue)

Track weekly in mission `outcome.md`:

| Metric | Meaning |
|--------|---------|
| Anonymous pipeline → lead selected | Proof engagement |
| Anonymous → draft section viewed | Outreach value seen |
| Anonymous → signup start from pipeline | Value converted to intent |
| Signup → first save within 24h | Activation |
| First save → copy draft | Workflow value |
| Save limit hit → pricing click | Earned upgrade moment |

---

## Relation to PMF and conversion docs

- [product_market_fit.md](product_market_fit.md) — **what** we sell (automated pipeline)
- [conversion_agent_challenges.md](conversion_agent_challenges.md) — **funnel** mechanics
- [competitive_positioning.md](competitive_positioning.md) — **why us** vs data tools
- **This doc** — **when** to ask for signup/payment (only after proof)

---

## Agent priority (re-ranked)

When choosing missions, prefer:

1. **Value proof for anonymous users** — outreach preview, full pitch actions, live data
2. **Activation** — first save, copy draft, HubSpot path
3. **Earned upgrade moments** — after free value consumed
4. **Pipeline trust** — junk/cache only when it blocks proof
5. **Lead quality depth** — supports proof, not a substitute for it
