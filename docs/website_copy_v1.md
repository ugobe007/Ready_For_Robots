# Website Copy v1: readyforrobots.com

**Owner:** Bob Christopher · **Status:** draft for Bob's approval · 2026-10-14
**Location in repo:** `docs/website_copy_v1.md`
**Goal:** a robot seller understands in 5 seconds what RFR gives them, and nothing on the site promises more than the product does today.

Text in **[brackets]** is a decision for Bob. Everything else is final copy unless Bob edits it.

---

## 1. Rules for all site copy

1. **One audience on public pages: robot sellers** (makers, distributors, integrators). Buyers/employers get their own page later.
2. **Plain words only.** Use: *buyer, workflow, why now, robot job, example.* Never on public pages: SIGNAL, HEIR, HEIF, FIND, Cal, "Profile A/B/C", "SKU" (say "product"), "desk", raw field names (`pipeline_action`, `robot_types_needed`).
3. **No number in copy unless it comes from the database at render time.** If the query fails, hide the number; don't show a fallback.
4. **Nothing labeled "verified," "live," or "active" unless it has a source link.**
5. **Value before sign-up.** A visitor sees results for their robot before any sign-up or upgrade prompt.

---

## 2. Navigation

**Top nav (public):** `Find buyers` · `How it works` · `Pricing` · `Sign in` · button: `Get early access`

**Signed-in nav adds:** `My robots` · `Saved buyers`

**Footer:** About · Newsletter · Privacy · Terms · Support

**Hide from public nav and require sign-in or admin** (routes stay, links go): Lead Pipeline, Robot Ready / humanoid index, Intelligence & HEIR, RaaS ROI Engine, Marketplace, Social, Compare, Signals, Sales console/workflow, Supply pipeline, Vendor design builder.
**Remove from production builds:** `/icons`, `/icon-review`, `/experiment`.

---

## 3. Home page (`/`)

**Eyebrow:** Jobs for robots

**Headline:** Find the companies ready to hire your robot.

**Subhead:** Paste your robot's product page. We show which companies are moving to automate that work, and why now.

**Input placeholder:** Paste a robot product page, e.g. richtechrobotics.com/solutions/adam
**Button:** Find buyers →
**Below input (small):** Have a whole product line? Paste your homepage and pick a product.

**Three proof points (no numbers):**
- **By product, not by company.** Each robot you make does different work for different buyers. We match them one at a time.
- **Why now, with sources.** Every buyer comes with the evidence: RFPs, pilots, expansion plans, automation hiring.
- **Right work, right robot.** A drink station matches bars and cafés, not bussing. A pallet mover matches warehouses, not dining rooms.

**Example strip heading:** What a robot job looks like
**Example strip note:** These are examples. Paste your robot to see your matches.

**Remove from home:** "Employers: Find robots for your job," "Daily Newsletter" button (move to footer), "Verified Physical Work Feed," "Unlock Engineering Feasibility & Commercial Proposals," "generate turnkey commercial quotes."

---

## 4. How it works (`/how-it-works`)

**Headline:** From your robot to the buyers who need it

1. **Paste your product page.** We read it and classify your robot: what it is, the work it does, and the industries it serves.
2. **We find companies moving to automate that work.** Public RFPs, announced pilots and budgets, expansion plans, automation hiring, and other signs that a company is about to automate.
3. **You get buyer cards.** Each card shows the company, the work, why now (with sources), and which of your robots fit. Workflows a company has already automated are left out.

**What counts as a robot job:** work a robot can perform at a company that is moving to automate it. People may do that work today; the signal is the company's move toward automation.

---

## 5. Results page (after "Find buyers")

**Header:** Buyers for {Product name}
**Robot summary line:** {Form} · {Main work} · {Industries}, e.g. "Stationary drink station · Drink-making and serving · Restaurants, bars, hotels"

**Card fields** (spec §8): Company · Location · Industry / Work and status / **Why now:** up to 3 reasons, each with source and date / Matching robots

**Example cards (until real buyers exist for that robot):** amber badge **Example**, with this note at the top of the list:
> **Early access.** Cards marked Example show the kind of work your robot matches. Live buyers with sources are rolling out industry by industry, starting with warehouses and logistics.

**Empty state:**
> **No buyers yet for this robot.** We haven't found companies moving to automate this work yet. We'll keep looking. [Save this robot] to get notified.

**Remove from results:** the "How to use this feed" box, the duplicate "Open CRM" button, the repeated "Uncheck a row to skip it / Apply from the desk" text, "Profile C," "Company identity not fully verified," "Pending robot résumé," the sign-up wall after 3 cards.

**Save action (signed out):** "Save buyers" → sign-in prompt *after* the visitor has seen all results.

---

## 6. Pricing (`/pricing`)

Replace the three tiers until live buyer signals ship (spec Phase 5).

**Headline:** Early access
**Subhead:** Ready For Robots is in early access. Use it free while we roll out live buyer signals by industry.

**One card: Founding customer**
- Free during early access
- Buyer matches for every robot you sell
- Save buyers and get notified when new ones appear
- Founding customers lock in **[founding price, e.g. $X/month]** when live signals launch
- Button: **Get early access**

**Optional services** (keep as is, shorter): Help with setup, integration planning, and installation through vetted local partners. Scoped separately.

**Remove:** Basic / Pro / Premium tiers, "Activated Buyer Leads," "Managed Outreach & Meeting Agent," "Vault Contact Protection," HubSpot/Hunter auto-sync, the Reevo comparison and field names in the FAQ.

**FAQ (keep 3):**
- *Where do buyer signals come from?* Public procurement notices, company filings and announcements, news, and automation hiring at buyer companies. Every signal links to its source.
- *Do you sell contact lists?* No. We show which companies are moving to automate and why. Contact data comes later, opt-in.
- *What does early access cost?* Nothing. Founding customers lock in their price before launch.

---

## 7. About (`/about`)

**Headline:** Robots need jobs. We find the work.
**Body:** Ready For Robots helps robot makers and sellers find companies that are moving to automate work their robots can do. We classify robots product by product, track public signs that a company is about to automate (RFPs, pilots, budgets, expansion, automation hiring), and show sellers which company, which work, and why now.

**Remove:** stat tiles "Verified Buyer Leads," "Robot Models," "Active Open Trials," "Daily Action Signals" (until fed by the database, rule 3).

---

## 8. Newsletter (`/newsletter`)

**Headline:** The weekly robot jobs brief
**Subhead:** Which companies are moving to automate, which work, and which robots fit. One email a week.
**Remove:** "Live Market Intelligence," "42 Active Commercial Humanoid & AMR Trials Open," per-industry "Open Trials" counts, "1-Click RaaS Underwriting." **[Bob kept these claims earlier; this doc proposes removing them on this page. Confirm.]**

---

## 9. Implementation order

**PR A (now, small):** §2 nav, §3 home, §6 pricing, §7 About stat tiles, remove sign-up wall and dev routes. No backend changes.
**PR B (now):** §5 results copy and cleanup on the current flow.
**With spec Phase 5:** results switch to real buyer cards; §4 "How it works" goes live with the new flow.

*Accept (PR A + B):* a first-time visitor on mobile and desktop sees the new headline, can paste a robot URL without signing in, sees all results without a wall, and finds no banned words (rule 2) on public pages.
