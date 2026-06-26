# Value-First Principle — ReadyForRobots

**Users do not buy unless they see value.** Every agent mission and product change must prove outcomes before asking for signup, save, or upgrade.

**Last updated:** 2026-06-25

---

## Core rule

> **Show → Believe → Act → Pay**

Never lead with account creation, pricing, or "Activate SIGNAL" when the user has not yet felt a concrete win. Value is not marketing copy — it is **evidence in the product** within 60 seconds of landing.

---

## What "value" means for robot sales teams

| Moment | User thinks | We must show |
|--------|-------------|--------------|
| **Anonymous browse** | "Is this real?" | Live HOT lead + company name + score + **pipeline_action** + **robot types** |
| **Lead selected** | "Would I send this?" | **Cal outreach draft** tied to their signal (subject + body preview) |
| **URL scan** | "Does this work for my ICP?" | Matched buyers with why-now, not empty results |
| **Free signup** | "Did signing up change anything?" | First save + copy draft + lead in workspace within one session |
| **Upgrade ask** | "Is Pro worth it?" | Blurred research they almost had, or save limit at 5/5 **after** they saved 5 |

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
