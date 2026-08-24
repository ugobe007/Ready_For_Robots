# Task models (job qualification)

**Status:** Canonical for QUALIFY (2026-08-24)  
**Surface:** Robot Job Card — FIND → QUALIFY. Not SIGNAL. Not Cal. Not a model marketplace.  
**Nickname (internal only):** people may say “certificates.” **Product language is task model.** Do not print “certificate” in UI.

---

## The hole

For each Robot Job the machine must perform a **physical task**. That task is executed by a **task model** — a trained policy or skill pack — not by the metal alone.

- Warehouse work needs warehouse pick / navigation policies.
- Hospital work needs clinical logistics policies (different SOP, different model).
- A humanoid or AMR can be **sold** into both rooms and still fail the job.

OEMs, distributors, and integrators often stop at “we sell this robot.” They do not budget for **task-specific models**. Those models are bought, licensed, or trained at high cost. ReadyForRobots must show that gap on the job, or qualification is a lie.

```
Robot SKU          →  can I physically be there?
Task model         →  can I do THIS work?
Channel (SI/dist)  →  can we commercially deliver both?
```

## Job Card contract

Every Robot Job must answer:

1. **What task models does this work require?** (slot + physical task)
2. **Where would you look for them?** (OEM runtime, foundation-robotics labs, Isaac, Hugging Face robotics — as search destinations)
3. **Does this candidate carry one?** (`unknown` until named evidence)

If (3) is unknown, qualification is **conditional**, not Qualified.

## Spine

Extends, does not replace:

`COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS → WORKFLOWS → JOB REQUIREMENTS → MATCH`

Never: `company → category → jobs`.  
Never: `robot has arms → warehouse jobs`.

## Out of scope this cycle

- A storefront that sells models
- Pretending public LLMs are site-qualified hospital/warehouse policies
- Ranking jobs by a model-vendor partnership
- SIGNAL / Cal surfaces

Ontology: [`ontology/ROBOT_TASK_MODEL_ONTOLOGY.md`](../ontology/ROBOT_TASK_MODEL_ONTOLOGY.md)
