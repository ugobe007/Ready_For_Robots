# Pricing plans — billing proposal

Status: Founding seller and Pro checkout are wired for Stripe **test mode**. Live checkout for them stays off until Bob sets `STRIPE_SELLER_PLANS_LIVE=1`. The RFP plan is still proposal only.

## Plans to show

| Audience | Plan | Price | What it includes |
| --- | --- | --- | --- |
| Robot sellers | Free | $0 | 1 robot. Top 3 opportunities, with reasons. |
| Robot sellers | Founding seller | $49/month | Up to 5 robots. Full ranked list. Live RFP alerts. The desk. Price locked while that subscription is active. |
| Robot sellers | Pro | $199/month | More robots and users. Deployment help. |
| Robot employers | Free | $0 | Post a robot job. This must stay available with no paid plan. |
| Robot employers | RFP | $149/month | Publish an RFP. Qualified sellers with evidence: match score, deployments in this workflow, runtime and setting fit, service coverage. |

## What “locked while subscribed” means

A founding subscription is created at $49/month. That Stripe price stays on the subscription until it is canceled. Canceling ends the lock. A new subscription later uses the price on the site at that time.

## Do not reuse the current Stripe products

Checkout today accepts `pro` and `premium` only (`app/services/stripe_billing.py`, `VALID_TIERS`). The config payload still displays `pro` at $49 and `premium` at $129. Those products are the old lead plans. The new founding plan is also $49, but the entitlement is different (5 robots, full list, RFP alerts, desk), so it needs its own Price. The new seller Pro is $199, not the old $49 Pro and not the old $129 Premium.

New tiers sit beside the old ones; the old price IDs are not reused:

| Tier slug | Plan | Env var |
| --- | --- | --- |
| `founding` | Founding seller, $49/month | `STRIPE_PRICE_FOUNDING_SELLER` |
| `seller_pro` | Pro, $199/month | `STRIPE_PRICE_SELLER_PRO` |
| (not wired) | Employer RFP, $149/month | `STRIPE_PRICE_EMPLOYER_RFP` |

`scripts/stripe_create_seller_prices.py` creates the two seller prices with a test key and prints the env lines. It refuses live keys.

Checkout for `founding` and `seller_pro` runs when the Stripe key is a test key, or on a live key once `STRIPE_SELLER_PLANS_LIVE=1`. Both tiers count as paid in `plan_entitlements.py`. Free plans have no Price.

## Existing subscriptions on the old plans

Old `pro` ($49) and `premium` ($129) stay valid tiers so current subscribers keep access and their Stripe price. Proposal: grandfather. Do not move anyone's subscription. If a grandfathered Pro subscriber wants the Founding seller plan, they switch in the Stripe portal by choice, at the same $49.

## Entitlements to enforce later

- Seller free: one watched robot, and only the top three opportunities, each with its reasons.
- Founding seller: up to five robots, the full ranked list, live RFP alerts, and the desk.
- Seller Pro: a higher robot cap and more than one user. The caps are not set yet. Deployment help carries the AI-analysis disclosure (`client/src/lib/disclosure.ts`).
- Employer free: `POST` a robot job on `/?visit=candidates` with no plan check. A missing or unpaid subscription must not block this.
- Employer RFP: publish an RFP and show the four evidence fields. Publishing an RFP is the paid action. Posting a job is not.

## Not in this change

No Fly secrets set. No webhook changes. No schema. No subscription changed. The RFP card still says checkout is not open.
