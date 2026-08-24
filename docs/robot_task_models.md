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

The expanded Job Card stays short:

1. Employer, workplace, work
2. **Which task model this work needs** (slot + unknown/present/absent)
3. **Three model links** (VLA / Isaac / OEM weights with URLs — not surveys, talent, or price maps)
4. Why it is listed, **three** open questions, next step = site assessment

Qualify-a-candidate filters and pricing lookups stay in the ontology for a later workflow step. Do not dump them on the posting.

If presence is unknown, qualification is **conditional**, not Qualified.

## Where we look

| Kind | Destination |
|------|-------------|
| OEM runtime | Skill / fleet / clinical / scrub / inspection packs sold with the machine |
| Open weights | [Hugging Face robotics](https://huggingface.co/models?pipeline_tag=robotics), [OpenVLA](https://huggingface.co/models?search=openvla), [LeRobot](https://huggingface.co/lerobot) |
| Surveys | [Argo-Robot manipulation FMs](https://github.com/Argo-Robot/foundation_models) (ACT, Octo, OpenVLA, Helix), [Robocloud robotics FMs](https://robocloud-dashboard.vercel.app/learn/blog/foundation-models-robotics) |
| Benchmarks | [Papers with Code robot manipulation](https://paperswithcode.com/task/robot-manipulation) |
| GitHub | [foundation-models topic](https://github.com/topics/foundation-models) / Awesome lists — weights often land here first |
| Training data | [Robotic Data](https://roboticdata.com/) — Physical AI traces (LiDAR, human/task). Not a site-qualified policy. |
| Sim-to-real | NVIDIA Isaac / GR00T; [World Labs real-to-sim-to-real](https://www.worldlabs.ai/blog/real-to-sim-to-real) (SceniX) — train/eval in reconstructed scenes |
| Talent | [Mercor](https://www.mercor.com/) — people who train/fine-tune/host the policy. Not SIGNAL buyers. |
| Labs | Physical Intelligence π-series |

**Not a lookup for this job:** GPT, Claude, Gemini, Llama, Mistral as *the* warehouse or hospital policy. Those are chat/VLM APIs. Search **VLAs** (OpenVLA, Octo, LeRobot, ACT) or an OEM pack.

## How we qualify a candidate

Once 3–4 candidates exist, filter:

1. **Task family** — robot policy / VLA / OEM pack, not a chat LLM
2. **Commercial license** — research-only CC cannot place paid work
3. **Compute footprint** — on-robot / edge often needs small or quantized policies (~<8B) or the OEM stack; cloud VLMs are not the cell
4. **Context** — long video/SOP vs a pick cell (a 1M-token window is not a motor policy)
5. **Site qualification** — a downloaded checkpoint is not qualified on this workplace until that site says so

## Where we find price

Do not scrape or invent dollars. Point at:

| Source | What it prices |
|--------|----------------|
| [BenchLM](https://benchlm.ai/llm-pricing) | Pay-per-token / image APIs |
| Vertex Model Garden, Amazon Bedrock, Azure AI Foundry, [Databricks FM APIs](https://docs.databricks.com/gcp/en/machine-learning/foundation-model-apis/) | Managed API list prices |
| [Axe Compute physical AI stack](https://axecompute.com/physical-ai-compute-stack/) | Why robot policies cost more than LLMs (sim + synthetic data + VLA train + always-on inference) |
| OEM application quote | Task pack for this SKU — usually not list-priced |
| Integrator SOW | Custom cell / fixture program |

Token price ≠ OEM warehouse pack price ≠ GPU hours to train a site policy.

## Spine

Extends, does not replace:

`COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → EMBODIMENT → TASK MODELS / LEARNED SKILLS → WORKFLOWS → JOB REQUIREMENTS → MATCH`

Hardware Fit (embodiment vs job physics) is separate from Intelligence Fit (public trained tasks vs job skills). Deployment readiness is their product with Environment Fit. See [`robot_task_intelligence.md`](robot_task_intelligence.md).

Never: `company → category → jobs`.  
Never: `robot has arms → warehouse jobs`.

## Out of scope this cycle

- A storefront that sells models
- Pretending public LLMs are site-qualified hospital/warehouse policies
- Ranking jobs by a model-vendor partnership
- SIGNAL / Cal surfaces

Ontology: [`ontology/ROBOT_TASK_MODEL_ONTOLOGY.md`](../ontology/ROBOT_TASK_MODEL_ONTOLOGY.md)
