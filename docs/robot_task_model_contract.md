# Task-model contract — how robot companies buy and train policies

**Audience:** OEM, distributor, integrator, RaaS  
**Product language:** task model (never “certificate” in UI)  
**Status:** Canonical for QUALIFY (2026-08-25)  
**Does not:** invent dollars, sell a model storefront, or treat chat LLMs as warehouse/hospital policies

Robot companies and distributors usually sell **hardware**. The job is performed by a **trained policy**. This page is the contract they should walk before quoting a placement.

```
FOUNDATION VLA  →  TASK LIBRARY (skill pack)  →  SITE-ADAPTED POLICY  →  THIS JOB
```

Hardware capability is not enough. Qualification stays **conditional** until a named pack covers this work on this workplace.

---

## 1. Classification (ontology)

ReadyForRobots stores three **layers**, not one “AI brain.”

| Layer | What it is | Who trains it | Typical time |
|-------|------------|---------------|--------------|
| **Foundation VLA** | Generalist policy (OpenVLA, π0.5, GR00T, Octo, ACT, LeRobot) | Lab / OEM | Months to years. Not the distributor’s job. |
| **Task library / skill pack** | Specific libraries for specific tasks: warehouse pick, hospital linen, floor scrub, kitchen dish | OEM application store | License + install: days to ~2 weeks. Not greenfield training. |
| **Site-adapted policy** | This floorplate, SKU mix, fixture, SOP | Integrator, OEM field, customer ops | 2–8 weeks typical; 4–12 weeks for CNC, clinical, or kitchen |

Yes — **models have specific libraries for specific tasks.** A warehouse pick pack is not a hospital linen pack. A floor-scrub coverage program is not a restroom program. Do not transfer a DC AMR stack into a hospital corridor and call it qualified.

Chat LLMs (GPT, Claude, Gemini, Llama) are **not** a layer in this stack. They do not pick cases.

Machine-readable: [`ontology/task_model_ontology.v1.json`](../ontology/task_model_ontology.v1.json) (`model_layers`, `training_time_bands`, `data_contract`, `pricing_contract`).

---

## 2. What the robot company / distributor must do

Walk these steps on every Robot Job. Costs sit on the last two; skipping them is how a sold robot fails the work.

1. **Name the slot** — which physical task (pick, nav, tend, linen, scrub, kitchen).
2. **Ask the OEM** which **task-library pack** they ship for this SKU class. Get the license terms (commercial vs research-only).
3. **Budget the site-adapted layer** — integrator SOW or OEM field. Do not assume the pack runs on day one.
4. **Collect the data contract** (below) before promising a date.
5. **Qualify on this workplace** — a Hugging Face checkpoint is not qualified until the site says so.
6. **Write the field-data clause now** — traces usually improve the OEM’s library, not the customer’s invoice.

### Training time (honest bands, not a promise)

| Situation | Expect |
|-----------|--------|
| License an existing OEM pack, map the floor, smoke test | **Days to ~2 weeks** |
| Fine-tune when demo traces already exist | **1–4 weeks** |
| Collect demos, fine-tune, evaluate on this cell | **2–8 weeks** |
| Custom fixture, clinical SOP, or kitchen menu | **4–12 weeks** |
| Train a foundation VLA from scratch | **Months to years** — not a channel quote |

If someone says “the robot will learn the job in a weekend,” they are selling the chassis, not the policy.

---

## 3. Data the robot company must provide (model contract)

The SKU URL is not training data. For the site-adapted layer, bring:

| You provide | Examples |
|-------------|----------|
| **Site map / layout** | CAD, BIM, fleet map, aisle widths, keep-out zones |
| **Work objects** | SKU list, tote/case dimensions, payload, fixture drawings, menu/dish mix |
| **Demonstration traces** | Teleop or human video of the successful task — hours of episodes, not a brochure |
| **Failure cases** | Drops, collisions, occlusions, night-shift lighting, wet floors |
| **SOP and safety envelope** | Who shares the aisle, infection-control rules, e-stop, payload limits |

You do **not** owe a foundation-VLA pretrain corpus. That is the lab/OEM layer.

---

## 4. How these models are priced

Do not invent dollars. Point at who writes the quote:

| Layer | How it is priced |
|-------|------------------|
| Foundation VLA | Research weights often free; commercial use needs a license. Not a distributor line item. |
| Task library | OEM quote: per robot, per site, or per fleet. Rarely a public list price. |
| Site-adapted | Integrator SOW — often the **largest** line. Channel partners who only resell hardware leave this unpaid. |

Token API indexes (BenchLM, Bedrock, Vertex) price **chat/VLM APIs**. They are not OEM warehouse-pack prices and not GPU hours for a cell policy. See lookups in the ontology (`pricing_lookups`).

### Field training and discounts

**No automatic rebate.** In-field traces usually make the OEM’s library better. The customer’s invoice drops **only if the contract says so** (data-for-license, reduced support, or a written rebate).

Do not promise “the robot will get cheaper as it learns.” Ask for that clause before the pilot.

---

## 5. What we show on the Job Card

Short. No price indexes.

- Which task model the work needs (slot + unknown/present/absent)
- **To place this job:** layer, who trains, typical time, data you provide
- Field traces do not automatically reduce the model price
- Three VLA project links (OpenVLA, π0.5, GR00T N1.5)

Qualify filters and dollar lookups stay in the ontology for a later step.

Related: [`docs/robot_task_models.md`](./robot_task_models.md) · [`ontology/ROBOT_TASK_MODEL_ONTOLOGY.md`](../ontology/ROBOT_TASK_MODEL_ONTOLOGY.md)
