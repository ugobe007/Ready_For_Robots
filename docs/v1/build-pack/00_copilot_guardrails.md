# Copilot Engineering Guardrails

Paste into project / agent instructions:

---

You are implementing an approved ReadyForRobots product specification.
Follow the canonical domain model. Preserve provenance and history.
Represent missing data as UNKNOWN. Keep Facility distinct from
Company. Keep Robotability distinct from Work Match. Treat jobs as
evidence of work, not direct robot leads. Keep extraction, scoring and
presentation logic separate. Version ontology, prompts and scoring
models. Create immutable Prediction Snapshots. Add tests before
changing decision logic. Surface known blockers explicitly. Prefer
deterministic rules over unnecessary LLM calls.

Do not invent product features, CRM functionality, automated outreach,
email sequencing or generic lead scores. Do not collapse facilities
into accounts. Do not convert UNKNOWN into false/zero. Do not present
inference as fact. Do not delete historical labor signals. Do not
overwrite Prediction Snapshots. Do not hide conflicting evidence. Do
not create unsupported ROI numbers. Do not infer labor shortage from
one posting. Do not treat a forklift keyword as proof of
autonomous-forklift fit. Do not change ontology IDs after release. Do
not change scoring thresholds without regression evaluation.

When requirements are ambiguous, flag the ambiguity rather than
inventing behavior.

API/DB truth states and priorities use **lowercase** values from
`docs/v1/openapi-v1.yaml`. Prefer OpenAPI path names
(`/robot-analyses`, …) over blueprint aliases. Prefer
`docs/v1/data_model.md` table names when the blueprint diverges.

Execution backlog: `docs/v1/build-pack/`. Implement only the sprint you
were assigned.

---

## Scoring PR checklist

```text
[ ] Golden harness executed (attach reports/calibration/*)
[ ] Riviana-class forklift positives still rank high
[ ] Tugger/AMR-only workflow still rejects forklift when expected
[ ] Mixed Material Handler remains partial — not full replacement — when expected
[ ] No UNKNOWN silently flipped to known/pass
[ ] model/prompt/ontology versions recorded on AI outputs
```
