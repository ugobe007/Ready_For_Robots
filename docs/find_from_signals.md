# FIND from signals

**Status:** proposal. This does not change `docs/buyer_opportunity_spec.md`. Bob approves before any code uses it.

FIND rows are buyer opportunities: company × workflow × why now. A signal becomes a row only when that signal names the work. A company with two signals that name different work gets two rows. A signal that does not name work never opens a row.

## What creates a row

The signal text has to say what the work is. Three kinds do that:

| Kind | When it names the work |
|---|---|
| RFP scope | Type is `rfp_posted`, `vendor_selection`, or `government_contract`, or the text says RFP, RFQ, RFI, request for proposal, or request for quote |
| Robotics role | Type is `strategic_hire`, `job_title_signals`, `automation_leadership_hire`, `job_posting`, or `robot_job`, and the text names a robot, robotics, automation engineer, automation manager, or automation lead |
| Pilot description | Type is `pilot_success` |

The workflow on the row is the work that signal names. The other signals for that company and that work stay on the row as why now.

## What never creates a row

These add to why now on a row that already exists. If the company has no row, they stay on the company and FIND does not show them.

- Funding, with no named work: `budget_allocated`, `capex`, `capex_financial_signals`, `funding_round`, `roi_documented`
- Expansion, with no named work: `expansion`, `expansion_facility_signals`, `scale_expansion`
- A robot installation (`robot_installation`) is a deployment. That workflow is committed and stays off the cards
- Labor pressure still cannot open a card on its own (`docs/buyer_opportunity_spec.md` §5)

This is tighter than the approved spec's company-wide signal (workflow null, half weight). On FIND, a company-wide funding or expansion note is not a buyer row.

## How many of the 1,174 get a row

Read-only cut, same companies as the earlier count. 2,026 companies whose latest score is at least 40. Strongest signal is A, then B, then C, then D. A–D is 1,222. Drop the 48 whose only D signal is `robot_installation`. That leaves 1,174.

Of those 1,174, **212** have at least one signal that names the work, so each would get at least one FIND row. **962** would not. A company can match more than one kind:

| Naming signal | Companies inside the 1,174 |
|---|---|
| RFP scope | 27 |
| Robotics role | 179 |
| Pilot description | 12 |
| At least one of those | 212 |

The 962 with no row include 865 that have an expansion signal and 237 that have a funding signal. Those sets overlap. They would show up on FIND only after some other signal names the work, and then only as why now.
