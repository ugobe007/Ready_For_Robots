# Job Cards

A Robot Job Card is the unit of value: named employer, workplace, work, qualification, open questions, and the task model this work needs. Anonymous users must see a card before signup.

## Sub-features

- `card-identity` shows employer / workplace / work (not Lead / Prospect).
- `card-qualify` stays Conditional until a site assessment and a named task model.
- `card-models` names the required task-model slot and lookups (OpenVLA, π0.5, GR00T).
- `card-select` checkboxes choose jobs for Next; there is no Next on the card.

## How to get to it (user POV)

- Complete FIND on `/` until step 02 `Here are its jobs`.
- Expand a row in the job list.
- Personalized `/jobs/:slug` still renders the same workspace.

## Driving it with verify-readyforrobots

Preconditions:

- Find-jobs drive returned at least one job title.
- Doctor still healthy.

- **List.** After FIND, the page heading includes `Jobs for your robot` and example jobs are capped at 5 before signup.
- **Expand.** Open a card. Employer and work are visible. Qualification is Conditional / pending robot — never a fake Qualified or invented FTE dollars.
- **API.** The find-jobs payload’s jobs may include `required_task_models`. When present, presence starts `unknown`. Do not invent “this SKU runs GR00T”.
- **Proof.** `python3 scripts/agent_verify.py drive --feature job-cards --evidence "$EVIDENCE"` plus `drive-find-jobs.json` titles. Browser: screenshot of an expanded card that shows employer + work.

## Gotchas

- Token price indexes and talent directories stay off the card.
- Chat LLMs are not warehouse/hospital policies.
- A match percentage is not a qualification.
- Empty `company_name` on requirement_v1 is a failed trust proof.
