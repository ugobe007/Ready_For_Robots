# FIND from signals

**Status:** proposal. This does not change `docs/buyer_opportunity_spec.md`. Bob approves before any code uses it.

FIND rows are buyer opportunities: company × workflow × why now. A signal becomes a card only when that signal names the work. Bob decided on 2026-10-16, replacing the earlier "only an RFP or a pilot" rule: the signal tier sets the card's label and its rank. It does not decide whether a card exists.

The line that stays: a signal that names no workflow never becomes a card.

## Labels

Stronger label ranks above the weaker one. A company with both an RFP and a robotics hire is **Budget confirmed**.

| Label | What it takes | Rank |
|---|---|---|
| Budget confirmed | An RFP, or a funded pilot (`pilot_success`) | 1 |
| Building a robot team | A robotics hire whose text names a robot or an automation role | 2 |
| Watch list | Expansion, funding, or labor pressure, and nothing that names the work | no card |

RFP scope is type `rfp_posted`, `vendor_selection`, or `government_contract`, or text that says RFP, RFQ, RFI, request for proposal, or request for quote. A funded pilot in this cut is `pilot_success` only. A budget or capex line is funding, not a pilot.

A robotics hire is type `strategic_hire`, `job_title_signals`, `automation_leadership_hire`, `job_posting`, or `robot_job`, and the text names a robot, robotics, or an automation engineer, manager, or lead. That is the stored stand-in for "names the work." The text is not yet parsed into a workflow. A hire that names no workflow stays off the cards once that parse exists.

These never create a card. On a card that already exists they attach as why now. If the company has no card, the company sits on the watch list.

- Expansion: `expansion`, `expansion_facility_signals`, `scale_expansion`
- Funding, with no named work: `budget_allocated`, `capex`, `capex_financial_signals`, `funding_round`, `roi_documented`
- Labor pressure: `labor_shortage`, `labor_pain`, `labor_signal`. `labor_pressure` is the spec name; the stored rows use the three types above
- A robot installation (`robot_installation`) is a deployment. That workflow is committed and stays off the cards

Two signals that name different work are two cards. This is tighter than the approved spec's company-wide signal (workflow null, half weight).

## Who pays

Robot sellers pay: makers, dealers, integrators, and robots-as-a-service operators. A seller pastes a robot URL and sees the top 3 cards with the reasons, before signup. That is the free proof. They pay for the full ranked list for their robots, for an alert when a new RFP or a robotics hire matches one of those robots, and for the desk to work the list. RFPs have deadlines, so the alert is the thing a seller pays not to miss.

## How many cards, read on 2026-10-17

Same cut as before. Latest score at least 40. Keep a company when it has an RFP, a pilot, a robotics hire, expansion, funding, or an installation. Drop a company whose only one of those is `robot_installation`. That is **1,177** companies (1,174 on the previous read; three more have since entered the cut).

| Label | Companies | What the number is |
|---|---|---|
| Budget confirmed | 39 | 27 RFP, 12 pilot, overlap 0. Six of the 39 also have a robotics hire. The label stays Budget confirmed |
| Building a robot team | 177 | Robotics hire, and no RFP or pilot. The gross hire count is 183 |
| Cards a seller can act on | 216 | 39 + 177 |
| Watch list, no card | 961 | Inside the 1,177, nothing names the work. 859 have expansion, 237 have funding, 171 have a labor signal. Those overlap |

Of the 39 Budget confirmed companies, 21 have an expansion signal and 16 have a funding signal. Those attach as why now on the card.
