# Mission: Reach 100 companies with an open robot-relevant RFP

**Date:** 2026-10-17
**Agent:** MarketIntel
**Status:** brief
**Type:** research

## Goal

A Budget confirmed card is an RFP or a funded pilot. This mission is only the RFP half of that label. Today the index holds **27** companies with an RFP-shaped signal (same cut as `docs/find_from_signals.md`: latest score at least 40, inside the 1,177). The target is **100 companies with an open robot-relevant RFP**. Robotics hires are a separate card, Building a robot team, and are not part of this 100.

This brief lists where those solicitations are public, which ones we can read legally, and what each source is likely to add. No ingest code in this mission.

An RFP is robot-relevant when the notice itself names a robot, an AMR, or automation equipment for a physical workflow (cleaning, delivery, inspection, warehouse, kitchen, farm, jobsite). A generic janitorial or IT notice does not count.

## What “open” means

The 27 are signals already stored on companies. They are not a census of solicitations that are open today. A same-day census of open US public notices that name a robot is likely well under 100. The way to 100 companies is a rolling set: open now, or closed within the last 12 months and still inside a buying window. Counts below are estimates, not a scrape.

## Sources

| Source | What it is | Legal to read | Expected yield |
|---|---|---|---|
| SAM.gov Contract Opportunities | Federal notices. We already call the API. The current personal key is 10 requests per day (`SAM_GOV_DAILY_REQUEST_LIMIT`). A role on the key raises that. | Yes. The public API is the machine path. | About 5–25 open robot-relevant notices at once. Over a year, on the order of 30–80 companies. Not 100 by itself. |
| State central bid boards | Cal eProcure, Texas ESBD, Florida VIP, New York Contract Reporter, Illinois BidBuy, and the other states' central portals. | Yes for notices posted without a login. They are public records. Use the portal's export or API when it has one. Do not bypass a login or a captcha. | A large state might have 0–3 open robot-relevant bids. All 50 states, maybe 15–40 open, and on the order of 40–80 companies over a year. Some are the same notice as SAM when the money is federal. |
| City and county portals | PlanetBids, BidNet Direct, OpenGov Procurement, PublicPurchase. Large cities and counties post here. | The listing is usually public. Attachments sometimes need a free vendor account, which is a normal registration, not a bypass. Bulk automation is often against the site terms; read the public search. | Across the 50 largest cities, maybe 10–30 open robot-relevant notices, many already on the state board. Over a year, on the order of 30–60 companies after deduping. |
| Transit agencies | Procurement pages of the largest systems (LA Metro, BART, WMATA, CTA, MTA, and peers). | Yes. The notices are public. | Few. Maybe 0–5 open (cleaning, inspection, yard vehicles). About 10 companies over a year. |
| Airports | Airport-authority procurement, often on the city's portal. | Yes when the notice is public. | Few. Maybe 0–5 open (floors, security, baggage). About 10–15 companies over a year. |
| Public universities and community colleges | Usually the state board, sometimes a campus purchasing page. | Yes for public institutions. Private universities often do not post. | Little that the state board does not already have. About 10–20 extra companies over a year. |
| Hospital systems | County and public hospitals post on the state board or SAM. Private systems (large nonprofits and chains) usually do not publish an open RFP. | Public notices, yes. A private portal behind a customer login is not a source for this mission. | Low. Under 10 open public notices that name a robot. Not a path to 100. |
| School districts | Public, often PlanetBids or the state board. Mostly janitorial and food service. | Yes for the public listing. | Robot-relevant notices are rare. Under 10 companies over a year. |

## How the yields add up

Adding the rolling-year estimates and then removing the same notice posted in two places (SAM and a state, a city and its state) lands near 100 companies, not comfortably above it. A single day's open set is more likely 30–70. The 27 already in the index are the floor, not a verified open count.

Order to read, if a later mission writes code: SAM.gov first (API, already in the product), then the state boards that publish an export, then city portals with a public search. Transit, airports, universities, hospitals, and school districts are mostly the same documents on those boards. They are not eight separate crawls.

## Acceptance

- [x] This brief lists the candidate public sources, which are legal to read, and an expected yield for each
- [ ] No scraper, no schema change, no database write
- [ ] A later mission, after Bob says so, turns the first source into stored RFP signals that can open FIND rows

## Out of scope

- Changing `docs/buyer_opportunity_spec.md`
- Treating a robotics hire or an expansion as a row
- Logging into a private bid room, or getting around a paywall, captcha, or access control
