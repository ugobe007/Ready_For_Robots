# Robot Job Ontology

**Purpose:** describe a unit of real-world work at a real place, and the terms on
which a robot may (or may not) match it. A robot job is:

```
COMPANY + WORKSITE + PHYSICAL WORKFLOW + REQUIREMENTS + EVIDENCE + UNKNOWNS + COMMERCIAL STATE
```

Code: `app/data/robot_job_match_corpus.json` (corpus rows),
`app/data/robot_job_requirements_gold.json` (gold requirements),
`app/services/robot_requirement_match.py` (evaluation).

## Job object

| Field | Meaning | Code |
|-------|---------|------|
| `company_name` | Employer / buyer at the worksite | `company_name` |
| `locality` / worksite | Where the work happens | `locality`, `path`, `industry` |
| Physical workflow | The work-physics family | `tape_family` (see [workflow ontology](ROBOT_WORKFLOW_ONTOLOGY.md)) |
| Requirements | Capabilities/constraints the work needs | `requirements[]` (`id`, `necessity`, `state`) |
| Evidence | Text/source grounding the work | `text`, `source`, gold spec |
| Unknowns | Constraints not established | `unknowns[]`, requirement `UNKNOWN` states |
| Commercial state | Buyability / deployment stage | `enums.v1.json::opportunity_states`, `commercial_maturity` |

## Match evaluation

For a given robot profile, each job requirement is evaluated against the robot's
**derived capabilities**:

| Requirement state | Meaning |
|-------------------|---------|
| `MATCHED` | Capability grounded and satisfies the requirement |
| `LIKELY` | Satisfied via a **named derivation** only (e.g. AMR class ⇒ indoor nav) |
| `UNKNOWN` | Job or robot value not established — preserved, never guessed |
| `UNMET` | Required capability is absent ⇒ hard reject |

**Verdict** (`_verdict`):
- any required `UNMET` → `NOT_A_MATCH`
- else any required `MATCHED`/`LIKELY` → `POSSIBLE_MATCH`
- else → `INSUFFICIENT`

No match percentage. No robot-type → family shortcut. Every `POSSIBLE_MATCH`
explains **why** (grounded capabilities), lists **still-unknown**, and surfaces
**blockers**.

## Ranking (among POSSIBLE_MATCH only)
1. Required capabilities satisfied (filter, not score)
2. Greater **distinctive-capability utilization** (not generic mobility)
3. Fewer critical unknowns
4. Stronger job evidence (named site / gold spec)

## Zero-state honesty
When no jobs match, the reason is classified truthfully (insufficient robot
evidence vs. no compatible jobs vs. corpus gap) — the UI never blames the corpus
for an under-extracted robot. See `docs/lead_quality_north_star.md` and the
Understanding freeze notes.

## Confidence flows through
Job-side and robot-side states use the same vocabulary
(`EXPLICIT`/`DERIVED`/`LIKELY`/`UNKNOWN`/`CONFLICTED`) — a `LIKELY` capability can
only produce a `LIKELY` requirement (via a named derivation), never a `MATCHED`.
Graph edges additionally carry a `truth_state`
([`enums.v1.json`](enums.v1.json), [`rfr_graph.v1.json`](rfr_graph.v1.json)):
`inferred → oem_verified → customer_confirmed → site_verified →
deployment_verified` (or `disproved`).
