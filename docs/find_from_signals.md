# FIND from signals

**Status:** proposal. This does not change `docs/buyer_opportunity_spec.md`. Bob approves before any code uses it.

FIND rows are buyer opportunities: company × workflow × why now. A signal becomes a row only when that signal names the work. Bob decided on 2026-10-16 that FIND is strict: only an RFP or a pilot opens a row.

## What creates a row

| Kind | When it names the work |
|---|---|
| RFP scope | Type is `rfp_posted`, `vendor_selection`, or `government_contract`, or the text says RFP, RFQ, RFI, request for proposal, or request for quote |
| Pilot description | Type is `pilot_success` |

The workflow on the row is the work that signal names. Two such signals that name different work are two rows.

## What never creates a row

These attach as why now on a row that already exists. If the company has no row, they stay on the company and FIND does not show them.

- Robotics hiring: `strategic_hire`, `job_title_signals`, `automation_leadership_hire`, `job_posting`, or `robot_job`, even when the text names a robot or an automation role
- Expansion: `expansion`, `expansion_facility_signals`, `scale_expansion`
- Funding, with no named work: `budget_allocated`, `capex`, `capex_financial_signals`, `funding_round`, `roi_documented`
- A robot installation (`robot_installation`) is a deployment. That workflow is committed and stays off the cards
- Labor pressure still cannot open a card on its own (`docs/buyer_opportunity_spec.md` §5)

This is tighter than the approved spec's company-wide signal (workflow null, half weight). On FIND, a company-wide funding, hiring, or expansion note is not a buyer row.

## How many of the 1,174 get a row

Read-only cut, same companies as the earlier count. 2,026 companies whose latest score is at least 40. A–D is 1,222. Drop the 48 whose only D signal is `robot_installation`. That leaves 1,174.

Of those 1,174, **39** have an RFP or a pilot, so each would get at least one FIND row. None of the 39 have both. **1,135** would not.

| Signal | Companies inside the 1,174 | Opens a row |
|---|---|---|
| RFP scope | 27 | yes |
| Pilot description | 12 | yes |
| Robotics hire | 179 | no — why now only |
| Expansion | 972 | no — why now only |
| Funding | 327 | no — why now only |

Of the 39 that get a row, 6 also have a robotics hire, 21 have an expansion signal, and 16 have a funding signal. Those attach as why now on the row the RFP or pilot opened.
