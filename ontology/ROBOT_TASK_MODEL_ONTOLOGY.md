# Robot Task-Model Ontology

**Product term:** task model  
**Internal nickname only:** “certificate” — never use in UI, APIs, or customer copy.

A **task model** is the trained policy / skill pack that makes a robot actually perform a **specific physical job**. It is not the robot SKU, not morphology, and not a generic “AI brain.”

```
HARDWARE  →  CAPABILITIES  →  TASK MODELS  →  WORKFLOWS  →  JOB REQUIREMENTS  →  MATCH
```

Hardware says the machine *can* move and grasp. A task model says it *knows this job* (this warehouse pick, this hospital linen run, this CNC fixture).

## Why this exists

A robot company can sell a machine that is physically able to enter a workplace and still be **unqualified** for the work because nobody trained or licensed the policy for that task.

Distributors and integrators usually sell platforms. They under-invest in **task-specific models**. Buying or training those models is expensive. That gap is the qualification hole ReadyForRobots must name on every Robot Job.

## What we store per job

| Field | Meaning |
|-------|---------|
| `id` | Slot id (`warehouse_pick_place_policy`) |
| `label` | Human name of the required policy class |
| `physical_task` | The work the policy must perform |
| `vertical` | Operating environment |
| `presence` | `unknown` until evidence names a model on this candidate |
| `where_to_look` | Places to find a model (OpenVLA, π0.5, GR00T N1.5, OEM store, HF checkpoints, Argo survey) — **lookups, not fake listings** |
| `qualify_filters` | VLA vs chat LLM, commercial license, on-robot compute, context, site qualification |
| `pricing_lookups` | BenchLM token index, cloud FM APIs, physical-AI compute, OEM quote, integrator SOW — **no invented dollars** |

We do **not** invent “Robot X has NVIDIA GR00T N1.5 for job Y.” Presence starts as `unknown`. We do identify **which slot the job needs** and **where a practitioner would search**.

Chat LLMs (GPT, Claude, Gemini, Llama) are named only as a **counterexample**. Search families: OpenVLA, π0.5, Octo, LeRobot, ACT, GR00T. Canonical project pages: [OpenVLA](https://openvla.github.io/), [π0.5](https://www.pi.website/blog/pi05), [GR00T N1.5](https://research.nvidia.com/labs/gear/gr00t-n1_5/).

## Match rule

- Missing hardware capability → `UNMET` (already true).
- Hardware present, task model `unknown` → job stays **conditional**. Open question: which model covers this work, and where is it published?
- Task model `absent` after evidence → not qualified, even if the arm/base is fine.
- Never a match percentage.

JSON: [`task_model_ontology.v1.json`](task_model_ontology.v1.json)  
Product: [`docs/robot_task_models.md`](../docs/robot_task_models.md)
