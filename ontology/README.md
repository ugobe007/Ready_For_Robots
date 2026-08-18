# ReadyForRobots Ontology Library

Five linked ontologies + one inference-rules file. Together they encode the
**one rule the copilot must never break**:

```
COMPANY
  → PRODUCT
    → CONFIGURATION
      → HARDWARE
        → CAPABILITIES
          → WORKFLOWS
            → JOB REQUIREMENTS
              → MATCH
```

And **never**: `company name → robot category → jobs`.

A robot's capabilities belong to a **specific product/configuration** grounded in
**hardware/evidence** — not to the company name and not to a morphology label.
"AMR" does not mean "cannot manipulate." "Humanoid" does not mean "can palletize."

## Files

| File | Ontology | Answers |
|------|----------|---------|
| [`ROBOT_ENTITY_ONTOLOGY.md`](ROBOT_ENTITY_ONTOLOGY.md) | Entity | Company → Product → Configuration → Components |
| [`ROBOT_HARDWARE_ONTOLOGY.md`](ROBOT_HARDWARE_ONTOLOGY.md) | Hardware | What physical parts are present? |
| [`ROBOT_CAPABILITY_ONTOLOGY.md`](ROBOT_CAPABILITY_ONTOLOGY.md) | Capability | What actions can it perform? (incl. manipulation hierarchy) |
| [`ROBOT_WORKFLOW_ONTOLOGY.md`](ROBOT_WORKFLOW_ONTOLOGY.md) | Workflow | What real jobs-of-work does it do? |
| [`ROBOT_JOB_ONTOLOGY.md`](ROBOT_JOB_ONTOLOGY.md) | Job | Company + worksite + workflow + requirements + evidence |
| [`ROBOT_VERTICAL_ONTOLOGY.md`](ROBOT_VERTICAL_ONTOLOGY.md) | Vertical | Operating environments (warehouse, healthcare, eldercare, hospitality, …) |
| [`ROBOT_INFERENCE_RULES.md`](ROBOT_INFERENCE_RULES.md) | **Rules** | How to infer capabilities from hardware — rules, not vibes |

## Confidence vocabulary (flows end-to-end)

Every fact, capability, and match carries a state from this closed set:

| Label | Meaning | Code (`epistemic` / requirement state) |
|-------|---------|----------------------------------------|
| `EXPLICIT` | Directly stated by the manufacturer | `explicit` |
| `DERIVED` | Logically inferred from grounded hardware/facts | `strongly_inferred` |
| `LIKELY` | Strongly suggested but incomplete | matcher `LIKELY` (named derivation) |
| `UNKNOWN` | Not enough evidence | `unknown` |
| `CONFLICTED` | Contradictory evidence | `contradicted` |

`EXPLICIT` and `DERIVED` are **GROUNDED** (matcher-visible). `LIKELY` is only
allowed via a named derivation. `UNKNOWN`/`CONFLICTED` never assert a capability.

## Machine-readable companions (loaded by the pipeline)

The Markdown files above are the human/copilot spec; these JSONs are the
**loadable, enforced** form used by the scraping/parsing → derive → match
workflow via `app/services/robot_ontology.py`:

- [`capability_ontology.v1.json`](capability_ontology.v1.json) — capabilities, their grounding predicates, distinctive/generic flags, confidence vocab, manipulation hierarchy. **The matcher sources its `DISTINCTIVE_CAPABILITIES` / `GENERIC_CAPABILITIES` from here.**
- [`workflow_ontology.v1.json`](workflow_ontology.v1.json) — work families → required capability.
- [`hardware_ontology.v1.json`](hardware_ontology.v1.json) — fact/hardware predicates the parser may ground.
- [`vertical_ontology.v1.json`](vertical_ontology.v1.json) — operating environments / verticals (healthcare, eldercare, hospitality, …). The extractor emits `operating_environment` = a vertical key.
- [`inference_rules.v1.json`](inference_rules.v1.json) — structured R1–R21 with status.

Pre-existing companions:
- [`primitives.v1.json`](primitives.v1.json) — frozen WORK primitive codes (IDs never renamed).
- [`enums.v1.json`](enums.v1.json) — truth states, maturity, source types, vendor roles (loaded by `app/domain/enums.py`).
- [`rfr_graph.v1.json`](rfr_graph.v1.json) — WORK-centric knowledge + truth graph.

**Loader:** `app/services/robot_ontology.py` (fail-open — a missing/invalid file
falls back to baked-in defaults that mirror the code). **Sync gate:**
`tests/test_robot_ontology.py` fails if the ontology JSON drifts from the live
derive capabilities, matcher families/sets, confidence states, or predicates —
so updating the ontology is meaningful and safe.

## Where the ontology lives in code

| Ontology | Implementation |
|----------|----------------|
| Entity | `app/models/robot_catalog.py` (`manufacturers → robot_families → robot_models → robot_configurations`); in-flight `app/services/robot_understanding_v1/models.py` |
| Hardware / Capability facts | `app/services/robot_understanding_v1/facts.py`, `app/services/robot_inference_engine.py` |
| Capabilities (derived) | `app/services/robot_capability_derive.py` |
| Workflow / Job requirements / Match | `app/services/robot_requirement_match.py`, `app/data/robot_job_match_corpus.json` |
| Subject scoping (no sibling leakage) | `app/services/robot_understanding_v1/sources.py` + `facts.py::_evidence_names_sibling_sku` |

> **Status legend used throughout:** ✅ implemented · 🟡 partial · ⬜ planned.
> These docs describe the target ontology *and* honestly mark what the engine
> grounds today, so the copilot has rules — not aspirations.
